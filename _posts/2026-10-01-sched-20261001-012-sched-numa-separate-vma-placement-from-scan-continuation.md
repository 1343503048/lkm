---
id: sched-20261001-012
date: '2026-10-01'
subject: 'sched/numa: separate VMA placement from scan continuation'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260930112206.205083-1-gourry@gourry.net>
lore_url: https://lore.kernel.org/all/20260930112206.205083-1-gourry@gourry.net/
authors:
- Gregory Price
maintainers_involved:
- David Hildenbrand
current_version: v4
patch_series:
- version: v4
  msgid: <20260930112206.205083-1-gourry@gourry.net>
  date: '2026-09-30'
  summary: 按 David 意见落地（显式布尔、修 sticky bit、promo_only 分离）；补生产数据；Fixes + Cc stable
  review_outcome: 10-01 David 对 3/7、4/7、5/7 给 Acked-by；作者附传参 fixlet 请 David 折叠
upstream_commit: null
fixes_commit: fc137c0ddab2
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 1/7、2/7、6/7、7/7 未见最终确认
  - 传参 fixlet 待折叠（或发 v5）
  next_action: David 折叠 fixlet 并确认整系列（或作者发 v5），随后收取 backport set
contribution_opportunities:
- kind: testing
  description: 内存 tiering 场景验证含 fixlet 的最终形态，测量提升成功率与 tier 带宽分配
- kind: review
  description: 对 1/7、2/7 补第二意见（本轮未见评审）
generated_at: '2026-10-09T01:00:00'
source_email_count: 4
related_articles:
- sched-20260923-008
- sched-20260925-014
- sched-20260930-015
tags:
- numa_balancing
title: 'sched/numa: separate VMA placement from scan continuation'
layout: article
---

> **subject**：`sched/numa: separate VMA placement from scan continuation`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-008-sched-numa-stop-vma-scan-filters-from-gating-promotion.html">sched-20260923-008</a>：Gregory Price 的 NUMA 内存 tiering 修复系列 v3（7 补丁）——VMA 扫描过滤器（placement_scan 等）此前误门控了页提升（promotion）。
- <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-014-sched-numa-stop-vma-scan-filters-from-gating-promotion.html">sched-20260925-014</a>：David Hildenbrand 逐枚 review v3 的 3/7~5/7，核心意见是 `placement_scan` 的 `&=` 布尔组合难读、建议显式 `if/else if`。
- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-015-sched-numa-stop-vma-scan-filters-from-gating-promotion.html">sched-20260930-015</a>：作者发 v4（7 补丁）按 David 意见落地，并补生产数据（CXL 带宽 45→5-10 GB/s、DRAM 200→250 GB/s、延迟 5ms→800us-2ms），`Fixes: fc137c0ddab2` + `Cc: stable`。
- <a class="article-ref" href="/lkm/2026/10/01/sched-20261001-012-sched-numa-separate-vma-placement-from-scan-continuation.html">sched-20261001-012</a>（今天）：David Hildenbrand 对 v4 的 3/7、4/7、5/7 三枚核心补丁逐一给出 `Acked-by`（backport 集合获 mm 侧认可）；对 4/7 提一处小建议（mm 可从 `vma->vm_mm` 取、只需传 vma），作者当场认同并附上「drop mm argument from vma_needs_placement_scan()」的 fixlet，请 David 折叠或由自己再发 v5。

## 背景与问题

（承接）NUMA balancing 用 hinting fault 同时做任务放置与内存 tier 提升，几个为避免无谓 socket 放置 fault 而设的过滤器却也挡住了提升。生产环境（768 GB DRAM + 256 GB CXL、`kernel.numa_balancing=2`、两个 ~430 GB 数据库负载、大 shmem VMA）下 patch 前 DRAM 带宽 150-200 GB/s、CXL 40-45 GB/s（打满设备）、请求延迟 5 ms+；根因是全局 balancing 模式只说「启用哪些机制」、无法描述单次 VMA/PTE walk 的意图（放置 vs 提升）。今天无新背景，进展是 mm 侧评审到位。

## 技术方案

（承接）v4 七补丁：1/7 promotion-only NUMA 保护 walk；2/7 eligible 共享 folio 提升到 fast tier；3/7 promotion-only 扫描放开 legacy file 放置过滤覆盖的映射；4/7 分离 VMA 放置资格与 partial-scan 继续（`promo_only` 状态）；5/7 扫描 PID-inactive VMA 用于提升；6/7 `change_protection()` flags 用 `BIT()`；7/7 触碰的 NUMA 平衡代码用 VMA flag API。

今天的增量：David 对 4/7 指出 `mm can be had from vma->vm_mm, so likely sufficient to only pass the vma?`（除此外「this looks much clearer to me」）；Gregory 认同并提供 fixlet——`vma_needs_placement_scan(struct mm_struct *mm, struct vm_area_struct *vma)` 改为只收 vma、函数内 `mm = vma->vm_mm`（`kernel/sched/fair.c` +3/−3），声称与 `git am -3` 无冲突，请 David 直接折叠。

## 版本演进与当前进展

- v2（09-11）、v3（09-22）、v4（09-30，`<20260930112206.205083-1-gourry@gourry.net>`）。
- 10-01：David 对 3/7（`<742ced29-d490-4b33-8fff-d6d503c0ee95@kernel.org>`）、4/7（`<e1728faa-5d50-48af-8ba0-5098be9124eb@kernel.org>`）、5/7（`<b64b32b5-711c-424a-8bf1-478ae75b9d20@kernel.org>`）逐一 `Acked-by`；Gregory 回帖认同并附 fixlet（`<20261001132913.486570-1-gourry@gourry.net>`），表示「If nothing else comes up on v4, could you please fold the fixlet below? Otherwise i can spin a v5」。

## Maintainer 意见与讨论焦点

- **David Hildenbrand**（mm 维护者）：3/7、4/7、5/7 三枚 `Acked-by`——覆盖了整个 backport 核心（1/7~5/7 中他此前已逐枚 review 过 3~5/7 的逻辑，v4 落地其全部可读性意见）；4/7 仅余传参精简建议。
- **Gregory Price**（作者）：完全认同建议、提供 conflict-free fixlet；把「折叠 fixlet 还是发 v5」的选择权交给 David。
- 无 NAK；剩余开放点是 1/7、2/7、6/7、7/7 的最终确认（当日未见新意见）与 fixlet 的折叠方式。

## 合入评估

*likelihood=high*。backport 集合（3/7~5/7 获 Acked-by，4/7、5/7 此前已 LGTM/逐轮 review）拿到 mm 侧正式认可，v4 生产数据与 `Fixes:`/`Cc: stable` 齐备，作者与 mm 维护者协作顺畅、剩余仅传参 fixlet 与非核心补丁的确认。*blocking_issues*：1/7、2/7、6/7、7/7 未见 David 或其他维护者的最终确认；fixlet 待折叠（或 v5）。*next_action*：David 折叠 fixlet 并确认整系列（或作者发 v5），随后由 mm/sched 侧维护者收取 1/7~5/7 backport set。

## 效果评估

本日无新数据。既有 v4 cover 生产数据：patch 前 DRAM 150-200 GB/s、CXL 40-45 GB/s（饱和）、延迟 5 ms+；patch 后 DRAM 250+ GB/s、CXL 5-10 GB/s、延迟 800 us-2 ms；热 20 GB hash table 从困在 CXL 变为 DRAM/CXL 均匀分配。

## 我可以参与的点

- `testing`：在内存 tiering（CXL/PMEM + DRAM）场景验证含 fixlet 的 v4 最终形态，测量提升成功率/迁移量与 tier 带宽分配——David 的 Acked-by 覆盖逻辑、缺独立性能复核。
- `review`：1/7（promotion-only walk 的 prot_none 注入意图 plumb）与 2/7（共享 folio 提升）未见本轮意见，可补第二意见。

## 参考链接

- David 对 4/7 的 Acked-by 与建议: https://lore.kernel.org/all/e1728faa-5d50-48af-8ba0-5098be9124eb@kernel.org/
- David 对 3/7 的 Acked-by: https://lore.kernel.org/all/742ced29-d490-4b33-8fff-d6d503c0ee95@kernel.org/
- David 对 5/7 的 Acked-by: https://lore.kernel.org/all/b64b32b5-711c-424a-8bf1-478ae75b9d20@kernel.org/
- Gregory 的 fixlet: https://lore.kernel.org/all/20261001132913.486570-1-gourry@gourry.net/
- v4 cover: https://lore.kernel.org/all/20260930112206.205083-1-gourry@gourry.net/
