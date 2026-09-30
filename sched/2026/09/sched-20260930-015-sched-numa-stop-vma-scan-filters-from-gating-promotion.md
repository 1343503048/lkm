# sched/numa: stop VMA scan filters from gating promotion

> **subject**：`sched/numa: stop VMA scan filters from gating promotion`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260923-008：Gregory Price 的 NUMA 内存 tiering 修复系列 v3（7 补丁）——VMA 扫描过滤器（placement_scan 等）此前误门控了页提升（promotion）。
- sched-20260925-014：David Hildenbrand 逐枚 review v3 的 3/7~5/7，核心意见是 `placement_scan` 的 `&=` 布尔组合难读、建议改成显式 `if/else if`，4/7、5/7「LGTM」；作者准备 v4。
- sched-20260930-015（今天）：作者发 **v4**（7 补丁）——按 David 意见落地（避免复杂布尔、修 sticky bit 问题、重命名、分离 `promo_only` 状态等），并补上生产数据（CXL 带宽 45→5-10 GB/s、DRAM 200→250 GB/s、latency 5ms→800us-2ms），`Fixes: fc137c0ddab2` + `Cc: stable`。

## 背景与问题

（承接）NUMA balancing 用 hinting fault 同时做任务放置与内存 tier 提升，几个为避免无谓 socket 放置 fault 而设的过滤器却也挡住了提升。生产环境（768 GB DRAM + 256 GB CXL、`kernel.numa_balancing=2`、两个 ~430 GB 数据库负载、大 shmem VMA）下：patch 前 DRAM 带宽 150-200 GB/s、CXL 带宽 40-45 GB/s（打满设备）、请求延迟 5 ms+ 且尾部更长；根因是全局 balancing 模式只说「启用哪些机制」，无法描述单次 VMA/PTE walk 的意图（放置 vs 提升）。v4 把扫描意图 plumb 进 prot_none 注入、同时保留放置扫描过滤。

## 技术方案

（承接）v4 仍 7 补丁：1/7 加 promotion-only NUMA 保护 walk 并在 folio 资格检查里派生私有 VMA 状态；2/7 允许 eligible 共享 folio 提升到 fast tier、谓词改名 `folio_numab_promotable()`；3/7 用 promotion-only 扫描放开 legacy file 放置过滤覆盖的映射；4/7 分离 VMA 放置资格与 partial-scan 继续；5/7 扫描 PID-inactive VMA 用于提升、并独立计 placement scan；6/7 `change_protection()` flags 用 `BIT()`；7/7 触碰到的 NUMA 平衡代码用 VMA flag API。

v4 changelog（回应 David）：1/7 commit message 修正与 balancing mode 检查提变量；2/7 改名与 typo 修正；3/7 每 VMA 计算一次 `placement_scan`、避免复杂布尔、修缩进；4/7 避免复杂布尔、in-progress 状态存为 `numab_state->promo_only`；5/7 避免复杂布尔、修「resumed scan 令合法 VMA 掉出 scanning-eligible 集合」的 sticky bit 问题。补丁 4 与 5 须一起 backport。

## 版本演进与当前进展

- v2（09-11）、v3（09-22，封面 `<20260922182928.2199090-1-gourry@gourry.net>`，7 补丁）。
- v4（09-30，封面 `<20260930112206.205083-1-gourry@gourry.net>`，7 补丁）：按 David 意见落地 + 补生产数据 + `Fixes: fc137c0ddab2` + `Cc: stable`。

## Maintainer 意见与讨论焦点

- David Hildenbrand 的意见（v3 期间）集中在可读性（连续 `&=` 难读、建议显式 if/else if），v4 已逐条落地。当日无新回帖（v4 刚发）。
- 无 NAK；该系列跨 mm + sched、仍需 mm 与 NUMA 平衡侧维护者（David、可能 Peter/Vincent）对 v4 的再确认。

## 合入评估

*likelihood=medium*。v4 已把 David 的可读性意见落地、补上生产环境量化数据与 `Fixes:`/`Cc: stable`，清晰度与证据充分性明显提升；但系列跨 mm/sched、尚未见第二维护者明确合入信号，backportable 修复集（1/7~5/7）需 mm 侧确认。*blocking_issues*：v4 仍未获 David 的第二轮确认或合入信号；缺第二位熟悉 NUMA balance 的 reviewer。*next_action*：等 David 对 v4 再确认，争取 mm 侧维护者合入 1/7~5/7（backport set）。

## 效果评估

v4 cover 给出生产数据：patch 前 DRAM 150-200 GB/s、CXL 40-45 GB/s（饱和）、延迟 5 ms+ 尾部更长；patch 后 DRAM 250+ GB/s、CXL 约 5-10 GB/s、延迟 800 us-2 ms。细分案例：一个热 20 GB hash table 此前完全困在 CXL、把 CXL 带宽推到不可持续水平，修复后 DRAM/CXL 均匀分、tier residency 随负载、CXL 带宽从 45 GB/s 降到 5-10 GB/s、DRAM 从 ~200 升到 250 GB/s+，数据库负载吞吐大幅改善。

## 我可以参与的点

- `review`：对 NUMA 平衡/tiering 熟悉者可逐枚审读 v4 的 1/7~5/7（尤其 4/7 的 `promo_only` 状态分离与 5/7 的 sticky bit 修复），给出第二意见（David 此前自陈未完全消化逻辑）。
- `testing`：在内存 tiering（CXL/PMEM + DRAM）场景验证 v4 放开被门控的提升，并测量提升成功率/迁移量与 tier 带宽分配。

## 参考链接

- lore（v4 cover）: https://lore.kernel.org/all/20260930112206.205083-1-gourry@gourry.net/
- lore（v3 cover）: https://lore.kernel.org/all/20260922182928.2199090-1-gourry@gourry.net/

---
id: sched-20260930-015
date: '2026-09-30'
subject: 'sched/numa: stop VMA scan filters from gating promotion'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260930112206.205083-1-gourry@gourry.net>'
lore_url: 'https://lore.kernel.org/all/20260930112206.205083-1-gourry@gourry.net/'
authors:
  - 'Gregory Price'
maintainers_involved:
  - 'David Hildenbrand'
current_version: v4
patch_series:
  - version: v3
    msgid: '<20260922182928.2199090-1-gourry@gourry.net>'
    date: '2026-09-22'
    summary: '7 补丁：放开 tiering 只读文件映射/PID 不活跃 VMA 扫描，解耦 VMA 放置与扫描继续'
    review_outcome: 'David 逐枚 review 3/7~5/7，提 placement_scan 可读性意见，4/7、5/7 LGTM'
  - version: v4
    msgid: '<20260930112206.205083-1-gourry@gourry.net>'
    date: '2026-09-30'
    summary: '按 David 意见落地（显式布尔、修 sticky bit、重命名）；补生产数据；Fixes + Cc stable'
    review_outcome: '无新回帖'
upstream_commit: null
fixes_commit: 'fc137c0ddab2'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'v4 尚未获 David 第二轮确认或合入信号'
    - '缺第二位熟悉 NUMA balance 的 reviewer'
  next_action: '等 David 对 v4 再确认，争取 mm 侧维护者合入 1/7~5/7（backport set）'
contribution_opportunities:
  - kind: review
    description: '逐枚审读 v4 1/7~5/7（promo_only 状态分离与 sticky bit 修复），给出第二意见'
  - kind: testing
    description: '在内存 tiering 场景验证 v4 放开被门控的提升并测量成功率/迁移量与 tier 带宽分配'
generated_at: '2026-10-01T01:00:00'
source_email_count: 3
related_articles:
  - sched-20260923-008
  - sched-20260925-014
tags:
  - numa_balancing
---