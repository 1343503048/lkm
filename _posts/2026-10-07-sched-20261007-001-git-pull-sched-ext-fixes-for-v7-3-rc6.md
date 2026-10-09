---
id: sched-20261007-001
date: '2026-10-07'
subject: '[GIT PULL] sched_ext: Fixes for v7.3-rc6'
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: <afa1dcf110d0a6c081e1232c6ae2c989@kernel.org>
lore_url: https://lore.kernel.org/all/afa1dcf110d0a6c081e1232c6ae2c989@kernel.org/
authors:
- Tejun Heo
- Kuba Piecuch
maintainers_involved: []
current_version: pull
patch_series:
- version: rc6-fixes
  msgid: <afa1dcf110d0a6c081e1232c6ae2c989@kernel.org>
  date: '2026-10-07'
  summary: 热插拔挂起 + remote dequeue + qseq per-task 三修复批量进主线
  review_outcome: pr-tracker-bot 确认合入 torvalds/linux（762122d75e50）
upstream_commit: 762122d75e50
fixes_commit: null
merged_branch: torvalds/linux (v7.3-rc6)
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 对照收取：任何 7.3 前的 sched_ext 部署分支
generated_at: '2026-10-08T01:00:00'
contribution_opportunities:
- kind: testing
  detail: 7.3-rc6 上跑 sched_ext 自测全套（含 dequeue_remote）
source_email_count: 2
related_articles:
- sched-20260924-003
- sched-20260929-008
- sched-20260930-001
- sched-20261001-004
- sched-20261003-004
- sched-20261004-003
tags:
- sched_ext
title: '[GIT PULL] sched_ext: Fixes for v7.3-rc6'
layout: article
---

> **subject**：`[GIT PULL] sched_ext: Fixes for v7.3-rc6`

## TL;DR

本文为增量更新，完整脉络见 related_articles。三条此前分别走完 review 的 sched_ext 修复线在 rc6 阶段汇成一批 pull request 并被 Linus 收进主线。

- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-008-sched-ext-fix-cpu-hotplug-hang-when-a-dying-cpu-s-tasks-sit.html">sched-20260929-008</a>（CPU 热插拔挂起）：Tejun Heo 的修复——正关机的 CPU 若还有任务停在 user DSQ 或被 BPF 调度器持有，`cpu_down()` 会永久挂起或直到 watchdog 弹掉调度器；补丁在 rq 下线时把非本地 DSQ 任务重入队到本地 DSQ，09-29 已进 `sched_ext/for-7.3-fixes`。
- <a class="article-ref" href="/lkm/2026/10/01/sched-20261001-004-sched-ext-fix-missing-ops-dequeue-on-remote-local-dsq-moves.html">sched-20261001-004</a>（remote local DSQ 的 ops.dequeue()）：Kuba Piecuch 的修复——任务被迁到另一 CPU 的 local DSQ 时 `ops.dequeue()` 推迟到被 pick 才报；v3 获 Andrea Reviewed-by、Tejun「fix looks good」，前两枚（修复 + 测试）已进 `for-7.3-fixes`。
- <a class="article-ref" href="/lkm/2026/10/04/sched-20261004-003-sched-ext-generate-qseq-from-a-per-task-counter.html">sched-20261004-003</a>（qseq 改 per-task 计数器）：Kuba Piecuch 的修复——防陈旧 dispatch 的 qseq 原为 rq 级计数器，任务跨 rq 迁移可撞号；v2 由 Tejun 收进 `for-7.3-fixes` 并追加 `Cc: stable # v6.12+`。
- <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-001-git-pull-sched-ext-fixes-for-v7-3-rc6.html">sched-20261007-001</a>（今天）：Tejun 发出 **sched_ext: Fixes for v7.3-rc6** pull request（4 commit：Kuba 3 + Tejun 1，+528/−17 含自测），pr-tracker-bot 确认已合入 `torvalds/linux.git`（merge commit `762122d75e50`）。三条修复线全部落进主线 7.3-rc6。

## 背景与问题

三条修复线各自的 bug 语义（承接 related 文章）：

1. **热插拔挂起**：`sched_cpu_wait_empty()` 只能被 dying CPU `__schedule()` 里的 `balance_push()` 唤醒；sched_ext 任务停在 user DSQ 或 BPF 调度器 custody 时仍计在该 rq 上，inactive CPU 不再调 `ops.dispatch()` 拉不回任务，`cpu_down()` 挂着 `cpu_hotplug_lock` 死等。
2. **remote local DSQ 迟到的 dequeue**：`SCX_DSQ_LOCAL_ON` 派发等路径把任务移到非本 rq 的 local DSQ 时，`p->scx.sticky_cpu` 在 `enqueue_task_scx()` 插入之后才清，custody 退出被跳过，BPF 只在被 pick 时收到带 `SCX_DEQ_CORE_SCHED_EXEC` 的迟到 `ops.dequeue()`。
3. **qseq 撞号**：`finish_dispatch()` 用 qseq 判断 QUEUED 实例是否 insert 时所见；rq 级计数器下任务在 insert 与 finish 之间迁往另一 rq 可撞上旧 qseq，过期 dispatch 被错误应用到新实例。

rc6 是 7.3 的收敛窗口，三条线都是「已进 for-7.3-fixes、等发版前批量上主线」的形态。

## 技术方案

pull 范围：`94480606a677`（cid_topo size 参数，09-26）→ `e6ac89b8b1c1`（qseq per-task，10-03），tag `sched_ext-for-7.3-rc6-fixes`。四枚 commit：

- Tejun Heo：`sched_ext: Fix CPU hotplug hang when a dying CPU's tasks sit in the BPF scheduler`——rq 下线时把 dying CPU 上仍被持有/停在 user DSQ 的任务重入队到本地 DSQ，让 CPU 像其它调度类一样把它们推走。
- Kuba Piecuch：`sched_ext: Call ops.dequeue() when a task arrives on a remote local DSQ`——插入目标 DSQ 时即调用 `ops.dequeue()`，与同 CPU 派发对齐。
- Kuba Piecuch：`selftests/sched_ext: Add a test for ops.dequeue() on remote local DSQ moves`——`dequeue_remote.bpf.c` + `dequeue_remote.c`（+270/+204 行）。
- Kuba Piecuch：`sched_ext: Generate qseq from a per-task counter`——qseq 改为 `p->scx.ops_qseq` 任务级计数，跨 rq 迁移不再撞号、永不生成 0。

改动面：`kernel/sched/ext/{ext.c,inlines.h,internal.h,sub.c}`、`kernel/sched/sched.h`、`include/linux/sched/ext.h` + 自测两个新文件，合计 +528/−17。

## 版本演进与当前进展

- 热插拔挂起：09-24 v1（<a class="article-ref" href="/lkm/2026/09/24/sched-20260924-003-sched-ext-fix-cpu-hotplug-hang-when-a-dying-cpu-s-tasks-sit.html">sched-20260924-003</a>）→ 09-29 Applied to for-7.3-fixes（<a class="article-ref" href="/lkm/2026/09/29/sched-20260929-008-sched-ext-fix-cpu-hotplug-hang-when-a-dying-cpu-s-tasks-sit.html">sched-20260929-008</a>）→ **10-07 随 rc6 pull 进主线**。
- remote dequeue：09-30 v3 获评（<a class="article-ref" href="/lkm/2026/09/30/sched-20260930-001-sched-ext-fix-missing-ops-dequeue-on-remote-local-dsq-moves.html">sched-20260930-001</a>）→ 10-01 Applied 1-2（<a class="article-ref" href="/lkm/2026/10/01/sched-20261001-004-sched-ext-fix-missing-ops-dequeue-on-remote-local-dsq-moves.html">sched-20261001-004</a>）→ **10-07 进主线**。
- qseq：10-03 v1→v2（<a class="article-ref" href="/lkm/2026/10/03/sched-20261003-004-sched-ext-generate-qseq-from-a-per-task-counter.html">sched-20261003-004</a>）→ 10-04 Applied（<a class="article-ref" href="/lkm/2026/10/04/sched-20261004-003-sched-ext-generate-qseq-from-a-per-task-counter.html">sched-20261004-003</a>）→ **10-07 进主线**。
- 10-07 08:45 pr-tracker-bot 确认：pull 已合入 `torvalds/linux.git`，merge commit `762122d75e50e4919ef77afc2dffdc4931c5be87`。

## Maintainer 意见与讨论焦点

无新增技术分歧——本批是已完成 review 的修复集合的例行收取。唯一值得记录的是 pull request 覆盖说明本身对三个 bug 的受众化重述（见背景节）。Linus 侧无附加意见，pr-tracker-bot 机械确认。

## 合入评估

*likelihood=merged*。merge commit `762122d75e50` 已落 `torvalds/linux.git`，7.3-rc6 起主线自带；qseq 修复带 `Cc: stable # v6.12+`，另两枚各自带 `Fixes:` + stable Cc（见各 related 文章），stable 回合窗口已开。*next_action*：任何基于 7.3 之前内核的 BPF 调度器部署分支都应对照收取这四枚。

## 效果评估

无新增 benchmark。各修复的效果证据沿用 related 文章：热插拔挂起的复现/消除、remote dequeue 的语义对齐与自测、qseq 的陈旧 dispatch 防护。本批的「效果」是发版层面的：7.3 正式版将带着这三个正确性修复出货。

## 我可以参与的点

- `testing`：在 7.3-rc6 上跑 sched_ext 自测全套（含新增 `dequeue_remote`），确认三修复在真实负载（CPU hotplug + SCX_OPS_ENQ_LAST + 跨 CPU DSQ 派发组合）下无回归。
- 回合视角：OLK-6.6 无 sched_ext，本批不适用；但任何内部 BPF 调度器分支若基于 6.12+ 主线，qseq 与 dequeue 修复应优先回合（都有 stable Cc）。

## 参考链接

- pull request: https://lore.kernel.org/all/afa1dcf110d0a6c081e1232c6ae2c989@kernel.org/
- pr-tracker 确认: https://lore.kernel.org/all/179133391720.2846339.7131187262623409143.pr-tracker-bot@kernel.org/
- 相关文章：<a class="article-ref" href="/lkm/2026/09/24/sched-20260924-003-sched-ext-fix-cpu-hotplug-hang-when-a-dying-cpu-s-tasks-sit.html">sched-20260924-003</a>、<a class="article-ref" href="/lkm/2026/09/29/sched-20260929-008-sched-ext-fix-cpu-hotplug-hang-when-a-dying-cpu-s-tasks-sit.html">sched-20260929-008</a>（热插拔挂起）、<a class="article-ref" href="/lkm/2026/09/30/sched-20260930-001-sched-ext-fix-missing-ops-dequeue-on-remote-local-dsq-moves.html">sched-20260930-001</a>、<a class="article-ref" href="/lkm/2026/10/01/sched-20261001-004-sched-ext-fix-missing-ops-dequeue-on-remote-local-dsq-moves.html">sched-20261001-004</a>（remote dequeue）、<a class="article-ref" href="/lkm/2026/10/04/sched-20261004-003-sched-ext-generate-qseq-from-a-per-task-counter.html">sched-20261004-003</a>（qseq）
