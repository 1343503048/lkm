---
id: sched-20261106-001
date: 2026-11-06
subject: 'sched/deadline: bandwidth accounting fixes and selftests'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261105193359.1450487-1-mathieu.desnoyers@efficios.com>
lore_url: https://lore.kernel.org/all/20261105193359.1450487-1-mathieu.desnoyers@efficios.com/
authors:
- Mathieu Desnoyers
- Andrea Parri
- Juri Lelli
maintainers_involved:
- Juri Lelli
current_version: v3
patch_series:
- version: v1
  msgid: <cover.1793804635.git.mathieu.desnoyers@efficios.com>
  date: 2026-11-03
  summary: 12 补丁修复 SCHED_DEADLINE 带宽记账 bug，含自测与 sched_debug。
  review_outcome: Sashiko AI 9 条评审，引出 v2 新增 9 个补丁。
- version: v2
  msgid: <20261104211207.1392343-1-mathieu.desnoyers@efficios.com>
  date: 2026-11-05
  summary: 21 补丁：17 修复 + 3 自测 + 1 sched_debug，49 用例。
  review_outcome: Juri 多封 Reviewed-by/Acked-by，patch 4/2/6 有保留；Marek Tested-by。
- version: v3
  msgid: <20261105193359.1450487-1-mathieu.desnoyers@efficios.com>
  date: 2026-11-06
  summary: 24 补丁：20 修复（修复在前供 stable 截取）+ sched_debug + 3 自测（52 用例），吸收 Juri 被丢弃的 4
    个 sched/urgent 修复，新增 patch 5/7/13/16。
  review_outcome: 当日 Kayra 复看 patch 1、Sashiko AI 逐封评审、Mathieu 自回复；未见 Juri/Ingo 新表态。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 系列规模大（24 补丁 + 3564 行自测），与 Ingo 严格 -stable 子集要求仍有张力
  - patch 2 的 KEEP_PARAMS ABI 变更需维护者拍板
  - LLM 参与写作，社区要求更仔细的人工审阅
  next_action: 等待 Juri/Ingo 对 v3 的逐封审阅与 Signed-off-by 补充
contribution_opportunities:
- kind: testing
  description: 在真实硬件（cpuset 分区/CPU hotplug/PREEMPT_RT/proxy）跑 sched/deadline 52 用例并回帖
- kind: review
  description: 人工仔细审阅 patch 14-18 的 root domain 记录逻辑与 patch 16 的 attach 竞态
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 30
related_articles:
- sched-20261105-001
tags:
- deadline
- cgroup
title: 'sched/deadline: bandwidth accounting fixes and selftests'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a>：Mathieu Desnoyers 的 v2 系列（21 补丁）在 Juri Lelli 此前 4 个 sched/urgent 修复之上再修 17 个 SCHED_DEADLINE 带宽记账 bug（其中 3 个可直接打死内核），带自测与 sched_debug。Juri 已对多数补丁给 Reviewed-by/Acked-by，Marek Szyprowski 实测修复了他复现的 CPU hotplug 崩溃并给 Tested-by；但 Ingo 要求「严格只含 -stable 可回退修复的子集」。
- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261106-001</a>（今天）：**v3 发出，扩到 24 补丁**——20 个修复（patch 1-20，按 Ingo 要求「修复在前」，stable 可直接截取 1-20）+ patch 21 sched_debug + patch 22-24 三个自测（52 用例）。v3 把 Juri 被 Ingo 丢弃的 4 个 sched/urgent 修复全部吸收（分别落入 patch 2/8/9/14），并新增 patch 5（sysrq-n 卡死 cpuset_mutex）、patch 7（deadline/runtime 残留）、patch 13（rebuild 扫描撞上临终任务）、patch 16（rebuild 穿过 attach）四个新修复。当日 Kayra 复看 patch 1、Sashiko AI 对 9 个补丁给出自动评审、Mathieu 自回复多条。作者仍明确披露 LLM 参与写作，请求熟悉该代码者仔细审阅修复本身。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a>）Juri Lelli 前一轮 4 个 SCHED_DEADLINE 带宽记账修复被 Ingo 从 tip/sched/urgent 移除——因为其中第一个补丁（cpuset 传输的 stale root domain）在 Marek Szyprowski 的 CPU hotplug 测试上崩溃。Mathieu 在此之上系统梳理 dl_bw/total_bw 记账边界缺陷，v3 把这 4 个修复的去向逐一交代：

- 1/4（stale root domain）→ patch 14（记录「记账该任务带宽的 root domain」而非从任务 mask 推导，mask 在 hotplug 期间无 active CPU 正是崩溃根因）；
- 2/4（离开类睡眠任务泄漏 total_bw）→ patch 8（合并 v2 的二次释放修复，去掉 Juri 的 Signed-off-by 留给他自己加回）；
- 3/4（KEEP_PARAMS 拒绝）→ patch 2（合并 v2 的摆放与 policy 变更修复）；
- 4/4（拒绝 exited 任务设 SCHED_DEADLINE）→ patch 9（Juri 的，扩展到「离开类的任务」第二次递减 cpuset 计数）。

20 个修复按后果分四类：两个直接打死内核（`__dl_sub()` 除零——debugfs 写 fair server 时 CPU 恰下线；隔离 CPU 全下线后重建记账对无家可归任务 BUG()）；两个让 cpuset_mutex 处于「此后无 deadline 任务可准入」的状态（二次解锁、sysrq-n 在 tasklist_lock 下睡眠持锁）；三个破坏预留保证（被 throttle 的任务切出又切回留下永久 throttle、0-lag 时间后回来沿用已放弃的预留、replenishment timer 残留）；其余 13 个让 root domain 的 total_bw 或 runqueue 的 this_bw 与真实任务不符（超额准入、拒绝全部准入并拒绝下线最后一颗 CPU、this_bw 下溢告警）。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a> 的「可追溯、可幂等」思路）v3 的核心手段与 v2 一致，并在关键处重做：

- **patch 1**：Andrea Parri 的 cpuset_mutex 二次解锁修复（Nov 2 发出、经 Waiman/Kayra/Juri 评审），原样携带 tags 进 v3，因为 patch 13 依赖它。
- **patch 2/3**：`SCHED_FLAG_KEEP_PARAMS` 的准入时序——patch 2 把准入检查挪到最后并拒绝「会改变 policy/class 的 KEEP_PARAMS」；patch 3 让被保留参数不再无锁读取。
- **patch 4**：`__dl_sub()`/`__dl_add()` 除零——按 Juri 意见改为「CPU inactive 时拒绝 debugfs 写」，而不是让写落到除法上；guard 保留给无写可拒绝的路径。
- **patch 9/14/15/17/18**：root domain 记账的「记录」改造——patch 9 拒绝 exited 任务；patch 14 记录记账 root domain 的 CPU；patch 15 只在确有腾挪空间时移动带宽（取 SCA_ 位 0x20，与 Andrea 的 0x10 错开）；patch 17 用 runqueue 锁下真实移动的 tally；patch 18 重建记账时取「记录中的 CPU」。
- **patch 16（新）**：sched_rt_runtime_us sysctl 或 energy model 触发的 sched 域重建会穿过 cpuset_can_attach/cpuset_attach 之间的空窗，重建等待 attach。
- **patch 12**：无 CONFIG_CPUSETS 时 `dl_rebuild_rd_accounting()` 是 stub，引入 deadline 自己的 mutex 串行化重建与准入。
- **patch 21**：sched_debug 显示每个 runqueue 的 this_bw/running_bw（使 patch 11 的下溢用户态可见）；**patch 22-24**：三个自测程序（deadline_bw_test 3564 行、deadline_rebuild_test、deadline_switch_test）共 52 用例，独立目录 `tools/testing/selftests/sched/deadline`（按 Juri 建议）。

v3 相对 v2 的关键重做还包括：patch 5 新增（sysrq-n 卡 cpuset_mutex，v6.5 以来的基线 bug）；patch 7 新增（deadline/runtime 在 `__dl_clear_params()` 后残留，两行修复）；patch 13 新增（rebuild 的两趟扫描可能在「释放带宽与重置 dl_bw 之间」撞上临终任务）；patch 19 在 patch 8 释放处一并取消 replenishment timer；patch 20 改测请求的 flags 而非 entity 旧 flags。v2 的 patch 5（无 active CPU mask 的 fallback）随其修复一并消失，v2 的 patch 19 即 Andrea 的补丁在此成为 patch 1。

## 版本演进与当前进展

*current_version: v3（2026-11-06 发出，msgid 20261105193359.1450487-1）*。

- v1（2026-11-03）：12 补丁。
- v2（2026-11-05）：21 补丁（17 修复 + 3 自测 + 1 sched_debug），获 Juri Reviewed-by/Acked-by、Marek Tested-by。
- v3（今天）：24 补丁，基点为 v7.4-rc1（`6628e7d4c6b2`，即当前 tip sched/urgent 所在点，去掉了 v2 所基于的 4 个被丢弃修复）。共 19 文件改动、+5218/-123 行。Juri 对 v2 patch 1/2 的 Reviewed-by 携带到 v3 的 patch 2（合并其 3/4）与 patch 3。

当日新讨论：Kayra Cizmeci 复看 patch 1 后追问细节；Sashiko AI 对 patch 04/08/11/14/16/18/19/20/24 逐封自动评审；Mathieu 对 patch 01/24 多次自回复说明。Andrea Parri 就「他的补丁被携带进 v3」回帖确认（v2 19/21 线程）。

## Maintainer 意见与讨论焦点

Juri Lelli（SCHED_DEADLINE 维护者）上一轮已对多数补丁给 Reviewed-by/Acked-by；v3 的 cover 直接面向「Hi Ingo, Juri」发出，把「哪 4 个修复落到 v3 哪处」讲清楚并请 Juri 自行加回 Signed-off-by。Ingo 此前的硬约束（「严格只含 -stable 可回退的修复子集」）已被 v3 的「修复在前（1-20）、stable 可截取」结构正面回应，但系列规模（24 补丁、3564 行自测）与「LLM 参与写作、请仔细人工审阅修复本身」仍是合入前的核心张力。Sashiko AI 的自动评审持续产出「潜在问题」提示，作者自述逐条对照代码后才落笔。当日未见 Juri/Ingo 对 v3 的新表态。

## 合入评估

*likelihood=medium*。方向无异议、有维护者此前的 Reviewed-by/Acked-by 背书、且 v3 主动对齐了 Ingo 的「修复在前」要求，但尚未满足合入条件：*blocking_issues*：① 系列规模大（24 补丁 + 3564 行自测），与「严格 -stable 子集」仍存在张力；② patch 2 的 KEEP_PARAMS ABI 变更仍需维护者拍板；③ LLM 参与写作，社区要求更仔细的人工审阅。*next_action*：作者按 Juri 此前 patch 4/8 意见修订，并等待 Juri/Ingo 对 v3 的逐封审阅与 Signed-off-by 补充。

## 效果评估

v3 测试：8 个 8-vCPU QEMU guest 上 52 用例全过；4 vCPU、PREEMPT_RT、CONFIG_SCHED_PROXY_EXEC 开关、无 CONFIG_CPUSETS 五种配置下 16 个 guest 无内核告警（lockdep 全开）。反向验证：在 v7.4-rc1 上，deadline_bw_test 失败 10 用例、deadline_rebuild_test 3 用例、deadline_switch_test 3 用例（4 个 4-vCPU guest）。v2 的 8 个独立 reproducer 在 v7.4-rc1 上：KEEP_PARAMS 泄漏单次调用 total_bw 419424→838854、移动竞态 200 次把分区 total_bw 卷到 2^64-262144、离去任务留下 104857、二次解锁报 "bad unlock balance detected!"、除零首轮即 oops。

## 我可以参与的点

- **testing**：在真实硬件（非 QEMU）跑 `tools/testing/selftests/sched/deadline/` 的 52 用例，尤其带 cpuset 分区、CPU hotplug、PREEMPT_RT、proxy execution 的配置，回帖数据可加速合入。
- **review**：作者明确请求「熟悉该代码者仔细审阅修复本身」（LLM 参与写作），尤其 patch 14-18 的 root domain 记录逻辑、patch 4 的除零拒绝路径、patch 16 的 attach 竞态。

## 参考链接

- lore thread（v3 cover）: https://lore.kernel.org/all/20261105193359.1450487-1-mathieu.desnoyers@efficios.com/
- 历史 v2 文章: <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a>（见 sched/2026/11/ 归档）
- Andrea Parri 的 patch 1 原帖 lore: https://lore.kernel.org/all/20261102135420.244745-1-parri.andrea@gmail.com/（来自 cover 引用，未在本日缓存内逐字核对）
