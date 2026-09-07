# sched: dynamic: Simplify PREEMPT_DYNAMIC

## TL;DR

Mark Rutland 的 PREEMPT_DYNAMIC 简化系列（`[PATCH v2 0/6]`）当天整批进 `tip/sched/core`（6 个 commit，
CommitterDate 09:37:22~09:37:24 +02:00），从此 **`PREEMPT_DYNAMIC` 依赖 `ARCH_HAS_PREEMPT_LAZY`，
dynamic 可选模型只剩 `full` 与 `lazy`**。同一天下午 Jinjie Ruan 报出的后遗症就被修掉：`preempt_modes[]`
没跟着删掉 `none`/`voluntary`，导致 `preempt_model_str()` 在 backtrace 里打错串、
`/sys/kernel/debug/sched/preempt` 输出为空；Mark 18:16 发补丁，18:54 已合入（`ef9293b3b797`）。
另一条线索需要纠正二手结论：`[PATCH RESEND] sched: Move some scheduler fields to new static branch API`
**至今没有合入**；当日真正发生的是 Peter 因为把 Hongyan Xia 的作者串写坏成 `Hongyan Xia =0A=` 而 rebase，
**四条** commit 被重新通知（不是三条）。

## 背景与问题

`PREEMPT_DYNAMIC` 允许同一个内核在启动时用 `preempt=` 选抢占模型。随着 `none`/`voluntary` 不再作为
可选 dynamic 模型、`PREEMPT_LAZY` 成为 lazy/full 的分界，老实现里留下大量只为「某模型不可选」
服务的分支，以及 `HAVE_PREEMPT_DYNAMIC_{CALL,KEY}` 两套架构侧开关。本系列把这些收干净：
统一 `preempt_modes[]` 与访问器、删不可达代码、简化 `{cond,might}_resched()`、
`preempt_schedule*()`、`irqentry_exit_cond_resched()`。

同一天还 queue 了另一批「把调度器里 deprecated 的 `static_key_*` 换成带类型的 `static_branch_*`」
的独立补丁（Hongyan Xia、Vladimir Zapolskiy、Liang Hao），两批容易被混为一谈——本文的合入评估
把它们分开处理。

## 技术方案

PREEMPT_DYNAMIC 六连（Author 全部 Mark Rutland，Committer Peter Zijlstra，msgid 家族
`20260803191731.3244294-{2..7}-mark.rutland@arm.com`）：

| Commit | 标题 | 要点 |
|---|---|---|
| `d3d16750693b` | Make PREEMPT_DYNAMIC depend on ARCH_HAS_PREEMPT_LAZY | `kernel/Kconfig.preempt` 加依赖，`kernel/sched/core.c` 删 60 行不可达代码 |
| `88e0b3bb9930` | Simplify {cond,might}_resched() | |
| `b9d267b9d632` | Simplify preempt_schedule{,_notrace}() | |
| `aa4178f63847` | Simplify irqentry_exit_cond_resched() | |
| `5b9a28eeed37` | Remove HAVE_PREEMPT_DYNAMIC_{CALL,KEY} | 架构侧 CALL/KEY 两套开关合一 |
| `9650ce11f2e3` | Simplify preempt model accessors | 每个模型一个 `preempt_model_*()`；commit message 明说保留 `preempt_model_voluntary()` "for consistency"（`Suggested-by: Shrikanth Hegde`） |

回归修复 `ef9293b3b797`（发出 18:16:37 +08，CommitterDate 12:54:21 +02:00）：
`const char *preempt_modes[] = { "none", "voluntary", "full", "lazy", NULL }` 改为
`{ "full", "lazy", NULL }`；`sched_dynamic_show()` 里
`int i = (IS_ENABLED(CONFIG_PREEMPT_RT) || IS_ENABLED(CONFIG_ARCH_HAS_PREEMPT_LAZY)) * 2;`
加一段手工数组长度的逻辑整体删掉，换成 `for (int i = 0; preempt_modes[i]; i++)`。
`Fixes: 9650ce11f2e3`，`Reported-by: Jinjie Ruan <ruanjinjie@huawei.com>`，
Cc Mete Durlu / Peter Zijlstra / Shrikanth Hegde。

同一批进树但独立的 static key 迁移：`2a672daa4b27` sched_feat（union 包住 true/false 两种 key 类型）、
`a5576ebce920` paravirt_steal（9 个文件，含 arm64/loongarch/powerpc/riscv/vmware/kvm/xen）、
`879eaa76e608` do_balance_callbacks（去掉 `(void (*)(struct rq *))` 强转）、
`f549101187c8` dl timer（`ktime_us_delta(act, now) < 0` → `ktime_before(act, now)`）。

## 版本演进与当前进展

- v2 六封（`20260803191731.3244294-*`）→ 09-02 09:37 全部进 `tip/sched/core`。六个补丁均带
  `Reviewed-by: Shrikanth Hegde`、`Reviewed-by: Jinjie Ruan`、
  `Tested-by: Mete Durlu / Shrikanth Hegde / Jinjie Ruan`，这是它能整批快速 queue 的直接原因。
- 09-02 18:16 的 `ef9293b3b797`（v1 单补丁，约 38 分钟后合入）。Mark 当天 00:03/00:04 的两封回帖
  已经预告了这件事："I had left those lines to indicate that those modes were deliberately not
  selectable with preempt_dynamic. Evidently keeping them was confusing, so I'll delete them." 以及
  "We'll also need to fix up sched_dynamic_show()... This is all a bit messy, given the enum value isn't
  used to define the string array. I'll see if I can figure a way to make that consistent by
  construction, but that probably needs a bit more rework..."——即**「字符串数组与 enum 不共源」这个
  结构性问题当日并未解决**，只是把表面对齐。
- Jinjie Ruan 的另一条 `ARCH_HAS_PREEMPT_LAZY` 追问到 9/3（`75632`）仍在问
  "Hi Mark, What do you think?"，无人回答。
- 未合入的 `[PATCH RESEND] sched: Move some scheduler fields to new static branch API`：
  整个缓存（至 9/7）没有任何 tip-bot 通知；作者 8/20 的信里写明它依赖 Mark 的系列先落地。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra** 是本批唯一 committer。当日 15:54 与 16:32~16:33 对同一批补丁发了两次通知，
  起因是 Hongyan Xia 16:18（`73274`）：`d92d1a182dc2d5dc5e4418765739f56bcbde806a` 与
  `087b40fe5934e4b8aa80b29b3debbd6542756ffd` 两个 commit 把她的名字变成
  `Author: Hongyan Xia =0A= <hongyan.xia@transsion.com>`——"While =0A= is certainly a cute last name,
  I want to ask if this has anything to do with the Outlook fix you mentioned last time."
  Peter 16:19（`73283`）认账："Argh, sorry about that. Sometimes I fail to spot issues like this.
  Let me go rebase those patches and fix." 结果同一条子分支上的四个 commit 全部换 hash：
  `d92d1a182dc2→2a672daa4b27`、`087b40fe5934→a5576ebce920`、`6c10af7c5443→f549101187c8`、
  `4248f68fe26d→879eaa76e608`。
- **Jinjie Ruan（华为）** 同时是这批的 reviewer、tester 和回归的 Reported-by；
  **Shrikanth Hegde**、**Mete Durlu** 提供 Tested/Reviewed/Suggested。
  static key 那批各自拿到独立背书：paravirt_steal `Acked-by: Juergen Gross`，dl timer
  `Acked-by: Juri Lelli`。
- Hongyan Xia 对未合入那封的定位值得记录（8/20）："These two do conflict. Would be nice if Mark's
  patch gets merged first... this change here is a nice-to-have, not really deprecation. The trend is
  to move from untyped static_key_* variants to typed static_branch_* ones... That touches all archs
  and may need review from Xen folks."

## 合入评估

**likelihood: likely**（PREEMPT_DYNAMIC 六连 + `ef9293b3b797` 均已进 `tip/sched/core`，
事实完成）。相关的 static key 迁移四连同为 likely（已进树）。
**未合入的 static branch API 那封为 possible**：Mark 的系列已落地、冲突前提解除，但它仍缺 arch/Xen
侧评审，作者自己也定位为 nice-to-have。

卡点：
1. `preempt_modes[]` 与 `enum preempt_dynamic` 仍是两份定义，Mark 明说要做成 "consistent by
   construction" 但 "needs a bit more rework"，同类回归仍会复发。
2. `ARCH_HAS_PREEMPT_LAZY` 依赖所暴露的架构侧问题（Jinjie Ruan）无人应答。
3. rebase 之后，已经摘过 `d92d1a182dc2`/`087b40fe5934`/`4248f68fe26d`/`6c10af7c5443` 的下游
   必须换成新 hash。

## 效果评估

系列没有性能数字，性质是删分支与统一访问器；最大单点改动是 `kernel/sched/core.c` 删 60 行，
收益在可维护性与不可达路径。**可观测的行为变化有两处**：dynamic 模式下不再提供 `none`/`voluntary`，
因此 `/sys/kernel/debug/sched/preempt` 的候选列表改变（回归修复前输出为空，修复后只剩 `full`/`lazy`）；
以及一段时间内 panic/backtrace 里 `preempt_model_str()` 给出错误的模型名——任何依赖抢占模型字符串
做诊断或自测的脚本都需要跟进。

## 我可以参与的点

- 接手 Mark 未完成的 "consistent by construction"：让 `preempt_modes[]` 由 enum 派生
  （designated initializer 或宏表生成），从编译期消除这类错位；这是维护者公开承认还没做的重构。
- 回答 Jinjie Ruan 悬空的 `ARCH_HAS_PREEMPT_LAZY` 问题；若在 6.6/ARM64 上验过依赖关系可以直接回帖。
- Hongyan Xia 那封 static branch API 现在前置依赖已满足、缺的是 arch 侧评审，可按
  Xen/arm64/riscv/loongarch 分片帮 test/ack。
- 回背侧：OLK-6.6 若带 `preempt=` 接口测试，需要确认 `preempt_modes[]` 的长度假设与
  `sched_dynamic_show()` 输出格式；被 rebase 的四个 hash 要一并更正。

## 参考链接

- v2 系列（`[PATCH v2 0/6]`）各补丁 Message-ID：
  - https://lore.kernel.org/all/20260803191731.3244294-2-mark.rutland@arm.com/
  - https://lore.kernel.org/all/20260803191731.3244294-3-mark.rutland@arm.com/
  - https://lore.kernel.org/all/20260803191731.3244294-4-mark.rutland@arm.com/
  - https://lore.kernel.org/all/20260803191731.3244294-5-mark.rutland@arm.com/
  - https://lore.kernel.org/all/20260803191731.3244294-6-mark.rutland@arm.com/
  - https://lore.kernel.org/all/20260803191731.3244294-7-mark.rutland@arm.com/
- 回归修复：https://lore.kernel.org/all/20260902101637.232129-1-mark.rutland@arm.com/
- Mark 的两封解释性回帖：https://lore.kernel.org/all/apb3XyPKQVTVJqQx@J2N7QTR9R3.cambridge.arm.com/ （v2 6/6）
  ；https://lore.kernel.org/all/apb3naadvUkEJxGM@J2N7QTR9R3.cambridge.arm.com/ （v2 0/6）
- rebase 起因：https://lore.kernel.org/all/b61b830d-4c6f-4c35-8b8c-1adc4340aaed@transsion.com/ （Hongyan Xia）
  ；https://lore.kernel.org/all/20260902081955.GT4120091@noisy.programming.kicks-ass.net/ （Peter Zijlstra）
- 未合入的 static branch API（正文给出的链接）：https://lore.kernel.org/all/20260819081207.12150-1-hongyan.xia@transsion.com/
- 同批进树的其余三个：https://lore.kernel.org/all/20260819081312.12447-1-hongyan.xia@transsion.com/ （sched_feat）
  ；https://lore.kernel.org/all/20260819080159.105433-1-vz@kernel.org/ ；
  https://lore.kernel.org/all/20260816032643.44969-1-haohlliang@gmail.com/
- 相关：[[sched-20260903-007]]、[[sched-20260903-013]]、[[sched-20260905-004]]

---
id: sched-20260902-002
date: '2026-09-02'
subject: 'sched: dynamic: Simplify PREEMPT_DYNAMIC'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20260803191731.3244294-7-mark.rutland@arm.com>
lore_url: https://lore.kernel.org/all/20260803191731.3244294-7-mark.rutland@arm.com/
upstream_commit: ef9293b3b797228fead10b55ed6bfb99bb7976b4
fixes_commit: 9650ce11f2e3
merged_branch: tip/sched/core
current_version: v2
generated_at: '2026-09-07'
authors:
- Mark Rutland
maintainers_involved:
- Peter Zijlstra
- Shrikanth Hegde
- Jinjie Ruan
- Mete Durlu
- Hongyan Xia
- Juergen Gross
- Juri Lelli
patch_series:
- 'sched: dynamic: Make PREEMPT_DYNAMIC depend on ARCH_HAS_PREEMPT_LAZY'
- 'sched: dynamic: Simplify {cond,might}_resched()'
- 'sched: dynamic: Simplify preempt_schedule{,_notrace}()'
- 'sched: dynamic: Simplify irqentry_exit_cond_resched()'
- 'sched: dynamic: Remove HAVE_PREEMPT_DYNAMIC_{CALL,KEY}'
- 'sched: dynamic: Simplify preempt model accessors'
- 'sched: dynamic: Fix preemption model strings'
merge_assessment:
  likelihood: likely
  blocking_issues:
  - preempt_modes[] 与 enum preempt_dynamic 仍是两份定义，Mark 自陈 consistent-by-construction
    还需 rework，同类回归可能复发
  - Jinjie Ruan 关于 ARCH_HAS_PREEMPT_LAZY 依赖的追问到 9/3 仍无人回答
  - 同批 rebase 使 4 个 commit hash 作废，已摘旧 hash 的下游需要更换
  - '独立的 [PATCH RESEND] sched: Move some scheduler fields to new static branch API
    至 9/7 仍无 tip-bot 通知，缺 arch/Xen 侧评审'
  next_action: 跟进 preempt_modes[] 与 enum 共源的后续重构；把 static branch API 那封按 arch 分片推评审
contribution_opportunities:
- 把 preempt_modes[] 改为由 enum 派生（designated initializer 或宏表），从编译期消除数组/枚举错位
- 回答 Jinjie Ruan 悬空的 ARCH_HAS_PREEMPT_LAZY 问题，并给出 6.6/ARM64 上的依赖验证
- 为 Hongyan Xia 未合入的 static branch API 承担 arm64/riscv/loongarch/Xen 分片的 Tested-by/Reviewed-by
- OLK-6.6 回背核对：preempt= 接口测试对 preempt_modes[] 长度假设，以及 4 个被 rebase 的 hash 更正
source_email_count: 20
related_articles: []
tags:
- sched/core
- preempt
---
