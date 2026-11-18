---
id: sched-20261118-001
date: '2026-11-18'
subject: 'sched/deadline: bandwidth accounting fixes and selftests'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <cover.1794922146.git.mathieu.desnoyers@efficios.com>
lore_url: https://lore.kernel.org/all/cover.1794922146.git.mathieu.desnoyers@efficios.com/
authors:
- Mathieu Desnoyers
maintainers_involved:
- Juri Lelli
current_version: v7
patch_series:
- version: v5
  msgid: <20261108185406.1549770-1-mathieu.desnoyers@efficios.com>
  date: '2026-11-09'
  summary: 29 补丁：25 修复 + sched_debug + 3 自测
  review_outcome: Juri 对多补丁 RB/Ack，对 08 存疑并给 bandaid 备选
- version: v7
  msgid: <cover.1794922146.git.mathieu.desnoyers@efficios.com>
  date: '2026-11-17'
  summary: 扩到 40 补丁，覆盖 boost/参数复位、root domain 迁移、cpuset 同步与自测
  review_outcome: Juri 对 04/05/08/13 给 RB，提议拆分地基子集先行合入
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 拆分方案未定
  - v8 尚未发出
  next_action: Mathieu 出 v8，并就 Juri 的拆分先行合入提议表态
contribution_opportunities:
- kind: review
  description: 就 Juri 拆分地基子集先行合入的提议给出判断
- kind: testing
  description: v8 后复跑 deadline_bw_test 与 hotplug/deboost 新用例
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 22
related_articles:
- sched-20261110-009
tags:
- deadline
- dl_server
- cgroup
title: 'sched/deadline: bandwidth accounting fixes and selftests'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a>：Mathieu Desnoyers 的 v2 系列（21 补丁）在 Juri Lelli 此前 4 个 sched/urgent 修复之上再修 17 个 SCHED_DEADLINE 带宽记账 bug（其中 3 个可直接打死内核），带自测与 sched_debug。Juri 已对多数补丁给 Reviewed-by/Acked-by，Marek Szyprowski 实测修复了 CPU hotplug 崩溃并给 Tested-by；Ingo 要求「严格只含 -stable 可回退修复的子集」。
- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261106-001</a>：v3 发出，扩到 24 补丁。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-002-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261107-002</a>：v4 发出，扩到 26 补丁。
- <a class="article-ref" href="/lkm/2026/11/08/sched-20261108-003-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261108-003</a> / 20261109-001：v5 发出（29 补丁，25 修复 + sched_debug + 3 自测），Juri 持续评审。
- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-009-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261110-009</a>：Juri Ack 07/09，对 08（deadline boost 从 waiter's rt_mutex node 取参数）存疑并给 bandaid 备选；Mathieu 回应并披露 v6 计划。
- <a class="article-ref" href="/lkm/2026/11/18/sched-20261118-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261118-001</a>（今天）：**v7 已扩大到 40 补丁**，今日为 Juri 对 v7 的密集评审日——Juri 对 04/05/13 给 Reviewed-by、对 08 给实现级 Reviewed-by 并建议改写 changelog，且**首次提出把「地基修复子集」（1-8、10、13、14、16、20、37）拆出先行合入**；Mathieu 对约 18 个补丁逐条回应「下一版将如何改」，披露大量 v8 计划与自测数据。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a> … 20261110-009）Juri Lelli 前一轮 4 个 SCHED_DEADLINE 带宽记账修复被 Ingo 从 tip/sched/urgent 移除，Mathieu Desnoyers 系统梳理 dl_bw/total_bw/this_bw 记账边界缺陷，按 Ingo「修复在前、stable 可截取」一路推进到 v7。系列规模随评审持续扩大（v5 的 29 补丁 → v7 的 40 补丁），覆盖：deadline boost / 参数复位、root domain 重建时的带宽迁移、任务跨 class 往返、cpuset 附着同步、以及一组新增的 selftests。今日评审焦点从「记账修复」扩展到「boost 语义与参数复位」这组最容易出 hang 的 PI 纠缠补丁，并触发了「系列太大、是否拆分先合地基」的讨论。

## 技术方案

今日围绕 Juri 的拆分提议与 Mathieu 的 v8 回应：

- **Juri 的拆分提议**：v7 不断变大，建议把「地基修复」子集 1-8、10、13、14、16、20、37 拆出先行合入（37 不是 fix 但无害），其余（尤其关联自测无法单独通过的）随后跟进。
- **05/40 `Refuse dl_server debugfs writes while the rq is offline`**：Juri v7 已给 Reviewed-by；Mathieu 采纳 sashiko-bot 指出的「cpu_active() 先于 rq->online 清零」时序，v8 改为 `if (!rq->online || !cpu_active(cpu_of(rq))) return -EBUSY；` 并补一个自测用例。
- **08/40 `Do not replenish a boost from cleared parameters`**：Juri 给实现级 Reviewed-by，但建议改 changelog（给出 rewritten 段落：一次读 dl_runtime/dl_deadline/dl_period、任一为 0 即 bail，owner 保持 runnable/unthrottled 直到 chain walk deboost，负 runtime 归零不摊到 owner 自身）。Mathieu 采纳并把「Sashiko AI 找到本次 lockup」的署名按 generated-content.rst 要求改写（去掉发布号、保留致谢）。
- **04/40、13/40**：Juri 给 Reviewed-by。10/11/12/26/27/28/29/33/36/38 等约 18 个补丁，Mathieu 逐条回应 Juri 的 review 意见，密集披露 v8 改动（详见「版本演进」），几乎每处都标注「这是读代码核查的 / 未复现」以示严谨。

## 版本演进与当前进展

*current_version: v7（2026-11-17 发出，`<cover.1794922146.git.mathieu.desnoyers@efficios.com>`，40 补丁）*。今日为评审日、无新版本；Mathieu 密集披露 v8 计划（要点）：

- **28/29（root domain 带宽迁移）**：v8 引入 `dl_bw_walking` 标志 + `dl_bw_move_blocked(p)` 助手，在「sched domain 重建中」或「walk 尚未数到该任务」两种情形阻止带宽迁移，把 28 的已知边界收窄；`select_fallback_rq()` 也在 patch 28 里改成「会把 mask 扩出任务 root domain 时改用该 domain 的 CPU」，修掉 `hotplug_fallback_running` 测试揭示的「运行中 deadline 任务在 offline 时离开 root domain」问题。
- **26（rebuild 记账）**：record 指向的 CPU 若已被 partition 取走，v8 先问 cpuset、只在 cpuset 仍持有该 CPU 时保留 record；新增 `rebuild_record_taken` 用例（v7 上 7 次运行均复现、v8 修复）。
- **29（last CPU in root domain）**：cgroup v2 从最近有效 partition root（或 top cpuset）向下走 `effective_cpus_below()`；新增 `hotplug_nested_refused` 用例（v7 上 offline 被接受、任务醒到隔离 CPU，v8 上 EBUSY，6/6 保持）。
- **33（blocked 任务开新 period）**：仅在 donor 变化时才开，回应 patch 9 上的讨论；「睡眠 deadline 任务保留旧 deadline 直到 wakeup」的问题列入 cover 「Not changed」。
- **36（参数变化的 runtime 检查）**：把新参数检查移到 `dl_deboost()`（在 `dl_drop_boost()` 之后），新增 `deboost_new_params_reboost` 用例——v7 上 owner 未被重新 boost 且被限流（20ms 工作量跑了 400ms×40 轮），v8 约 20ms×40 轮。
- **05/38（selftests）**：修 deadline_bw_test 的 `PTHREAD_STACK_MIN` 栈太小、setup 拆分逐步报错、semaphore 双 case 结束销毁等。
- 其余：12（`ENQUEUE_REPLENISH` 语义等同列出队列任务 boost）、10/11 的「deboost 时刻 0-lag 无法无处存放 boost 前 deadline/runtime 修复」等关键点均列入 cover 「Not changed」并说明原因。

## Maintainer 意见与讨论焦点

- **Juri Lelli（sched/deadline 维护者）**：对 04/05/13 给 Reviewed-by，对 08 给实现级 Reviewed-by + changelog 改写建议（并质疑 changelog 里「AI review 署名」类信息是否值得写入历史）；在 00/40 首次提出**拆分地基子集先行合入**（「我们在 upper half 上花了时间，是否把 lowest part 拆出让 foundation fixes 先合」）。
- **Mathieu Desnoyers（作者）**：逐条回应约 18 个补丁的 review，全部标注核查方式（绝大多数「read code，not reproduced」）；对 08 的 Sashiko 署名按 generated-content.rst 保留致谢但去掉发布号。
- 无 NAK；Juri 已对多个补丁放下 RB，主要未决点是「拆分先行合入 vs 整套继续迭代」。

## 合入评估

*likelihood=high*。技术分歧（08 的完整机制 vs bandaid，见 20261110-009）已随 v7 收敛——Juri 对 08 从「存疑」转为「给 RB 并仅要求改 changelog」；Juri 主动提议拆分地基子集先行合入，说明维护者已在考虑收取路径。*blocking_issues*：① 拆分方案悬而未决（作者尚未表态接不接受 1-8+10+13+14+16+20+37 的子集划分）；② v8 尚未发出（大量改动仍在「下一版」）。*next_action*：Mathieu 出 v8；就「拆分先行合入」给出态度。

## 效果评估

今日无基准数据；价值在正确性。Mathieu 披露了若干「v7 复现→v8 修复」的自测数据：`deboost_new_params_reboost`（v7 400ms→v8 20ms，各 40 轮）、`hotplug_fallback_running`（v7 8/8 失败→v8 全过）、`hotplug_nested_refused`（6/6 保持）、`rebuild_record_taken`（7 次运行复现→修复）。均为作者自测，未获独立第三方复现。

## 我可以参与的点

- **review**：就 Juri「拆分地基子集 1-8+10+13+14+16+20+37 先行合入」的提议给出判断（哪些补丁可独立落地、哪些依赖后续上下文），这是当日最实质的收敛决策。
- **testing**：在 v8 发出后复跑 `deadline_bw_test` 与作者预告的新用例（`deboost_new_params_reboost`、`hotplug_fallback_running`、`rebuild_record_taken` 等），并验证 08 相关 PI+DEADLINE 场景不再 hang。

## 参考链接

- lore thread（v7 cover）: https://lore.kernel.org/all/cover.1794922146.git.mathieu.desnoyers@efficios.com/
- Juri 的拆分提议（Re: 00/40）: https://lore.kernel.org/all/av3J3zMfkRplg-N4@jlelli-thinkpadt14gen4.remote.csb/
- Juri 对 08 的实现 RB 与 changelog 建议: https://lore.kernel.org/all/av2k8JlLvUcBBOhn@jlelli-thinkpadt14gen4.remote.csb/
