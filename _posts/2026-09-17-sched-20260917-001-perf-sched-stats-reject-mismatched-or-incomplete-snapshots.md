---
id: sched-20260917-001
date: '2026-09-17'
subject: 'perf sched stats: Reject mismatched or incomplete snapshots'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260916161125.2548499-1-hi@tychen.cc>
lore_url: https://lore.kernel.org/all/20260916161125.2548499-1-hi@tychen.cc/
authors:
- Tianyi Chen
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260916161125.2548499-1-hi@tychen.cc>
  date: '2026-09-17'
  summary: perf sched stats 快照按时间戳/CPU 配对并做 ID/版本校验，附合成快照 shell 测试
  review_outcome: 暂无评审
upstream_commit: null
fixes_commit: 5a357ae6ad63
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无 perf 维护者评审
  next_action: 等待 perf 维护者评审并反馈配对策略
contribution_opportunities:
- kind: testing
  description: 在多核机器测量窗口内做 CPU 热插拔，验证匹配校验无误报
- kind: review
  description: 审查配对策略对 record/report 与 live 路径的边界覆盖
generated_at: '2026-09-18T09:00:00'
source_email_count: 1
related_articles: []
tags:
- perf
- sched_debug
title: 'perf sched stats: Reject mismatched or incomplete snapshots'
layout: article
---

## TL;DR
Tianyi Chen 提交 tools/perf 补丁，修复 `perf sched stats` report 子命令的快照配对缺陷：before/after 记录按列表位置配对，测量期间 CPU/domain 消失会导致计数错位或游标越界。补丁改为按时间戳/CPU 顺序识别第二份快照并校验 ID/版本一致，附合成快照 shell 测试。新补丁暂无评审。

## 背景与问题
`perf sched stats` 的 report 子命令（Fixes: 5a357ae6ad63）通过两次采样 /proc/schedstat 生成 before/after 两份快照，按列表位置一一配对相减。若采样期间有 CPU 或调度域消失（热插拔、拓扑变化），计数器会从错误的记录相减、或直接被当作绝对值保留；多余记录还可能让游标越过列表末尾，产生错误统计输出。属工具健壮性问题，不影响内核本身。

## 技术方案
- 用时间戳或 CPU 顺序识别"第二份快照"，相减前要求 CPU/domain ID 与版本号匹配。
- 打印前校验每条记录都有对端记录，缺失即报错。
- diff 对两个输入的错误都做传播。
- 新增 shell 测试 `tools/perf/tests/shell/schedstat_snapshots.sh`，覆盖相等时间戳、CPU 过滤、缺失/乱序 CPU/domain 记录等合成场景。

## 版本演进与当前进展
v1 刚发出（`<20260916161125.2548499-1-hi@tychen.cc>`），暂无 review 意见。

## Maintainer 意见与讨论焦点
当日线程无维护者或资深成员表态。作者自述"新 shell 测试在 GCC/Clang ASan/UBSan 下通过、在未打补丁的 perf 上失败"。

## 合入评估
likelihood=medium。小范围工具修复，带 Fixes 标签与回归测试，门槛低；但尚无 perf 维护者（Arnaldo/Namhyung 等）评审，配对策略是否被接受待观察。blocking_issues：无 perf 维护者评审。next_action：等待 perf 维护者评审。

## 效果评估
无性能数据。作者自述：新 shell 测试通过，live/record/report/diff 用临时 /proc/schedstat fixture 校验通过，未打补丁时测试失败（证明测试有效）。

## 我可以参与的点
- kind=testing：在真实多核机器上跑 `perf sched stats` 并在测量窗口内做 CPU online/offline，验证匹配校验是否误报。
- kind=review：审查快照配对策略对 record/report 与 live 两条路径的边界覆盖。

## 参考链接
- lore: https://lore.kernel.org/all/20260916161125.2548499-1-hi@tychen.cc/
