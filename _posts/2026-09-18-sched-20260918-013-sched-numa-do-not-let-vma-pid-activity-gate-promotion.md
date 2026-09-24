---
id: sched-20260918-013
date: '2026-09-18'
subject: 'sched/numa: do not let VMA PID activity gate promotion'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260911001826.2109390-5-gourry@gourry.net>
lore_url: https://lore.kernel.org/all/20260911001826.2109390-5-gourry@gourry.net/
authors:
- Gregory Price
maintainers_involved:
- Peter Zijlstra
- David Hildenbrand
current_version: v2
patch_series:
- version: v1
  msgid: null
  date: '2026-09-05'
  summary: stop VMA scan filters from gating promotion（早期版本不在本窗口）
  review_outcome: 见 sched-20260917-013
- version: v2
  msgid: <20260911001826.2109390-5-gourry@gourry.net>
  date: '2026-09-11'
  summary: 改名 do not let VMA PID activity gate promotion，纳入 4 补丁系列
  review_outcome: Peter 有条件认可（待 Mel）；David 要求简化 promo_only()
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 等待 Mel Gorman 反馈
  - promo_only() 可读性待优化
  next_action: 作者简化 promo_only() 并等待 Mel 表态
contribution_opportunities:
- kind: review
  description: 协助重写 promo_only() 为更清晰形式
- kind: testing
  description: 在 numab=3 模式回归 promotion 行为
generated_at: '2026-09-19T09:00:00'
source_email_count: 3
related_articles:
- sched-20260917-013
tags:
- numa_balancing
title: 'sched/numa: do not let VMA PID activity gate promotion'
layout: article
---

## TL;DR
增量更新：Gregory Price 的 NUMA tiering 修复（v2 系列 4/4，去掉 VMA PID 活动对 promotion 的门控）本日获 Peter Zijlstra 有条件点头——"我对 tiering 代码引发的问题不喜欢，但这版应该行，Mel?"（等待 Mel Gorman 确认）；David Hildenbrand 批评 `promo_only()` 计算太 messy、应用更简洁写法；作者回应已试 3~4 种方式、这是最不难看的，愿再美化一点。

## 背景与问题
背景见 <a class="article-ref" href="/lkm/2026/09/17/sched-20260917-013-sched-numa-stop-vma-scan-filters-from-gating-promotion.html">sched-20260917-013</a>：NUMA memory-tiering 模式下，VMA 的 PID 活动被用作 promotion 的门控条件，导致部分应被提升的内存页无法提升。v2 系列将其改为 4/4 "do not let VMA PID activity gate promotion"（v1 名为 "stop VMA scan filters from gating promotion"）。

## 技术方案
移除 VMA PID 活动对 promotion 的门控，使 promotion 不再被该条件阻挡。当前实现的 `promo_only()` 计算被 David 认为过于绕。

## 版本演进与当前进展
- v1（早前，名为 "stop VMA scan filters from gating promotion"）：单补丁。
- v2 4/4（09-11，`<20260911001826.2109390-5-gourry@gourry.net>`）：改名并纳入 4 补丁系列；本日 Peter 有条件认可、待 Mel 确认。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**："Not a fan of what that tiering code is causing :/ But I suppose this will do; Mel?" —— 对整体 tiering 代码状态不满，但对本补丁表示可接受，转问 Mel Gorman 意见。
- **David Hildenbrand**："相当 messy，光看 promo_only() 计算就知道……一定有更干净的写法"。
- **Gregory Price（作者）**：试过 3~4 种写法、这是最不丑的；坦言 scan 序列与 numab=3（NORMAL|TIERING）模式让推理很痛苦；愿意再美化一点。
- 未决：Mel Gorman 尚未表态；promo_only() 的可读性待改。

## 合入评估
*likelihood=medium*。Peter 已给出"this will do"的倾向性认可，但需 Mel Gorman 确认、且代码可读性有改进空间。*blocking_issues*：等待 Mel Gorman 反馈；promo_only() 可读性待优化。*next_action*：作者按 David 意见简化 promo_only() 写法，等待 Mel 表态后推进。

## 效果评估
本日无新增 benchmark；作者强调这是"可回移的 bugfix"（tiering 自 ~6.14 起的数据都被该 bug 影响，见 3/4 讨论语境）。

## 我可以参与的点
- kind=review：协助把 `promo_only()` 复写为更清晰的形式（David 明确"一定有更干净的写法"，作者欢迎）。
- kind=testing：在 numab=3（NORMAL|TIERING）模式下回归 promotion 行为，验证去掉 PID 门控后无过度提升。

## 参考链接
- lore（v2 4/4）: https://lore.kernel.org/all/20260911001826.2109390-5-gourry@gourry.net/
