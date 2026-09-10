# sched/eevdf: fix rb augmented with multi fields

## TL;DR

本文为增量更新，缺陷成因与补丁的完整代码分析见 related_articles 中的 sched-20260908-004。09-09 这条单补丁拿到了 K Prateek Nayak 的 `Reviewed-by` + `Tested-by`，而且他说明自己 2025 年 2 月就撞上过同一个问题、当时是在调度器层面绕开的——这等于独立确认了缺陷真实存在且此前的绕行方案不如泛化 rb 模板。剩下唯一未处理的意见是一条注释 nit，作者当天 21:20 已承认「就是复制粘贴的结果」。

## 背景与问题

EEVDF 的运行树增广了三个字段（`min_vruntime`/`min_slice`/`max_slice`），但 `RB_DECLARE_CALLBACKS` 只支持一个 `RBAUGMENTED`，于是 `_copy` 与 `_rotate` 在树再平衡时只搬 `min_vruntime`。补丁把模板泛化成 `RB_DECLARE_CALLBACKS_MULTI`（由调用方提供一个 copy 函数），fair.c 里用 `min_vruntime_copy()` 一次拷三个字段，`Fixes: aef6987d8954`。这些在 09-08 那篇里已经拆开写过，本日无新增技术内容。

## 技术方案

同 09-08 那篇：`RB_DECLARE_CALLBACKS` 保留为单字段特例（自己生成 `_copy_single` 再转调 MULTI），因此其它增广树用户零改动。本日讨论没有触及方案本身，只有一条注释 nit（见下）。我在本地主线（`v7.0-rc5+` 树）核对过：`RB_DECLARE_CALLBACKS` 仍是单字段版本，`git log --grep='rb augmented with multi fields'` 无结果，即该修复尚未进主线，问题依旧存在。

## 版本演进与当前进展

- 09-08 21:55 v1（`<20260908135526.2783039-1-vincent.guittot@linaro.org>`），`include/linux/rbtree_augmented.h | 35 +++++---`、`kernel/sched/fair.c | 15 ++-`。
- 09-09 04:37 Prateek 给 `Reviewed-by` + `Tested-by`，并附带一条 nit。
- 09-09 21:20 作者回应该 nit，承认注释是复制粘贴的产物（即会删除）。无 v2 发出（截至当天邮件）。
- 无 tip-bot 收录，无 stable 回合。

## Maintainer 意见与讨论焦点

Prateek 的意见分三层，第一层信息量最大：

> I remember stumbling on this in `20250220093257.9380-22-kprateek.nayak@amd.com` but working around the problem in the scheduler layer instead. Generic rb-tree layer extension makes more sense.

也就是说这条缺陷不是纸面推演——他在 EEVDF 的上游化过程中就碰到过，当时的处理是在调度器层规避。这既独立佐证了症状，也回答了「为什么不只在 fair.c 里补」这个潜在的质疑。第二层是认可：直接 `Reviewed-by`/`Tested-by`。第三层是一条 nit：

> nit. Do we need this comment? It doesn't really describe the copy callback. The one over here above min_vruntime_update() makes sense and should suffice IMO.

正是我 09-08 那篇里点出的「`min_vruntime_copy()` 上方那段从 `min_vruntime_update()` 复制来的注释」。作者 21:20 回 "No, it was just the result of a copy/paste"，等于接受删除。

**仍未解决的**是 09-08 那篇列出的另一个问题：整条讨论里没有人给出可观测症状（哪个判定会偏、什么负载会暴露），Prateek 说"stumbling on this"但没有展开当时具体看到了什么。Peter Zijlstra 本日也未表态——`rbtree_augmented.h` 是公共头，理论上需要他或 rbtree 侧过一眼。

## 合入评估

`likelihood=high`。评审面已无异议：一位非作者身份的资深调度器贡献者给了 `Reviewed-by`+`Tested-by`，并说明自己在上游化过程中独立遇到过同一问题；作者是 EEVDF/fair.c 维护者；带明确的 `Fixes` 目标；唯一的意见是删一段注释且已被接受。

卡点纯是流程：还需要 Peter Zijlstra 收下（改动落在 `include/linux/rbtree_augmented.h`），以及配套的一次全树构建验证。至于「缺可观测症状」——Prateek 那句"stumbling on this... working around the problem in the scheduler layer"实际上部分补上了这块，因此它更可能影响的是被定级为 `sched/urgent` 还是走常规窗口，而不是能否合入。

## 效果评估

依然没有 benchmark，也没有修复前后对比数据。本日新增的证据只有一条定性陈述：Prateek 说他在 2025 年 2 月的 EEVDF 系列里遇到过并选择在调度器层规避（他给的链接是那一系列的第 22 封）。`Tested-by` 说明他在真实内核上验证过补丁不破坏行为，但邮件里没有给出任何量化偏差（例如哪些工况下 `cfs_rq_min_slice()`/`cfs_rq_max_slice()` 读数会错、错多少）。所以「修的是真 bug」有两人交叉印证，「修了会带来多大可观测改善」仍然是无数据的推断。

## 我可以参与的点

- `review`：现在最缺的是把公共头改动的验证做实——扫一遍全树其它 `RB_DECLARE_CALLBACKS*` 用户，确认有没有第二处「`RBCOMPUTE` 实际维护了多个字段却只声明一个 `RBAUGMENTED`」的同源缺陷。这个 bug 模式源于通用宏的设计，EEVDF 不必是唯一受害者，而且这个检查不需要任何硬件即可完成。
- `testing`：`Tested-by` 目前只覆盖了「不破坏」，还缺「确实修正了读数」。构造运行树频繁旋转的负载（不同 slice/权重实体反复入队出队，例如混合 `sched_latency` 与 cgroup 份额动态调整），比较打补丁前后 `cfs_rq_min_slice()`/`cfs_rq_max_slice()` 采样与实体 lag 分布；同时可以直接问 Prateek 当年在 `20250220093257.9380-22` 那里看到的具体症状是什么——那是全场唯一可能存在但没写出来的症状描述。
- `new_patch`：回合到自家分支时，这一条应与 09-07 的 `sched/eevdf: Fix augmented max_slice` 成对回合（两者共同维护「增广字段完整性」这一不变式）；若自家分支也带 `min_slice` 向 cgroup 层级传播的那条提交，`Fixes` 需引用自家分支的 commit 而非上游 `aef6987d8954`。

## 参考链接

- v1 邮件: https://lore.kernel.org/all/20260908135526.2783039-1-vincent.guittot@linaro.org/
- Prateek Nayak 的 Reviewed-by/Tested-by 与同源历史: https://lore.kernel.org/all/88404fc2-22e5-4792-9de3-ffce55e98055@amd.com/
- 作者回应复制粘贴注释: https://lore.kernel.org/all/CAKfTPtBqrSwD9Ccp9jYEmcT4+y83Zd-qhw-yRDd2Eoi32J4_BQ@mail.gmail.com/
- Prateek 当年在调度器层规避的那封（2025-02-20，EEVDF 系列 22/…）: https://lore.kernel.org/lkml/20250220093257.9380-22-kprateek.nayak@amd.com/
- `Fixes` 目标 `sched/eevdf: Propagate min_slice up the cgroup hierarchy`: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=aef6987d8954
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: "sched-20260909-008"
date: "2026-09-09"
subject: "sched/eevdf: fix rb augmented with multi fields"
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: "<20260908135526.2783039-1-vincent.guittot@linaro.org>"
lore_url: "https://lore.kernel.org/all/88404fc2-22e5-4792-9de3-ffce55e98055@amd.com/"
upstream_commit: null
fixes_commit: "aef6987d8954"
merged_branch: null
current_version: v1
generated_at: "2026-09-10T00:50:00"
authors:
  - "Vincent Guittot"
maintainers_involved:
  - "K Prateek Nayak"
patch_series:
  - version: v1
    msgid: "<20260908135526.2783039-1-vincent.guittot@linaro.org>"
    date: "2026-09-08"
    summary: "把 RB_DECLARE_CALLBACKS 泛化为 RB_DECLARE_CALLBACKS_MULTI（由调用方提供 RBCOPY），原单字段宏改为自动生成 _copy_single 后转调 MULTI；fair.c 新增 min_vruntime_copy() 同时搬运 min_vruntime/min_slice/max_slice。"
    review_outcome: "09-09 04:37 K Prateek Nayak 给 Reviewed-by+Tested-by，并说明他在 2025-02 的 EEVDF 系列中遇到过同一问题、当时在调度器层规避，认为泛化通用 rb 层更合理；另提一条 nit：min_vruntime_copy() 上方的注释未描述 copy 语义。作者 21:20 承认是复制粘贴结果。"
merge_assessment:
  likelihood: high
  blocking_issues:
    - "需 Peter Zijlstra 收下 include/linux/rbtree_augmented.h 的公共头改动，本日他未表态"
    - "唯一遗留意见是删除 min_vruntime_copy() 上方复制来的注释，作者已接受但当天未发 v2"
    - "仍缺可观测症状描述（哪个判定/统计会偏、什么负载会暴露），影响定级为 sched/urgent 还是走常规窗口"
  next_action: "作者发带注释修正的 v2 或 Peter 直接收取；有人补上可观测偏差证据"
contribution_opportunities:
  - kind: review
    description: "扫描全树其它 RB_DECLARE_CALLBACKS 用户，确认是否存在同样「RBCOMPUTE 维护多字段但只声明一个 RBAUGMENTED」的同源缺陷，无需硬件即可完成"
  - kind: testing
    description: "比对补丁前后 cfs_rq_min_slice()/cfs_rq_max_slice() 采样与实体 lag 分布，并向 Prateek 追问他在 20250220093257.9380-22 处实际看到的症状是什么"
  - kind: new_patch
    description: "与前一日的 sched/eevdf: Fix augmented max_slice 成对回合到自家分支以恢复增广字段完整性不变式，Fixes 引用自家分支 commit 而非上游 aef6987d8954"
source_email_count: 2
related_articles:
  - "sched-20260908-004"
  - "sched-20260907-001"
  - "sched-20260908-005"
tags:
  - "eevdf"
  - "cfs"
---
