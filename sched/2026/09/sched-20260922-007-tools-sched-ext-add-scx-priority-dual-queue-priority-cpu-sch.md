# tools/sched_ext: Add scx_priority dual-queue priority CPU scheduler

## TL;DR
rahadbhuiya 提交一个 sched_ext 示例调度器 `scx_priority`：双队列（高优先级 nice<0 / 普通）区分延迟敏感与批处理任务，高优先级任务享 boosted slice 并优先 drain。Andrea Righi 回帖认为其功能已被现有示例覆盖、不建议合入内核，建议改投社区调度器仓库 sched-ext/scx。合入前景低。

## 背景与问题
作者想提供一个能区分「延迟敏感/交互型任务（nice < 0）」与「普通/批处理任务」的双队列优先级调度器，高优先级任务获得提升的时间片，并在核心可用时优先 drain 高优先级队列。

## 技术方案
新增 `scx_priority.bpf.c`（两个 DSQ：high priority 与 normal）、`scx_priority.c`（用户态 monitor 实时吞吐）、并更新 Makefile 与 README。共 253 行新增。

## 版本演进与当前进展
v1 当日发出，尚无作者对 Andrea 意见的回复。

## Maintainer 意见与讨论焦点
- **Andrea Righi**（sched_ext 维护者）：明确不看好合入内核——`tools/sched_ext` 下的调度器主要是演示 API 用法的示例，此补丁功能已被现有示例充分代表；若目标是提供实际可用的调度器，建议提 PR 到社区调度器仓库 <https://github.com/sched-ext/scx>。

## 合入评估
likelihood=low。维护者明确建议改投社区仓库，未 NAK 但方向不认可内核合入。blocking_issues：功能与现有示例重叠、定位不符 `tools/sched_ext` 的示例意图。next_action：作者改投 sched-ext/scx 社区仓库，或补充说明该示例相对现有示例的独特教学价值。

## 效果评估
无 benchmark 数据；作者自述「tracking live throughput」的用户态 monitor，但未见量化结果。

## 我可以参与的点
- **testing**：在本地跑 `scx_priority`，验证 nice<0 任务的延迟收益与吞吐影响，给出实测数据（可补作者缺失的评测）。
- **discussion**：若有该示例相对 `scx_simple`/`scx_qmap` 等的独特教学价值，可回帖讨论其内核示例定位。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260922084557.532-1-rahadbhuiya2021@gmail.com/

---
id: sched-20260922-007
date: '2026-09-22'
subject: 'tools/sched_ext: Add scx_priority dual-queue priority CPU scheduler'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260922084557.532-1-rahadbhuiya2021@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20260922084557.532-1-rahadbhuiya2021@gmail.com/'
authors:
  - 'rahadbhuiya'
maintainers_involved:
  - 'Andrea Righi'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260922084557.532-1-rahadbhuiya2021@gmail.com>'
    date: '2026-09-22'
    summary: '双 DSQ 优先级调度器示例，区分 nice<0 与普通任务'
    review_outcome: 'Andrea 建议改投 sched-ext/scx 社区仓库'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - '功能与现有示例重叠，定位不符 tools/sched_ext 示例意图'
  next_action: '改投 sched-ext/scx 仓库，或补充独特教学价值说明'
contribution_opportunities:
  - kind: testing
    description: '本地实测 nice<0 任务延迟收益与吞吐影响，补评测数据'
  - kind: discussion
    description: '讨论该示例相对现有示例的独特价值与内核示例定位'
generated_at: '2026-09-23T00:00:00'
source_email_count: 2
related_articles: []
tags:
  - sched_ext
---