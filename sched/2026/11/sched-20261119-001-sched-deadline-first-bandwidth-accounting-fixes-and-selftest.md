# sched/deadline: first bandwidth accounting fixes and selftests

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261105-001：Mathieu Desnoyers 的 v2（21 补丁）在 Juri Lelli 此前 4 个 sched/urgent 修复之上再修 17 个 SCHED_DEADLINE 带宽记账 bug（其中 3 个可直接打死内核），带自测与 sched_debug；Ingo 要求「严格只含 -stable 可回退修复的子集」。
- sched-20261106-001 / 20261107-002 / 20261108-003 / 20261109-001 / 20261110-009：v3（24 补丁）→ v4（26）→ v5（29），Juri 持续评审，对 deadline boost 补丁（08）存疑并给 bandaid 备选。
- sched-20261118-001：**v7 扩到 40 补丁**，Juri 密集评审并**首次提出把「地基修复子集」（1-8、10、13、14、16、20、37）拆出先行合入**。
- sched-20261119-001（今天）：**Mathieu 采纳拆分提议，一天内把地基子集迭代出 v1→v2→v3**（16→16→17 补丁；修复数 13→13→14，另加 1 个 sched_debug + 2 个 selftests），系列定名「**first** bandwidth accounting fixes and selftests」，其余子集将作为 v8 叠加其上。Juri 实测 v2（lockdep+proxy exec，8 vCPU）：deadline_switch_test 5/5、deadline_bw_test 45/46、无 splat，并补测了 cgroup v1 与 sched_ext 场景；v3 把独立的 0-lag 溢出修复收编为 patch 10，数目从 16 扩到 17。

## 背景与问题

（承接 sched-20261105-001 … 20261118-001）Juri Lelli 前一轮 4 个 SCHED_DEADLINE 带宽记账修复被 Ingo 从 tip/sched/urgent 移除后，Mathieu Desnoyers 系统梳理 `dl_bw`/`total_bw`/`this_bw` 记账边界缺陷，按 Ingo「修复在前、stable 可截取」的原则一路推进。系列随评审不断膨胀（v5 的 29 补丁 → v7 的 40 补丁），Juri 在 11/18 明确提议「先拆地基、再跟上半部」。今日正是该拆分落地：Mathieu 把 v7 的前 14 个修复（v7 编号 1-8、10、13、14、16、20、37）拆成独立系列「first bandwidth accounting fixes and selftests」，其余（尤其 boost 语义、参数复位、root domain 带宽迁移等最易 hang 的 PI 纠缠补丁）留待 v8 作为第二系列叠加之上。

修复子集覆盖的实际问题（据 cover）：**2 个可直接打死内核**——patch 4（root domain active CPU 数为 0 时的除零崩溃）与 patch 8（从被清零参数 refill boost 导致 owner CPU lockup）；patch 6 会让 `sysrq-n` 遗留 `cpuset_mutex` 未释放；patch 7 让 throttled 任务切出再切回后永远不再运行；其余多数是 root domain 的 `total_bw`、runqueue 的 `this_bw` 记错，导致 root domain 超额接纳 deadline 任务、或一律拒收。

## 技术方案

今日核心变化是**拆分 + 一天三次迭代**：

- **拆分**：fix 在前、`-stable` 可截取 patches 1-14；patch 15 在 sched_debug 显示每 rq 的 deadline 带宽；patch 16/17 为两个 selftests。v7 编号 1-8、10、13、14、16、20、37 对应本系列 14 个修复，其余 v7 内容（含关联自测用例）留作叠加其上的 v8。
- **编号与署名**：patch 11「Release the bandwidth of a task that leaves the class asleep」与 patch 12「Reject SCHED_DEADLINE on exited tasks」为 Juri 的修复、patch 13(14)「Check the affinity of a deadline task under the runqueue lock」为 Andrea Parri 的修复，Mathieu 原样携带；Sebastian Siewior review 了 affinity 修复。Juri 被 Ingo 从 sched/urgent drop 的 4 个修复里有 3 个在这里（2/4→patch 11、3/4→patch 1、4/4→patch 12），1/4 留在第二系列。
- **v2→v3 的关键改动**：把此前单独贴出的「sched/deadline: Fix an overflow of the 0-lag time with long periods」（0-lag 时间改用 128 位计算，避免长 period 晚数秒才释放带宽）按 Juri 要求收编为 **patch 10**，并插到「Release the bandwidth…」之前（因为后者引用前者修的 0-lag 计算），修复数从 13 增至 14、总补丁 16→17。
- **测试矩阵**（v3 cover）：50 个用例在 25 个 QEMU guest 上全部通过（带 lockdep、无 kernel warning），覆盖 proxy exec 关/PREEMPT_RT/无 CONFIG_CPUSETS/isolcpus=domain/RT_GROUP_SCHED 等组合；在 v7.4-rc2 上则有 6 个 `deadline_bw_test` 用例在 16 个 guest 各失败、`overrun_caught` 在 3 个 guest 失败、`hotplug_server` 触发 patch 4 修的除零直接崩内核、`throttled_round_trip`/`asleep_round_trip` 失败、sysrq 用例因 cpuset_mutex 遗留（patch 6）无法运行。

## 版本演进与当前进展

*current_version: v3（2026-11-19，`<cover.1795092090.git.mathieu.desnoyers@efficios.com>`，17 补丁=14 修复+1 sched_debug+2 selftests）*。

- **v1**（04:06，`<cover.1795031605.git.mathieu.desnoyers@efficios.com>`）：16 补丁、13 修复，作为 split 后首版发出。
- **v2**（05:24，`<cover.1795037078.git.mathieu.desnoyers@efficios.com>`）：仍 16 补丁。Juri 随后实测并补测 cgroup v1 与 sched_ext。
- **v3**（21:49）：17 补丁、14 修复——收编 0-lag 128 位溢出修复为 patch 10 并前移，后续编号顺延（原 10-16 → 11-17）；按 Juri 的 v2 评审回应：把 cgroup v1 与 sched_ext 从「Not tested」移出并署名 Juri 已测；server 用例在 sched_ext 加载时改用 `ext_server`、`hotplug_server` 直接 skip；把「refill 只给 owner 近零 runtime/deadline」的因果解释挪进 patch 10 的 changelog。

## Maintainer 意见与讨论焦点

- **Juri Lelli（sched/deadline 维护者）**：对拆分响应积极（「Thanks for splitting this out」），并给出当日最实质的实测：v2 在 8 vCPU + lockdep + proxy exec 下 `deadline_switch_test` 5/5（含 sysrq）、`deadline_bw_test` 45/46（`move_cancelled` 无 RT_GROUP_SCHED 跳过）、无 splat；revert patch 10 会复现 `asleep_round_trip`/`stopped_switched_out`/`overrun_caught`。补测两项作者「未测」项：① cgroup v1 cpuset（两 exclusive cpuset、root 负载均衡关）下 admission/affinity/refused move/hotplug 与 rc2 一致，A→B→A 迁移会把带宽留在 B 导致 A 少算（rc2 上也有、v7 全文修复，**非回归**）；② sched_ext 下 in-tree selftests 通过、`server_*` 用例指向 `fair_server` 因 ext 挂载被 detach 而失败，`hotplug_server` 因 scx_simple 被 offline eject 而失败——要求测试「选当前 active 的 server」。与 Desnoyers 系列 patch 5「Refuse dl_server debugfs writes while rq is offline」属同一主题但作者不同（Sebastian 侧 8 补丁系列）。
- **Mathieu Desnoyers（作者）**：逐条回应 Juri（server 用例改用 `ext_server`、`hotplug_server` skip；0-lag 修复前移等）。
- **sashiko-bot（AI review 机器人，非维护者）**：对 v1/v2/v3 逐补丁发 AI 复审，v3 命中 17/17（selftests 死代码/未用变量 Low）、09/17（`__dl_clear_params()` 未取消 `dl_timer`、PI deboost 后 donor runtime/deadline 未复位，Medium）、04/17（`__dl_sub()` 在 inactive CPU 上 `total_bw` 下溢）、10/17（`task_non_contending()` 除零与溢出）。
- 无 NAK；系列拆分为先行合入扫清路径，焦点转向子集内各补丁的收尾。

## 合入评估

*likelihood=high*。Juri 的拆分提议已被作者落地，且 Juri 给出带完整测试矩阵的实测背书、无未解决分歧；子集 14 修复 + 2 自测规模可控，符合 Ingo「修复在前、stable 可截取」的收取偏好。*blocking_issues*：① v3 今日晚 21:49 才发出，Juri 尚未对 v3（尤其收编后的 patch 10 与 17 补丁结构）给出合入表态；② 个别 sashiko-bot Medium 提示（如 `dl_timer` 未取消、`__dl_sub()` 下溢）需确认是否已由本系列其他补丁覆盖。*next_action*：等 Juri 对 v3 复审；作者按需出 v4 后由 Ingo 收取 patches 1-14。

## 效果评估

核心价值在正确性，无性能类基准。可观测数字来自测试矩阵：25 个 guest 50 用例全过、v7.4-rc2 上 6 个 `deadline_bw_test` 用例在 16 个 guest 失败（本系列修复对应）；Juri 实测 45/46 通过（仅 `move_cancelled` 因无 RT_GROUP_SCHED 跳过）。均为作者/维护者自测，未见第三方独立复现。

## 我可以参与的点

- **review**：核对 v3 相对 v2 的编号变动是否引入遗漏（尤其 patch 10 前移后 11-17 的逐条 diff），并判断 sashiko-bot 的 Medium 提示（`__dl_sub()` 下溢、`dl_timer` 未取消）是否已被相邻补丁覆盖。
- **testing**：在 PREEMPT_RT / CONFIG_CPUSETS=n / isolcpus=domain 组合上复跑 `deadline_bw_test` 与 `deadline_switch_test`，重点验证 patch 4（除零）、patch 6（sysrq-n）、patch 8（owner lockup）三个高危修复。

## 参考链接

- lore thread（v3 cover）: https://lore.kernel.org/all/cover.1795092090.git.mathieu.desnoyers@efficios.com/
- v2 cover: https://lore.kernel.org/all/cover.1795037078.git.mathieu.desnoyers@efficios.com/
- v1 cover: https://lore.kernel.org/all/cover.1795031605.git.mathieu.desnoyers@efficios.com/
- Juri 的 v2 实测与 sched_ext/cgroup v1 反馈: https://lore.kernel.org/all/av7NchMg0wnyzjcd@jlelli-thinkpadt14gen4.remote.csb/
- Juri 的拆分提议（Re: v7 00/40）: https://lore.kernel.org/all/av3J3zMfkRplg-N4@jlelli-thinkpadt14gen4.remote.csb/

---
id: sched-20261119-001
date: '2026-11-19'
subject: "sched/deadline: first bandwidth accounting fixes and selftests"
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: "<cover.1795092090.git.mathieu.desnoyers@efficios.com>"
lore_url: "https://lore.kernel.org/all/cover.1795092090.git.mathieu.desnoyers@efficios.com/"
authors: [Mathieu Desnoyers, Juri Lelli, Andrea Parri]
maintainers_involved: [Juri Lelli]
current_version: v3
patch_series:
  - version: v1
    msgid: "<cover.1795031605.git.mathieu.desnoyers@efficios.com>"
    date: '2026-11-19'
    summary: "split 后首版：16 补丁（13 修复 + sched_debug + 2 selftests）"
    review_outcome: "sashiko-bot 逐补丁 AI 复审"
  - version: v2
    msgid: "<cover.1795037078.git.mathieu.desnoyers@efficios.com>"
    date: '2026-11-19'
    summary: "仍 16 补丁；Juri 实测 45/46、补测 cgroup v1 与 sched_ext"
    review_outcome: "Juri 反馈 server 用例与 hotplug_server 问题，要求 changelog 说明"
  - version: v3
    msgid: "<cover.1795092090.git.mathieu.desnoyers@efficios.com>"
    date: '2026-11-19'
    summary: "17 补丁（14 修复）：收编 0-lag 128 位修复为 patch 10 并前移；按 Juri 意见修订"
    review_outcome: "待 Juri 对 v3 复审"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["v3 刚发出 Juri 未复审", "sashiko-bot 的 Medium 提示需确认是否被覆盖"]
  next_action: "Juri 复审 v3，作者按需出 v4 后由 Ingo 收取 patches 1-14"
contribution_opportunities:
  - kind: review
    description: "核对 v3 编号变动无遗漏、判断 sashiko-bot Medium 提示是否已被覆盖"
  - kind: testing
    description: "PREEMPT_RT/CONFIG_CPUSETS=n/isolcpus 组合复跑 deadline_bw_test 与 deadline_switch_test"
generated_at: "2026-11-20T09:00:00+08:00"
source_email_count: 66
related_articles: [sched-20261105-001, sched-20261106-001, sched-20261107-002, sched-20261108-003, sched-20261109-001, sched-20261110-009, sched-20261118-001]
tags: [deadline, dl_server, cgroup]
---