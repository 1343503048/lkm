# [linus:master] [sched/core] 118a2cf4ce: stress-ng.schedpolicy.ops_per_sec 14.1% regression

## TL;DR
kernel test robot（0day/LKP）报告：commit `118a2cf4ced60777a2408001e2b4838fed1cea55`（"sched/core: Call wakeup_preempt() for queued tasks during class change"）在 linus master 上使 `stress-ng.schedpolicy` 的 `ops_per_sec` 相对 v7.3-rc7 回退 **14.1%**（275785 → 236940），`SCHED_*` 各调度策略的 `schedules_per_sec` 同步 -14.1%；同时 `time.voluntary_context_switches` 暴涨 +634.5%、`involuntary_context_switches` +734.4%。属对已合入 mainline 提交的性能回退报告，尚无任何修复/作者回应，需定位到该提交的 wakeup_preempt 语义变化。

## 背景与问题
0day 机器人对 linus:master 的该提交做回归对比：测试机为 224 线程 2 socket Intel Xeon Platinum 8480CTDX（Sapphire Rapids）、256G 内存，config `x86_64-rhel-9.4`、gcc-14、cpufreq governor=performance、stress-ng 参数 `nr_threads=100% testtime=60s test=schedpolicy`。基线 v7.3-rc7 与 `118a2cf4ce` 对比中，`schedpolicy` 相关所有指标一致 -14.1%。报告请求若另修于独立补丁则加 `Reported-by: kernel test robot` 与 `Closes:` 标签。

## 技术方案
非补丁，为回归报告。报告给出复现材料与内核配置下载地址（`https://download.01.org/0day-ci/archive/20261023/202610231954.51716452-lkp@intel.com`）。被报告提交 `118a2cf4ce` 即「在类切换时对 queued 任务调用 `wakeup_preempt()`」的改动（对应社区系列「sched/core: Call wakeup_preempt() for queued tasks during class change」）。

## 版本演进与当前进展
非补丁系列。当日为 0day 的自动回归报告，缓存内无该提交作者或维护者的回应。

## Maintainer 意见与讨论焦点
无维护者表态。报告指向的语义变化是 `wakeup_preempt()` 现在会在类切换（task 在 fair/rt 等类之间迁移）时对 queued 任务被调用，疑似改变了 `schedpolicy` 这类大量 `sched_setscheduler()` 调用的负载的抢占行为——上下文切换计数的大幅变化（voluntary +634%、involuntary +734%）与之一致，但具体根因尚无分析。

## 合入评估
*likelihood=unknown*。这是针对已合入 mainline 提交的性能回退报告，不是补丁；需 `118a2cf4ce` 作者（或 sched 维护者）复现并判断是接受、优化还是 revert。*blocking_issues*：尚无复现/归因；回退 14.1% 且伴随巨量上下文切换，需确认是否真实回归还是测试方法差异。*next_action*：作者复现 schedpolicy 负载、定位 wakeup_preempt 在类切换路径上的多余切换/抢占，给出修复或 revert。

## 效果评估
0day 实测数据（Sapphire Rapids，performance governor）：`stress-ng.schedpolicy.ops_per_sec` 275785 → 236940（**-14.1%**）；`SCHED_BATCH/SCHED_DEADLINE/SCHED_FIFO/SCHED_OTHER/SCHED_RR_schedules_per_sec` 均 246.24 → 211.56（-14.1%）；`time.voluntary_context_switches` 78783 → 578684（**+634.5%**）、`time.involuntary_context_switches` 85768 → 715671（**+734.4%**）；`time.system_time` 13087 → 11737（-10.3%）。上下文切换暴涨与吞吐下降并存的模式提示「抢占/切换被显著放大」。

## 我可以参与的点
- *kind: discussion*：复现 `schedpolicy` 负载并分析 `118a2cf4ce` 在类切换路径上是否引入了不必要的 wakeup 抢占（可用 `perf sched`/tracepoint 对比切换来源），回帖提供归因线索。

## 参考链接
- 报告: https://lore.kernel.org/all/202610231954.51716452-lkp@intel.com/
- 被报告提交: https://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git/commit/?id=118a2cf4ced60777a2408001e2b4838fed1cea55
- 复现材料: https://download.01.org/0day-ci/archive/20261023/202610231954.51716452-lkp@intel.com

---
id: sched-20261023-009
date: 2026-10-23
subject: "[linus:master] [sched/core] 118a2cf4ce: stress-ng.schedpolicy.ops_per_sec 14.1% regression"
subsystem: sched
type: regression
status: under_review
severity: high
thread_root_msgid: "<202610231954.51716452-lkp@intel.com>"
lore_url: "https://lore.kernel.org/all/202610231954.51716452-lkp@intel.com/"
authors: ["kernel test robot"]
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: "118a2cf4ced60777a2408001e2b4838fed1cea55"
fixes_commit: null
merged_branch: "linus/master"
merge_assessment:
  likelihood: unknown
  blocking_issues: ["无复现/归因", "回退 14.1% 且伴随巨量上下文切换需确认是否真实回归"]
  next_action: "作者复现 schedpolicy 负载、定位类切换路径上 wakeup_preempt 的额外切换，修复或 revert"
contribution_opportunities:
  - kind: discussion
    description: "复现 schedpolicy 负载并用 perf sched/tracepoint 定位额外 wakeup 抢占来源，回帖提供归因"
generated_at: "2026-10-24T09:08:00"
source_email_count: 1
related_articles: []
tags: [cfs, preempt, regression, perf, x86]
---