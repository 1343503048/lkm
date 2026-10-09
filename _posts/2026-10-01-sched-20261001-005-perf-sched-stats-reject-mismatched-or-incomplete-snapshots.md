---
id: sched-20261001-005
date: '2026-10-01'
subject: 'perf sched stats: Reject mismatched or incomplete snapshots'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20260916161125.2548499-1-hi@tychen.cc>
lore_url: https://lore.kernel.org/all/ar1Pnn1EtP030Pq1@x2/
authors:
- Tianyi Chen
maintainers_involved:
- Arnaldo Carvalho de Melo
current_version: v1
patch_series:
- version: v1
  msgid: <20260916161125.2548499-1-hi@tychen.cc>
  date: '2026-09-16'
  summary: perf sched stats 快照按时间戳/CPU 配对并做 ID/版本校验，附合成快照 shell 测试
  review_outcome: 10-01 Arnaldo 应用到 perf-tools-next，目标 v7.4
upstream_commit: null
fixes_commit: 5a357ae6ad63
merged_branch: perf-tools-next
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 跟踪 perf-tools-next 进主线（v7.4 窗口）
contribution_opportunities:
- kind: testing
  description: 在多核机器测量窗口内做 CPU 热插拔，验证匹配校验无误报
generated_at: '2026-10-09T01:00:00'
source_email_count: 1
related_articles:
- sched-20260917-001
tags:
- perf
- sched_debug
title: 'perf sched stats: Reject mismatched or incomplete snapshots'
layout: article
---

> **subject**：`perf sched stats: Reject mismatched or incomplete snapshots`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/17/sched-20260917-001-perf-sched-stats-reject-mismatched-or-incomplete-snapshots.html">sched-20260917-001</a>：Tianyi Chen 的 tools/perf 修复——`perf sched stats` report 子命令的 before/after 快照按列表位置配对，测量期间 CPU/domain 消失（热插拔、拓扑变化）会导致计数错位或游标越界；补丁改为按时间戳/CPU 顺序识别第二份快照并校验 ID/版本一致，附合成快照 shell 测试，带 `Fixes: 5a357ae6ad63`。
- <a class="article-ref" href="/lkm/2026/10/01/sched-20261001-005-perf-sched-stats-reject-mismatched-or-incomplete-snapshots.html">sched-20261001-005</a>（今天）：perf 维护者 Arnaldo Carvalho de Melo 回帖「Thanks, applied to perf-tools-next, for v7.4.」——补丁已收取进 perf-tools-next 分支，将随 v7.4 合入窗口进入主线。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/17/sched-20260917-001-perf-sched-stats-reject-mismatched-or-incomplete-snapshots.html">sched-20260917-001</a>）`perf sched stats` 的 report 子命令通过两次采样 /proc/schedstat 生成 before/after 快照、按列表位置一一配对相减。若采样期间有 CPU 或调度域消失，计数器会从错误记录相减或被当作绝对值保留；多余记录还可能让游标越过列表末尾，产生错误统计输出。属工具健壮性问题，不影响内核本身。今天无新背景，事件是收取落地。

## 技术方案

（承接）用时间戳或 CPU 顺序识别「第二份快照」，相减前要求 CPU/domain ID 与版本号匹配；打印前校验每条记录都有对端、缺失即报错；diff 对两个输入的错误都做传播；新增 shell 测试 `tools/perf/tests/shell/schedstat_snapshots.sh` 覆盖相等时间戳、CPU 过滤、缺失/乱序 CPU/domain 记录等合成场景。今天无代码变更。

## 版本演进与当前进展

- v1（09-16，`<20260916161125.2548499-1-hi@tychen.cc>`）：首发，暂无评审。
- 10-01：Arnaldo 应用到 perf-tools-next（`<ar1Pnn1EtP030Pq1@x2>`），目标 v7.4。

## Maintainer 意见与讨论焦点

- **Arnaldo Carvalho de Melo**（perf 维护者）：「Thanks, applied to perf-tools-next, for v7.4.」——收取即认可，未附带修改意见。
- 无 NAK、无未决争议。

## 合入评估

*likelihood=merged*。perf 维护者已直接收取进 perf-tools-next、目标 v7.4 合入窗口，此前 blocking issue（无 perf 维护者评审）解除。*blocking_issues*：无。*next_action*：跟踪 perf-tools-next → 主线的合入；无需进一步动作。

## 效果评估

本日无新数据。既有证据（作者自述）：新 shell 测试在 GCC/Clang ASan/UBSan 下通过、在未打补丁的 perf 上失败（证明测试有效）；live/record/report/diff 用临时 /proc/schedstat fixture 校验通过。

## 我可以参与的点

- `testing`：在真实多核机器上跑 `perf sched stats` 并在测量窗口内做 CPU online/offline，验证匹配校验无误报（补丁已收取，实测反馈仍可回帖补充）。

## 参考链接

- Arnaldo 的收取通告: https://lore.kernel.org/all/ar1Pnn1EtP030Pq1@x2/
- v1 补丁: https://lore.kernel.org/all/20260916161125.2548499-1-hi@tychen.cc/
