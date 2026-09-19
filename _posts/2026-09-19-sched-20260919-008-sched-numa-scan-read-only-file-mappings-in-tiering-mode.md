---
id: sched-20260919-008
date: '2026-09-19'
subject: 'sched/numa: scan read-only file mappings in tiering mode'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260911001826.2109390-1-gourry@gourry.net>
lore_url: https://lore.kernel.org/all/20260911001826.2109390-4-gourry@gourry.net/
authors:
- Gregory Price
maintainers_involved:
- Lorenzo Stoakes
current_version: v2
patch_series:
- version: v2
  msgid: <20260911001826.2109390-4-gourry@gourry.net>
  date: '2026-09-11'
  summary: tiering 模式扫描只读文件映射（3/4）
  review_outcome: Lorenzo 反对引入语义不明的 VMA helper，主张内联+注释，作者周末重写
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 3/4 VMA 判定语义（MAP_PRIVATE、write-sealed memfd）与实现形式待重写
  next_action: 作者重写 3/4（内联+注释或厘清语义），Lorenzo 可协助跟进
contribution_opportunities:
- kind: review
  description: 分析 VMA 判定对各类文件映射边界的正确性
- kind: testing
  description: 在 NUMA tiering + 只读文件映射负载上验证扫描行为
generated_at: '2026-09-20T09:00:00'
source_email_count: 2
related_articles:
- sched-20260918-014
tags:
- numa_balancing
title: 'sched/numa: scan read-only file mappings in tiering mode'
layout: article
---

## TL;DR
增量更新：Gregory Price 的 NUMA tiering 修复系列 3/4（让 tiering 模式也扫描只读文件映射）本日继续被 mm 维护者 Lorenzo Stoakes 敲打——他指出该补丁的 VMA 判定函数名不符实、实际会囊括 write-sealed memfd 与 MAP_PRIVATE 文件映射等，不建议在此引入新的 VMA helper，主张 hotfix 用内联代码+注释；作者回应"给我周末时间清理"。

## 背景与问题
背景见 sched-20260918-014：NUMA tiering 模式下只读文件映射此前不被扫描，导致某些 tiering 场景下 numa balancing 行为缺失。3/4 试图让 tiering 模式也扫描这类映射。

## 技术方案
3/4（`sched/numa: scan read-only file mappings in tiering mode`）：新增 VMA 判定，让 tiering 模式扫描只读文件映射。本日讨论集中在判定语义与 helper 形式。

## 版本演进与当前进展
- v2 3/4（2026-09-11，`<20260911001826.2109390-4-gourry@gourry.net>`）：扫描只读文件映射（见 sched-20260918-014）。
- 本日 Lorenzo Stoakes（`<aq1inYWiNWtZlyoo@gremlin>`）继续反对该 VMA helper 的写法；作者 Gregory Price（`<aq1o3TYZR9JNkXXP@gourry-fedora-PF4VCD3F>`）回应"给我周末时间清理"。

## Maintainer 意见与讨论焦点
- **Lorenzo Stoakes（mm 维护者）**：指出该检查"as-written"会囊括 write-sealed memfd、MAP_PRIVATE 文件映射等，作者需先厘清这些是否应被纳入；明确"希望你（Gregory）不要在这里引入这样的 VMA helper"——它名不符实、甚至可能不是作者以为的那样。建议：a) 先判断是否在意 MAP_PRIVATE、write-sealed memfd 等情形；b) 作为 hotfix 用内联代码+注释实现。并主动提出"我可以自己跟进，只要你们督促我"。
- **Gregory Price（作者）**：稍带情绪（"被你的'看看我 40 patch 系列'戳到"），承诺"给我周末时间，我看看能清理什么"。
- 分歧/未决：3/4 的 VMA 判定语义（MAP_PRIVATE、write-sealed memfd 是否应纳入）与实现形式（独立 helper vs 内联+注释）未定。

## 合入评估
likelihood=medium。3/4 的 VMA 判定仍需按 Lorenzo 意见重写（内联+注释或厘清语义），但方向（tiering 模式扫描只读文件映射）本身未被否定。blocking_issues：VMA helper 语义与形式待作者重写。next_action：作者重写 3/4（内联+注释，或先厘清 MAP_PRIVATE/write-sealed memfd 语义），Lorenzo 表示可协助跟进。

## 效果评估
本日无新增测试数据；讨论为 VMA 语义与代码形式，无性能数字。

## 我可以参与的点
- kind=review：分析 3/4 的 VMA 判定对 MAP_PRIVATE、write-sealed memfd、共享只读文件映射等边界的正确性，给出具体建议。
- kind=testing：在 NUMA tiering + 只读文件映射负载上验证扫描行为是否符合预期。

## 参考链接
- lore（v2 3/4 patch）: https://lore.kernel.org/all/20260911001826.2109390-4-gourry@gourry.net/
- lore（Lorenzo 回复）: https://lore.kernel.org/all/aq1inYWiNWtZlyoo@gremlin/
