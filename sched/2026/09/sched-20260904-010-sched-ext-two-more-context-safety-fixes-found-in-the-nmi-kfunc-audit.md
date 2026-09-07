# sched_ext: two more context-safety fixes found in the NMI kfunc audit

## TL;DR

Wanwu Li 把 sashiko 机器人挑起的 NMI kfunc 审计继续推下去，从「暴露给 `BPF_PROG_TYPE_TRACING` 的 any / idle / cid 三组 kfunc」里又找出两处上下文不安全，做成 2 补丁：`scx_locked_rq()` 在源头加 `in_nmi()` 判断、NMI 下返回 NULL，让三个 any 类 kfunc 一起落到非快速路径；idle CPU 搜索用的 per-CPU `per_cpu_unvisited` nodemask 从 `preempt_disable()` 改为 `guard(irqsave)()`。两处都是照 Tejun Heo 09-03 的明示做法。本日 Tejun Heo 回复「Applied 1-2 to sched_ext/for-7.4」，两片已进维护者树、目标 7.4。

## 背景与问题

两处问题都属于「kfunc 被允许在比预期更危险的上下文里执行」这一类，起因是 `e06ece82d7b0` 之后 sched_ext 的错误/退出路径已做成 NMI 安全，但 kfunc 成功路径自身的加锁没管。

1. `scx_locked_rq()`：三个 any 类 kfunc 会读 `scx_locked_rq()`，返回值非 NULL 就走「已持锁」的快速路径。但 any 类 kfunc 可被挂在 NMI 中运行的 tracing 程序调用，此时这个快速路径不安全。逐个 kfunc 加门禁被维护者否掉，改为在源头让它在 NMI 返回 NULL，三个调用方自然都走解锁路径。
2. idle 搜索的 per-CPU 暂存：`pick_idle_cpu_from_online_nodes()` 沿 online node 遍历节点时，把未访问集合放在 per-CPU 的 `per_cpu_unvisited` nodemask 里，只用 `preempt_disable()` 保护。而 `preempt_disable()` 不屏蔽中断，idle 类 kfunc 又可被开中断的上下文调用，于是同 CPU 上的嵌套调用会在外层仍在迭代该 mask 时用 `nodes_copy()` 覆写它，导致「a wrong node traversal and a wrong idle CPU pick」。

## 技术方案

- **1/2 `sched_ext: Make scx_locked_rq() return NULL from NMI`**：改动落在 `kernel/sched/ext/internal.h`（封面 diffstat：`internal.h +9`），在该 helper 里加 `in_nmi()` 并返回 NULL，因此不需要给三个调用方各自加保护——封面原话「This supersedes guarding them individually」。
- **2/2 `sched_ext: Protect the idle-search scratch nodemask with irqsave`**：`kernel/sched/ext/idle.c` 中把 `preempt_disable()` / `preempt_enable()` 换成一个 `guard(irqsave)()`，并在其上写明理由的注释；改动 12 增 2 删。
- 取舍：栈上分配 nodemask 同样能关掉这个竞态，但会把 diff 放大去修一个本身很少见的竞态（需要 per-node idle、`CONFIG_NUMA` 且真的跨节点搜索同时成立），所以选 irqsave 作为「针对实际触发上下文的最小修复」。
- NMI 情形故意不处理：没有从 NMI 调 `pick_idle` 的合法理由，且这样做不会崩机，作者原话 `"so such a caller is on its own"`。
- 系列整体 diffstat：`kernel/sched/ext/idle.c +14/-2`、`kernel/sched/ext/internal.h +9`，合计 21 增 2 删。

## 版本演进与当前进展

- 09-03 05:51 Tejun Heo 在 `[PATCH v2] sched_ext: Reject NMI calls to lock-taking kfuncs` 线程里给出这两条做法（`d84b31727f04e1ed0d40042ba1c09e61@kernel.org`）。
- 09-03 11:29 Wanwu Li 发出 `[PATCH 0/2]`（`20260903032953.659847-1-liwanwu@kylinos.cn`），11:57 发出 2/2。缓存中未拉到 1/2 的正文，该补丁内容只有封面转述。
- 09-04 02:42 Tejun Heo：`"Applied 1-2 to sched_ext/for-7.4. Thanks."` → 两片均已入维护者树，无 v2。
- 本日按 subject 匹配到 1 封邮件（该 apply 通报）。

## Maintainer 意见与讨论焦点

**Tejun Heo（sched_ext 维护者）既是方向给出者也是合入者**，两条意见在 09-03 就把实现位置定死了：
1. `"Let's add the in_nmi() test to scx_locked_rq() so that it returns NULL from NMI. That sends all three down their unlocked paths."` —— 否决「逐个 kfunc 加保护」，要求在公共谓词的源头改。
2. `"That probably needs to be irqsave'd. preempt_disable() doesn't mask IRQs either and the idle kfuncs can be called from IRQ-enabled contexts. As for NMI, if someone is calling pick_idle from NMI, they're asking for it. As long as the machine doesn't crash, it doesn't matter."` —— 明确修复边界：只补 IRQ，NMI 不管。

09-04 的 apply 通报即是对本系列的最终表态，无遗留异议、无 `Reviewed-by` 需要再收集。

**同期上下文**：这一对补丁的母系列（`Reject NMI calls to lock-taking kfuncs`）里曾有过一次方向之争——Andrea Righi 主张把会加锁/改状态的 kfunc 从 `scx_kfunc_ids_any` 拆出、只注册给 `BPF_PROG_TYPE_STRUCT_OPS`，在验证期就拒绝而不是在调度器路径上加运行时检查；Tejun 以 `"but it *is* useful to be able to e.g. kick a CPU or trigger reenq from a trace event, no?"` 反对，Andrea 随后接受运行时检查路线并给出 `Acked-by`，同时留下「也许应按 kfunc 逐个决定 tracing 可见性，而不是全部 any + 运行时检查」的后续议题。本对补丁正是这条「保留运行时检查」路线的延伸成本。

## 合入评估

likelihood: **likely**（已合入维护者树）。

依据：Tejun Heo 09-04 明确 `Applied 1-2 to sched_ext/for-7.4`，两个补丁一次通过、无人提异议，实现本身就是维护者指定的写法。

卡点：
- 只剩常规流程：`sched_ext/for-7.4` 需在 7.4 merge window 向主线发 pull。
- 从可见正文看 2/2 未附 `Fixes:` 标签（只有 `Suggested-by` + `Link:`），因此不会被自动派到 stable；对已发布内核而言要手工回合。
- 1/2 的完整实现细节（哪三个 kfunc、`internal.h` 具体判据）缓存中未拉到，若要引用需回 lore 核对。

## 效果评估

邮件中未提供效果数据。两处都是上下文安全修复，作者与维护者都没有给出 benchmark 或复现计数，apply 通报也未要求任何测试。可量化的信息只有规模与触发条件：2/2 为 12 增 2 删、系列合计 21 增 2 删；作者自述 2/2 的竞态需要 per-node idle、`CONFIG_NUMA` 与跨节点搜索同时成立，属少境情形，这也是选择最小修法而非栈上 nodemask 的理由。

## 我可以参与的点

- **可直接复用的审查手法**：per-CPU scratch 只靠 `preempt_disable()` 保护，是可批量搜索的反模式。内部树里凡是「per-CPU 暂存 + 可从中断开上下文进入的入口」都应核对是否需要 `irqsave`；cpuset/cgroup 相关的 cpumask 暂存尤其值得一并过一遍。这个审查不需要硬件、不需要 benchmark，且本邮件给了可引用的判例。
- **值得跟踪的机制点**：`scx_locked_rq()` 是「调用者是否已持 rq 锁」的谓词，一旦让它在 NMI 下返回 NULL，三个 any 类 kfunc 在 NMI 下的行为整体改变。任何内部实现里若有同类「按锁状态挑快路径」的 helper，都需要一并考虑 NMI/IRQ 上下文判定，而不是只在调用点加保护。
- **最小修复 vs. 干净修复的取舍可以直接引用**：作者明确论证了为何不用栈上 nodemask（放大 diff 去修一个罕见竞态不值），这类论证在内部评审里很好用。
- **回合可行性判断**：两片都很小且相互独立（`idle.c` 12 行、`internal.h` 9 行）。可操作动作是先确认内部树是否已引入 `pick_idle_cpu_from_online_nodes()` 与 `scx_locked_rq()`——若没有 sched_ext 的 sub-sched/idle 搜索路径，本对补丁没有回合对象；若有，则属低冲突回合项，且因缺 `Fixes:` 标签不会自动进 stable，需要自己排队。
- **可补的缺口**：apply 通报未要求测试，系列也没有 selftest。为 NMI/IRQ 上下文下的 kfunc 行为写一个 kselftest 覆盖（例如验证 `scx_locked_rq()` 在 NMI 返回 NULL 后调用方仍成功），是明确没人做的切入点。

## 参考链接

- 邮件线程：
  - `[PATCH 0/2]` 封面: <https://lore.kernel.org/all/20260903032953.659847-1-liwanwu@kylinos.cn/>
  - 2/2 补丁: <https://lore.kernel.org/all/20260903035754.722451-1-liwanwu@kylinos.cn/>
  - Tejun Heo 指定做法的邮件（2/2 的 `Link:`）: <https://lore.kernel.org/all/d84b31727f04e1ed0d40042ba1c09e61@kernel.org/>
  - Tejun Heo 的 apply 通报: <https://lore.kernel.org/all/7567d46cf1bbae3377b0c84aa5e4a030@kernel.org/>
- 相关文章/系列：
  - [[sched-20260903-003]] sched_ext NMI kfunc 审计后续修复（拒 NMI 拿锁 kfunc v3 + 两处 irqsave）。
- 相关代码/commit：
  - `kernel/sched/ext/idle.c` `pick_idle_cpu_from_online_nodes()`
  - `kernel/sched/ext/internal.h` `scx_locked_rq()`

---
id: sched-20260904-010
date: '2026-09-04'
subject: 'sched_ext: two more context-safety fixes found in the NMI kfunc audit'
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: 20260903032953.659847-1-liwanwu@kylinos.cn
lore_url: https://lore.kernel.org/all/20260903032953.659847-1-liwanwu@kylinos.cn/
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
current_version: v1
generated_at: '2026-09-07'
authors:
- Wanwu Li
maintainers_involved:
- Tejun Heo
patch_series:
- 'sched_ext: Make scx_locked_rq() return NULL from NMI'
- 'sched_ext: Protect the idle-search scratch nodemask with irqsave'
merge_assessment:
  likelihood: merged
  blocking_issues:
  - 无技术卡点，仅剩 sched_ext/for-7.4 向主线发 pull 的常规流程
  - 可见正文中 2/2 未附 Fixes 标签，不会自动派生 stable 回合
  - 1/2 补丁正文未拉到，具体涉及的三个 kfunc 名单需回 lore 核对
  next_action: 等待 7.4 merge window 的 pull 通报；如需内部使用，自行确认 pick_idle_cpu_from_online_nodes() 与 scx_locked_rq() 是否存在于内部树再排队回合。
contribution_opportunities:
- 批量排查 per-CPU scratch 仅靠 preempt_disable() 保护的可重入模式，尤其是 cpumask 暂存
- 为 NMI/IRQ 上下文下的 sched_ext kfunc 行为补 kselftest 覆盖
- 核对 scx_locked_rq() 改为 NMI 返回 NULL 后三个 any 类 kfunc 的解锁路径是否都正确
source_email_count: 1
related_articles:
- sched-20260903-003
tags:
- sched_ext
---
