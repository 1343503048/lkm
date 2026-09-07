---
id: sched-20260906-001
date: '2026-09-06'
subject: 'sched_ext: Fix keep-last for sub-scheduler tasks and two scx_qmap placement
  loops'
subsystem: sched
type: bug
status: merged_tip
severity: medium
thread_root_msgid: <20260905160958.1565156-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20260905160958.1565156-1-tj@kernel.org/
upstream_commit: null
fixes_commit: 88234b075c3f
merged_branch: sched_ext/for-7.3-fixes
current_version: v1
generated_at: '2026-09-07'
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
patch_series:
- version: v1
  msgid: <20260905160958.1565156-1-tj@kernel.org>
  date: '2026-09-06'
  summary: PATCHSET（4 片，基线 sched_ext/for-7.3-fixes 0a85182723b6，分支 sub-keep-last-rescue）：1/4
    dispatch_one() 中 sch 改名 root_sch（无功能变化）；2/4 两处 keep 决策改用 scx_task_sched(prev)
    的 ops.flags/bypass 并把 SCX_EV_DISPATCH_KEEP_LAST 计到该调度器，每次判定时重读 sched；3/4 scx_qmap
    的三处 rescue 插入不再加 needs_immed()；4/4 新增 avail_cids（ops.sub_ecaps_updated）与 usable_cids=self&avail，放置只按
    usable_cids、stranded 判定仍用 self_cids。diffstat +97/-40。
  review_outcome: 03:25 Andrea Righi 全系列 Reviewed-by（4/4 有保留意见但非 blocker）；06:25 Tejun
    回「Applied 1-4 to sched_ext/for-7.3-fixes with Andrea's Reviewed-by tags.」
- version: v1-followup
  msgid: <4c9a9c9cabc3547e23bae5ae00421a52@kernel.org>
  date: '2026-09-06'
  summary: '追加单片 sched_ext: scx_qmap: Fix pending partition work handoff：qmap 可能把
    partition work 留在无人执行的状态（effective-cap 回调在抢 part_busy 失败后才 publish、redistribute()
    在释放 part_busy 后才检查 pending）。改为请求先 publish、释放 guard 后再检查 pending，所有 holder（含 stats
    flush）都调 execute_partition() 排空，并用 PART_REFRESH/PART_REDISTRIBUTE 区分掩码刷新与重分区。Fixes:
    e9151ed5c944，Reported-by: Andrea Righi。'
  review_outcome: 22:02 Andrea Righi Reviewed-by；是否已 apply 到 for-7.3-fixes 本日邮件未获取到
merge_assessment:
  likelihood: likely
  blocking_issues:
  - 本系列已 apply 进 sched_ext/for-7.3-fixes，无技术卡点；追加的 handoff fix 已获 Reviewed-by，只差 apply
    确认
  - '本日邮件中未见向 Linus 的 pull 或 tip-bot 记录，进主线时点未获取到；也未见 Cc: stable，是否回合 stable 无法判断'
  next_action: 跟踪 sched_ext/for-7.3-fixes 的下一轮 pull request；若分支含 88234b075c3f 的 sub-scheduler
    抽象，评估把 2/4 的内核侧修复回合到 OLK-6.6
contribution_opportunities:
- kind: backport
  description: 排查自有分支里 dispatch_one() 的两处 keep 判定是否仍读 root 调度器的 SCX_OPS_ENQ_LAST/scx_bypassing；只要带了
    88234b075c3f 的 scx_task_sched() 语义就同样需要 2/4 这一处判定改动，并注意每次判定时重读 sched 而不是缓存指针
- kind: review
  description: 3/4 只在 scx_qmap 去掉了 RESCUE|IMMED 组合；扫一遍其它 example/自研 scheduler（含 scx_nitosis）是否还有同样的
    rescue 插入会被内核当成合法放置并 REENQ 弹回
- kind: testing
  description: 在打开 hierarchical sub-scheduling（e9151ed5c944）+ round-robin time-share
    下跑 scx_qmap，验证追加片修掉的 part_busy/part_pending handoff 是否还会出现 usable_cids 长时间 stale
source_email_count: 10
related_articles:
- sched-20260903-004
- sched-20260904-011
tags:
- sched_ext
title: 'sched_ext: Fix keep-last for sub-scheduler tasks and two scx_qmap placement
  loops'
layout: article
---

## TL;DR

Tejun 把 scx_qmap 当作 scx_nitosis 的 sub-scheduler 跑，暴露出 1 个内核侧 bug 和 2 个 scx_qmap 放置 bug：`dispatch_one()` 用 **root** 调度器的 `SCX_OPS_ENQ_LAST`/bypass 状态决定是否 keep 运行 `@prev`，而这两个属性其实属于 `@prev` 自己的调度器，判错时会把任务以 `SCX_ENQ_LAST` 塞给从未 opt-in 的调度器，触发 `put_prev_task_scx()` 的 `WARN_ON_ONCE` 且没有后续调度事件、可能 stall。4 片已于 09-06 06:25 被 Tejun apply 进 `sched_ext/for-7.3-fixes`（带 Andrea Righi 的 Reviewed-by）；Andrea 在 4/4 新代码里发现的第二个竞态，Tejun 当天追加 1 片修掉并已拿到 R-b。

## 背景与问题

cover letter 列出三类问题（0001-0002 修内核，0003-0004 修 scx_qmap）：

- **keep-last 归属错**：`dispatch_one()` 全程用 root 调度器做两个 keep 决策（有剩余 slice 的早退 keep、结尾的 keep-last）。root 设置了 `SCX_OPS_ENQ_LAST` 而 `@prev` 所属 sub-scheduler 没设置时，任务不被 keep，反而带 `SCX_ENQ_LAST` 入队到一个没 opt-in 的调度器 → `put_prev_task_scx()` 里 `WARN_ON_ONCE`；sub-scheduler 按普通任务排队、不再产生调度事件，任务可能 stall。
- **rescue insert 被 IMMED 变成合法放置**：qmap 的 stranded fallback 把「在自己所有 self cid 上都跑不了」的任务用 `SCX_ENQ_RESCUE` 压到第一个 allowed cid，若该 cid 是它持有的 time-share 还要加 `SCX_ENQ_IMMED`。结果内核看到 IMMED 就放行插入、跳过 rescue 转移；该 cid 的 CPU 忙 → 任务带 `SCX_ENQ_REENQ` 弹回 qmap → qmap 输入相同、重复插入，中间没有任何事情运行，最终撞上 reenqueue 上限、调度器以 `SCX_EXIT_ERROR_REENQ` 被 eject。触发面很宽：caps 在 `ops.sub_attach()` 之后才下发，而 per-cid effective caps 要等 bypass 解除后的第一次 dispatch 才上报，所以「首次入队就落在 time-share cid 上」的每次 attach 都会进这个环。
- **放置跑在 caps 生效之前**：qmap 只用 `ops.sub_caps_updated()` 推出的 `self_cids` 决定放置，这个视图领先于 CPU；`ops.update_idle()` 只在 BASE 生效后才有，idle 门控的放置只能靠早前持有的残留 idle bit 命中，而 highpri 扫描完全没有门控——在窗口期内往该 cid 的每次 highpri move 都被拒、带 `REENQ_CAP` 弹回，形成抖动。

## 技术方案

内核侧的核心是 2/4：两处 keep 判定改为对 `scx_task_sched(prev)` 读 `ops.flags` 与 bypass，`SCX_EV_DISPATCH_KEEP_LAST` 事件也计到该调度器；并且**每次判定时重新读取 sched**——中间的 dispatch 可能释放 rq lock，`@prev` 期间可能换 class 或换调度器。1/4 是纯改名（`sch`→`root_sch`），为 2/4 腾出命名空间，无功能变化。

qmap 侧：3/4 从三处 rescue 插入（`qmap_enqueue()` 的 stranded fallback、`scan_shared_dsq()` 中两处 `scx_bpf_dsq_move()`）去掉 `needs_immed()`，让插入回到 rescue 转移路径；4/4 新增 `avail_cids`（来自 `ops.sub_ecaps_updated()`）与 `usable_cids = self & avail`，放置判定改用 `usable_cids`，而 stranded 测试仍用 `self_cids`（它问的是「这个 split 是否给任务留了地方」），从而把「持有什么/委派什么」与「现在能不能在这 CPU 上跑」两个角色分开。

系列基线 `sched_ext/for-7.3-fixes` (0a85182723b6)，diffstat：`kernel/sched/ext/ext.c` 33 行、`tools/sched_ext/scx_qmap.bpf.c` 101 行、`tools/sched_ext/scx_qmap.h` 3 行（+97/-40）。

## 版本演进与当前进展

v1 一次成型，无重发，本日即完成 review 与 apply（时间均为 +08:00）：

- 09-06 00:09 Tejun 发出 PATCHSET（4 片，cover `<20260905160958.1565156-1-tj@kernel.org>`）。
- 00:40 Tejun 回复 Sashiko 对 4/4 的 race 报告，判定该竞态可接受。
- 03:24 Andrea Righi 在 4/4 子线程指出 `qmap_sub_ecaps_updated()` 的 busy/pending handoff 存在另一处竞态。
- 03:25 Andrea 给全系列 `Reviewed-by`，并说明 4/4 的保留意见「I don't think it's a blocker」。
- 06:25 Tejun：「Applied 1-4 to sched_ext/for-7.3-fixes with Andrea's Reviewed-by tags.」
- 06:53 Tejun 追加单片 `sched_ext: scx_qmap: Fix pending partition work handoff`（`Fixes: e9151ed5c944`、`Reported-by: Andrea Righi`），06:57 在 4/4 子线程回帖贴上链接。
- 22:02 Andrea 对该追加片回 `Reviewed-by`。是否已一并 apply，本日邮件中未获取到。

## Maintainer 意见与讨论焦点

- **Andrea Righi（Nvidia，09-06 03:25）**：全系列 Reviewed-by，唯一保留意见落在 4/4，且明确表示不阻塞。
- **Andrea Righi（09-06 03:24）**：给出 CPU0/CPU1 交错图，说明 `part_pending` 可能在 `part_end()` 之后才被置位、当下没有 owner 消费，`usable_cids` 会一直 stale 到下一次 `rr_advance()`/`redistribute()`：「It should self-correct, but a task may remain queued until another dispatch event.」并强调这是独立于 Sashiko 所报 transient `self_cids` 问题的另一件事。
- **Tejun Heo（09-06 00:40）**：对 bot 报告的 4/4 竞态采取「不改设计」的态度——「Yes, but scx_qmap is an example scheduler and the result is a spurious rescue insert, which isn't critical. The race is acceptable.」这条边界值得记录：example scheduler 里的良性竞态不被视为修复对象。
- **Tejun Heo（09-06 06:53）**：对 Andrea 的发现全盘接受并立刻修复，手法是「请求在抢 `part_busy` 之前 publish、释放 guard 之后才检查 pending」，让所有 holder（含 stats flush）都调 `execute_partition()` 排空，并把 `PART_REFRESH` 与 `PART_REDISTRIBUTE` 分开，使 effective-cap 更新只在确实请求重分时才重建 partition。
- 本线程未出现 David Vernet、Peter Zijlstra 等人的意见；无任何 NAK。

## 合入评估

`likelihood=likely`。依据：4 片已由维护者 apply 进 `sched_ext/for-7.3-fixes`（09-06 06:25），并带 Andrea 的 Reviewed-by；2/4 标注 `Fixes: 88234b075c3f ("sched_ext: Introduce scx_task_sched[_rcu]()")`，属 fixes 分支内容，随后随该分支进 Linus 树是常规路径。卡点：本系列已无技术卡点，追加的 handoff fix 也已获 R-b、只差 apply 确认。两点未获取到：本日邮件中没有 tip-bot / 向 Linus pull 的记录，也未见 `Cc: stable`，因此进入主线的具体时点与是否回合 stable 无法判断。对回合工作而言，真正的内核侧改动只有 2/4 的判定归属（1/4 仅改名），3/4、4/4 与追加片都在 `tools/sched_ext/`。

## 效果评估

邮件中未提供效果数据（无 benchmark、无 stall 计数）。作者给出的验证方式是「把 scx_qmap 作为 sub-scheduler 跑在 scx_nitosis 之下」复现出 `put_prev_task_scx()` 的 `WARN_ON_ONCE` 与潜在 stall。定性收益为三项：消除 sub-scheduler 场景下的误 WARN 与任务 stall、消除 qmap 因 reenqueue 上限被 `SCX_EXIT_ERROR_REENQ` eject、消除 highpri 任务在 caps 未生效窗口内被 `REENQ_CAP` 反复弹回的抖动。

## 我可以参与的点

- 回合排查：凡是分支里带了 `scx_task_sched[_rcu]`（88234b075c3f）这一层 sub-scheduler 抽象的，检查 `dispatch_one()` 两处 keep 判定是否仍读 root 的 `ops.flags`/`scx_bypassing(root_sch)`——这是本系列唯一的真实内核 bug，2/4 在 `kernel/sched/ext/ext.c` 上只有 +14/-9，适合直接照搬；同时确认在 `@prev` 可能换 class 的路径上没有缓存 sched 指针（必须每次重读）。
- 3/4 只修了 scx_qmap 一处模式，其它 example/自研 scheduler（含 scx_nitosis 自身）里 `SCX_ENQ_RESCUE | needs_immed()` 这类组合值得同样扫一遍，可提补丁或至少回报。
- 验证追加片：在打开 hierarchical sub-scheduling（e9151ed5c944）+ round-robin time-share 的配置下跑 scx_qmap，观察 `part_pending` 是否还会长时间无人消费（例如 caps 更新后 `usable_cids` 不刷新）。
- 关注 `git://git.kernel.org/pub/scm/linux/kernel/git/tj/sched_ext.git` 的 `sub-keep-last-rescue` 分支与 `for-7.3-fixes` 后续 rebase，判断何时适合跟进。

## 参考链接

- cover letter: https://lore.kernel.org/all/20260905160958.1565156-1-tj@kernel.org/
- 1/4 改名: https://lore.kernel.org/all/20260905160958.1565156-2-tj@kernel.org/
- 2/4 内核侧修复: https://lore.kernel.org/all/20260905160958.1565156-3-tj@kernel.org/
- 3/4 rescue IMMED: https://lore.kernel.org/all/20260905160958.1565156-4-tj@kernel.org/
- 4/4 caps in effect: https://lore.kernel.org/all/20260905160958.1565156-5-tj@kernel.org/
- Andrea 的全系列 Reviewed-by: https://lore.kernel.org/all/apxsw4KfJifR7qJx@gpd4/
- Andrea 的 part_busy/part_pending 竞态报告: https://lore.kernel.org/all/apxsZjPo7IzPuC1x@gpd4/
- Tejun「Applied 1-4」: https://lore.kernel.org/all/1dae151ab83d3d2a75e33a7c7ee152a8@kernel.org/
- 追加片 Fix pending partition work handoff: https://lore.kernel.org/all/4c9a9c9cabc3547e23bae5ae00421a52@kernel.org/
- 追加片的 Reviewed-by: https://lore.kernel.org/all/ap1yb7oMEFeBNTPZ@gpd4/
- Sashiko 对 4/4 的 race 报告（msgid 取自本线程 in-reply-to，正文未拉取到本地缓存）: https://lore.kernel.org/all/20260905162223.6EF521F00A3A@smtp.kernel.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到
- 相关：[[sched-20260903-004]]、[[sched-20260904-011]]
