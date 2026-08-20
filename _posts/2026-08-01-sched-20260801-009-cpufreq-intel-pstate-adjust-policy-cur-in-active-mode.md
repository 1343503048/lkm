---
id: sched-20260801-009
date: 2026-08-01
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <uid-13553@qq-imap>
lore_url: unknown
authors:
- Jing Wu
- Qiliang Yuan
maintainers_involved:
- Rafael J. Wysocki
- Srinivas Pandruvada
current_version: v1
patch_series:
- version: v1
  msgid: unknown
  date: 2026-07-29
  summary: intel_pstate_set_policy() 在 CPUFREQ_POLICY_PERFORMANCE 分支中把 CPU 钉在固定 pstate
    并直接编程，但随后又无条件把 policy->cur 覆写为 policy->min，丢弃了刚算出并应用的钉住值。在 nohz_full 隔离 CPU 上，arch_freq_get_on_cpu()
    的 APERF/MPERF 采样长期不刷新而回退到 cpufreq_quick_get()，导致该 CPU 永远上报频率下限。本 patch 改为在该分支把
    policy->cur 设为实际钉住的频率（pstate * scaling）
  review_outcome: Rafael J. Wysocki 与 Srinivas Pandruvada 均已参与讨论，具体结论在本次采样中未完整获取
upstream_commit: null
fixes_commit: d51847acb018
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 本次仅采样到 2 封回复邮件且正文截断，Rafael 与 Srinivas 的最终意见未能完整获取，无法判断是否存在实质异议
  - 属于 cpufreq 子系统而非 kernel/sched，与调度的关联点在 nohz_full 隔离场景
  next_action: 跟踪 Rafael J. Wysocki 与 Srinivas Pandruvada 的完整回复，确认是否需要 v2
contribution_opportunities:
- kind: testing
  description: 在开启 nohz_full 的 Intel 机器上，把隔离 CPU 设为 performance policy 并只跑一个可运行任务，对比
    /sys/devices/system/cpu/cpuX/cpufreq/scaling_cur_freq 与实际 APERF/MPERF 测得频率，验证上报值是否确实长期停在下限
generated_at: '2026-08-02T00:55:00'
source_email_count: 2
related_articles: []
tags:
- cpufreq
- nohz
- idle
title: 'cpufreq: intel_pstate: Adjust policy->cur in active mode to policy'
layout: article
---

## TL;DR

`intel_pstate` 在 performance policy 下把 CPU 钉到固定 pstate 后，却又把 `policy->cur` 覆写成 `policy->min`，导致 nohz_full 隔离 CPU 因为拿不到新的 APERF/MPERF 采样而**永远上报频率下限**。修复很直接：把 `policy->cur` 设为实际钉住的频率。Rafael 与 Srinivas 均已介入讨论。

## 背景与问题

这是一个「调度隔离」与「频率上报」交叉处的问题，链条有三环：

**第一环——driver 自相矛盾**。当 `cpu->policy` 为 `CPUFREQ_POLICY_PERFORMANCE` 时，`intel_pstate_set_policy()` 会把 CPU 钉在一个固定 pstate（`max(min_pstate, max_perf_ratio)`）并直接编程下去。代码里已有的注释说明了为什么要这么做：**"NOHZ_FULL CPUs need this as the governor callback may not be invoked on them"**——nohz_full CPU 上 governor 回调可能根本不会被调用，所以必须主动钉住。

但仅仅两行之后，同一个函数又**无条件地**把 `policy->cur` 下调为 `policy->min`，把刚刚算出并已经应用的钉住值丢掉了。

**第二环——上报路径回退到 policy->cur**。`arch_freq_get_on_cpu()` 在它的 APERF/MPERF 采样过期（stale）时，会回退到 `cpufreq_quick_get()`，也就是读 `policy->cur`。

**第三环——nohz_full 让回退变成常态**。一个 tick 正常运行的 CPU 会不断刷新 APERF/MPERF 采样，几乎不会命中回退路径。但一个被 `nohz_full` 覆盖的隔离 CPU，如果只有一个可运行任务，**tick 会被完全关掉，采样再也不会刷新**——于是它永久地走回退路径，永久地上报那个被错误覆写的下限值。而这个 CPU 实际上正被钉在上面算出的那个频率上稳定运行。

结果就是：用户在最需要精确频率信息的隔离 CPU 上，看到的是一个恒定的、错误的最低频率。`Fixes:` 指向 `d51847acb018 ("cpufreq: intel_pstate: set stale CPU frequency to minimum")`，即引入这个覆写行为的 commit。

## 技术方案

在 `CPUFREQ_POLICY_PERFORMANCE` 分支中，把 `policy->cur` 设为**精确的钉住频率**（`pstate * scaling`），而不是让它落到统一的 `policy->min` 覆写上；只有在通用情况下——即没有新采样就确实无从得知当前频率时——才保留回退到 `policy->min` 的行为。

设计上的取舍很清楚：`d51847acb018` 引入「stale 时上报最小值」是一个保守的兜底策略，本身没错；问题在于它被无差别地应用到了一个**频率其实是已知的**分支上。修复没有推翻原策略，只是把「已知」与「未知」两种情况区分开——这是比直接回退原 commit 更精确的做法。

改动规模：`drivers/cpufreq/intel_pstate.c` 15 增 5 删。

## 版本演进与当前进展

v1 于 2026-07-29 由 Jing Wu 发出（Qiliang Yuan 为 Co-developed-by）。2026-08-01 当日 thread 中有两封回复：01:05 Rafael J. Wysocki、01:20 Srinivas Pandruvada。

**需要如实说明信息完整度**：本次采样到的两封邮件正文均为引用原 patch 的部分且在关键处截断，**两位 maintainer 的实际评论内容未能完整获取**。因此下一节无法给出他们的具体意见。

## Maintainer 意见与讨论焦点

**信息不完整**。Rafael J. Wysocki（cpufreq / PM 子系统 maintainer）与 Srinivas Pandruvada（intel_pstate 主要维护者）两人当日都在 thread 中发言，这本身说明该 patch 已经进入了正确的 review 视野——这两位恰好是最有资格判断此改动的人。

但本次采样到的邮件正文停在引用原文处，**没有捕获到他们的实际评论**。因此无法判断：是认可、是要求修改、还是存在异议。不能仅凭「maintainer 已回复」就推断进展顺利。

## 合入评估

合入可能性 **medium**，且该判断置信度有限。

**有利因素**：问题分析链条完整且有代码注释佐证（注释本身就说明了 nohz_full 场景需要钉住）；`Fixes:` tag 明确；修复方式精确、不推翻原有保守策略；改动小且局限在单个 driver；两位关键 maintainer 已经在看。

**不确定因素**：两位 maintainer 的实际意见未知。intel_pstate 的频率上报语义历史包袱较重，`policy->cur` 在 active mode 下究竟应该表达「请求值」还是「实际值」本身可能有既定约定，Srinivas 有可能提出与作者不同的语义理解。

## 效果评估

**暂无量化数据**。邮件中没有给出 `scaling_cur_freq` 的错误读数与实际频率的对比测量，也没有说明该问题影响的用户场景规模。

问题描述本身是基于代码路径的严密推导（钉住 → 覆写 → 采样不刷新 → 回退读到被覆写值），逻辑链完整；但按模板要求，「隔离 CPU 永久上报下限」这一结论目前属于**作者的代码分析结论，未见实测数据佐证**。

## 我可以参与的点

- **测试（能把代码推导变成实证）**：在开启 `nohz_full` 的 Intel 机器上，将某个隔离 CPU 的 policy 设为 performance，在其上只跑一个可运行任务（保证 tick 关闭），然后对比 `/sys/devices/system/cpu/cpuX/cpufreq/scaling_cur_freq` 的读数与用 `turbostat` 或直接读 APERF/MPERF 测得的真实频率。若能给出「上报 800MHz、实际 3.5GHz」这类具体数字，对该 patch 的说服力提升很大。
- **说明**：本条目属于 `drivers/cpufreq` 而非 `kernel/sched`，纳入调度日报是因为其触发条件完全依赖 `nohz_full` 调度隔离配置——这是调度侧配置在电源管理侧引发的可观测性问题。若只关注 `kernel/sched/*` 的改动，本条目优先级可以放低。

## 参考链接

- lore thread: 未获取到
- 被修复的 commit: `d51847acb018 ("cpufreq: intel_pstate: set stale CPU frequency to minimum")`
- tip-bot commit: 未获取到
- stable backport: 未获取到
