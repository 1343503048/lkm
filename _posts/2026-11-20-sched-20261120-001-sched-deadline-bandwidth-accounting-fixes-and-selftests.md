---
id: sched-20261120-001
date: '2026-11-20'
subject: 'sched/deadline: bandwidth accounting fixes and selftests'
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: <cover.1795181240.git.mathieu.desnoyers@efficios.com>
lore_url: https://lore.kernel.org/all/cover.1795181240.git.mathieu.desnoyers@efficios.com/
authors:
- Mathieu Desnoyers
maintainers_involved:
- Juri Lelli
- Waiman Long
current_version: v9
patch_series:
- version: v8
  msgid: <cover.1795116790.git.mathieu.desnoyers@efficios.com>
  date: '2026-11-20'
  summary: 33 补丁：作为地基系列之上第二系列发出，承接 v7 其余内容，按主题分组并带自测用例
  review_outcome: sashiko-bot 逐补丁 AI 复审；Mathieu 致 Waiman 确认 cpuset offline 边界
- version: v9
  msgid: <cover.1795181240.git.mathieu.desnoyers@efficios.com>
  date: '2026-11-20'
  summary: 修正 Sashiko AI 对 v8 的复审发现，新增 4 个自测用例
  review_outcome: 待 Juri 对 v9 复审
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v9 尚未获 Juri 逐补丁复审结论
  - cpuset offline 顺序边界待 Waiman 确认
  next_action: Juri 复审 v9、Waiman 确认 cpuset 边界后由 Ingo 收取
contribution_opportunities:
- kind: review
  description: 核对 v9 相对 v8 改动无遗漏，重点 patch 20/21 donor UAF 在 proxy execution 下的正确性
- kind: testing
  description: PREEMPT_RT/CONFIG_CPUSETS=n/isolcpus/sched_ext 组合复跑 self测试验证 patch
    13、20/21
- kind: discussion
  description: 就 patch 16 的 cpuset offline 顺序预测（select_fallback_rq 先于 cpuset 更新）提供判断
generated_at: '2026-11-21T09:00:00+08:00'
source_email_count: 216
related_articles:
- sched-20261105-001
- sched-20261106-001
- sched-20261107-002
- sched-20261108-003
- sched-20261109-001
- sched-20261110-009
- sched-20261118-001
- sched-20261119-001
tags:
- deadline
- dl_server
- cgroup
title: 'sched/deadline: bandwidth accounting fixes and selftests'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a>：Mathieu Desnoyers 的 v2（21 补丁）在 Juri Lelli 此前 4 个 sched/urgent 修复之上再修 17 个 SCHED_DEADLINE 带宽记账 bug（其中 3 个可直接打死内核），带自测与 sched_debug；Ingo 要求「严格只含 -stable 可回退修复的子集」。
- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261106-001</a> … 20261110-009：v3（24 补丁）→ v4（26）→ v5（29），Juri 持续评审，对 deadline boost 补丁存疑并给 bandaid 备选。
- <a class="article-ref" href="/lkm/2026/11/18/sched-20261118-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261118-001</a>：v7 扩到 40 补丁，Juri 密集评审并首次提出把「地基修复子集」拆出先行合入。
- <a class="article-ref" href="/lkm/2026/11/19/sched-20261119-001-sched-deadline-first-bandwidth-accounting-fixes-and-selftest.html">sched-20261119-001</a>：拆分落地，地基子集独立成系列「first bandwidth accounting fixes and selftests」，一天内迭代 v1→v3（17 补丁）。
- <a class="article-ref" href="/lkm/2026/11/20/sched-20261120-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261120-001</a>（今天）：**第二系列（33 补丁，v7 其余部分）一天内发出 v8 与 v9**。v9 修正了 Sashiko AI 对 v8 的复审发现并新增 4 个自测用例。本系列单独修 26 个 SCHED_DEADLINE bug，其中 1 个可直接打死内核（patch 13）、2 个让 rtmutex 链 walk 的 owner 持有可退出的 donor 从而读已释放内存（patch 20/21，UAF）。sashiko-bot 逐补丁 AI 复审，Mathieu 密集回应；Juri 对整体进度表态「starting to look good」。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a> … 20261119-001）Juri Lelli 此前 4 个 SCHED_DEADLINE 带宽记账修复被 Ingo 从 tip/sched/urgent 移除后，Mathieu Desnoyers 系统梳理 `dl_bw`/`total_bw`/`this_bw` 记账边界缺陷，并把系列按 Ingo 的「修复在前、stable 可截取」原则拆分：地基 14 修复已独立成「first」系列（本日另文 <a class="article-ref" href="/lkm/2026/11/20/sched-20261120-002-sched-deadline-first-bandwidth-accounting-fixes-and-selftest.html">sched-20261120-002</a>），本系列是 v7 其余部分，叠放在地基系列之上，覆盖更难的单向问题——root domain 重建/迁移时的带宽归属、cpuset 附着同步、partition / isolcpus=domain 下的 root domain 语义、rtmutex 链 walk 的 donor 生命周期、deadline boost 记账，以及参数变更时的 runtime/deadline 处理。

据 cover，本系列修 26 个 bug：patch 13 可直接打死内核；patch 20/21 让 rtmutex 链 walk 中的 owner 保留一个「可退出」的 donor，之后再读到已释放内存（UAF），这两处也闭合了地基系列 patch 11 描述的已知边界；patch 24 会留下一个永不运行的任务；其余多数是 root domain 的 `total_bw` 或 runqueue 的 `this_bw` 记错，导致 root domain 超额接纳 deadline 任务、或一律拒收。

## 技术方案

按主题分组（每组末尾是 `deadline_bw_test` 的自测用例）：

- **root domain 记账重建（1-6）**：保留退出任务的带宽、从 task list 重建记账、记录「持有某任务带宽」的 root domain、重建时排除已释放带宽的 dying 任务。
- **cpuset 附着（7-12）**：带宽只在 attach 腾出空间处迁移、attach 完成前等待、policy/affinity 变更等待进行中的 attach、退回 attach 未迁移的带宽、在每个任务迁入的 root domain 预留带宽。
- **带 partition 与 isolcpus=domain 的 root domain 语义（13-18）**：让重建按任务实际运行的 root domain 计数、迁移带宽到该 domain、在计数 domain 内选 CPU、拒绝让任务在计数 domain 内失去最后一颗 CPU 的 offline、拒绝留下无 CPU 可用的 cpuset 变更。
- **extra_bw（19）**：仅按 active CPU 数分摊 total_bw 变化。
- **rtmutex 链 walk（20-22）**：waiter 的 deadline donor 变化时继续链 walk、owner 的 top pi waiter 迁到另一把锁时继续链 walk，避免 owner 持有可退出 donor。
- **deadline boost（23-28）**：deboost 时开新 period、补足睡眠中被 boost 的 throttled 任务、把 boosted 任务带宽计入 this_bw、为等 rt_mutex 入类的任务给 deadline、类外 deboost 时开新 period 并立即释放带宽。
- **参数变更（29-33）**：取消与参数绑定的 replenishment timer、constrained 任务的剩余 runtime 上限 dl_runtime、按 wakeup 同款检查回来可运行任务的剩余 runtime 等。

版本演进：v8 时 Juri 要求把前 14 补丁拆出独立系列后，本系列承接 v7 其余内容；v9 修掉 Sashiko AI 对 v8 的复审发现并新增 4 个自测用例。

## 版本演进与当前进展

*current_version: v9（2026-11-20，`<cover.1795181240.git.mathieu.desnoyers@efficios.com>`，33 补丁）*。

- **v8**（`<cover.1795116790.git.mathieu.desnoyers@efficios.com>`）：33 补丁，作为地基系列之上的第二系列发出，承接 v7 其余内容。
- **v9**（当天晚些）：修正 Sashiko AI 对 v8 的复审发现，并新增 4 个自测用例（各主题组用例数从 v8 的 7/22/24/2/7 增至 7/23/25/2/8 等）。

## Maintainer 意见与讨论焦点

- **Juri Lelli（sched/deadline 维护者）**：在评审地基系列 v5 时对整体进度表态「I have the impression this is starting to look good, what do you think?」（致 Peter、Ingo）；对地基 0-lag 溢出 patch 给 Reviewed-by 及「加注释 helper、每处检查前写清比较对象」的可读性 nit。
- **Waiman Long（cpuset 维护者）**：Mathieu 在 patch 16 的回帖（`<20261119202257.419139-1-mathieu.desnoyers@efficios.com>`）里列出对 cpuset offline 后 effective CPUs 的 6 点预测 + 1 个疑问（offline 时 `select_fallback_rq()` 先于 cpuset 更新运行，任务可能短暂落在 root domain 之外），请 Waiman 确认。
- **sashiko-bot（AI review 机器人，非维护者）**：对 v8/v9 逐补丁发 AI 复审，v9 修正了它对 v8 的发现。
- 无 NAK。方向已获维护者认可，剩余是逐补丁收尾与 cpuset 边界确认。

## 合入评估

*likelihood=high*。系列已按 Ingo/Juri 愿望拆分为「地基先行 + 本系列随上」两段，地基 v5 获 Juri 实测背书（45/46、45/45 全过、无 splat）与「starting to look good」表态；本系列 v9 已响应 AI 复审并收敛。*blocking_issues*：① 本系列 v9 尚未获 Juri 逐补丁复审结论；② 与 cpuset 的 offline 顺序边界（Mathieu 致 Waiman 的疑问）待 Waiman 确认；③ sched_ext/服务器场景等交叉验证仍在补充。*next_action*：Juri 对 v9 复审，Waiman 确认 cpuset 边界，随后由 Ingo 收取。

## 效果评估

正确性修复，无性能基准。可观测数字来自测试矩阵：地基系列 25 个 guest 用例全过；Juri 实测 `deadline_switch_test` 5/5、`deadline_bw_test` 46/47（`move_cancelled` 跳过）、sched_ext selftests 40/40、`test_cpuset_prs.sh` 通过、lockdep 无 splat；v7.4-rc2 上 6 个 `deadline_bw_test` 用例在 16 个 guest 各失败（本修复对应）。均为作者/维护者自测。

## 我可以参与的点

- **review**：核对 v9 相对 v8 的改动（AI 复审修正 + 4 个新用例）是否有遗漏，尤其是 patch 20/21（rtmutex 链 walk 的 donor UAF）在 proxy execution 下的正确性。
- **testing**：在 PREEMPT_RT、CONFIG_CPUSETS=n、isolcpus=domain、sched_ext 加载等组合上复跑 `deadline_bw_test`/`deadline_rebuild_test`，重点验证 patch 13（打内核）、patch 20/21（UAF）两个高危修复。
- **discussion**：就 patch 16 对 cpuset offline 顺序的预测（尤其第 7 点 `select_fallback_rq()` 先于 cpuset 更新的边界）提供 cgroup/cpuset 侧的判断。

## 参考链接

- lore thread（v9 cover）: https://lore.kernel.org/all/cover.1795181240.git.mathieu.desnoyers@efficios.com/
- v8 cover: https://lore.kernel.org/all/cover.1795116790.git.mathieu.desnoyers@efficios.com/
- 致 Waiman 的 patch 16 回帖: https://lore.kernel.org/all/20261119202257.419139-1-mathieu.desnoyers@efficios.com/
