# sched/deadline: bandwidth accounting fixes and selftests

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261105-001：Mathieu Desnoyers 的 v2 在 Juri Lelli 此前 4 个 sched/urgent 修复之上再修 17 个 SCHED_DEADLINE 带宽记账 bug，带自测与 sched_debug；Ingo 要求「严格只含 -stable 可回退修复的子集」。
- sched-20261106-001 … 20261110-009：v3（24 补丁）→ v4（26）→ v5（29），Juri 持续评审，对 deadline boost 补丁存疑并给 bandaid 备选。
- sched-20261118-001：v7 扩到 40 补丁，Juri 密集评审并首次提出把「地基修复子集」拆出先行合入。
- sched-20261119-001：拆分落地，地基子集独立成「first bandwidth accounting fixes and selftests」系列，一天内迭代 v1→v3（17 补丁）。
- sched-20261120-001：第二系列（v7 其余部分）一天内发出 v8/v9，v9 修掉 Sashiko AI 对 v8 的复审发现；Juri 表态「starting to look good」。
- sched-20261121-001（今天）：**v10 发出（40 补丁，+11432/-531 行）**。覆盖前一版遗留 + Sashiko AI 对 v9 的复审发现，新增 6 个修复与 14 个自测用例（累计修 32 个 bug）；sashiko-bot 当日对 v10 逐补丁复审，已在新 patch 35/38 上提出 Medium/High 级别新发现，指向还需一轮收敛（v11）。

## 背景与问题

（承接 sched-20261105-001 … 20261120-001）Juri Lelli 此前 4 个 SCHED_DEADLINE 带宽记账修复被 Ingo 从 tip/sched/urgent 移除后，Mathieu Desnoyers 系统梳理 `dl_bw`/`total_bw`/`this_bw` 记账边界，把系列按 Ingo「修复在前、stable 可截取」原则拆为两段：地基 14 修复独立成「first」系列，本系列是其上、覆盖更难的 root domain 重建/迁移带宽归属、cpuset 附着同步、partition/isolcpus=domain 语义、rtmutex 链 walk donor 生命周期、deadline boost 记账与参数变更。v10 精简为「修 32 个 bug」：patch 13 可直接打死内核；patch 21-23 让 rtmutex 链 walk 中 owner 持有可退出的 donor 从而读已释放内存（UAF）；patch 26 会留下永不运行的任务；其余多数使 root domain 的 `total_bw` 或 runqueue 的 `this_bw` 记错。

## 技术方案

按主题分组（每组末尾是 `deadline_bw_test` 自测用例）——v10 相对 v9 的主要变化：

- **root domain 重建（1-6）**：保留退出任务带宽、从 task list 重建、记录持有带宽的 root domain、重建时排除已释放带宽的 dying 任务；patch 3 在 `move_became_deadline_no_room` 中把 move 后的变更失败从 EPERM 改 EBUSY。
- **cpuset 附着（7-12）**：带宽只在 attach 腾空间处迁移、attach 完成前等待、policy/affinity 变更等待进行中的 attach；patch 16（新的拒绝语义）在「offline 使 sibling partition 失效」时也拒绝。
- **root domain 语义（13-18）**：patch 15 让 offline 迁移先保持在 root domain 内再 WARN；patch 16/17 拒绝让 deadline 任务在计数 domain 内失去 CPU 的 offline / cpuset 变更（Waiman Long 关注的 cpuset 交互点）。
- **extra_bw（19-20）**：patch 20（新增）修 32 位截断——带宽和在 `__dl_add/sub()` 里可能越过 S32_MAX。
- **rtmutex 链 walk（21-24）**：patch 22 移除第二个提前终止点；patch 23（新增）让 boosted 任务持有 donor 引用（`dl_set_donor()` 用 `tryget_task_struct()`，修复链 walk 被抢占时 donor 可退出的 UAF）。
- **deadline boost（25-31）**：patch 25 deboost 取消 refill 武装的 inactive timer；patch 28 从 `dl_set_donor()` 装入的 donor 检测新 donor；patch 30（新增）`task_blocks_on_rt_mutex()` 刷新 FUTEX_CMP_REQUEUE_PI requeue 任务的 deadline。
- **参数变更（32-39）**：patch 35 `rt_mutex_setprio()` 先 deboost 再比较；patch 36/37/38（新增）分别「重调度入队即被节流的运行任务」「跨 dl_deadline 变更保持 period 起点（新字段 period_start）」「boost 无法在自身 reservation 上运行的 owner」；patch 40（新增）共享 deadline 自测 helper。

作者在 cover 声明本系列由 LLM 编码助手在其指导与评审下写成，并明确「reproducer 停止失败只说明症状消失，不说明这是你会写的修法」，请熟悉 SCHED_DEADLINE 的人仔细读码。

## 版本演进与当前进展

*current_version: v10（2026-11-21，`<cover.1795207232.git.mathieu.desnoyers@efficios.com>`，40 补丁）*。

- **v9**（`<cover.1795181240.git.mathieu.desnoyers@efficios.com>`）：33 补丁，修 26 bug，回应 Sashiko AI 对 v8 的复审。
- **v10**（今天）：扩到 40 补丁、修 32 bug；新增 6 修复（patch 20/23/30/36/37/38）与 14 个用例，逐条消化 Sashiko AI 对 v9 的复审与 v9 遗留清单。当日 Mathieu 另发 7 封回帖（对 v9 各 patch 的逐条回应），确认了哪些「will fix in v10」「是旧 bug，非本系列引入」「是 boost 的既有语义」。

## Maintainer 意见与讨论焦点

- **Juri Lelli（sched/deadline 维护者）**：在评审地基系列时表态「I have the impression this is starting to look good, what do you think?」，并要求 deadline boost 相关细节分组、给出 bandaid 备选；本日缓存未见 Juri 对 v10 的新回复。
- **sashiko-bot（AI review 机器人，非维护者）**：当日对 v10 逐补丁复审，已在 patch 35（`dl_proxy_block()` 缺 `dl_new_params` 检查、PI futex requeue 缺 boost 等 3 条 Medium/Low）、patch 38（`dl_deboost()` 缺 throttle 恢复、`replenish_dl_entity()` 把 donor period 加进 `own_deadline` 等 2 条 High + 4 条 Medium）上提出新发现。这些指向 v10 仍未收敛、作者大概率还要再发一版。
- 无 NAK。方向获维护者认可，剩余是逐补丁收尾 + AI 复审新发现 + cpuset 边界确认。

## 合入评估

*likelihood=high*。系列已按 Ingo/Juri 期望拆为「地基先行 + 本系列随上」两段，地基获 Juri 实测背书与「starting to look good」表态；v10 已系统性消化 AI 复审。*blocking_issues*：① 当日 sashiko-bot 对 v10 patch 35/38 的新 High 发现尚未被作者回应；② Juri 尚未对 v10 逐补丁复审；③ cpuset offline 顺序边界（patch 16/17）待 Waiman Long 确认。*next_action*：作者回应 sashiko-bot 对 v10 的新发现（大概率发 v11），Juri 复审、Waiman 确认 cpuset 边界后由 Ingo 收取。

## 效果评估

正确性修复，无性能基准。可观测数字来自测试矩阵（v10 cover）：141 个用例在 20 个 QEMU guest（4-8 vCPU）全过、lockdep 无警告，覆盖 proxy execution 开/关、PREEMPT_RT、无 CONFIG_CPUSETS、CONFIG_RT_GROUP_SCHED、isolcpus=domain 多种组合；每个测试补丁点新增用例在 12 个 guest 全过；3 个 kmemleak guest 全系列无泄漏；40 个补丁各自独立可编译。patch 20 因需 >2048 CPU 的带宽、patch 23 因需链 walk 恰在正确步进被抢占，无独立用例覆盖。均为作者自测。

## 我可以参与的点

- **review**：重点读 patch 21-23（rtmutex 链 walk donor UAF）与 patch 38（boost 无法自运行的 owner）在 proxy execution 下的正确性，以及 sashiko-bot 对 patch 38 的两条 High 发现是否属实。
- **testing**：在 PREEMPT_RT、CONFIG_CPUSETS=n、isolcpus=domain、sched_ext server（作者列明未测）等组合上复跑 `deadline_bw_test`/`deadline_rebuild_test`。
- **discussion**：就 patch 16/17 的 cpuset offline order 边界（`select_fallback_rq()` 先于 cpuset 更新）提供 cgroup/cpuset 侧判断。

## 参考链接

- lore thread（v10 cover）: https://lore.kernel.org/all/cover.1795207232.git.mathieu.desnoyers@efficios.com/
- v9 cover: https://lore.kernel.org/all/cover.1795181240.git.mathieu.desnoyers@efficios.com/
- 前置「first」系列: https://lore.kernel.org/all/cover.1795115075.git.mathieu.desnoyers@efficios.com/
- sashiko-bot 对 patch 38 的复审: https://lore.kernel.org/all/sashiko-outbox-226195@kernel.org/

---
id: sched-20261121-001
date: '2026-11-21'
subject: "sched/deadline: bandwidth accounting fixes and selftests"
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: "<cover.1795207232.git.mathieu.desnoyers@efficios.com>"
lore_url: "https://lore.kernel.org/all/cover.1795207232.git.mathieu.desnoyers@efficios.com/"
authors: [Mathieu Desnoyers]
maintainers_involved: [Juri Lelli, Waiman Long]
current_version: v10
patch_series:
  - version: v9
    msgid: "<cover.1795181240.git.mathieu.desnoyers@efficios.com>"
    date: '2026-11-20'
    summary: "33 补丁：修 26 个 SCHED_DEADLINE 带宽记账 bug，按主题分组并带自测"
    review_outcome: "sashiko-bot 逐补丁 AI 复审；Mathieu 当日逐条回应确认修法"
  - version: v10
    msgid: "<cover.1795207232.git.mathieu.desnoyers@efficios.com>"
    date: '2026-11-21'
    summary: "40 补丁：修 32 个 bug，新增 6 修复（20/23/30/36/37/38）与 14 用例，消化 Sashiko AI 对 v9 的复审与遗留清单"
    review_outcome: "sashiko-bot 对 v10 patch 35/38 提出新的 Medium/High 发现；Juri 未复审"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["sashiko-bot 对 v10 patch 35/38 的新 High 发现未回应", "Juri 未对 v10 逐补丁复审", "cpuset offline 顺序边界待 Waiman 确认"]
  next_action: "作者回应 sashiko-bot 对 v10 的新发现（或发 v11），Juri 复审、Waiman 确认 cpuset 边界后由 Ingo 收取"
contribution_opportunities:
  - kind: review
    description: "读 patch 21-23/38 在 proxy execution 下的 donor 生命周期正确性，核对 sashiko-bot 对 patch 38 的两条 High 发现"
  - kind: testing
    description: "PREEMPT_RT/CONFIG_CPUSETS=n/isolcpus/sched_ext 组合复跑 deadline_bw_test 与 deadline_rebuild_test"
  - kind: discussion
    description: "就 patch 16/17 的 cpuset offline order 边界提供 cgroup/cpuset 侧判断"
generated_at: "2026-11-22T01:00:00+08:00"
source_email_count: 91
related_articles: [sched-20261105-001, sched-20261106-001, sched-20261107-002, sched-20261108-003, sched-20261109-001, sched-20261110-009, sched-20261118-001, sched-20261119-001, sched-20261120-001]
tags: [deadline, dl_server, cgroup]
---