# Improving latency of short slice tasks

## TL;DR

Vincent Guittot（sched/fair 维护者）的 v3 大系列（20 补丁）继续改进短 slice 任务的调度延迟：为正 lag 引入衰减、在选 CPU 时考虑 slice、为 fair 类新增 push 回调机制、用 push 把「入队时没跑上」的短任务迁移到更合适的 CPU、让 feec()（EAS）按 cost+slice 选 CPU、并修复多任务同时醒来堆叠同一 idle CPU 的角例。作者在 dragonboard rb5 上的测试显示：4 个短任务同时醒来时平均延迟从约 1051us 降到约 61us，hackbench pipe 提升 15-25%；但 cyclictest 的 99.9 分位略回退（正 lag 衰减所致）。刚发出 v3，尚无评审。

## 背景与问题

EEVDF 落地后仍有一类延迟问题：多个短 slice（short slice）任务同时运行时，任务容易堆叠在同一颗 CPU 上——即使系统里有 idle CPU，也只有第一个任务能立即运行，其余要等。同时「永恒的正 lag」会让长时间睡眠、攒了大量正 lag 的任务在醒来时抢占/挤占短任务，让短任务无法先跑。系列目标是分块收敛这些角例：正 lag 的记账、slice 参与 CPU 选择、短任务在 wakeup 时「没被选中」后的补救迁移，以及 EAS（feec）对 slice 的考虑。

## 技术方案

系列把 20 个补丁分成 5 个部分：

- **Patch 1-4（正 lag 衰减）**：`decay_entity_lag()` 在 wakeup 入队时用睡眠时长与 cfs 负载、任务权重衰减正 lag（负 lag 已由 delayed dequeue 处理）；并在「prev CPU 进入过 idle」「迁移且 prev 已 idle」「在 idle CPU 醒来」三种情形重置 lag，杜绝长时间睡眠任务凭陈旧正 lag 抢占短任务。
- **Patch 5-6（slice 参与选 CPU）**：为每个 CPU 缓存 lockless 的 `min_slice`（`struct rq` 内，范围 [100us:100ms]），并在选 CPU 时新增「min slice 检查」这一层级，帮醒来的任务选到能最快运行的那颗 CPU。
- **Patch 7-12（fair 的 push 回调）**：为 fair 类新增 push 任务机制（patch 8）、优化（patch 9）、rq flag 传给 tick 参数以在 tick 中强制迁移（patch 10）、force push（patch 11）、并让 `select_idle_sibling` 支持「非 wakeup」场景（patch 12），使 `select_task_rq_fair()` 能对已入队的任务重新选 CPU。
- **Patch 13-15（push 迁移没跑上的短任务）**：把「设为 next buddy 但仍未被 pick」的短 slice 任务加进 pushable 列表（patch 14），并启用 preempt short 的 push（patch 15），让它们有机会被 push 到更合适的 CPU。
- **Patch 16-19（feec 用 cost 而非 spare capacity）**：energy model 增加「取前一状态」函数（16）、移除未用的 `em_cpu_energy()`（18），feec() 改用 cost 并在 cost 相同时按 slice 选 CPU（17/19）。
- **Patch 20（修堆叠）**：当多个任务同时醒来选中同一 idle CPU 时，只有第一个立即运行；补丁利用 push 回调为「输掉竞争、没被 pick」的任务找别的 CPU，并让更高调度类也走 `wakeup_preempt`，使 fair 能准备好处理堆叠。

## 版本演进与当前进展

*current_version: v3（2026-11-06 发出，msgid 20261106151947.3991524-1）*。v3 相对 v2 的变化：移除 wake_affine 里的 min_slice 比较（最终无收益）、新增迁移时重置 lag、修复 idle CPU 堆叠角例、并尽量吸收 v2 收到的全部意见。相对 v1：`decay_entity_lag` 计入 cfs 负载但暂不含迁移任务、CPU 进入 idle 则重置 lag、lockless min_slice 移入 `struct rq` 用 unsigned long、min_slice 选择并入 `select_idle_capacity()/select_idle_cpu()`、新增 push 回调机制、push 未选中的短任务、feec 按 slice 选 CPU。当日无评审（系列晚间 23:19 发出）。

## Maintainer 意见与讨论焦点

本日刚发出，暂无维护者或 reviewer 回应。作者本人是 sched/fair 维护者，系列为自研方向。此前 patch 06/20（min slice 检查）曾以独立补丁形式在 10 月迭代多轮（见十月归档），已有社区审阅积累。

## 合入评估

*likelihood=unknown*。系列刚发出、尚无评审，且规模大（20 补丁、横跨 EEVDF/EAS/push 机制）、触及调度器热路径，需要逐封审阅与更多独立数据背书。*blocking_issues*：暂无（尚无反对意见）。*next_action*：等待 Peter Zijlstra、以及 EAS/push 方向相关 reviewer 的评审意见。

## 效果评估

作者在 dragonboard rb5 上的调度延迟测试（每个 130s）：

- 4 个短 slice 任务（各 1ms/7777ms，uclamp min 512）+ 16 个普通任务同时醒来：4 个短任务平均延迟从 tip/sched/core 的约 1051/52/1051/1093us 降到约 61/61/60/61us，99.9 分位 2400/120/2518/2408us 降到 1839/2012/63/2175us——tip 上 4 任务倾向堆同一 CPU，本系列会把没被 pick 的任务 push 走。
- cyclictest 单独跑：99 分位 91→92us（-1%）、99.9 分位 128→161us（-26%）、最大值 273→223us（+18%）——99.9 分位略回退主因是正 lag 衰减（cyclictest 运行时什么都不做、靠缓慢下降的大正 lag 获益，现在正 lag 在睡眠中消逝、多数时候以 0 lag 入队）。
- hackbench pipe（默认 2.8ms slice）：4/8/16 组 process 提升约 18%/15%/15%，thread 提升约 17%/25%/13%；作者指出「Decay positive lag」这一补丁贡献了大部分提升，且提升在预期之外。

## 我可以参与的点

- **testing**：在 x86（尤其大小核/多 NUMA）与其它平台上复跑作者的 cyclictest、rt-app 多短任务、hackbench 用例，验证 99.9 分位回退是否在其它负载下同样出现、短任务延迟收益是否可复现——这是最有价值的参与点。
- **review**：审视 push 回调机制与 `select_task_rq_fair()` 支持「已入队任务」重选 CPU 的路径（patch 7-15），以及 feec() 从 spare capacity 换到 cost 的取舍（patch 16-19）。

## 参考链接

- lore thread（v3 cover）: https://lore.kernel.org/all/20261106151947.3991524-1-vincent.guittot@linaro.org/

---
id: sched-20261106-002
date: 2026-11-06
subject: "Improving latency of short slice tasks"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261106151947.3991524-1-vincent.guittot@linaro.org>"
lore_url: "https://lore.kernel.org/all/20261106151947.3991524-1-vincent.guittot@linaro.org/"
authors: [Vincent Guittot]
maintainers_involved: []
current_version: v3
patch_series:
  - version: v1
    msgid: null
    date: null
    summary: "正 lag 衰减 + min_slice 选 CPU 的早期版本。"
    review_outcome: "未获取到 v1 具体日期与评审记录。"
  - version: v2
    msgid: null
    date: null
    summary: "吸收 v1 评审，新增 push 回调机制与 feec slice 改造。"
    review_outcome: "未获取到 v2 具体日期与评审记录。"
  - version: v3
    msgid: "<20261106151947.3991524-1-vincent.guittot@linaro.org>"
    date: 2026-11-06
    summary: "20 补丁：正 lag 衰减、slice 选 CPU、fair push 回调、push 短任务、feec 用 cost、修 idle CPU 堆叠。"
    review_outcome: "刚发出，暂无评审。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: "等待 Peter Zijlstra 及 EAS/push 方向 reviewer 的评审意见"
contribution_opportunities:
  - kind: testing
    description: "在 x86/大小核/多 NUMA 平台复跑 cyclictest、rt-app 多短任务、hackbench，验证 99.9 分位回退与短任务延迟收益"
  - kind: review
    description: "审阅 push 回调机制与 select_task_rq_fair 对已入队任务重选 CPU、feec 从 spare capacity 换 cost 的取舍"
generated_at: "2026-11-07T09:00:00+08:00"
source_email_count: 18
related_articles: []
tags: [cfs, eevdf, load_balance, perf]
---
