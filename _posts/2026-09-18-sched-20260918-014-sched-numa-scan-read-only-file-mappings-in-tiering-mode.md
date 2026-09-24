---
id: sched-20260918-014
date: '2026-09-18'
subject: 'sched/numa: scan read-only file mappings in tiering mode'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260911001826.2109390-4-gourry@gourry.net>
lore_url: https://lore.kernel.org/all/20260911001826.2109390-4-gourry@gourry.net/
authors:
- Gregory Price
maintainers_involved:
- David Hildenbrand
- Lorenzo Stoakes
current_version: v2
patch_series:
- version: v1
  msgid: null
  date: '2026-09-07'
  summary: tiering 模式扫描只读文件映射（早期版本，见 sched-20260907-009）
  review_outcome: 见 sched-20260907-009
- version: v2
  msgid: <20260911001826.2109390-4-gourry@gourry.net>
  date: '2026-09-11'
  summary: 纳入 4 补丁系列，VMA 判定搬入 helper
  review_outcome: David/Lorenzo 要求更清晰 VMA 语义；作者坚持最小可回移修复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - VMA 判定 helper 语义与命名待收敛
  - 清理 patch 是否拆分待定
  next_action: 与 David/Lorenzo 就 VMA 判定语义达成一致后推进
contribution_opportunities:
- kind: new_patch
  description: 独立提交 vma_maps_shared_readonly_file() 的 VMA helper 清理
- kind: review
  description: 确认各 VMA 边界下的正确判定语义
generated_at: '2026-09-19T09:00:00'
source_email_count: 7
related_articles:
- sched-20260907-009
tags:
- numa_balancing
- mm
title: 'sched/numa: scan read-only file mappings in tiering mode'
layout: article
---

## TL;DR
增量更新：Gregory Price 的 NUMA tiering 修复（v2 系列 3/4，让 tiering 模式也扫描只读文件映射）本日集中讨论 VMA 判定语义——David Hildenbrand 认为函数名误导、应用新 VMA flags API；Lorenzo Stoakes 给出详尽的 VMA 标志分析并建议引入 `vma_maps_shared_readonly_file()` helper；作者坚持先做"可回移的最小 bugfix"、把更激进的 VMA 清理留给后续 patch。

## 背景与问题
背景见 sched-20260907-009：memory-tiering 模式下，只读文件映射（如库文件/数据文件的 MAP_SHARED 只读映射）此前不被 NUMA 扫描，导致其页面无法被正确迁移/提升到更近的 memory tier。

## 技术方案
- 在 tiering 模式下把"只读文件映射"纳入扫描范围；v2 把既有 VMA 判定代码搬到 helper 中（作者未改动既有判定逻辑）。
- 本日争议聚焦判定条件：作者现用 `vma->vm_file && !vma_test(vma, VMA_WRITE_BIT)`（近似），David/Lorenzo 建议用 `VMA_MAYSHARE_BIT && !VMA_MAYWRITE_BIT` 语义。

## 版本演进与当前进展
- v1（09-07，`<20260907-…-gourry@gourry.net>`）：单补丁，见 sched-20260907-009。
- v2 3/4（09-11，`<20260911001826.2109390-4-gourry@gourry.net>`）：纳入 4 补丁系列；本日围绕 VMA 判定展开讨论。

## Maintainer 意见与讨论焦点
- **David Hildenbrand**：MAP_PRIVATE 也可带写权限映射只读文件，函数名误导；建议 helper 放到其他 vma helper 旁、语义清晰；倾向 >80c 单行或直接用 `numab_mode & NUMA_BALANCING_MEMORY_TIERING` 布尔；可能可去掉某 flag。
- **Lorenzo Stoakes**：用新 VMA flags API；`VMA_READ_BIT` 判定存疑（写隐含读）；建议 helper `vma_maps_shared_readonly_file()` 用 `vma_test(vma, VMA_MAYSHARE_BIT) && !vma_test(vma, VMA_MAYWRITE_BIT)`；提醒 MAP_PRIVATE-/dev/zero 匿名、驱动清 VMA_MAYWRITE_BIT、写密封 memfd 等边界。
- **Gregory Price（作者）**：承认建议合理，但想平衡"改进"与"可回移 bugfix"；自己只是把既有 VMA 判定搬进 helper、未评估其正确性；明确反对"修 bug 同时顺手改其他微妙逻辑"的混合 patch，请 David/Lorenzo 在补丁之上另提清理 patch。
- 分歧点：本补丁该"最小可回移修复"还是"顺带重写 VMA 判定语义"；VMA 判定 helper 的最终语义。

## 合入评估
*likelihood=medium*。方向明确、作者坚持最小可回移修复，但 VMA 判定语义尚未收敛（David/Lorenzo 要求更清晰语义，作者请其另提 patch）。*blocking_issues*：VMA 判定 helper 语义与命名待定；清理 patch 是否拆分。*next_action*：作者与 David/Lorenzo 就 VMA 判定语义达成一致（最小修复 + 独立的清理 patch），再推进。

## 效果评估
本日无新增 benchmark。作者强调该系列是"可回移的 bugfix"，并指出 tiering 特性自 ~6.14 起的使用数据已被此 bug 影响（定性陈述，未见量化数据）。

## 我可以参与的点
- kind=new_patch：按 Lorenzo 建议，独立提交 `vma_maps_shared_readonly_file()` 的 VMA helper 清理 patch（作者已明确希望把清理拆到补丁之上）。
- kind=review：确认只读文件映射在 MAP_SHARED/MAP_PRIVATE、驱动清 MAYWRITE、memfd 等边界的正确判定语义。

## 参考链接
- lore（v2 3/4）: https://lore.kernel.org/all/20260911001826.2109390-4-gourry@gourry.net/
