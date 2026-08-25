# sched/fair: Prefer waker CPU for non-SMT reciprocal sync wakeups

## TL;DR

Madadi Vineeth Reddy 提出让 `WF_SYNC` 同步唤醒把 wakee 放到 waker 所在 core 的 SMT 兄弟线程上，以保住已经热的 cache。POWER11 上 hackbench 小规模场景有 6–8% 提升，但 reviewer 当天就指出这个收益可能高度依赖 SMT 编号连续性，x86 上未必成立——在补齐跨平台数据之前不宜下结论。

## 背景与问题

`WF_SYNC` 语义是「waker 即将阻塞」。`wake_affine_idle()` 已经据此行事：当 waker 的 runqueue 上只有一个可运行任务时，它返回 waker 的 CPU。

但这个决策随后被 `select_idle_sibling()`（SIS）丢弃：对于一个仍在运行 waker 的 CPU，`available_idle_cpu()` 返回 false，于是 SIS 继续在 LLC 内向别处扫描。

当 wakee 的 `prev_cpu` 空闲且与 target 共享 cache 时，SIS 会提前返回它，没有损失。但一旦 `prev_cpu` 繁忙，扫描就没有任何手段区分两种情况：

- 「这个 core 真的忙」
- 「这个 core 上只跑着那个马上就要睡的 waker」

结果 wakee 被放到一个冷 CPU 上，而 waker 的 core 明明马上就要空出容量、且数据还在 cache 里。

## 技术方案

把 waker 的 CPU（`sync_cpu`）沿调用链一路传下去，`select_idle_sibling()` 与 `select_idle_core()` 都增加该参数。在 `select_idle_core()` 遍历 `cpu_smt_mask(core)` 时，对 `cpu == sync_cpu` 的情形不再要求 `available_idle_cpu()` 为真，而是把它当作 idle 处理。这样 waker 所在 core 依然是 idle-core 候选，wakee 就会落到它的某个 SMT 兄弟线程上。

作者明确列出了该改动的 no-op 边界，这一点做得比较扎实——以下情况行为完全不变：waker 的 core 没有空闲兄弟线程时、waker 的 runqueue 上不止一个可运行任务时、wakee 的 `prev_cpu` 本身已是合法 target 时、以及非 SMT 系统上。

值得注意的是，同期社区里存在**三个针对同一类问题的不同切入点**：本 patch 从 SMT 侧改 `select_idle_core()`；Shubhang Kaushik (Ampere) 的 v3 从 non-SMT 侧直接偏好 waker CPU；K Prateek Nayak 则建议把判断下推进 `select_idle_sibling()`、在已知 `test_idle_core()` 结果的位置统一决策。作者本人在另一封邮件中说明，他从 v2 讨论起就在关注 SMT 这一侧，本 patch 即是其产物。

## 版本演进与当前进展

v1 于 2026-08-01 11:55 发出（作者本地时间 08-01 09:25 IST），当日 14:43 即收到 Zhan Xusheng 的第一条 review。目前仍在 v1 阶段，作者尚未回应 review 中提出的关键质疑。

## Maintainer 意见与讨论焦点

Zhan Xusheng 的意见构成本 thread 唯一也是最核心的争议点，他的论证链条相当具体：

`select_idle_cpu()` 的扫描顺序是 `for_each_cpu_wrap(cpu, cpus, target + 1)`，而 `select_idle_core()` 返回它命中的**第一个**完全空闲的 core。

- 在 POWER SMT8 上，SMT 兄弟线程编号是**连续**的，waker 的兄弟正好位于 `target + 1`，最先被访问——恰好符合本 patch 的意图；
- 但在兄弟线程与 waker **不相邻**的布局上（例如 x86 常见的枚举方式，兄弟位于 `cpu + nr_cores` 而非 `cpu + 1`），扫描会先访问其他 core，只要其中任何一个完全空闲，就会在到达 waker 的兄弟之前先返回那个**冷 core**。

他的结论是：这种情况下 cache 共享的收益不会兑现，wakee 落在普通 SIS 本来就会放的位置；不至于回退，但**收益看起来可能主要局限于 SMT 编号连续的平台**。他明确要求补充 x86 / arm64 SMT2 的数据。

这是一条尚未被回应的、直指方案普适性的质疑，不宜淡化。此外作者自己给出的数据里，hackbench thread-pipe 4-group 出现 **-8.8%** 的回退，邮件中未见解释。

## 合入评估

合入可能性 **medium**。方案思路本身合理、no-op 边界清晰，但有三个实打实的阻碍：

1. **跨平台收益未证实**。Zhan Xusheng 的扫描顺序分析很有说服力，在 x86 数据补齐之前，无法排除「这是一个 POWER 特化优化」的判断。
2. **存在未解释的回退**。thread-pipe 4-group -8.8%，虽然标注 sd% 7.9 说明噪声不小，但作者没有就此作出说明。
3. **方案竞争**。同一时期至少有三条技术路径在解决同一问题，社区大概率会要求收敛成一个统一方案，而不是各自合入。K Prateek Nayak 建议的「下推进 select_idle_sibling() 统一决策」在结构上更有整合三者的潜力。

下一步动作很明确：补 x86 / arm64 SMT2 数据、解释 4-group 回退、并与并行方案协调边界。

## 效果评估

作者在 **POWER11、SMT8、160 CPU / 20 core** 上测试，每种情况 5 轮，全部归一化到 baseline：

**producer_consumer**（time/access 中位数，越低越好）：

| load | base | base+patch |
|---|---|---|
| -l 5 | 1.00 | 0.89 (+11.11%) |
| -l 10 | 1.00 | 0.92 (+7.69%) |
| -l 20 | 1.00 | 1.00 (+0.00%) |
| -l 100 | 1.00 | 1.00 (+0.00%) |

作者自己的解读很诚实：这是严格的两任务 handoff，随着每次迭代的工作量增大，唤醒路径占比下降、放置决策的影响也随之消失——`-l 5` 时 11%，`-l 20` 起归零。

**hackbench**（平均完成时间，越低越好，150000 loops）：

| case | load | baseline | base+patch | sd% |
|---|---|---|---|---|
| process-pipe | 1-group | 1.00 | 0.94 (+6.39%) | 6.2 |
| thread-pipe | 1-group | 1.00 | 0.92 (+7.83%) | 8.4 |
| process-pipe | 2-group | 1.00 | 0.94 (+6.18%) | 7.1 |
| thread-pipe | 2-group | 1.00 | 0.97 (+3.12%) | 7.9 |
| process-pipe | 4-group | 1.00 | 0.98 (+1.69%) | 7.2 |
| thread-pipe | 4-group | 1.00 | 1.09 (**-8.8%**) | 7.9 |

需要指出：所有 case 的标准差都在 6–8.4% 区间，与多数提升幅度同量级，因此这批数据的置信度本身有限；而 thread-pipe 4-group 的 -8.8% 回退无论是否为噪声，都需要作者给出说明。**目前完全没有 x86 / arm64 平台的数据**。

## 我可以参与的点

- **测试（高价值，且是 thread 中明确悬空的问题）**：在 x86（SMT 兄弟为非连续编号）与 arm64 SMT2 上跑 `perf bench sched pipe`、producer_consumer 与 hackbench，直接验证 Zhan Xusheng 的质疑——wrap 扫描在非连续编号布局下是否真的会先命中冷 core。这个问题作者当日未回应，补上数据对推进 thread 有直接作用。建议同时用 `trace-cmd` 或 BPF 抓 wakee 实际落点分布，比单纯的吞吐数字更能说明问题。
- **讨论**：本 patch、Shubhang Kaushik 的 non-SMT 方案与 K Prateek Nayak 的内联改法三者在解决同一类问题，可以帮忙梳理适用边界（SMT/非 SMT、有无 idle core、编号布局），在 thread 中提出统一方案的建议。

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260801035532.260625-1-vineethr@linux.ibm.com/
- 相关讨论（作者在 v2 中提出 SMT 侧思路）: https://lore.kernel.org/all/60a584c5-25ac-4077-a725-a2f9ee74318d@linux.ibm.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched/fair: Let sync wakeups target the waker's core"
id: sched-20260801-003
date: 2026-08-01
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<uid-14193@qq-imap>"
lore_url: "https://lore.kernel.org/lkml/20260801035532.260625-1-vineethr@linux.ibm.com/"
authors: [Madadi Vineeth Reddy]
maintainers_involved: [Zhan Xusheng]
current_version: v1
patch_series:
  - version: v1
    msgid: "<uid-14193@qq-imap>"
    date: 2026-08-01
    summary: "WF_SYNC 唤醒且 waker runqueue 只有一个可运行任务时，把 waker 的 CPU 传给 select_idle_core() 并让它计为 idle，使 waker 所在 core 保持 idle-core 候选资格，wakee 落到其 SMT 兄弟线程上；在 POWER11 SMT8 上 producer_consumer 最多提升 11%、hackbench 1-group 提升 6-8%"
    review_outcome: "Zhan Xusheng 指出收益可能依赖 SMT 编号连续性（POWER 连续、x86 不连续），要求补 x86/arm64 SMT2 数据"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["缺少 x86/arm64 SMT2 平台的基准数据，收益是否只在 SMT 编号连续的平台上成立尚未证实", "hackbench thread-pipe 4-group 出现 -8.8% 回退，未见解释", "与 Shubhang Kaushik 的 non-SMT 方案、K Prateek Nayak 的 select_idle_sibling() 内联方案存在方案竞争，社区需要收敛到一条路径"]
  next_action: "补充 x86 / arm64 SMT2 平台的基准测试数据，并解释 thread-pipe 4-group 的回退；同时与并行的 non-SMT 方案协调，明确二者是互补还是需要合并为统一方案"
contribution_opportunities:
  - kind: testing
    description: "在 x86（SMT 兄弟为 cpu+nr_cores 的非连续编号）与 arm64 SMT2 上跑 perf bench sched pipe / producer_consumer / hackbench，验证 Zhan Xusheng 提出的『非连续编号下 wrap 扫描会先命中其他冷 core』这一质疑，这正是当前 thread 中明确悬空、作者尚未回应的问题"
  - kind: discussion
    description: "本 patch 与同期的 non-SMT reciprocal sync wakeup 方案、以及 K Prateek Nayak 的 select_idle_sibling() 内联改法在解决同一类问题，可以帮忙梳理三者的适用边界并在 thread 中提出统一方案建议"
generated_at: "2026-08-02T00:55:00"
source_email_count: 2
related_articles: []
tags: [cfs, load_balance, perf, hyperthreading]
---
