---
id: sched-20261110-002
date: '2026-11-10'
subject: 'sched/numa: stop VMA scan filters from gating promotion'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261110150446.2452975-1-gourry@gourry.net>
lore_url: https://lore.kernel.org/all/20261110150446.2452975-1-gourry@gourry.net/
authors:
- Gregory Price
maintainers_involved: []
current_version: v5
patch_series:
- version: v5
  msgid: <20261110150446.2452975-1-gourry@gourry.net>
  date: '2026-11-10'
  summary: 把扫描意图传入 prot_none 注入，promotion-only 扫描穿透放置过滤器
  review_outcome: patch 4 采纳 David 的格式化意见；sashiko east-west false positive 在 changelog
    记录
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 跨 mm 与 sched 子系统，需两方维护者确认
  - 补丁 4/5 需成对 backport 的界定待 stable 维护者认可
  next_action: 等待 David/Rik 及 mm 维护者评审，确认 4/5 打包 backport
contribution_opportunities:
- kind: testing
  description: 在 NUMA tiering（CXL/慢内存）平台复跑 shmem 大 VM，验证热页不再滞留慢层
- kind: review
  description: 核对 patch 4/5 必须成对 backport 的拆分是否有单独可用性
generated_at: '2026-11-11T09:00:00+08:00'
source_email_count: 4
related_articles: []
tags:
- numa_balancing
title: 'sched/numa: stop VMA scan filters from gating promotion'
layout: article
---

## TL;DR

Gregory Price（Meta）发 v5 七补丁系列，修复 NUMA balancing 的 fault-injection（PROT_NONE 喷涂）侧被「为 socket 放置设计的过滤器」误伤、导致内存 tier 升级（promotion）被完全卡死的问题：作者在测 fairness 控制时发现 numa balancing 在最近的 shmem 修复之后彻底失效，热内存长期滞留 CXL 慢层。系列把「扫描意图（placement vs promotion）」显式下传，保留放置扫描的过滤、但允许 promotion-only 扫描穿透这些过滤器。AMD Zen5（768GB DRAM + 256GB CXL）实测 DRAM 带宽 150-200→250+ GB/s、CXL 带宽 40-45→5-10 GB/s、请求延迟从 >5ms 降到 800us-2ms。补丁 1-5 是可 backport 的修复集，6-7 是独立清理。

## 背景与问题

NUMA balancing 同时用 hinting fault 做两件事：任务放置（task placement）和内存层升级（memory-tier promotion）。为「避免无谓的 socket 放置 fault」而设计的一批过滤器，也一并拦掉了升级。作者在测 fairness 控制 [1] 时观察到层间带宽利用异常，追查到 numa balancing 已完全失效，起点是最近的 shmem 修复 [2]。这些测试负载不使用任何其他 NUMA 控制（无 numactl/mbind/mempolicy，无 cpuset.mems），所以问题出在 fault-injecting 侧（喷 PROT_NONE）而非 fault-handling 侧。

核心症结：全局 balancing mode 只表达了「哪些机制被启用」，没有表达某次 VMA/PTE 遍历的「意图」（是放置还是升级）。本系列把扫描意图传入 prot_none 注入逻辑，同时保留放置扫描原有的过滤。

## 技术方案

系列（10 文件 +140/-73）把扫描推理（reasoning）下沉进 prot_none 注入：① `mm: support promotion-only NUMA hinting scans`（在 folio eligibility 检查里派生私有 VMA 状态）；② `mm: allow shared folios to be promoted to a fast tier`（并把升级谓词改名为 `folio_numab_promotable()`）；③ `sched/numa: scan read-only file mappings in tiering mode`（用 promotion-only 扫描穿透 legacy file placement 过滤器）；④ `sched/numa: separate VMA placement from scan continuation`；⑤ `sched/numa: scan PID-inactive VMAs for promotion` 并单独记账 placement 扫描。补丁 4/5 同属一个修复、为便于 review 拆开，但必须一起 backport。补丁 6/7 是独立清理（`change_protection()` flags 用 `BIT()`、NUMA balancing 代码改用 VMA flag API）。

## 版本演进与当前进展

*current_version: v5（2026-11-10，`<20261110150446.2452975-1-gourry@gourry.net>`）*。v5 变化很小：patch 4 一处格式化改动与 changelog 注释（回应 David 与 sashiko 的 east-west false positive 问题）。系列已相当成熟，本次改动收窄到收尾清理。

## Maintainer 意见与讨论焦点

当日缓存中无维护者新回复。v5 changelog 提及 David（评审者）的小改动意见已采纳。无 NAK，无方向性争议；此前 sashiko 提出的 east-west false positive 问题在 patch 4 changelog 中被记录回应。

## 合入评估

*likelihood=medium*。修复动机与实测数据清晰、且带了 backport 边界说明（1-5 为修复集、4/5 需成对 backport），但本次窗口未见 sched/numa 与 mm 维护者的显式 Ack。*blocking_issues*：① 跨 mm 与 sched 两个子系统，需两方维护者确认；② 补丁 4/5 需成对 backport 的界定需 stable 维护者认可。*next_action*：等 David/Rik 及 mm 维护者评审，确认 4/5 打包 backport 后即可推进。

## 效果评估

作者给出 AMD Zen5 平台（768GB DRAM + 256GB CXL，两个约 430GB 的 shmem 大 VM）量化数据：打补丁前 DRAM 带宽 150-200 GB/s、CXL 40-45 GB/s 饱和、请求延迟 >5ms 且长尾、大量热内存滞留 CXL；打补丁后 DRAM 250+ GB/s 持续、CXL 约 5-10 GB/s、延迟 800us-2ms、热内存正确迁移回本地节点。

## 我可以参与的点

- **testing**：在 NUMA tiering（如 CXL/慢内存）平台上复跑作者的 fairness 负载或自建 shmem 大 VM，验证 numa_balancing=2/3 下热页是否不再滞留慢层（作者已验证，社区复现可加速合入）。
- **review**：核对 patch 4/5「必须成对 backport」的拆分是否确实没有单独可用性（这是作者明确标出的边界，值得确认）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110150446.2452975-1-gourry@gourry.net/
- [1] fairness 控制: https://lore.kernel.org/all/20260807202059.2620949-1-joshua.hahnjy@gmail.com/
- [2] shmem 修复: https://lore.kernel.org/all/20260629163337.1264881-1-hannes@cmpxchg.org/
