# [GIT PULL] Scheduler updates for v7.4

## TL;DR

Ingo Molnar 向 Linus 发 v7.4 合入窗口的主调度器 pull request（tip 树 `sched-core-2026-10-18`，截至 `b99b7f60c5b473d374c68b53753153b4aa9e0702`），涵盖 Kconfig、fair（RUN_TO_PARITY 清理、augmented callback、hrtick 重播、短 slice 任务时延）、DL/RT、EAS steal_governor、负载均衡、cache-aware、NUMA、proxy execution（sleeping owner + sched_ext 兼容铺垫）、基础设施与调试等多个方向。kernel test robot 已确认该 tip/sched/core 树 `BUILD SUCCESS`。当日缓存未见 pr-tracker-bot 的合并确认回帖。

## 背景与问题

v7.4 合入窗口开启，Ingo 汇总 `sched/core` 分支（自上个窗口以来累积的调度改动）提请 Linus 收取。这是窗口期的例行主 pull，集中了此前多个已 review 通过、进 tip 的补丁系列。

## 技术方案

pull 范围（`git://git.kernel.org/pub/scm/linux/kernel/git/tip/tip.git sched-core-2026-10-18`，截至 `b99b7f60c5b473d374c68b53753153b4aa9e0702`），按类别：

- **Kconfig**：简化 PREEMPT_DYNAMIC（Mark Rutland）。
- **Fair**：移除冗余 RUN_TO_PARITY 检查（Elif Topuz）；按字段声明 augmented callback、修 `rb_add_augmented_cached()` 下潜（Yiwei Lin、Peter Zijlstra）；同任务 re-pick 后重播 fair hrtick（Shubhang Kaushik）；改善短 slice 任务调度时延（Vincent Guittot）。
- **DL/RT**：`start_dl_timer` 到期改用 `ktime_before()` 判读（Liang Hao）；irq_work 在 PREEMPT_RT 上的 CPU 热插拔改进（Sebastian Andrzej Siewior）。
- **EAS**：实现 steal_governor、引入 preferred CPU 与 steal 驱动的 vCPU backoff（Shrikanth Hegde）。
- **负载均衡**：NVIDIA Olympus 上启用 preferred SMT sibling（Andrea Righi）；等浅 idle CPU 随机化选择（Christian Loehle）；移除冗余 `core_sched_seq`（Hui Su）。
- **Cache-aware**：避免发布部分 LLC 利用率（Jemmy Wong）。
- **NUMA**：扫描周期更新后重置 NUMA fault locality（Eric Kim）。
- **Proxy execution**：sleeping owner 处理的持续推进（John Stultz、Vasily Gorbik）；使 sched_ext 兼容 proxy execution 的铺垫（Andrea Righi）。
- **基础设施与修复**：移除 PSI trigger 销毁的 RCU wait（Shakeel Butt）；失败优先级注册避免修改 wait-entry（Hui Su）；sched_feat 改用新 static key API（Hongyan Xia）；paravirt_steal 改新 static key API（Hongyan Xia）；cputime 修复 dyntick-idle 后 idle 时间重复记账（Stian Halseth）。
- **调试**：`__trace_set_need_resched()` 前置 `TIF_NEED_RESCHED`（Sechang Lim）；非 preferred CPU push 的 context analysis 错误（Shrikanth Hegde）。
- 另有多项杂项清理与修复（Christian Loehle、Shubhang Kaushik、Thomas Huth、Vladimir Zapolskiy）。

## 版本演进与当前进展

*current_version: null*。pull request 当日发出（2026-10-18，`<atSiuBt4n03_iQNW@gmail.com>`）；kernel test robot 同日确认 tip/sched/core `BUILD SUCCESS b99b7f60c5b473d374c68b53753153b4aa9e0702`。缓存内未见 Linus 合并回帖。

## Maintainer 意见与讨论焦点

Ingo Molnar（调度 maintainer）作为发起人汇总；Linus 侧无回帖（缓存内未见）。无争议。

## 合入评估

*likelihood=high*。这是 v7.4 窗口的例行主 pull，覆盖的每条改动此前都已各自通过 review 进 tip/sched/core；截至 `b99b7f60c5b473` 且 kernel test robot 确认构建成功。*blocking_issues*：当日缓存未见 pr-tracker-bot 合并确认，是否已被 Linus 收取未确认。*next_action*：等待 Linus 合入（通常窗口期内完成）；关注 tip:sched/core 的 ld.lld 报错（`[tip:sched/core 35/37]`，kernel test robot 同日另报）是否影响该 pull。

## 效果评估

无量化数据，属合并动作；各条改动自身的性能/正确性效果见其各自补丁系列的历史文章（短 slice 任务时延、EAS steal、cache-aware LLC、proxy execution 等）。

## 我可以参与的点

- `review`/`testing`：本 pull 汇入后可在 v7.4 合入窗口的 -rc 阶段集中回归 scheduler 相关负载（EAS steal、cache-aware LLC、proxy execution、短 slice 任务时延），为各条改动的真实回归窗口提供信号。
- `discussion`：kernel test robot 报告的 `[tip:sched/core 35/37]` ld.lld relocation 报错（`__UNIQUE_ID_addressable_overflowuid_553`）尚未在本缓存内看到处理回帖，可跟进确认是否为工具链误报。

## 参考链接

- GIT PULL：https://lore.kernel.org/all/atSiuBt4n03_iQNW@gmail.com/
- tip/sched/core BUILD SUCCESS：https://lore.kernel.org/all/202610180527.7mHOZpOj-lkp@intel.com/
- tip/sched/core ld.lld 报错：https://lore.kernel.org/all/202610170544.6hPndDUW-lkp@intel.com/

---
id: sched-20261018-011
date: 2026-10-18
subject: "[GIT PULL] Scheduler updates for v7.4"
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: "<atSiuBt4n03_iQNW@gmail.com>"
lore_url: "https://lore.kernel.org/all/atSiuBt4n03_iQNW@gmail.com/"
authors: ["Ingo Molnar"]
maintainers_involved: ["Ingo Molnar"]
current_version: null
patch_series: []
upstream_commit: "b99b7f60c5b473d374c68b53753153b4aa9e0702"
fixes_commit: null
merged_branch: "sched-core-2026-10-18"
merge_assessment:
  likelihood: high
  blocking_issues: ["当日缓存未见 pr-tracker-bot 合并确认"]
  next_action: "等待 Linus 合入，关注 tip:sched/core 的 ld.lld 报错是否影响 pull"
contribution_opportunities:
  - kind: testing
    description: "在 v7.4 窗口 -rc 阶段集中回归 EAS steal、cache-aware LLC、proxy execution、短 slice 任务时延"
  - kind: discussion
    description: "跟进 [tip:sched/core 35/37] ld.lld relocation 报错是否为工具链误报"
generated_at: "2026-10-19T09:00:00"
source_email_count: 2
related_articles: []
tags: [cfs, eevdf, load_balance, numa_balancing, proxy_execution]
---