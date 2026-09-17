# cpufreq: CPPC: Keep the policy across CPU hotplug

## TL;DR
增量更新：Jie Zhan 的"CPPC 热插拔期间保持 policy"系列（v4 1/4）继续评审。Sumit Gupta 质疑为复位值准备的 MIN/MAX 顺序化 prep 非必需（平台可能把 MAX 复位到更低值，先恢复 MIN 会短暂出现 MIN>MAX），询问 Christian 是否同意按 v3 那样直接用 cppc_set_perf() 恢复、把顺序化 MIN/MAX 更新放到独立的 CPPC core 系列处理；Christian 基本同意，但坚持该 prep 应落在 cppc_set_perf() 内部而非 cppc-cpufreq。

## 背景与问题
背景见 sched-20260807-004：CPPC 在 CPU 热插拔时丢失 OSPM 设置的 policy。本日焦点是复位恢复时的 MIN/MAX 写入顺序是否正确、该逻辑应放在哪一层。

## 技术方案
方案本身不变；本日围绕"顺序化 MIN/MAX 更新"这一 prep 的归属展开：是保留在 cppc-cpufreq 的保持 policy 补丁里，还是下沉到 cppc_set_perf() 核心、或彻底拆到独立的 CPPC core 系列。

## 版本演进与当前进展
- v4（本日讨论，1/4 补丁）已发出；Christian 的 v3 评论是 prep 的触发来源。
- 09-17：Sumit 已发布其自身的 v5 [2] 且保留了该 prep；询问是否按 v3 简化。

## Maintainer 意见与讨论焦点
- **Sumit Gupta**：复位值虽安全但非必需；非 PCC 系统上平台可能把 MAX 复位到 lowest_perf 而保存的 MIN 更高，先恢复 MIN 会短暂 MIN>MAX；建议按 v3 直接用 cppc_set_perf() 恢复，把顺序化 MIN/MAX 更新交给独立 CPPC core 系列。
- **Christian Loehle**：基本认同 Jie；此前对 v3 的评论是要求把 prep 放进 cppc_set_perf() 内部，而非 cppc-cpufreq 层。
- 分歧点：prep 的去留与归属层级仍是开放小项，未闭合。

## 合入评估
likelihood=medium。评审在收尾但 prep 归属未定，且涉及与 Sumit 自身 v5 系列的重叠；当日无 cpufreq 维护者最终表态。blocking_issues：MIN/MAX prep 的去留与归属层级待定；与 Sumit v5 系列的关系需厘清。next_action：Christian 明确是否同意丢弃 prep，或由作者把顺序化更新下沉/拆分。

## 效果评估
无性能数据；属正确性/电源管理语义讨论。

## 我可以参与的点
- kind=review：分析非 PCC 系统上"先恢复 MIN 后恢复 MAX"是否真的会短暂越界，给出 cppc_set_perf() 内部顺序化的具体建议。

## 参考链接
- lore（v4 讨论线程根）: https://lore.kernel.org/all/20260806200857.601152-1-sumitg@nvidia.com/

---
id: sched-20260917-016
date: '2026-09-17'
subject: 'cpufreq: CPPC: Keep the policy across CPU hotplug'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: '<20260806200857.601152-1-sumitg@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20260806200857.601152-1-sumitg@nvidia.com/'
authors:
  - 'Jie Zhan'
maintainers_involved:
  - 'Sumit Gupta'
  - 'Christian Loehle'
current_version: v4
patch_series:
  - version: v4
    msgid: '<20260806200857.601152-2-sumitg@nvidia.com>'
    date: '2026-08-06'
    summary: 'CPPC 热插拔保持 policy；本日讨论 MIN/MAX prep 归属'
    review_outcome: 'Sumit/Christian 就 prep 去留交换意见，未闭合'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'MIN/MAX prep 的去留与归属层级待定'
    - '与 Sumit 自身 v5 系列关系需厘清'
  next_action: 'Christian 明确是否丢弃 prep，作者据此下沉或拆分'
contribution_opportunities:
  - kind: review
    description: '分析非 PCC 系统先恢复 MIN 是否短暂 MIN>MAX，给出顺序化建议'
generated_at: '2026-09-18T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260807-004
tags:
  - cpufreq
---