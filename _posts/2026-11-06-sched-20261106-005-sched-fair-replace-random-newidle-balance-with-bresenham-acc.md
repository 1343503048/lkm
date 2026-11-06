---
id: sched-20261106-005
date: 2026-11-06
subject: 'sched/fair: Replace random newidle_balance with Bresenham accumulator'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261030091946.2498870-1-wangqing7171@gmail.com>
lore_url: https://lore.kernel.org/all/20261030091946.2498870-1-wangqing7171@gmail.com/
authors:
- Qing Wang
maintainers_involved: []
current_version: v4
patch_series:
- version: v4
  msgid: <20261030091946.2498870-1-wangqing7171@gmail.com>
  date: 2026-10-30
  summary: Bresenham 累加器替换 NI_RANDOM，newidle_window_pos 位置不清零。
  review_outcome: Peter 就初值收敛；Tim Chen 今日原则性反对（无偏采样丢失）。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - Tim Chen 原则性反对：固定步长与负载拍频、跨 CPU 同步
  - 收益温和（sembench +2%、tbench 中性），不足以覆盖丢无偏性代价
  next_action: 作者回应 Tim 的拍频/同步论点或提供更显著的 benchmark 数据
contribution_opportunities:
- kind: discussion
  description: 回应/验证 Tim Chen 的拍频与跨 CPU 同步论证
- kind: testing
  description: 复现周期负载验证 Bresenham 固定步长是否导致 domain 停止均衡
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261105-007
tags:
- cfs
- idle
- perf
title: 'sched/fair: Replace random newidle_balance with Bresenham accumulator'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-007-sched-fair-replace-random-newidle-balance-with-bresenham-acc.html">sched-20261105-007</a>：Qing Wang 的 v4 用 Bresenham 累加器替换 `newidle_balance` 的随机（NI_RANDOM）触发，把 idle 均衡变成确定性计数；前日 Qing 与 Peter 就 `newidle_window_pos` 初值收敛，Chengfeng Lin 给 sembench 数据（815 worker 吞吐 +2%）。
- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-005-sched-fair-replace-random-newidle-balance-with-bresenham-acc.html">sched-20261106-005</a>（今天）：Tim Chen（Intel）给出**原则性反对**——`newidle_ratio` 是从实际均衡尝试「学」来的，必须让尝试成为所有 newidle 调用的无偏样本；随机恰好保证无偏，而「每第 N 次调用均衡一次」的固定步长会与负载的周期模式对齐，导致「永远踩空」的境界（例如任务每 4 次出现一次、比例跌到 0 后 Bresenham 每 1024 次才试一次、又都落在空位，domain 从此不再均衡）。跨 CPU 的同步起始累加器还会让各 CPU 同时均衡或同时跳过。他明确建议：除非有清晰 benchmark 收益（Kayra 的 tbench 数据大致中性），否则保留 NI_RANDOM。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-007-sched-fair-replace-random-newidle-balance-with-bresenham-acc.html">sched-20261105-007</a>）`newidle_balance` 用随机方式决定是否在 CPU 进入 idle 时做负载均衡，避免各 CPU 同步均衡的抖动；随机带来的不确定性是作者想消除的点。v4 已通过「不清零位置」修掉历史丢调用问题，初值语义也在收敛。今天的焦点从「实现细节」转向「确定性到底是不是好事」这一更根本的问题。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-007-sched-fair-replace-random-newidle-balance-with-bresenham-acc.html">sched-20261105-007</a>）Bresenham 累加器方案本身未变：`newidle_window_pos` 按每个调度域权重累加，达到 1024 触发一次并扣减，位置不清零。今天的争议是 Tim Chen 指出的两个内在缺陷：① 固定步长会与负载周期「拍频」——当任务每 4 次 newidle 出现一次、真实成功率 1/4，若比例跌到 0，Bresenham 每 1024 次才尝试一次且都落在空位，该 domain 会永久停止均衡；而随机能在约 1/4 的尝试中命中好调用、把比例拉回正确水平。② 各 CPU 累加器同值同比例起步，同时 idle 的 CPU 会同时均衡/同时跳过，失去随机带来的独立性。

## 版本演进与当前进展

*current_version: v4（2026-10-30 发出）*。今日无新版，仅 Tim Chen 就 v4 方法论给出反对；作者尚未回复。此前 Qing 与 Peter 已就初值语义往返多轮。

## Maintainer 意见与讨论焦点

Tim Chen（Intel 资深调度 reviewer）的反对是原则性的：「随机骰子的方差是我们为无偏估计付出的代价，我认为值得付」。他同时指出 Kayra 的 tbench 数据大致中性、现有数据不足以证明确定性版本更好。这是继 Peter 对初值语义的保留之后，又一层针对方案本身的质疑。未出现 NAK，但方向认同度在下降。

## 合入评估

*likelihood=low*。v4 实现已较成熟，但确定性方案正遭遇对其理论基础（无偏采样）的直接质疑，且有数据「大致中性」而非显著收益。*blocking_issues*：① Tim Chen 的原则性反对（固定步长与负载拍频、跨 CPU 同步）；② 仅有约 +2% 的温和 sembench 收益，不足以覆盖「丢无偏性」的代价。*next_action*：作者回应 Tim 的拍频/同步论点，或提供能证明确定性收益超过其代价的 benchmark 数据。

## 效果评估

Chengfeng Lin 的原生 MMTests sembench 数据：815 worker 吞吐提升约 2%（前日文章），显著低于此前「直接禁用 NI_RANDOM」的诊断对比。Kayra 的 tbench 数据大致中性。以上为方向受到质疑的核心——收益温和、代价（无偏采样丢失）明确。

## 我可以参与的点

- **discussion**：作者尚未回应 Tim Chen 的「拍频」与「跨 CPU 同步」论证——是否有 load 能复现 Tim 描述的永久饿死场景、或能否证明 2% 收益值得放弃无偏性，是当前最能推动结论的点。
- **testing**：复现「任务每 N 次 newidle 出现一次」的周期负载，验证 Bresenham 固定步长是否会与负载拍频导致 domain 停止均衡。

## 参考链接

- lore thread（v4）: https://lore.kernel.org/all/20261030091946.2498870-1-wangqing7171@gmail.com/
- Tim Chen 今日回帖: https://lore.kernel.org/all/804c415ed6c1111674577cd24431706a742f5825.camel@linux.intel.com/
