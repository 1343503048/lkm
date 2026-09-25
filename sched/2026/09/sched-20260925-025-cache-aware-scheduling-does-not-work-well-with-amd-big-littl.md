# Cache-aware scheduling does not work well with amd big/little cores

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260916-018：Klaus 反馈 Chen Yu 侧补丁后 AMD big/little 上 cache-aware 性能已基本追平无 cache-aware，偏正面修复确认。
- sched-20260924-010：Tim Chen 给出替代补丁（hybrid 上让 asym packing 优先于 cache-aware），请 Klaus 复测。
- sched-20260925-025（今天）：Klaus 回复——替代补丁打 7.2.7 时大段 fuzz 且 `fair.c` 编译失败（`sched_use_asym_prio` 未声明/冲突、`env` 未声明），并指出新增的 `sched_asym` 调用因 C 的 `inline` 不看前文而不会真正内联。目前补丁无法在目标内核上编译，复测被卡在第一步。

## 背景与问题

（承接 sched-20260924-010）cache-aware 调度在 AMD big/little（Zen4/Zen4c 混合）平台上把 cache 密集任务错放到小核 LLC。根源是 asym packing 与 cache-aware 表达互相冲突的放置策略。Tim Chen 的替代补丁让 asym packing 在 hybrid 上优先。今天的进展是补丁的**可用性**问题：它针对较新内核编写，打 7.2.7 时上下文对不上。

## 技术方案

（承接 sched-20260924-010）Tim Chen 替代补丁三处改动：`can_migrate_llc_task()` 在 `sched_asym(env->sd, dst_cpu, src_cpu)` 时直接 unrestricted、`llc_balance()` 在 `SD_ASYM_PACKING` 且目的组 asym priority 更高时跳过 LLC 聚合、`need_active_balance()` 把 asym 判断提前。今天 Klaus 指出的编译问题落在同一补丁：新增的 `sched_asym`/`sched_use_asym_prio` 调用点在前向声明与 `env` 作用域上缺失，导致 7.2.7 上无法构建。

## 版本演进与当前进展

- 09-24：Tim Chen 发替代补丁。
- 09-25：Klaus 回帖（`<e2c87de0-31f7-4ed0-b80e-7f9aa7d0e511@computerix.info>`）报告两条：第 1 条，补丁打 7.2.7 大量 fuzz、`fair.c` 编译失败（`sched_use_asym_prio` 调用先于声明、类型冲突、`env` 未声明）；第 2 条，`inline` 在 C 里不看前文，新增的 `sched_asym` 调用会变真实调用而非内联。尚未见 Tim Chen 或维护者回应。

## Maintainer 意见与讨论焦点

- 无 NAK；Tim Chen 的替代补丁路线仍未被否定，但当务之急是先解决补丁与目标内核（7.2.7）的兼容/编译问题，Klaus 才能复测。
- 路线分歧（Chen Yu 原补丁 vs Tim Chen 替代补丁）仍悬而未决；今天没有维护者表态。

## 合入评估

*likelihood=medium*。修复方向有实测背书（16-018 追平基线），但替代补丁当前无法在报告者的 7.2.7 上编译，复测无法进行；路线选择也未收敛。*blocking_issues*：替代补丁需改成能在目标内核干净打上并编译通过（声明顺序、作用域、内联语义）；asym packing vs cache-aware 的优先级策略待维护者裁决。*next_action*：Tim Chen 修编译问题后 Klaus 复测；维护者选定路线。

## 效果评估

今日无新数据。沿用 16-018 的实测：两个构建测试几乎同速于无 cache-aware 内核、比早期 cache-aware 快约 2%。

## 我可以参与的点

- `testing`：把替代补丁移植到 7.2.7/报告者内核清理编译问题后，在 AMD Ryzen AI HX 370 的 Clang full-LTO link 上复测，给出 cache 密集负载的对照数据。
- `review`：确认 `sched_use_asym_prio`/`sched_asym` 的前向声明顺序与 `env` 作用域，以及 `inline` 语义在无优化构建下的真实代价。

## 参考链接

- Klaus 报编译失败: https://lore.kernel.org/all/e2c87de0-31f7-4ed0-b80e-7f9aa7d0e511@computerix.info/
- 线程根: https://lore.kernel.org/all/7b83cf0cd1704b552978af88d7de9c57970c23a1.camel@linux.intel.com/

---
id: sched-20260925-025
date: 2026-09-25
subject: "Cache-aware scheduling does not work well with amd big/little cores"
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: "<8aea0f25-0317-42ac-b59f-1a008c6eb106@computerix.info>"
lore_url: "https://lore.kernel.org/all/7b83cf0cd1704b552978af88d7de9c57970c23a1.camel@linux.intel.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: "2026-09-26T01:15:00"
authors:
  - "Klaus Kusche"
maintainers_involved:
  - "Tim Chen"
patch_series: []
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "替代补丁打 7.2.7 编译失败（sched_use_asym_prio 声明顺序、env 作用域、inline 语义）"
    - "Chen Yu 原补丁 vs Tim Chen 替代补丁的路线选择未定"
  next_action: "Tim Chen 修编译问题后 Klaus 复测；维护者选定路线"
contribution_opportunities:
  - kind: testing
    description: "把替代补丁移植清理编译问题后，在 AMD Ryzen AI HX 370 的 Clang full-LTO link 上复测给出对照数据"
  - kind: review
    description: "确认 sched_use_asym_prio/sched_asym 前向声明顺序、env 作用域与 inline 语义在无优化构建下的代价"
source_email_count: 1
related_articles:
  - "sched-20260924-010"
  - "sched-20260916-018"
  - "sched-20260914-001"
tags:
  - load_balance
  - cfs
---