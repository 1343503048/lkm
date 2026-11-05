---
id: sched-20261105-010
date: 2026-11-05
subject: 'sched_ext: Decompose scx_cid_init()'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261105065013.784398-1-zhangqiao22@huawei.com>
lore_url: https://lore.kernel.org/all/20261105065013.784398-1-zhangqiao22@huawei.com/
authors:
- Zhang Qiao
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261105065013.784398-1-zhangqiao22@huawei.com>
  date: 2026-11-05
  summary: 4 补丁纯搬移拆解 scx_cid_init()，为 partial-SMT 计数与单核 shard 修复清路。
  review_outcome: 刚发出，暂无 review。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 等待 sched_ext 维护者对拆解方式与 scx_cid_builder 边界的意见
contribution_opportunities:
- kind: review
  description: 审阅拆解是否纯搬移、scx_cid_builder 边界是否为后续修复留足接口
- kind: extend
  description: 基于此系列补上 partial-SMT core 计数与单核 shard 上限的修复
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 5
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Decompose scx_cid_init()'
layout: article
---

## TL;DR

Zhang Qiao 的 4 补丁系列把 sched_ext 里约 230 行的 `scx_cid_init()` 单体函数拆解为共享一个 file-private builder 结构体的若干 stage helper，纯代码搬移、无行为变化，为后续修 `calc_shard_layout()` 的 partial-SMT core 计数与单核 shard 硬上限角例做铺垫。基于 tj/sched_ext for-7.5，刚发出、暂无评审。

## 背景与问题

`sched_ext` 的 `scx_cid_init()` 经过多轮演进后膨胀成约 230 行的「单体」，把表分配、node/LLC/cluster/core 拓扑遍历、无拓扑 tail、shard 范围收尾四条逻辑交错在一起，难以定位与修改。作者计划接着修两个真实问题——`calc_shard_layout()` 的 partial-SMT 核计数、以及单核 shard 的硬上限角例——但先要把该函数拆开，否则后续修复会叠在难读的结构上。因此本系列刻意只做纯代码搬移，把行为修复排除在外。

## 技术方案

四步、每步独立可编译：

1. `01/04` 抽出 no-topology tail 与表 finalization；
2. `02/04` 把构建状态收进 `scx_cid_builder` 私有结构；
3. `03/04` 抽出单个 LLC cid range 的构建；
4. `04/04` 抽出 online（node 级）遍历。

不改变行为：WARN 检查、错误路径、shard 策略与发布时机均保持原样。作者强调这是「纯 code motion」，为后续 fix 清路。

## 版本演进与当前进展

*current_version: v1（2026-11-05 发出）*。刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点

暂无任何维护者或 reviewer 回复，本日无讨论。

## 合入评估

*likelihood=unknown*。刚发出的纯重构系列，无评审信号，无法判断走向。*blocking_issues*：暂无（尚未有人表态）。*next_action*：等待 sched_ext 维护者（Tejun Heo 等）对拆解方式（尤其 `scx_cid_builder` 结构边界）的意见。

## 效果评估

无性能数据（纯重构，无行为变化）。

## 我可以参与的点

- review：审阅四步拆解是否真为纯搬移（WARN/错误路径/shader 发布时机未变），以及 `scx_cid_builder` 的字段边界是否合理、为后续 `calc_shard_layout()` 修复留足了接口。
- extend：后续可直接基于此系列补上 partial-SMT core 计数与单核 shard 硬上限的修复补丁。

## 参考链接

- lore thread（系列 cover）: https://lore.kernel.org/all/20261105065013.784398-1-zhangqiao22@huawei.com/
