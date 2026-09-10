# Cache-aware scheduling does not work well with amd big/little cores

## TL;DR
本文为增量更新，完整背景见 related_articles 中的 sched-20260909-009 / sched-20260905-007。09-10 线程出现关键技术修正：Tim Chen 经 Ricardo 提醒确认 AMD 混合 CPU 依赖 SD_ASYM_PACKING 而非 SD_ASYM_CPUCAPACITY，因此他此前被当作对照组的补丁（20260825174112）对 Klaus 的系统根本无效；新的候选是 Chen Yu 的 ITMT 与 cache-aware scheduling 协调补丁，Tim 请 Klaus 叠加 Mario 的 ITMT/debugfs 补丁测试，Chen Yu 跟进索要调度域 dump 等三项诊断信息。报告者仍在休假，验证悬空。

## 背景与问题
Klaus Kusche 报告 AMD 大小核（Strix/HX 类，大核 16MB L3、小核 8MB L3）平台上 cache-aware scheduling 效果不佳：开启后部分负载反而变差，且需要打开 ITMT 才有改善。前几日线程已完成补丁归因澄清（被简称 patch 的是 Tim Chen 的 20260825174112.2580942-1，而非 Mario Limonciello 的 c1e7fe5e75ed debugfs 参数暴露补丁），报告者随后休假。

## 技术方案
本日的新分析（无新代码）：
- Tim Chen：AMD hybrid CPU 用的是 SD_ASYM_PACKING，不是 SD_ASYM_CPUCAPACITY；他的补丁只修 SD_ASYM_CPUCAPACITY 情形，「would not have an effect on your test system」。Klaus 需要开 ITMT 才能改善这一现象也指向同一结论（ITMT 走的正是 asym packing 路径）。
- 新的候选修复：Chen Yu 的 ITMT 与 cache-aware scheduling 兼容补丁（https://lore.kernel.org/lkml/20260810033742.1688718-1-yu.c.chen@intel.com/），作用是防止任务卡死在错误的 LLC（ITMT 场景）。Tim 请 Klaus 把它与 Mario 的 ITMT/debugfs 补丁叠加测试。
- Chen Yu 确认该补丁意图（coordinate ITMT with cache-aware scheduling），并索要三项诊断：/sys/kernel/sched/debug/domains/* 的 dump（确认 MC 域设置了 SD_ASYM_PACKING）、/sys/kernel/debug/x86/sched_itmt_enabled（确认 ITMT 开启）、/sys/kernel/debug/x86/sched_core_priority（查看 CPU 优先级）。

## 版本演进与当前进展
非补丁线程，无版本。进展时间线：09-09 完成补丁归因澄清、报告者休假 → 09-10 Tim 推翻「他的补丁适用于 AMD」的前提、给出 Chen Yu ITMT 补丁作为新候选并定义验证步骤 → Chen Yu 补充诊断信息清单。当前所有验证动作都卡在报告者（或其 HX-370 机器）身上。

## Maintainer 意见与讨论焦点
- Tim Chen（Intel，ITMT/cache-aware 相关工作作者）：主动修正自己补丁的适用范围，给出可执行的测试组合（Chen Yu 补丁 + Mario debugfs 补丁）。
- Chen Yu（Intel，ITMT 兼容补丁作者）：确认补丁意图，给出三项诊断信息要求，并表态愿意跟进（前文 09-09 他已启动 sanity 测试，见 sched-20260910-011 关联线程）。
- 焦点/未决：AMD 平台上 ITMT（x86 asym packing 机制）与 cache-aware scheduling 的交互尚无人在真实 AMD 大小核机器上按新组合验证；Tim 此前提过 CAS 主动负载均衡路径有两个待修问题，本线程仍未展开。

## 合入评估
不适用（问题报告线程，无待合入补丁）。相关补丁状态：Chen Yu 的 ITMT 兼容补丁 2026-08-10 已发出（其合入状态本缓存内无信息，未获取到）；Tim 的 20260825174112 补丁与本问题的相关性已被否定。likelihood: unknown——在 AMD 平台验证完成前，无法判断问题是会被 Chen Yu 补丁解决还是需要 AMD 侧（SD_ASYM_PACKING 语义下）的新修复。

## 效果评估
本日无新测试数据。既有数据（Klaus 的对照测试）因补丁归因修正而需要重新解读：原先归因给 Tim 补丁的对照组在 AMD 上无效，相关结论作废。Chen Yu 提到已启动 sanity 测试、结果未出。

## 我可以参与的点
- 在 AMD 大小核机器（Strix Point/HX 类）上按新组合复现：基线 / +Chen Yu ITMT 补丁 / +Mario debugfs 补丁，并附上 Chen Yu 要的三项诊断信息（domains dump、sched_itmt_enabled、sched_core_priority）回帖——报告者休假中，这是当前线程最缺的数据（testing）。
- 检查 AMD 平台（amd-pstate preferred core）下 SD_ASYM_PACKING 在 MC 域的设置路径与 Intel ITMT 的差异，判断 Chen Yu 补丁的 intel_pstate/ITMT 假设在 AMD 上是否成立（review）。
- 追问 Tim 此前提到的 CAS active load balance 路径两个待修问题与 nr_pref_llc_running 讨论线（sched-20260910-011）是否同源（discussion）。

## 参考链接
- lore thread（本日 Tim 的修正）: https://lore.kernel.org/all/4da55124e32dd0587a3516c8f5ed512bffbbb42e.camel@linux.intel.com/
- Chen Yu 的诊断要求: https://lore.kernel.org/all/2fe2c681-b748-41fa-8b56-1169c86cefbc@intel.com/
- Chen Yu 的 ITMT 兼容补丁（邮件内引用）: https://lore.kernel.org/lkml/20260810033742.1688718-1-yu.c.chen@intel.com/
- Tim 此前的 SD_ASYM_CPUCAPACITY 补丁（邮件内引用，已确认不适用 AMD）: https://lore.kernel.org/lkml/20260825174112.2580942-1-tim.c.chen@linux.intel.com/

---
id: sched-20260910-010
date: 2026-09-10
subject: "Cache-aware scheduling does not work well with amd big/little cores"
subsystem: sched
type: bug
status: stalled
severity: medium
thread_root_msgid: "<2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info>"
lore_url: "https://lore.kernel.org/all/4da55124e32dd0587a3516c8f5ed512bffbbb42e.camel@linux.intel.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: "2026-09-11T10:40:00"
authors:
  - "Klaus Kusche"
maintainers_involved:
  - "Tim Chen"
patch_series:
  - version: v1
    msgid: "<2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info>"
    date: "2026-09-09"
    summary: "问题报告线程。09-10 Tim Chen 确认 AMD hybrid 走 SD_ASYM_PACKING，其 20260825174112 补丁（只修 SD_ASYM_CPUCAPACITY）对报告系统无效；新候选为 Chen Yu 的 ITMT 兼容补丁 20260810033742，叠加 Mario 的 debugfs 补丁验证。"
    review_outcome: "Chen Yu 确认补丁意图并索要 domains dump、sched_itmt_enabled、sched_core_priority 三项诊断；验证依赖休假中的报告者或其他人接手。"
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "报告者休假，新测试组合（Chen Yu 补丁 + Mario debugfs 补丁）无人执行"
    - "AMD 平台上 ITMT 机制假设是否成立未经验证"
    - "Tim 提到的 CAS active load balance 两个待修问题仍未展开"
  next_action: "由报告者或第三方在 AMD 大小核机器上按新组合复现并提供 Chen Yu 要求的三项诊断信息"
contribution_opportunities:
  - kind: testing
    description: "在 AMD Strix/HX 类大小核机器上按 基线/+Chen Yu ITMT 补丁/+Mario debugfs 补丁 组合复现，附 domains dump、sched_itmt_enabled、sched_core_priority 回帖"
  - kind: review
    description: "核查 amd-pstate preferred core 下 SD_ASYM_PACKING 的设置路径与 Intel ITMT 的差异，判断 Chen Yu 补丁在 AMD 上的适用性"
  - kind: discussion
    description: "追问 Tim 提到的 CAS ALB 路径两个问题与 nr_pref_llc_running 线程的修复是否同源"
source_email_count: 2
related_articles:
  - "sched-20260909-009"
  - "sched-20260905-007"
  - "sched-20260831-006"
tags:
  - load_balance
  - topology
  - x86
---
