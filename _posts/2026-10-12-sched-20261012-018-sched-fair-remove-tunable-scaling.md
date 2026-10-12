---
id: sched-20261012-018
date: '2026-10-12'
subject: 'sched/fair: Remove tunable scaling'
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: <20261002124538.79658-1-torvic9@mailbox.org>
lore_url: https://lore.kernel.org/all/20261002124538.79658-1-torvic9@mailbox.org/
authors:
- Tor Vic
maintainers_involved:
- Vincent Guittot
current_version: v1
patch_series:
- version: v1
  msgid: <20261002124538.79658-1-torvic9@mailbox.org>
  date: '2026-10-02'
  summary: 删除 sched 可调参数缩放机制，sched_base_slice 固定 2ms
  review_outcome: Vincent 质疑动机与「base_slice 非任意」，作者澄清误读
merge_assessment:
  likelihood: low
  blocking_issues:
  - Vincent 质疑移除动机与结论（base_slice 非任意选择）
  - 删除长期存在的缩放机制需要更强理由
  next_action: 作者回应 Vincent 的质疑，说明为何值得移除
contribution_opportunities:
- kind: discussion
  description: 就「是否仍有发行版依赖 none/linear 缩放」补充生态侧证据（作者自己不确定）
generated_at: '2026-10-13T01:40:00'
source_email_count: 2
related_articles:
- sched-20261002-012
tags:
- cfs
title: 'sched/fair: Remove tunable scaling'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-012-sched-fair-remove-tunable-scaling.html">sched-20261002-012</a>：Tor Vic 的 2 补丁 RFC——删除 2.6.33 时代引入的调度器可调参数缩放机制（先删 `none`/`linear`、再删整个机制把 `sched_base_slice` 固定 2ms）。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-018-sched-fair-remove-tunable-scaling.html">sched-20261012-018</a>（今天）：Vincent Guittot 质疑「如何得出该结论、为何值得移除」，并指出 `sysctl_sched_base_slice` 的取值并非任意（引 commit 说明）；作者澄清误会——是他自己在补丁里选的 2ms 任意，不是内核默认 0.7ms 任意，并承认不确定是否有发行版默认用 none/linear。

## 背景与问题

（承接 20261002-012）作者认为 sched 可调参数缩放机制（`none`/`linear`/`logarithmic`）基本无人用、维护负担大于价值，RFC 提议删除、把 `sched_base_slice` 固定为 2ms（当前 log2 缩放实际取 0.7/1.4/2.1/2.8ms，2ms 居中）。

## 技术方案

（承接 20261002-012）方案维持 RFC 不变，今日聚焦动机与理由的澄清。

## 版本演进与当前进展

v1（10-02）→ 今日（10-12）Vincent 质疑、作者澄清误解；尚无 v2。

## Maintainer 意见与讨论焦点

- **Vincent Guittot**：质疑「如何得出该结论、为何值得移除」，明确 `sysctl_sched_base_slice` 的取值不是任意选的（指向相关 commit 的理由）。
- **Tor Vic**：澄清「任意 2ms」是指自己补丁里的选择，非内核默认；承认不确定发行版默认值分布。

## 合入评估

*likelihood=low*。删除长期存在的缩放机制，维护者对其动机与结论存疑。*blocking_issues*：动机未获认可。*next_action*：作者回应 Vincent，给出移除的充分理由。

## 效果评估

无性能数据（RFC 动机讨论，未见数字支撑）。

## 我可以参与的点

- `discussion`：补充「发行版是否默认用 none/linear 缩放」的生态侧证据，帮助判断移除的真实影响面。

## 参考链接

- lore（cover）: https://lore.kernel.org/all/20261002124538.79658-1-torvic9@mailbox.org/
- lore（Vincent 质疑）: https://lore.kernel.org/all/CAKfTPtDVXVzsRCUavub+6cXrC8Ke9=Vrv7A4cMcEG2WwDtJKKg@mail.gmail.com/
