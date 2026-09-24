---
id: sched-20260914-001
date: '2026-09-14'
subject: Cache-aware scheduling does not work well with amd big/little cores
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info>
lore_url: https://lore.kernel.org/all/aqfy8PjSUOYI-_Ju@chenyu-dev/
authors:
- Klaus Kusche
maintainers_involved:
- Chen Yu
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 禁用方案仅编译验证，缺多 LLC 混合 AMD 平台实测
  - 需确认禁用 CAS 是否损失纯 AMD 平台本可受益的场景
  next_action: Klaus 实测 Chen Yu 的禁用补丁并回传数据；有效后再补正式 patch 系列进入评审
contribution_opportunities:
- kind: testing
  description: 在 AMD 混合平台实测「ASYM_PACKING 时禁用 CAS」补丁并回帖数据，可用 python uv build 作敏感用例
- kind: discussion
  description: 分析「开 CAS wallclock 变慢但 cpu seconds 略低」的机理，帮助判断禁用是否最优解
generated_at: '2026-09-15T09:30:00'
source_email_count: 2
related_articles:
- sched-20260910-010
- sched-20260909-009
- sched-20260905-007
tags:
- load_balance
- topology
- x86
title: Cache-aware scheduling does not work well with amd big/little cores
layout: article
---

## TL;DR
本文为增量更新，完整背景见 related_articles。09-14 报告者 Klaus Kusche 结束休假返回，给出三组快速实测：cache-aware scheduling（CAS）在 7.2.5（已含 Tim Chen 的 misfit 补丁）下相对关闭仍整体略慢、wallclock 无改善；而之前被点名叠加的 Chen Yu ITMT 协调补丁（20260810033742）显著恶化，构建超 8 分钟。Chen Yu 据此定位根因——AMD 混合平台依赖 SD_ASYM_PACKING 而非 ASYM_CPUCAPACITY，CAS 与之冲突——并给出「检测到 ASYM_PACKING 时禁用 CAS」的仅编译验证补丁，请 Klaus 实测。

## 背景与问题
AMD 大小核（Strix/HX 类，大核 16MB L3、小核 8MB L3）平台上 CAS（v7.2 合入）效果不佳，部分负载开启后反而变差。前几轮（见 <a class="article-ref" href="/lkm/2026/09/09/sched-20260909-009-cache-aware-scheduling-does-not-work-well-with-amd-big-littl.html">sched-20260909-009</a> / <a class="article-ref" href="/lkm/2026/09/05/sched-20260905-007-cache-aware-scheduling-does-not-work-well-with-amd-big-little-cores.html">sched-20260905-007</a>）已完成归因澄清：被简称 patch 的是 Tim Chen 的 misfit 补丁（20260825174112），而非 Mario 的 debugfs 参数暴露补丁；报告者随后休假。

今日 Klaus 返岗实测，先交代系统状态：`/sys/kernel/sched/debug/domains/*` 在他的系统上**不存在**（即便开了 debugfs）；`/sys/kernel/debug/x86/sched_itmt_enabled` 为 "Y"，`sched_core_priority` 数值正常（大核约为小核两倍）。

## 技术方案
今日无正式合入动作，核心是 Klaus 的三组数据 + Chen Yu 的一个新方向：

- 陈 Yu 定性结论：此前点名的 20260810033742（ITMT 协调补丁）"inhibits ASYM_PACKING and favors Cache-Aware-Scheduling, which is the opposite of what your platform expects"——AMD 混合平台靠 SD_ASYM_PACKING 决定优先级，CAS 的「按 LLC 聚合」与之相反。
- Chen Yu 新提案：检测到 ASYM_PACKING 时直接禁用 CAS（后者倾向于把线程聚到随机 L3，而前者更看重高优先级 CPU）。补丁（仅编译验证）要点：新增 `sched_asym_packing_active` 静态键；`_sched_cache_active_set()` 里若该键为真则 `static_branch_disable_cpuslocked(&sched_cache_active)` 并返回；`build_sched_domains()` 里用 `highest_flag_domain(i, SD_ASYM_PACKING)` 检测并 `inc` 该键，`detach_destroy_domains()` 对应 `dec`。
- Chen Yu 自述 "just compile tested, as I do not have a multi-LLC hybrid AMD platform for testing"。

## 版本演进与当前进展
- 09-05 / 09-09 / 09-10：补丁归因澄清与诊断信息收集，报告者休假（承 <a class="article-ref" href="/lkm/2026/09/09/sched-20260909-009-cache-aware-scheduling-does-not-work-well-with-amd-big-littl.html">sched-20260909-009</a> / <a class="article-ref" href="/lkm/2026/09/10/sched-20260910-010-cache-aware-scheduling-does-not-work-well-with-amd-big-littl.html">sched-20260910-010</a>）。
- 09-14（本文窗口）：Klaus 返岗给出三组实测；Chen Yu 抛出新方向（禁用 CAS if ASYM_PACKING）并附 compile-tested 补丁，等 Klaus 实测。

## Maintainer 意见与讨论焦点
- **Chen Yu（Intel，CAS 相关维护者之一）**：主动定位冲突根因（ASYM_PACKING 与 CAS 互斥）并给出禁用方案，且明确标注只编译验证、缺真实 AMD 混合硬件。
- **Tim Chen**（承 09-10）：已确认 AMD 混合平台依赖 ASYM_PACKING 而非 ASYM_CPUCAPACITY，此前提是被当作对照组的补丁对 Klaus 系统无效。
- 分歧/未闭合处：禁用方案尚未在任何真实 AMD 混合平台验证；Klaus 三组数据混入多个补丁变量（7.2.5 自带 misfit 补丁 + 单独叠加 ITMT 协调补丁），因果隔离仍不干净。

## 合入评估
*likelihood=medium*：方向已收敛到「ASYM_PACKING 与 CAS 互斥」，根因定位明确，但方案未经真实硬件验证。*blocking_issues*：编译验证、无多 LLC 混合 AMD 平台实测；需确认禁用 CAS 是否会在纯 AMD 平台本可受益的场景上造成损失。*next_action*：Klaus 在其平台实测 Chen Yu 的禁用补丁并回传数据；若有效，Chen Yu 需补真实 patch 系列与测试矩阵再进入评审。

## 效果评估
Klaus 三组数据（AMD 大小核，wallclock 时间）：

- kernel build（full LTO）：关闭 CAS 6:16 vs 开启 6:19——几乎不变、略慢；
- python uv build：关闭 4:50 vs 开启 5:20——明显更慢（Klaus 标注 "seems to be a very interesting test case"）；
- 叠加 Chen Yu ITMT 协调补丁（20260810033742）：显著恶化，LTO 步骤与 CC 压缩步骤长时间落在小核，构建总时长超过 8 分钟；
- 补充观察：开 CAS 时尽管 wallclock 更长，cpu seconds 有时略低——报告者未给出量化归因，属观察性数据。

## 我可以参与的点
- kind=testing：在 AMD 混合平台（Strix/HX 类）实测 Chen Yu 的「ASYM_PACKING 时禁用 CAS」补丁并回帖数据，可用 Klaus 的 python uv build 作为敏感用例。
- kind=discussion：Klaus 数据中「开 CAS wallclock 变慢但 cpu seconds 略低」的现象尚无机理解释，可分析其与 ASYM_PACKING/CAS 交互关系，帮助确定禁用方案是否是最优解。

## 参考链接
- Chen Yu 禁用方案回帖：https://lore.kernel.org/all/aqfy8PjSUOYI-_Ju@chenyu-dev/
- Klaus 三组实测回帖：https://lore.kernel.org/all/6b173ff1-6fde-401d-a4a8-6fa8bbe3287c@computerix.info/
- 原始报告（承前）线程根 msgid：2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info
