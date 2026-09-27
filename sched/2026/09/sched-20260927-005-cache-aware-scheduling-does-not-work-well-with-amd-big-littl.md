# Cache-aware scheduling does not work well with amd big/little cores

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260916-018：Klaus 反馈 Chen Yu 侧补丁后 AMD big/little 上 cache-aware 性能基本追平基线。
- sched-20260924-010：Tim Chen 给出替代补丁（hybrid 上让 asym packing 优先于 cache-aware），请 Klaus 复测。
- sched-20260925-025：Klaus 报告替代补丁打 7.2.7 大段 fuzz、`fair.c` 编译失败，并质疑新增 `sched_asym` 调用不会真正内联。
- sched-20260926-004：Tim Chen 把补丁 rebase 到 v7.2.7（真·回移，两处适配），逐条反驳编译/内联质疑，请 Klaus 再测。
- sched-20260927-005（今天）：Klaus 复测结论正面——回移版「looks good」，无 core 分配异常（没有进程滞留小核而大核空闲），两个编译任务的 wallclock 优于此前所有 cache-aware 版本、且不差于关掉 cache-aware 的无补丁内核。此前唯一的复测卡点解除。

## 背景与问题

（承接 sched-20260924-010 / 20260926-004）cache-aware 调度在 AMD big/little（Ryzen AI HX 370）混合平台上把 cache 密集任务错放到小核 LLC——小核频率低（3.3 vs 5.1 GHz）、L3 只有一半（8 vs 16 MB），锁在小核 LLC 双重吃亏，Clang full-LTO link 相比无 cache-aware 内核大幅变慢。根源是 asym packing（放最高优先级 CPU）与 cache-aware（同进程任务共置到同一 LLC）表达互相冲突的放置策略。

## 技术方案

（承接 sched-20260926-004）Tim Chen 替代补丁让 asym packing 在 hybrid 上优先于 cache-aware，三处改动：`can_migrate_llc_task()` 在 `sched_asym(...)` 时直接 unrestricted、`llc_balance()` 在 `SD_ASYM_PACKING` 且目的组 asym priority 更高时跳过 LLC 聚合、`need_active_balance()` 把 asym 判断提前。上一版已给出 v7.2.7 回移（`can_migrate_llc_task()` 签名适配、misfit early-out 位置调整）。今天无新代码，是回移版的首份正面复测结论。

## 版本演进与当前进展

- 09-24：Tim Chen 发替代补丁（针对 sched/urgent）。
- 09-25：Klaus 报 7.2.7 编译失败 + inline 质疑。
- 09-26：Tim Chen 给出 7.2.7 回移版。
- 09-27：Klaus（`<c3e26de1-85de-4b44-8498-9878e95f4d5c@computerix.info>`）复测回移版：无 core 分配异常；两个编译任务 elapsed wallclock 优于此前所有 cache-aware 补丁/版本，且至少不差于无补丁 + 关 cache-aware；uv build 收益大于 kernel build（其负载有较多「半载核」阶段，放置影响更大）。

## Maintainer 意见与讨论焦点

- **Klaus Kusche**（报告者，AMD 平台）：给出关键正面复测，确认回移版在功能（无滞留小核）与性能（追平/优于基线）上都达标。
- 路线分歧（Chen Yu 原补丁 vs Tim Chen 替代补丁）仍未正式收敛；asym packing 优先于 cache-aware 的放置策略仍待调度维护者（Peter/Vincent）裁决是否采纳为正式方向。

## 合入评估

*likelihood=medium*。昨日「7.2.7 无法复测」卡点已由 Klaus 正面结论解除（功能与性能都达标），方向获得实测背书。*blocking_issues*：asym packing vs cache-aware 优先级策略仍待维护者裁决；替代补丁尚未以维护者认可的形式进入 sched/urgent fusion 树（本日 GIT PULL 的 sched/cache 修复不含本 asym 优先级补丁）。*next_action*：等 Peter/Vincent 对替代方案路线表态；Tim Chen 可把替代补丁整理成对 sched/urgent 的正式提交。

## 效果评估

今日新增 Klaus 复测数据（定性 + 相对结论）：回移版两个编译任务的 elapsed wallclock「有时略优、有时显著优」于此前所有 cache-aware 版本，且至少与无补丁 + 关 cache-aware 的内核持平；uv build 因存在「约半载核」阶段收益更大。未见具体秒数/百分比数字。

## 我可以参与的点

- `testing`：在 AMD Ryzen AI HX 370（或同类 Zen4/Zen4c 混合平台）复现回移版三列对照（回移版 / 无 cache-aware / Chen Yu 原补丁）跑 Clang full-LTO link，给出具体数值。
- `review`：核对 v7.2.7 回移版两处适配（`can_migrate_llc_task` 签名、misfit early-out 位置）与 sched/urgent 原版语义等价，确认无行为差异。

## 参考链接

- Klaus 复测回帖: https://lore.kernel.org/all/c3e26de1-85de-4b44-8498-9878e95f4d5c@computerix.info/
- Tim Chen 回移版回帖: https://lore.kernel.org/all/c69168ffeeb1d6ea4399b1a9ed6da7b24ac69bb8.camel@linux.intel.com/
- 线程根: https://lore.kernel.org/all/7b83cf0cd1704b552978af88d7de9c57970c23a1.camel@linux.intel.com/

---
id: sched-20260927-005
date: 2026-09-27
subject: "Cache-aware scheduling does not work well with amd big/little cores"
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: "<7b83cf0cd1704b552978af88d7de9c57970c23a1.camel@linux.intel.com>"
lore_url: "https://lore.kernel.org/all/c3e26de1-85de-4b44-8498-9878e95f4d5c@computerix.info/"
authors:
  - "Tim Chen"
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<7b83cf0cd1704b552978af88d7de9c57970c23a1.camel@linux.intel.com>"
    date: 2026-09-24
    summary: "Tim Chen 替代补丁：hybrid 上 asym packing 优先于 cache-aware（can_migrate_llc_task / llc_balance / need_active_balance 三处）。"
    review_outcome: "Klaus 09-27 复测 v7.2.7 回移版为正面：无滞留小核、性能追平/优于基线。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "asym packing vs cache-aware 优先级策略仍待维护者裁决"
    - "替代补丁尚未进入 sched/urgent 正式提交（本日 GIT PULL 不含本 asym 优先级补丁）"
  next_action: "等 Peter/Vincent 对替代路线表态；Tim Chen 整理成对 sched/urgent 的正式提交"
contribution_opportunities:
  - kind: testing
    description: "在 AMD 混合平台复现回移版三列对照（回移版/无 cache-aware/Chen Yu 原补丁）跑 Clang full-LTO link，给出具体数值"
  - kind: review
    description: "核对 v7.2.7 回移版两处适配与 sched/urgent 原版语义等价，确认无行为差异"
generated_at: "2026-09-28T09:00:00"
source_email_count: 1
related_articles:
  - sched-20260916-018
  - sched-20260924-010
  - sched-20260925-025
  - sched-20260926-004
tags:
  - load_balance
  - regression
  - x86
---