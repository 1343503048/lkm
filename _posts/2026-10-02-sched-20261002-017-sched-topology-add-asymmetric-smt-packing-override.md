---
id: sched-20261002-017
date: '2026-10-02'
subject: 'sched/topology: Add asymmetric SMT packing override'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <20260929165538.726616-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260929165538.726616-3-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
current_version: v7
patch_series:
- version: v6
  msgid: <20260917140707.3807229-1-arighi@nvidia.com>
  date: '2026-09-17'
  summary: sched_smt_asym_packing={auto,on,off} boot 选项
  review_outcome: Vincent 质疑 auto/off 冗余；Shrikanth 三点疑问
- version: v7
  msgid: <20260929165538.726616-1-arighi@nvidia.com>
  date: '2026-09-30'
  summary: 收为仅 =on；补文档
  review_outcome: Breno Tested-by；10-01 合入 tip/sched/core
upstream_commit: 648d44bda7314ffb5805f2bea8910b4cdccaecd0
fixes_commit: null
merged_branch: tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 tip 树进下个合并窗口
contribution_opportunities:
- kind: review
  description: 评审新内核参数在 arm64/ppc 自定义 SMT 拓扑回调下的语义边界与文档一致性
generated_at: '2026-10-03T01:00:00'
source_email_count: 1
related_articles:
- sched-20260919-007
- sched-20260930-014
tags:
- topology
- hyperthreading
title: 'sched/topology: Add asymmetric SMT packing override'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/19/sched-20260919-007-sched-topology-add-asymmetric-smt-packing-override.html">sched-20260919-007</a>：2/2（新增内核参数覆盖 asymmetric SMT packing）收到 Vincent Guittot 的质疑——`auto` 取值冗余、仅 `on` 强制项有意义；Andrea 两度回应，说明该参数是 ACPI 固件属性标准化前的过渡方案，并同意砍掉 `auto`/`off`、只保留显式强制项。
- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-014-sched-enable-preferred-smt-siblings-on-nvidia-olympus.html">sched-20260930-014</a>：作者发 v7——boot 选项收紧为只接受 `sched_smt_asym_packing=on`；补上吞吐量化（OpenBLAS +3.20%、NVPL +6.73%）；1/2 集齐多位 reviewer 的 Reviewed-by，系列高度收敛。
- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-017-sched-topology-add-asymmetric-smt-packing-override.html">sched-20261002-017</a>（今天）：**v7 系列 2/2 已被 Peter Zijlstra 合入 tip/sched/core**（commit `648d44bda7314ffb5805f2bea8910b4cdccaecd0`，CommitterDate 2026-10-01，tip-bot 于 10-02 回帖公告）。合入版本带 Breno Leitao 的 Tested-by。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-014-sched-enable-preferred-smt-siblings-on-nvidia-olympus.html">sched-20260930-014</a>）NVIDIA Olympus 的 Spatial SMT 需要 SMT 层的 asymmetric packing 策略，但其固件无法描述该偏好；从 CPU 型号推断又会把平台特定策略嵌进内核。POWER7 则由 arch 自设在 SMT 域上使用 `SD_ASYM_PACKING`，无需 boot 选项。因此需要一个显式的内核参数，让固件不描述偏好的平台可以强制开启 SMT 层 asymmetric packing，同时不改变省略时的架构/固件拓扑。

## 技术方案

（承接）2/2 新增 `sched_smt_asym_packing=on` boot 选项（v7 收紧后仅此一档，省略即保持原拓扑）：

- `__setup("sched_smt_asym_packing=", ...)` 早期参数，仅接受字符串 `on`。
- 在 `sd_init()` 中对带 `SD_SHARE_CPUCAPACITY` 的调度域追加 `SD_ASYM_PACKING` 标志——中央化应用，覆盖 powerpc 等使用自定义 SMT 拓扑回调的架构。
- 优先级仍由 `arch_asym_cpu_priority()` 决定：弱默认偏好低编号逻辑 CPU，架构覆盖保持权威；等优先级的 sibling 不建立偏好。x86 在 `CONFIG_SCHED_MC_PRIO` 下两个 SMT sibling 通常同核优先级，开启该选项不会偏向任一 sibling。
- 同步更新 `Documentation/admin-guide/kernel-parameters.txt`（+12 行文档）。

## 版本演进与当前进展

- v6（09-17，`<20260917140707.3807229-1-arighi@nvidia.com>`）：`{auto,on,off}` 三档设计，Vincent/Shrikanth 质疑冗余。
- v7（09-30，`<20260929165538.726616-1-arighi@nvidia.com>`）：收为仅 `=on`。
- 10-01 合入 tip/sched/core（commit `648d44bda7314ffb5805f2bea8910b4cdccaecd0`，`kernel/sched/topology.c` +18、文档 +12），10-02 tip-bot 公告。补丁链接 `https://patch.msgid.link/20260929165538.726616-3-arighi@nvidia.com`。

## Maintainer 意见与讨论焦点

- 无 NAK。Vincent Guittot 此前对 `auto`/`off` 冗余的质疑与 Shrikanth Hegde 的三点疑问（changelog 缺失、为何不由 arch 提供、对不收益架构的困惑）均已在 v7 的收紧与文档补全中回应。
- Peter Zijlstra 直接收取，未提额外意见；合入 commit 带 Breno Leitao `Tested-by`。

## 合入评估

*likelihood=merged*。已合入 `tip/sched/core`（commit `648d44bda7314ffb5805f2bea8910b4cdccaecd0`），与 1/2（<a class="article-ref" href="/lkm/2026/10/02/sched-20261002-016-sched-fair-honor-asymmetric-smt-priority-in-idle-selection.html">sched-20261002-016</a>）同批进树。*blocking_issues*：无。*next_action*：随 tip 树进下个合并窗口；新内核参数已定稿为仅 `=on`。

## 效果评估

本补丁为 boot 选项与文档（`kernel/sched/topology.c` +18 / kernel-parameters.txt +12），自身无性能数据；系列级吞吐数据见 1/2 文章（OpenBLAS +3.20%、NVPL +6.73%）。

## 我可以参与的点

- `review`：评审新内核参数在 arm64/ppc 自定义 SMT 拓扑回调下的语义边界与文档一致性（合入后仍可提 follow-up）。

## 参考链接

- lore（v7 cover）: https://lore.kernel.org/all/20260929165538.726616-1-arighi@nvidia.com/
- lore（2/2 补丁）: https://lore.kernel.org/all/20260929165538.726616-3-arighi@nvidia.com/
- tip commit: https://git.kernel.org/tip/648d44bda7314ffb5805f2bea8910b4cdccaecd0
