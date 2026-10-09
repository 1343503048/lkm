---
id: sched-20261007-008
date: '2026-10-07'
subject: 'sched/eevdf: Add min slice check when selecting CPU'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261002154415.2270586-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20261002154415.2270586-1-vincent.guittot@linaro.org/
authors:
- Vincent Guittot
maintainers_involved:
- Chen Yu
- Tim Chen
- Kayra Cizmeci
current_version: v2
patch_series:
- version: v2
  msgid: <20261002154415.2270586-1-vincent.guittot@linaro.org>
  date: '2026-10-02'
  summary: 18 补丁 v2：min slice 选 CPU + lag 管理 + push task + feec 重构
  review_outcome: 10-05 Kayra 三连；10-07 Tim Chen（hint 污染+修复）、Chen Yu（实测+cache-aware
    扩展）、Kayra 两封；作者均未回
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 作者对累计七封 review 零回复
  - push 路径 recent_used_cpu 污染需修复进系列
  next_action: 等 Vincent 批量回应与 v3；跟踪 cache-aware×push 评估结果
generated_at: '2026-10-08T01:00:00'
contribution_opportunities:
- kind: review
  detail: 复核 hint 修复与 wakeup 语义等价性；逐点核对 PE 下 donor 语义边界
- kind: testing
  detail: 补不同 time slice 混合负载 hackbench；cache-aware×push 迁移测试
- kind: extend
  detail: 把 cache-aware×push 评估补丁整理成正式 follow-up 系列
source_email_count: 4
related_articles:
- sched-20260921-001
- sched-20260929-018
- sched-20261001-010
- sched-20261002-001
- sched-20261005-001
tags:
- eevdf
- load_balance
title: 'sched/eevdf: Add min slice check when selecting CPU'
layout: article
---

> **subject**：`sched/eevdf: Add min slice check when selecting CPU`
> 本文为增量更新，完整脉络见下。

## TL;DR

- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-001-sched-eevdf-add-min-slice-check-when-selecting-cpu.html">sched-20261002-001</a>：Vincent Guittot 把 8 补丁 v1 扩张成 **18 补丁 v2** 重发——`select_slice_cpu()` 并入 `select_idle_capacity()` 与 `select_idle_cpu()`；系列同时吸收 lag 管理（睡眠实体正 lag 衰减、idle CPU 唤醒重置 lag）、per-cpu min_slice 缓存、wake_affine min slice 比较，并新增 fair 的 push task 机制与 feec() 重构（用 OPP cost 而非 spare capacity 选 CPU、EAS 计入 slice）。
- <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-001-sched-eevdf-add-min-slice-check-when-selecting-cpu.html">sched-20261005-001</a>：Kayra Cizmeci 对 v2 连发三封 review（02/18、04/18、05/18），各带一个实质技术点——DEQUEUE_SAVE 疑漏、`cfs_rq_min_slice()` 值域（空 cfs_rq/RT 压制翻转）、`select_idle_cpu()` 预算耗尽时 slice_cpu 不晋升。Vincent 未回。
- <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-008-sched-eevdf-add-min-slice-check-when-selecting-cpu.html">sched-20261007-008</a>（今天）：**review 大幅升温，四封来自三方**——Tim Chen 审 06/18，指出 push 路径复用 `select_idle_sibling()` 会**污染 `recent_used_cpu` 提示**（push 的 prev 是当前排队 CPU，失败后 hint 退化，后续唤醒丢失第二候选），并给出 +7/−4 的修复 diff；Chen Yu 审 07/18，192 核 Xeon hackbench **无明显差异**（-7.42%~+2.50% 波动内），「it is good now」，并按 Qais 建议发起**cache-aware 调度复用 push 机制**的评估补丁（+82/−7）；Kayra 审 10/18 与 18/18，分别提出 proxy execution 下 `task_tick_fair()` 拿 `rq->donor` 的边界疑虑与 feec() 中「恒假/恒真」的死条件。Vincent 当日仍未回复任何 review。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-001-sched-eevdf-add-min-slice-check-when-selecting-cpu.html">sched-20261002-001</a> → <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-001-sched-eevdf-add-min-slice-check-when-selecting-cpu.html">sched-20261005-001</a>）EEVDF 下短 slice 任务「放置时不挑 CPU、放错后无人推走」的两阶段问题；v2 以 18 补丁覆盖 min slice 选 CPU、lag 管理、push task 机制、feec() OPP cost 重构。今天的 review 暴露的是 v2 把选 CPU 路径开放给非 wakeup 调用方（push）之后的**副作用面**：`select_idle_sibling()` 内部维护的 `recent_used_cpu` 唤醒提示语义只对 wakeup 成立；以及 push 机制与既有机制（cache-aware LB）的组合空间——Chen Yu 的评估补丁正是后者的第一次实现。

## 技术方案

（承接 v2 框架，18 补丁分组不变）今天新增的 review 技术点：

- **06/18（Tim Chen）push 污染 recent_used_cpu**：`select_idle_sibling()` 每次调用都执行 `p->recent_used_cpu = prev`。wakeup 语义下 prev 是「上次运行的 CPU」，旧 hint 成为下次唤醒的第二候选；push 语义下 prev 是「当前排队的 CPU」——push 未迁移任务时 hint 变成当前 CPU，任务之后睡眠再在本 CPU 唤醒时 `recent_used_cpu == prev`，唤醒丢失第二候选；每次失败的 push 都重复这个过程。**修复 diff（+7/−4）**：`select_idle_sibling()` 增加 `select_flags` 参数，仅 `WF_TTWU` 时更新 hint；`fair_push_task()` 迁移任务时把源 CPU 存为 hint（对齐 wakeup 迁移后 hint 的语义）。
- **07/18（Chen Yu）实测 + 扩展方向**：192 核 Xeon、默认参数 hackbench，process/threads × G1/4/8/16 共 8 组，DIFF% 在 +2.50%（process G1 改善）到 -7.42%（threads G8 回退）间波动、多数在噪声带内，结论「no obvious difference, I think it is good now」，预告再测不同 time slice 混合负载。扩展：按 Qais 建议，**cache-aware 调度可作为 push 机制的第二用户**——评估补丁（+82/−7）让 cache-aware 敏感任务经 push 路径被推到其偏好 LLC；论点：push 触发门槛高（需抢占 runnable task），频率低于 wakeup，可降低与 cache-aware LB 的竞争、更快完成偏好 LLC 上的任务聚集。简单迁移测试已启动。
- **10/18（Kayra）proxy execution 边界**：push 检查从 `task_tick_fair()` 进入，而 `task_tick_fair()` 由 `sched_tick()` 以 `rq->donor` 调用——proxy execution 下该指针可能是 donor 而非 curr，`fair_check_pushable_task()` 对「 rq->curr / next」的判断在 PE 语义下可能成立也可能不成立（「Or maybe I'm missing something. Dunno.」），并提醒系列里还有多处同构调用点需要同样审。
- **18/18（Kayra）feec() 死条件**：重构后的 feec() 有 `if (p->on_rq && !p->se.sched_delayed && cpu == prev_cpu)`，其后外部调用 `update_best_cpu()`——若该条件为真，则 prev 的 min_slice 不可能大于 p 的 task_slice：**target 为 prev 时第一检查恒假、min->cpu 为 prev 时第二检查恒真**，指向一段实际不可达/无判别力的代码。

## 版本演进与当前进展

- v1（09-21，8 补丁「Improving latency of short slice tasks」，<a class="article-ref" href="/lkm/2026/09/21/sched-20260921-001-improving-latency-of-short-slice-tasks.html">sched-20260921-001</a>）：dragonboard rb5 数据（cyclictest 99.9 分位 +14%~+25%、hackbench pipe +11%~+30%）。
- v2（10-02，18 补丁，<a class="article-ref" href="/lkm/2026/10/02/sched-20261002-001-sched-eevdf-add-min-slice-check-when-selecting-cpu.html">sched-20261002-001</a>）：扩张为 min slice + lag + push + feec 全家桶。
- 10-05：Kayra 三连 review（<a class="article-ref" href="/lkm/2026/10/05/sched-20261005-001-sched-eevdf-add-min-slice-check-when-selecting-cpu.html">sched-20261005-001</a>）。
- 10-07：Tim Chen、Chen Yu、Kayra 四封 review（`<95c9b871…camel@linux.intel.com>`、`<asWyZtW7zPVo3k-A@chenyu-dev>`、`<20261006192414.7308-1-kayracizmeci@gmail.com>`、`<20261007143614.27368-1-kayracizmeci@gmail.com>`）。**Vincent 对 10-05 以来的全部 review 均未回复**；尚无 v3 迹象。

## Maintainer 意见与讨论焦点

- **Chen Yu**（Intel，sched/fair 维护者）：本系列第一位维护者级表态——实测背书（「it is good now」）+ 主动扩展方向（cache-aware × push 评估补丁）。这既是对 push 机制架构通用性的确认，也把系列与 cache-aware 调度线（Tim Chen 家族）连了起来。
- **Tim Chen**（Intel，sched 资深）：抓到 push 复用 wakeup 基础设施的真实语义 bug（hint 污染），带修复 diff——这是「v2 引入非 wakeup 调用方」这一步的直接代价清单。
- **Kayra Cizmeci**（活跃 reviewer）：延续 10-05 风格，两处均为「边界条件是否被审过」式提问（PE 下的 donor 语义、feec() 死条件），无结论性判断。
- 焦点：push 机制的正确性边界（hint、PE）与生态位（与 cache-aware 的组合）。全部意见**待作者回应**。

## 合入评估

*likelihood=medium*。正面：维护者级实测背书首次出现、review 密度说明社区关注度高、暴露的问题都有清晰修法。负面：Vincent 对累计七封 review 零回复，v3 的消化周期未知；Tim Chen 的 hint 修复若作为系列内补丁需要重排系列，cache-aware 扩展则可能催生后续系列。*blocking_issues*：作者未回应累计 review；push 路径的 hint 污染需要修复进系列。*next_action*：等 Vincent 的批量回应与 v3；cache-aware×push 评估补丁的结果值得跟踪。

## 效果评估

- Chen Yu 192 核 Xeon hackbench（默认参数，8 组）：DIFF% ∈ [+2.50%, -7.42%]，process G1/G16 改善、threads G8 最差 -7.42%——大核数默认负载下中性，作者预告补不同 time slice 混合的测试。
- cache-aware×push 评估补丁的迁移测试结果**尚未给出**（「will update later」）。
- 其余沿用 v1 数据（dragonboard rb5 cyclictest/hackbench 改善）。

## 我可以参与的点

- `review`：两个现成的复核点——Tim Chen 修复 diff 里「push 成功迁移时以源 CPU 为 hint」与 wakeup 迁移语义的完全等价性；Kayra 指出的 `sched_tick()` 以 `rq->donor` 调用 fair tick 的 PE 边界在 06-14/18 各补丁中的逐点核对（她自己也说「Some more places could have the same case」）。
- `testing`：补 Chen Yu 预告的「不同 time slice 混合负载」hackbench，或在其评估补丁上跑 cache 密集负载（LLC 偏好任务聚集速度 vs cache-aware LB 单独工作）。
- `extend`：cache-aware×push 若验证成立，把它整理成正式 follow-up 系列是现成的空间（Chen Yu 已给评估补丁雏形 +82/−7）。
- 回合视角：系列未定稿，暂不回合；若只取 05/18（min slice 选 CPU）子集，注意其依赖 03/18 的 per-cpu min_slice 缓存。

## 参考链接

- Tim Chen 审 06/18: https://lore.kernel.org/all/95c9b871ab66588afdf09d6ec9bac577c139b8d8.camel@linux.intel.com/
- Chen Yu 审 07/18（含 cache-aware×push 评估补丁）: https://lore.kernel.org/all/asWyZtW7zPVo3k-A@chenyu-dev/
- Kayra 审 10/18: https://lore.kernel.org/all/20261006192414.7308-1-kayracizmeci@gmail.com/
- Kayra 审 18/18: https://lore.kernel.org/all/20261007143614.27368-1-kayracizmeci@gmail.com/
- 系列封面（v2）: https://lore.kernel.org/all/20261002154415.2270586-1-vincent.guittot@linaro.org/
- 相关文章：<a class="article-ref" href="/lkm/2026/09/21/sched-20260921-001-improving-latency-of-short-slice-tasks.html">sched-20260921-001</a>（v1）、<a class="article-ref" href="/lkm/2026/09/29/sched-20260929-018-sched-eevdf-add-min-slice-check-when-selecting-cpu.html">sched-20260929-018</a>、<a class="article-ref" href="/lkm/2026/10/01/sched-20261001-010-sched-eevdf-add-min-slice-check-when-selecting-cpu.html">sched-20261001-010</a>、<a class="article-ref" href="/lkm/2026/10/02/sched-20261002-001-sched-eevdf-add-min-slice-check-when-selecting-cpu.html">sched-20261002-001</a>（v2）、<a class="article-ref" href="/lkm/2026/10/05/sched-20261005-001-sched-eevdf-add-min-slice-check-when-selecting-cpu.html">sched-20261005-001</a>（Kayra 三连 review）
