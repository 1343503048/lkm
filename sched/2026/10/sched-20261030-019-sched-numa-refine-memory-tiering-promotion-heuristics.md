# sched/numa: refine memory tiering promotion heuristics

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261014-002（v1 0/6）：Li Zhe（字节跳动）发系列修 NUMA balancing 的 scan-period 调整、memory-tiering promotion 反馈污染、陈旧 task-placement 三类问题；Gregory Price 要求补「用户可见性能影响」数据。
- sched-20261015-026：Li Zhe 回应，坦承部分补丁无说服力数据，计划把严重修复与启发式改动拆开。
- sched-20261029-004（v2 0/3）：收束为 free-space bypass 可配置（1/3）、tiering promotion 不污染 task-placement 统计（2/3）、tiering-only scan-period 调整（3/3）；Bharata 质疑 1/3 对「自然溢出」场景的收益，Li Zhe 决定 2/3 拆独立 fix、1/3 与 3/3 并入 pghot 讨论。
- sched-20261030-019（今天）：Bharata Rao 复信「Thanks for this information about the deployment model. This is a useful conclusion to reach.」——认可 Li Zhe 关于 1/3「刻意 DRAM/CXL 配比」部署模型的说明，1/3 的使用场景之争基本画上句号。

## 背景与问题
（承接 v1/v2）三类 NUMA balancing/memory-tiering 缺陷收敛为 v2 三条主线。今日无新背景，是 1/3（free-space bypass 可配置）的「使用场景是否真实存在」这一分歧的收尾——Bharata 此前质疑非 overcommitted 场景下 free-space bypass 优化的价值，今日认可 Li Zhe 提供的部署模型说明。

## 技术方案
（承接 v2，今日无新代码）方向不变：1/3 给 free-space bypass 加开关（默认维持现状、关闭后回落 hotness/rate-limit 检查）；2/3 停止把 tiering promotion 结果喂进 task-placement 统计（已决定拆独立 fix + Fixes 标签 + stable）；3/3 从 `should_numa_migrate_memory()` 驱动 tiering-only scan-period（待与 pghot 分层讨论）。今日无技术演进。

## 版本演进与当前进展
*current_version: v2*（2026-10-28 发出；今日为 1/3 场景之争的收尾确认）。今日进展有限：Bharata 认可 1/3 的部署模型结论，但未改变「2/3 拆独立 fix、1/3+3/3 并入 pghot 讨论」的既定路线。

## Maintainer 意见与讨论焦点
- **Bharata Rao（AMD，pghot 作者，非 maintainer）**：今日认可 Li Zhe 的部署模型说明，认为这是「useful conclusion」。
- 无 maintainer 参与今日讨论；此前 Ying Huang（NUMA maintainer）被点名澄清 tiering fault 统计问题，尚无后续。

## 合入评估
*likelihood=medium*。2/3 是货真价实的 fix、方向已获认可，将拆成独立补丁（Fixes + stable），合入概率较高；1/3、3/3 属启发式/策略，随 pghot 讨论推进，短期难合。*blocking_issues*：2/3 需确认引入该路径的确切 commit 以补 Fixes；1/3、3/3 与 pghot 方向绑定。*next_action*：作者发 2/3 独立 fix 版本。

## 效果评估
无性能数据；今日为纯讨论性收尾（部署模型认可）。

## 我可以参与的点
- **review**：作者发 2/3 独立 fix 后，核对「tiering promotion 污染 task-placement 统计」的确切引入 commit 与 Fixes 标签准确性。
- **discussion**：参与 1/3 的「自然溢出 vs 刻意配比」方法讨论，或提供真实 tiering 部署的观测数据。

## 参考链接
- lore thread（v2 封面）: https://lore.kernel.org/all/20261028041253.74839-1-lizhe.67@bytedance.com/

---
id: sched-20261030-019
date: 2026-10-30
subject: "sched/numa: refine memory tiering promotion heuristics"
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: "<20261028041253.74839-1-lizhe.67@bytedance.com>"
lore_url: "https://lore.kernel.org/all/20261028041253.74839-1-lizhe.67@bytedance.com/"
authors: [Li Zhe]
maintainers_involved: []
current_version: v2
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "2/3 需确认引入该路径的确切 commit 以补 Fixes 标签"
    - "1/3、3/3 与 pghot 方向绑定"
  next_action: "作者发 2/3 独立 fix 版本（补 Fixes + Cc stable）"
contribution_opportunities:
  - kind: review
    description: "核对 2/3 独立 fix 的引入 commit 与 Fixes 标签准确性"
  - kind: discussion
    description: "参与 1/3 的「自然溢出 vs 刻意配比」讨论或提供真实 tiering 部署数据"
generated_at: "2026-10-31T09:00:00"
source_email_count: 1
related_articles: [sched-20261014-002, sched-20261015-026, sched-20261029-004]
tags: [numa_balancing]
---