# sched/cputime: Preserve iowait accounting across waking interrupts in dyntick-idle

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261014-003：Wei Gao 修复 liburing `test/iowait.t` 在 tickless + 无 IRQ time accounting 下间歇失败——任务在中断处理函数里被唤醒时 `rq->nr_iowait` 在 CPU 退出 idle 前已减到 0，整段 iowait 被记成 CPUTIME_IDLE；作者在 `kcpustat_irq_enter()` 检查 `nr_iowait_cpu()` 提前结算。Peter 当日否决——「用 `nr_iowait_cpu()` 是掷骰子」，合入可能性低。
- sched-20261015-015（今天）：Peter 澄清他理解作者为何走这条路（`get_cpu_iowait_time_us()` 用 `nr_iowait_cpu()`，thermal/cpufreq 都在用）；Christian 指出 thermal 用 `io_is_busy=0`、ondemand 也默认 0（仅 Intel Pentium Pro 例外），并非不可绕；Wei Gao 承认「per-CPU iowait 记账在 SMP 上根本有缺陷，不该再为当前记账造补丁」，改评估/跳过测试。

## 背景与问题
（承接 20261014-003）根因是 commit `7198e3927a14` 优化后，IRQ time accounting 关闭时不再于 IRQ 进入处暂停 idle 记账，但未覆盖「任务在 IRQ 处理函数内被唤醒」的窗口；导致 `test/iowait.t` 把整 1 秒 iowait 记成 CPUTIME_IDLE，断言失败。

## 技术方案
（承接 20261014-003）作者原方案在 `kcpustat_irq_enter()` 追加 `|| nr_iowait_cpu(smp_processor_id()) > 0`，提前暂停并结算 iowait。该方案已被 Peter 否决。今日讨论转向「per-CPU iowait 记账本身是否值得继续修」：Peter 点明 `get_cpu_iowait_time_us()` 走 `nr_iowait_cpu()` 且被 thermal 与 cpufreq 使用；Christian 分析 thermal 用 `io_is_busy=0`、ondemand 的 `io_is_busy` 默认 0（仅 Intel Pentium Pro 特殊），「如果只有这些用户，总有办法绕开」。Wei Gao 收敛为：per-CPU iowait 记账在 SMP 上根本有缺陷，不再为其造补丁，测试改为重估或跳过。

## 版本演进与当前进展
- v1（2026-10-14，<20261014015258.13967-1-wegao@suse.com>）：`kcpustat_irq_enter()` 追加 nr_iowait_cpu 检查。
- 今天（2026-10-15）：讨论转向是否放弃该修法；作者倾向放弃、改评估测试本身。

## Maintainer 意见与讨论焦点
Peter Zijlstra 维持否决：`nr_iowait_cpu()` 是聚合计数、可被任意任务污染，用它判「本 CPU 是否 iowait」不可靠。同时他承认 per-CPU iowait 因为 `/proc` 的暴露「可能永远无法完全去掉」，但「减少内核消费者可行」。分歧已从「怎么修」转向「还要不要修这个测试」。

## 合入评估
*likelihood=low*。作者方案被维护者否决，且作者本人今日认同「per-CPU iowait 记账根本有缺陷、不该再造补丁」，原修复路径大概率放弃。*blocking_issues*：方案被否；作者倾向放弃并重估测试。*next_action*：如仍有兴趣，需另寻更精确的记账路径（或接受测试失败/跳过，等待更大的 iowait 记账重构）。

## 效果评估
无新的量化数据。原问题的表现是 `test/iowait.t` 断言 `diff < 50` 失败；今日无新测试结果。

## 我可以参与的点
- *discussion*：参与「per-CPU iowait 记账在 SMP 上是否应被更精确的机制取代」的讨论（Peter 提出可减少内核消费者，是更上层的重构机会）。

## 参考链接
- Peter 的澄清：https://lore.kernel.org/all/20261015073508.GH4121339@noisy.programming.kicks-ass.net/
- Christian 的 consumer 分析：https://lore.kernel.org/all/a6cc5f59-da1a-4e8a-b91f-f32743b02383@arm.com/
- Wei Gao 的收敛：https://lore.kernel.org/all/atA6UsI1CldllKSP@autotest-wegao.qe.prg2.suse.org/

---
id: sched-20261015-015
date: 2026-10-15
subject: "sched/cputime: Preserve iowait accounting across waking interrupts in dyntick-idle"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261014015258.13967-1-wegao@suse.com>"
lore_url: "https://lore.kernel.org/all/20261014015258.13967-1-wegao@suse.com/"
authors: ["Wei Gao"]
maintainers_involved: ["Peter Zijlstra"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261014015258.13967-1-wegao@suse.com>"
    date: 2026-10-14
    summary: "kcpustat_irq_enter() 追加 nr_iowait_cpu 检查提前结算 iowait"
    review_outcome: "Peter 否决（nr_iowait_cpu 不可靠）；作者倾向放弃"
upstream_commit: null
fixes_commit: "7198e3927a14"
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues: ["方案被维护者否决；作者认同 per-CPU iowait 记账有缺陷、倾向放弃"]
  next_action: "另寻更精确记账路径，或接受测试失败/跳过并等待更大的 iowait 记账重构"
contribution_opportunities:
  - kind: discussion
    description: "参与 per-CPU iowait 记账在 SMP 上是否应被更精确机制取代的讨论"
generated_at: "2026-10-16T01:05:00"
source_email_count: 4
related_articles: ["sched-20261014-003"]
tags: [cfs, cpufreq, psi]
---