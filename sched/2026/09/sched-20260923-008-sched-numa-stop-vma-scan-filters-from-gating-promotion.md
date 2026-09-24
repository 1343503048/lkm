# sched/numa: stop VMA scan filters from gating promotion

## TL;DR
- sched-20260918-013：Gregory Price 的 NUMA tiering 修复 v2 系列 4/4（去掉 VMA PID 活动对 promotion 的门控）获 Peter Zijlstra 有条件点头（等 Mel Gorman 确认）；David Hildenbrand 批评 `promo_only()` 计算太 messy；作者回应已试 3~4 种写法、这是最不难看的。更早 v1 名为「stop VMA scan filters from gating promotion」。
- sched-20260919-009：该系列（v2 4-patch，整体目标是移除 VMA 扫描过滤器对 promotion 的门控）在 cover 信层面收到 Zi Yan 的测试范围质询；Gregory 澄清这些修复源于 Joshua 的 tiered memcg limits 补丁测试时发现的「numa balancing 彻底失效」，纯内部一致性问题。
- sched-20260923-008（今天）：Gregory Price 发出 v3（7 枚）：把可回合的修复集扩为 5 枚（新增「scan PID-inactive VMA for promotion」），补上 `Fixes:`/`Cc: stable` 标签（3/7 `Fixes: c574bbe91703`、4/7 `Fixes: fc137c0ddab2`），另加 2 枚独立 mm 清理（BIT()、VMA flag helper）。cover 给出首个量化收益：DRAM 带宽 150-200→250+ GB/s、CXL 带宽 40-45→5-10 GB/s、请求延迟 >5ms→800us-2ms。

## 背景与问题
- sched-20260918-013：NUMA memory-tiering 模式下，VMA 的 PID 活动被用作 promotion 的门控条件，导致部分应被提升的内存页无法提升。
- sched-20260919-009：系列整体要解决的是 NUMA balancing 用 hinting fault 同时做任务放置与 memory-tier 晋升时，几个为避免无效 socket-placement fault 而设的过滤器误伤了 promotion；测试源于 tiered memcg limits 补丁发现的「numa balancing 彻底失效」。
- sched-20260923-008（今天）：生产部署（kernel.numa_balancing=2，768 GB DRAM + 256 GB CXL，两个 ~430 GB 数据库负载、大 shmem VMA）出现 NUMA balancing 行为劣化：修前 DRAM 带宽仅 150-200 GB/s、CXL 带宽 40-45 GB/s 打到设备饱和、请求延迟 >5 ms 且尾部长。

## 技术方案
- sched-20260918-013：移除 VMA PID 活动对 promotion 的门控，使 promotion 不再被该条件阻挡（当前实现的 `promo_only()` 计算被 David 认为过于绕）。
- sched-20260919-009：系列核心思路是把 scan reasoning 塞进 prot_none 注入、同时保留 placement 过滤。
- sched-20260923-008（今天）：v3 结构变化——**patches 1-5 = 可回合的修复集**（须一起回退）：1. mm: support promotion-only NUMA hinting scans；2. mm: allow shared folios to be promoted to a fast tier；3. sched/numa: scan read-only file mappings in tiering mode（`Fixes: c574bbe91703`）；4. sched/numa: separate VMA placement from scan continuation（`Fixes: fc137c0ddab2`，`vma_is_accessed()` 改名 `vma_needs_placement_scan()`，扫描续态移到 `task_numa_work()`）；5. sched/numa: scan PID-inactive VMAs for promotion（新增）。**patches 6-7 = 独立清理**：`mm: use BIT() for change_protection() flags`、`mm: use VMA flag helpers in NUMA balancing`。

## 版本演进与当前进展
- v2（09-11，4 枚）：去掉 VMA PID 活动对 promotion 的门控（4/4）、scan read-only file mappings（3/4），获 Peter Zijlstra 有条件点头。
- **v3**（09-22 23:29 UTC，`<20260922182928.2199090-1-gourry@gourry.net>`，7 枚）：本日进入缓存（0/7、3/7、4/7）。补 `Fixes:`/`Cc: stable` 标签，修复集扩为 5 枚，新增 2 枚独立清理。

## Maintainer 意见与讨论焦点
本日无维护者新表态（v3 首日）。此前 Zi Yan 的「测试范围」质询在 v3 cover 中以明确的生产部署背景与量化数据得到回应。无 NAK；3/4、4/4 的 VMA 判定实现意见（`promo_only()` 计算过绕、`vma_is_accessed()` 改名与扫描续态位置）是否已全部落实，需待复审。

## 合入评估
*likelihood=medium*。系列方向清晰、带 `Fixes:`/`Cc: stable` 与首次量化收益数据，可回合性增强；但仍属 mm + sched 跨子系统改动（10 文件），需 mm 维护者与 sched 侧复审，3/4、4/4 的既有实现意见待确认。*blocking_issues*：mm 侧（mempolicy/memory-tiers 等）维护者 ack 未取得；3/4、4/4 既有 review 意见待落实。*next_action*：等 mm/sched 维护者对 v3 复审，确认修复集可单独回退。

## 效果评估
cover 给出首个量化收益（768 GB DRAM + 256 GB CXL，两个 ~430 GB 数据库负载）：

- DRAM 带宽：150-200 GB/s → **250+ GB/s**
- CXL 带宽：40-45 GB/s（打满设备）→ **约 5-10 GB/s**
- 请求延迟：>5 ms（尾部长）→ **800 us - 2 ms**

为系列首次出现的实测背书。

## 我可以参与的点
- kind=testing：在 NUMA tiering 环境按「预期行为列表」（Zi Yan 建议）核对 7 枚补丁各自行为，补充可对照数据。
- kind=review：评估 5 枚修复集移除 promotion 门控后是否存在过度 promotion 的回归风险（尤其新增的 patch 5 PID-inactive 扫描）。

## 参考链接
- lore（v3 cover）: https://lore.kernel.org/all/20260922182928.2199090-1-gourry@gourry.net/
- lore（v2 cover）: https://lore.kernel.org/all/20260911001826.2109390-1-gourry@gourry.net/

---
id: sched-20260923-008
subject: 'sched/numa: stop VMA scan filters from gating promotion'
date: '2026-09-23'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260922182928.2199090-1-gourry@gourry.net>'
lore_url: 'https://lore.kernel.org/all/20260922182928.2199090-1-gourry@gourry.net/'
authors:
  - 'Gregory Price'
maintainers_involved: []
current_version: v3
patch_series:
  - version: v2
    msgid: '<20260911001826.2109390-1-gourry@gourry.net>'
    date: '2026-09-11'
    summary: '4 枚：移除 VMA 扫描过滤器对 promotion 的门控 + tiering 扫描只读文件映射'
    review_outcome: 'Zi Yan 质询测试范围，作者澄清'
  - version: v3
    msgid: '<20260922182928.2199090-1-gourry@gourry.net>'
    date: '2026-09-22'
    summary: '7 枚：修复集扩为 5 枚并补 Fixes/Cc: stable，另加 2 枚 mm 清理'
    review_outcome: '首日，待 mm/sched 复审'
upstream_commit: null
fixes_commit: 'c574bbe91703'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'mm 侧维护者 ack 未取得'
    - '3/4、4/4 既有 review 意见待确认落实'
  next_action: '等 mm/sched 维护者复审 v3，确认修复集可单独回退'
contribution_opportunities:
  - kind: testing
    description: '按预期行为列表在 tiering 环境核对 7 枚补丁行为'
  - kind: review
    description: '评估移除 promotion 门控后是否存在过度 promotion 回归风险'
generated_at: '2026-09-24T09:00:00'
source_email_count: 3
related_articles:
  - sched-20260919-009
  - sched-20260918-013
tags:
  - numa_balancing
---