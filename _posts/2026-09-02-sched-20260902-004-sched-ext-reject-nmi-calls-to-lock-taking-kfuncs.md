---
id: sched-20260902-004
date: '2026-09-02'
subject: 'sched_ext: Reject NMI calls to lock-taking kfuncs'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20260901095652.1009104-1-liwanwu@kylinos.cn>
lore_url: https://lore.kernel.org/all/20260902093611.52651-1-liwanwu@kylinos.cn/
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
current_version: v3
generated_at: '2026-09-07'
authors:
- Wanwu Li
maintainers_involved:
- Tejun Heo
- Andrea Righi
patch_series:
- 'sched_ext: Reject NMI calls to lock-taking kfuncs'
- 'sched_ext: two more context-safety fixes found in the NMI kfunc audit'
merge_assessment:
  likelihood: merged
  blocking_issues:
  - 无：v3 已于 9/3 applied 到 sched_ext/for-7.4，追加的 2 个上下文安全修复 9/4 也 applied
  - Andrea 提出的 per-kfunc tracing 可见性（STRUCT_OPS-only 集合）被明确挂起，未解决
  - scx_locked_rq() 的 in_nmi() 收敛与 idle kfunc 的 per_cpu_unvisited irqsave 仍是后续补丁
  next_action: 跟 scx_locked_rq() 后续补丁是否由作者发出；推动 per-kfunc 可见性清单化
contribution_opportunities:
- 把 lock-taking/state-changing kfunc 迁到 STRUCT_OPS-only 集合，做成 per-kfunc 可见性清单 RFC（Andrea
  的方向）
- 按 Tejun 指定实现 scx_locked_rq() 在 NMI 返回 NULL，一次解决 task_set_slice/dsq_nr_queued/locked_rq
  三处
- 为 per-node idle 扫描的 per_cpu_unvisited 补 irqsave 保护并给出 NUMA 机型验证
- 把「只靠 irq mask 保护的 per-CPU 状态在 NMI 下不可用」这一判据用于自研 kfunc 的体检
source_email_count: 8
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Reject NMI calls to lock-taking kfuncs'
layout: article
---

## TL;DR

`scx_kfunc_context_filter()` 把一批 sched_ext kfunc 开放给 `BPF_PROG_TYPE_TRACING`，而 tracing 程序可以
attach 到跑在 NMI 里的函数——于是 `scx_bpf_destroy_dsq()`、`scx_bpf_dsq_reenq()`、
`scx_bpf_cpuperf_set()` 这些内部拿 raw spinlock 的 kfunc 一旦在 NMI 中命中「被打断上下文已持同一把锁」
的 CPU，就会自旋到硬锁死。Wanwu Li 用一个 `scx_kf_allowed_ctx()` 统一在入口 `in_nmi()` 判并
`scx_error()` 退出。09-02 是 v2→v3 的收口日，**Tejun Heo 在 9/3 07:05 明确 "Applied to
sched_ext/for-7.4"**，并给出两处他自己的落地改动；作者顺手把审计继续做下去，9/3 又发 0/2 追两刀，
9/4 也被 applied。这是一条完整的「社区发现 → 维护者塑形 → 进树」闭环样本。

## 背景与问题

`e06ece82d7b0 ("sched_ext: Report NMI kicks with scx_error()")` 的封面已经描述过可达性："are callable
from tracing progs that can attach to functions running in NMI"，不巧就会 "could deadlock the machine"；
那次修的是 error/exit 路径（让 `scx_error()` 在 NMI 下安全，见 `f883dbb64ca5 ("sched_ext: Make exit
claiming lock-free")`）。**但那只封闭了每个 kfunc 的错误路径，没管成功路径上 kfunc 自己拿的锁。**
v3 正文给出完整危险表：

- `scx_bpf_destroy_dsq()` → `dsq->lock`
- `scx_bpf_dsq_reenq()` → rq 的 `deferred_reenq_lock`
- `scx_bpf_cpuperf_set()` / `scx_bpf_cidperf_set()` → `rq->lock`
- `scx_bpf_sub_grant()` / `scx_bpf_sub_revoke()` → pshard lock（共用 `sub_cap_preamble()`）
- `bpf_iter_scx_dsq_next()` / `bpf_iter_scx_dsq_destroy()` → `dsq->lock`

作者的定位是防御性的："As things stand, there is no scenario for reenqueueing, iterating a DSQ,
setting a performance target or granting sub-caps from NMI. The guards defend against a buggy or
malicious BPF program turning an 'any'-category kfunc into a machine-wide hard-lockup."

## 技术方案

所有点统一走新的 `scx_kf_allowed_ctx()`，复用 `scx_bpf_kick_cpu()` 已有的 `in_nmi()` 检查
（现在与 cid 版本 `scx_bpf_kick_cid()` 共用在 `scx_kick_cpu()` 里），"so the rule is stated once and
the coverage is auditable from one place"。有返回值的 kfunc 一律返回 `-EDEADLK`（Tejun 指定：
"`-EBUSY` suggests retrying would help. Let's use `-EDEADLK` which is what's being avoided."）。

iter 三件套只在 `bpf_iter_scx_dsq_new()` 拒一次，`next()`/`destroy()` 不再检查——因为 `kit->dsq`
留 NULL 时两者本就是 no-op（v1 的写法是三处都查）。只读成员（`dsq_peek`、`dsq_nr_queued` 等）
保持对 tracing 可见，不加固。

Tejun 落地时的最终形态（9/3 07:05 的 applied 消息里贴出）恢复了 inline + 宏包装：

```
static __always_inline bool __scx_kf_allowed_ctx(struct scx_sched *sch, const char *who)
{
        if (unlikely(in_nmi())) {
                scx_error(sch, "%s called from NMI", who);
                return false;
        }
        return true;
}
#define scx_kf_allowed_ctx(sch)     __scx_kf_allowed_ctx((sch), __func__)
```

## 版本演进与当前进展

v1 `70697`（9/1 17:56）→ Andrea 提替代方案 `72272` → Tejun `72313` 反驳 → Andrea `72339` **Acked-by**
→ Tejun 三条具体意见 `72404` → v2 `72742`（9/2 10:31）→ Tejun `73059` 三条 → v3 `73501`（9/2 17:36）
→ 作者继续审计 `74156`（9/2 21:48）→ Tejun `75364`（9/3 05:51）→ **Tejun `75523`（9/3 07:05）
"Applied to sched_ext/for-7.4 with the following changes"**。

改名也是评审产物：v1 的 `scx_kfunc_nmi_safe()` 被 Tejun 判定 "reads as if it's testing a property of
the kfunc"，改成 `scx_kf_allowed_ctx()` 以对齐 `scx_kf_allowed()`；v1 让每个调用点自己传 `@who`，
Tejun 要求改成宏包装传 `__func__`（v2/v3 一度把宏去掉，Tejun 在 applied 时说明
"'No need to wrap' in my v2 reply was about the line wrap of the function signature"，于是把 inline +
宏的形态又恢复回来）。他还顺手纠正描述里的一处概念错误："struct_ops don't run in task context (e.g.
ops.tick() runs from the tick interrupt). They just never run in NMI."

后续：作者 9/3 发 `[PATCH 0/2] sched_ext: two more context-safety fixes found in the NMI kfunc audit`
（`75824`），**Tejun 9/4 02:42 "Applied 1-2 to sched_ext/for-7.4."**（`77880`）。

## Maintainer 意见与讨论焦点

- **Andrea Righi（NVIDIA）** 提出的是更彻底的替代设计（`72272`）："we should prevent these kfuncs from
  being called by tracing programs altogether instead of adding runtime checks... move them out of
  `scx_kfunc_ids_any` into a separate set registered only for `BPF_PROG_TYPE_STRUCT_OPS`"，理由是
  "reject invalid programs at verification time, avoid the runtime overhead and make the API boundary
  explicit"。Tejun `72313` 的反对很具体："it *is* useful to be able to e.g. kick a CPU or trigger reenq
  from a trace event, no?" Andrea 让步并保留意见（`72339`）："Kicking a CPU, yes - scx_pair is actually
  using that. I'm less convinced about the reenq case... **Maybe we should decide tracing visibility per
  kfunc rather than exposing every 'any' kfunc and adding the runtime check to all of them. But this can
  be revised/improved later.** In the meantime this seems to fix a real issue and the approach looks
  correct, so: Acked-by"。→ 运行期检查先落地，**per-kfunc 可见性是明确挂起的后续**。
- **Tejun Heo** 的意见全部可执行（`-EDEADLK`、注释长度、命名、宏包装、iter 只在 `new()` 拒、
  `unlikely(!sch)`），并且他自己在 applied 时改回两处——典型的 maintainer 塑形案例。
- 审计未收口（`74156` 提出、`75364` Tejun 定调）：`scx_bpf_task_set_slice()` 与 `update_curr_scx()`
  对 `p->scx.slice` 的 RMW 竞争（sashiko 发现）、`scx_bpf_dsq_nr_queued()` 把 `SCX_DSQ_LOCAL`
  解错 rq、`scx_bpf_locked_rq()` 把被打断上下文的 rq 交给 BPF。Tejun 的方向："Let's add the
  `in_nmi()` test to `scx_locked_rq()` so that it returns NULL from NMI. That sends all three down
  their unlocked paths." 另一类是 `scx_bpf_pick_idle_cpu_node()`/`pick_any_cpu_node()` 在
  `pick_idle_cpu_from_online_nodes()`（`kernel/sched/ext/idle.c:151`）里写 per-CPU 临时 nodemask
  `per_cpu_unvisited`（idle.c:146），只有 `preempt_disable()` 保护 → NMI 会踩脏；Tejun 定性为
  "That probably needs to be irqsave'd... As for NMI, if someone is calling pick_idle from NMI,
  they're asking for it. As long as the machine doesn't crash, it doesn't matter."

## 合入评估

**likelihood: likely（事实已完成）**——v3 已于 9/3 进 `sched_ext/for-7.4`，追加的两个上下文安全修复
于 9/4 进同一分支。`scx_locked_rq()` 的 `in_nmi()` 收敛与 idle nodemask 的 irqsave 属后续补丁，
其中 idle 那一类 Tejun 已明说不急。

## 效果评估

无性能数据，也无需性能数据：作者与 Andrea 都同意这些路径**不存在合法 NMI 用例**，因此收益是消除一类
「有 bug 或恶意的 BPF 程序把 any 类 kfunc 变成整机 hard lockup」的攻击面，代价是每个 kfunc 入口一次
`unlikely(in_nmi())`。可审计性的提升是实在的：规则集中在一个宏里，覆盖面可以从一处核对。
需要留意的负向影响被 Tejun 一句话消解："The return value doesn't matter much as the scheduler is
being terminated."——拒绝即退出调度器，不影响正常调度路径。

## 我可以参与的点

- 接手挂起的 **per-kfunc tracing 可见性**方案（Andrea 的 STRUCT_OPS-only 集合）。它比现在的一刀切
  `in_nmi()` 更干净，但需要逐个 kfunc 判断「tracing 里到底有没有真实用例」，适合做成清单式 RFC。
- 按 Tejun 指定的方向把 `in_nmi()` 加进 `scx_locked_rq()`，一次解掉三个假阳性点；作者本人说了
  "I'll send a follow-up patch"（`75648`），先确认是否已发出以免撞车。
- idle kfunc 的 per-CPU nodemask 竞争是唯一被 maintainer 判为「不崩就行」的欠账；若要做 NUMA 感知的
  sched_ext 调度器，这条得在自有内核先补 irqsave 并回报上游。
- 自研参考：任何把自家 kfunc 暴露给 tracing 的子系统都适用同一判据——只靠 irq mask 保护的 per-CPU
  状态与 raw spinlock 在 NMI 下不可用。

## 参考链接

- v1：https://lore.kernel.org/all/20260901095652.1009104-1-liwanwu@kylinos.cn/
- v2：https://lore.kernel.org/all/20260902023124.1422942-1-liwanwu@kylinos.cn/
- v3（进树版本）：https://lore.kernel.org/all/20260902093611.52651-1-liwanwu@kylinos.cn/
- Andrea 的替代方案与 Acked-by：https://lore.kernel.org/all/apcsyS2j-N8j5-BN@gpd4/ ；
  https://lore.kernel.org/all/apc1XBAIV3AWQ3jt@gpd4/
- Tejun 的意见链：https://lore.kernel.org/all/apcx5yUysXEuEYAf@slm.duckdns.org/ 、
  https://lore.kernel.org/all/3a9bfba228c46c69408fe1ef392e60f0@kernel.org/ 、
  https://lore.kernel.org/all/49faaba5039a29f38ab6f254da6fb8dc@kernel.org/ 、
  https://lore.kernel.org/all/d84b31727f04e1ed0d40042ba1c09e61@kernel.org/
- applied 通知：https://lore.kernel.org/all/27793d61e70c3d4df415729e1d150ad0@kernel.org/
- 审计后续（作者 9/2 长贴、9/3 的 0/2、9/4 applied）：
  https://lore.kernel.org/all/1d5f2636-a5e3-4b67-bbb9-12922fa0d804@kylinos.cn/ 、
  https://lore.kernel.org/all/20260903032953.659847-1-liwanwu@kylinos.cn/ 、
  https://lore.kernel.org/all/7567d46cf1bbae3377b0c84aa5e4a030@kernel.org/
- 相关：[[sched-20260903-003]]、[[sched-20260904-010]]
