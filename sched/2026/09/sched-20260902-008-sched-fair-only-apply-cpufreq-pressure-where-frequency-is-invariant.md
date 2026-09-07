# sched/fair: Only apply cpufreq pressure where frequency is invariant

## TL;DR

cpufreq pressure 只在频率不变的平台施加。补丁自 8 月进入评审以来仍未收口，9/2 是 Jianyong Wu 与
Hongyan Xia 就「概念到底该怎么表述」往返，没有新版本、没有新数据。

## 背景与问题

（本文为增量更新，完整背景见 related_articles 中 08-24/08-25 的文章）

cpufreq 压力（cpufreq pressure）按「可达最高频率/当前可达最高频率」降 capacity，但
utilization 仅在频率不变（frequency invariant）架构才带匹配 scaling，导致语义不一致。
焦点集中在「是否仅在不 invariant 场景施加 pressure」。

本期（Re: UID 73378 / 73396 / 73507）为讨论继续，未见新版本号或新基准数据，主要围绕
实现细节与正确性论证。

## 技术方案

- 延续此前方向：将 cpufreq 压力施加范围限制到「频率为不变量」的场景。
- 避免在非不变平台上产生误导性的利用率压缩。

## 版本演进与当前进展

- 当前状态：**under_review / 讨论中**（增量更新，无新版本）。
- 合入可能性 medium。

## Maintainer 意见与讨论焦点

- 当天 16:49、17:00 jong wu（Jianyong Wu）两次回帖（73359/73394），17:37 Hongyan Xia 回（73503），
  9/3 10:04 Jianyong 再回（75681）。引文链上是 Vincent Guittot（8/25 21:05）与 Hongyan Xia（8/24）的意见，
  也就是说真正提反对的是这两位，作者一直在解释而非改代码。
- 作者自认表述有问题（73394 引用）："My original commit message did not clearly describe the conc…"
  （截断）。焦点集中在概念口径（frequency invariant 到底指什么、pressure 与 utilization 的匹配关系）。
- 无 NAK，也没有任何一位给出「同意」的表述。

## 合入评估

**中偏低**。硬卡点：一周多没有新版本，讨论停在 commit message 与概念层，实现层面没有推进；同时缺
「非频率不变平台上 pressure 造成误导性利用率压缩」的实测证据。要合入至少需要先让 Vincent Guittot 认可
口径并出一个带清晰说明的新版本。

## 效果评估

暂无效果数据。当日缓存内无人引用 benchmark，也无容量压缩前后的对比。文章正文里此前记录的焦点也仍是
论证而非测量。

## 我可以参与的点

- 这是当前线程最缺的一环：在非频率不变的平台（无 AMU / highest_perf 不可靠）实测 pressure 开/关两种
  情况下 capacity 被压缩后对 `util_fits_cpu()` 与 pick 决策的影响，量化后回帖。
- 也可以只做语义层面的一件事：把 "frequency invariant" 与 arch_scale_cpu_capacity / CPPC highest_perf
  的关系写成一张判定表回帖，减少往返成本。

## 参考链接

- 003 sched/cache use-after-free、002 PREEMPT_DYNAMIC（同属调度核心活跃话题）

---
id: sched-20260902-008
date: '2026-09-02'
subject: 'sched/fair: Only apply cpufreq pressure where frequency is invariant'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Vincent Guittot
- Jianyong Wu
- Jianyong Wu
- Hongyan Xia
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: low_medium
  blocking_issues:
  - "无新版本，讨论停留在 commit message 与概念口径层面"
  - "缺非频率不变平台上压力导致误导性利用率压缩的实测数据"
  - "Vincent Guittot / Hongyan Xia 对最新一轮解释未表态"
  next_action: "在非频率不变平台量化 pressure 对 capacity 与选核决策的影响，并整理 frequency-invariant 判定口径"
contribution_opportunities:
- "在无 AMU / highest_perf 不可靠的平台上量化 cpufreq pressure 对 utilization 压缩的影响并回帖"
- "整理 frequency-invariant 与 arch_scale_cpu_capacity/CPPC highest_perf 的判定表，终结概念层往返"
- "推动作者基于新证据发 v2，明确改动范围"
source_email_count: 9
related_articles:
- sched-20260824-004-sched-fair-cpufreq-pressure-invariant.md
- sched-20260825-006-sched-fair-cpufreq-pressure-invariant.md
- sched-20260826-003-sched-cpufreq-reevaluate-tickless-idle.md
tags:
- schedutil
- sched/fair
- regression
---
