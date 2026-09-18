# sched/cache: Introduce infrastructure for cache-aware load balancing

## TL;DR
增量更新：Tim Chen 的 cache-aware 负载均衡系列（v4，22 补丁）本日仅在 01/22 上有 Zenghui Yu 一句简短回应——对某条 review 建议表示"I agree，我会试试"。系列整体无新的实质进展或反对意见。

## 背景与问题
背景见 sched-20260915-004：为在多 LLC/众核系统上做 cache-aware 的负载均衡，引入基础设施（task 的 cache 亲和/分组、LLC 级别聚合等）。

## 技术方案
沿用 v4 方案（22 补丁），本日无方案变更。

## 版本演进与当前进展
- v4（见 sched-20260915-004，cover `<cover.1775065312.git.tim.c.chen@linux.intel.com>`）：本日 Zenghui Yu 对 01/22 的个别建议表示认可并愿尝试。

## Maintainer 意见与讨论焦点
- **Zenghui Yu**（01/22）：对某条建议回复 "I agree. I'll have a try. Thanks for the heads up!"，属局部细节，未涉及整体方案评价。
- 本日无维护者层面的新分歧或 NAK。

## 合入评估
likelihood=medium。系列处于逐 patch review 阶段，本日进展有限；无阻塞性反对。blocking_issues：暂无明确阻塞（整体 22 补丁仍在 review 中）。next_action：持续跟踪后续 patch 的 review 反馈与作者是否出下一版。

## 效果评估
本日无新增数据；历史数据见 sched-20260915-004 及系列内相关文章。

## 我可以参与的点
- kind=review：该 22 补丁系列仍有大量 patch 未见回帖，可挑选未 review 的补丁（尤其负载均衡算法核心路径）提出意见或实测。

## 参考链接
- lore（v4 cover）: https://lore.kernel.org/all/cover.1775065312.git.tim.c.chen@linux.intel.com/

---
id: sched-20260918-015
date: '2026-09-18'
subject: 'sched/cache: Introduce infrastructure for cache-aware load balancing'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<cover.1775065312.git.tim.c.chen@linux.intel.com>'
lore_url: 'https://lore.kernel.org/all/cover.1775065312.git.tim.c.chen@linux.intel.com/'
authors:
  - 'Tim Chen'
maintainers_involved: []
current_version: v4
patch_series:
  - version: v4
    msgid: '<cover.1775065312.git.tim.c.chen@linux.intel.com>'
    date: '2026-09-11'
    summary: '22 补丁 cache-aware LB 基础设施'
    review_outcome: 'Zenghui Yu 对 01/22 细节表示认可'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: '持续跟踪余下 patch 的 review 反馈'
contribution_opportunities:
  - kind: review
    description: '挑选系列内未 review 的补丁提出意见或实测'
generated_at: '2026-09-19T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260915-004
tags:
  - load_balance
  - topology
---