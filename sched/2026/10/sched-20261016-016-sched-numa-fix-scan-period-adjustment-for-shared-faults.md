# sched/numa: fix scan-period adjustment for shared faults

## TL;DR
本文为增量更新，完整脉络见 related_articles（这是「sched/numa: fix several NUMA balancing issues」系列的 3/6 补丁）。

- sched-20261014-002 / 20261015-026：Li Zhe 发 0/6 系列修复 NUMA balancing 多处问题；其中 3/6 改 shared fault 的 scan-period 调整，作者此前承认「无广泛收益数据、动机是 scan-period 决策一致性」。
- sched-20261016-016（今天）：Gregory Price 回 3/6，要求把「非明显 Fixes 的启发式改动」从系列中拆出，并为启发式改动补充展示行为变化的实测数据，特别提醒近期 shmem 扫描修复曾连带引发 4-5 个回归。

## 背景与问题
（承接 20261014-002/20261015-026）3/6 是 scan-period 调整的启发式改动（shared fault 语义），作者坦承没有可量化的用户可见收益，动机是 scan-period 决策的一致性。Gregory 今天明确要求把这类启发式改动与「严重修复」分开，避免难懂的启发式改动混入。

## 技术方案
（承接 20261014-002）无新补丁；今天为 reviewer 对 3/6 单独提出拆分与补数据要求。

## 版本演进与当前进展
系列仍在 v1，作者此前已计划「严重修复 vs 启发式改动」拆分；Gregory 今天的意见进一步确认 3/6 属于应拆出的启发式改动，并需补实测数据。

## Maintainer 意见与讨论焦点
Gregory Price（reviewer）：「The heuristic changes that aren't obvious Fixes: should not be lumped in. For heuristic changes, please try to generate some kind of data that demonstrate the behavior being changed.」并举 shmem 扫描修复引发 4-5 个回归的例子，强调启发式改动的回归风险。

## 合入评估
*likelihood=medium*。作者已承认缺数据、方向在收敛，但 3/6 需拆出并补实测数据。*blocking_issues*：启发式改动缺行为数据；需从系列拆出。*next_action*：作者为 3/6 补 scan-period 行为变化的实测数据，或将其从「严重修复」子集拆出单独推进。

## 效果评估
无量化数据；reviewer 明确要求补齐。

## 我可以参与的点
- *testing*：为 shared fault 的 scan-period 调整补一组展示行为变化的数据（如不同 fault 类型下 scan-period 的分布变化），回帖佐证或反驳该启发式改动的必要性。

## 参考链接
- Gregory 对 3/6 的回复：https://lore.kernel.org/all/atD3qhbqzN2R9Bxx@gourry-fedora-PF4VCD3F/
- 系列 cover：https://lore.kernel.org/all/20261014094347.99157-1-lizhe.67@bytedance.com/

---
id: sched-20261016-016
date: 2026-10-16
subject: "sched/numa: fix scan-period adjustment for shared faults"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261014094347.99157-1-lizhe.67@bytedance.com>"
lore_url: "https://lore.kernel.org/all/20261014094347.99157-1-lizhe.67@bytedance.com/"
authors: ["Li Zhe"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261014094347.99157-1-lizhe.67@bytedance.com>"
    date: 2026-10-14
    summary: "3/6 改 shared fault 的 scan-period 调整（启发式改动）"
    review_outcome: "Gregory Price 要求拆出并补实测数据"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["启发式改动缺行为数据；需从系列拆出"]
  next_action: "为 3/6 补 scan-period 行为变化实测数据，或拆出单独推进"
contribution_opportunities:
  - kind: testing
    description: "补 shared fault scan-period 调整的行为变化数据，佐证/反驳该启发式改动的必要性"
generated_at: "2026-10-17T01:30:00"
source_email_count: 1
related_articles: ["sched-20261014-002", "sched-20261015-026"]
tags: [numa_balancing, cfs]
---