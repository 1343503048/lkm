# sched/numa: scan PID-inactive VMAs for promotion

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261110-002：Gregory Price（Meta）发 v5 七补丁系列，修复 NUMA balancing 的 fault-injection（PROT_NONE 喷涂）侧被「为 socket 放置设计的过滤器」误伤、导致内存 tier 升级（promotion）被完全卡死的问题：作者在测 fairness 控制时发现 numa balancing 在最近的 shmem 修复之后彻底失效，热内存长期滞留 CXL 慢层。系列把「扫描意图（placement vs promotion）」显式下传，保留放置扫描的过滤、允许 promotion-only 扫描穿透。AMD Zen5 实测 DRAM 带宽 150-200→250+ GB/s、CXL 40-45→5-10 GB/s、请求延迟 >5ms→800us-2ms。
- sched-20261111-019（今天）：**作者回应 sashiko-bot 对 patch 5/7 的评审**——sashiko 认为 `prev_scan_seq` 的跳过会波及 `prev_placement_scan_seq`；作者反驳其影响被夸大：模式 1（placement）/2（tiering）行为与原来完全一致，只有模式 3（placement+tiering）下 starvation 计数器不被复位——但 VMA 仍被扫描、一切照常工作。作者称可另发一个补丁修这点，但影响很低、不值得为此增加 churn。

## 背景与问题

（承接 sched-20261110-002）NUMA balancing 同时用 hinting fault 做「任务放置」和「内存层升级」两件事；为「避免无谓 socket 放置 fault」设计的过滤器也一并拦掉了升级。全局 balancing mode 只表达「哪些机制启用」，未表达某次 VMA/PTE 遍历的意图。本系列把扫描意图传入 prot_none 注入逻辑，保留放置扫描过滤、允许 promotion-only 扫描穿透。patch 5/7 处理「PID-inactive VMA」的 promotion 扫描，并单独记账 placement 扫描。

## 技术方案

（承接 v5）patch 5/7 `scan PID-inactive VMAs for promotion` 让 promotion-only 扫描覆盖 PID-inactive 的 VMA。今日讨论的是其内部 `prev_scan_seq` 跳过逻辑：sashiko 指出该跳过现在也适用于 `prev_placement_scan_seq`（placement 侧），作者回应这是既有条件、三模式下行为可预期——模式 3 唯一差异是 starvation 计数器未复位，但 VMA 仍被扫描故无功能影响，可另发低影响补丁。

## 版本演进与当前进展

*current_version: v5（2026-11-10，`<20261110150446.2452975-1-gourry@gourry.net>`）*。今日为评审回应，无新版本；作者倾向不为低影响边角另发补丁（除非后续要求）。

## Maintainer 意见与讨论焦点

- **sashiko-bot（AI 评审）**：对 patch 5/7 的 `prev_scan_seq` 跳过提出质疑。
- **Gregory Price（作者）**：逐条反驳，认为影响被夸大、三模式行为可预期，且另发补丁不值得 churn。
- 无维护者 NAK；分歧为低影响边角，作者选择「先不改」。

## 合入评估

*likelihood=medium*。系列修复的是真实且影响重大的 promotion 失效问题（有明确 benchmark），补丁 1-5 为可 backport 修复集；但仍处 AI 评审交互与维护者确认阶段，今日仅回应 sashiko、无维护者新表态。*blocking_issues*：无硬阻塞；等 sched/numa 维护者（Mel Gorman 等）对 v5 的实质评审。*next_action*：维护者评审 v5；作者决定是否补 patch 5/7 的 starvation 复位边角。

## 效果评估

（承接 v5 数据）AMD Zen5（768GB DRAM + 256GB CXL）：DRAM 带宽 150-200→250+ GB/s、CXL 带宽 40-45→5-10 GB/s、请求延迟 >5ms→800us-2ms。今日无新增数据。

## 我可以参与的点

- **testing**：在带 CXL 内存层的系统上复测 promotion 是否恢复、以及 mode 3 下 starvation 计数器不复位是否会在长跑中累积出可观测影响（作者认为不会，值得独立验证）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110150446.2452975-1-gourry@gourry.net/
- 作者对 sashiko 的回应: https://lore.kernel.org/all/179434297609.2530531.2349001562856798404.b4-reply@b4/

---
id: sched-20261111-019
date: '2026-11-11'
subject: "sched/numa: scan PID-inactive VMAs for promotion"
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: "<20261110150446.2452975-1-gourry@gourry.net>"
lore_url: "https://lore.kernel.org/all/20261110150446.2452975-1-gourry@gourry.net/"
authors: [Gregory Price]
maintainers_involved: []
current_version: v5
patch_series:
  - version: v5
    msgid: "<20261110150446.2452975-1-gourry@gourry.net>"
    date: '2026-11-10'
    summary: "把扫描意图传入 prot_none 注入，允许 promotion-only 扫描穿透放置过滤器"
    review_outcome: "回应 sashiko 对 5/7 的质疑，称影响被夸大"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: "sched/numa 维护者评审 v5"
contribution_opportunities:
  - kind: testing
    description: "在带 CXL 内存层系统复测 promotion 恢复与 mode 3 starvation 计数器影响"
generated_at: "2026-11-12T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261110-002]
tags: [numa_balancing]
---