---
id: sched-20261029-015
date: 2026-10-29
subject: 'cpufreq: intel_pstate: Restore P-state request on resume without HWP'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261027143725.3763827-1-zakbrightonknight@gmail.com>
lore_url: https://lore.kernel.org/all/20261027143725.3763827-1-zakbrightonknight@gmail.com/
authors:
- Zak Brighton Knight
maintainers_involved:
- Rafael Wysocki
current_version: v2
patch_series:
- version: v1
  msgid: <20261027143725.3763827-1-zakbrightonknight@gmail.com>
  date: 2026-10-27
  summary: resume 路径恢复 P-state 请求（访问 MSR_IA32_PERF_CTL）
  review_outcome: Rafael 转达 Sashiko 的并发 race，需打磨
- version: v2
  msgid: null
  date: 2026-10-29
  summary: Zak 的 V2 补丁（并发 race 处理）
  review_outcome: Doug Smythies Tested-by（Zak V2 与 Rafael 补丁均实测通过）
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Sashiko 点名的并发 race 需在 review 中确认已处理
  - Zak V2 与 Rafael 补丁形态最终择一合入
  next_action: 完成并发 race 处理与代码 review，择一形态合入
contribution_opportunities:
- kind: testing
  description: 在其它无 HWP 的 intel_pstate 平台复现 suspend 后 turbo 丢失并验证补丁
- kind: review
  description: 结合 Sashiko race 核对 resume 写 MSR_IA32_PERF_CTL 与其它路径的并发
generated_at: '2026-10-30T09:30:00'
source_email_count: 1
related_articles:
- sched-20261027-015
tags:
- cpufreq
title: 'cpufreq: intel_pstate: Restore P-state request on resume without HWP'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/27/sched-20261027-015-cpufreq-intel-pstate-restore-p-state-request-on-resume-witho.html">sched-20261027-015</a>：Zak Brighton Knight 报告并修 intel_pstate 被动模式的 resume 缺陷——无 HWP 的 Ivy Bridge（ThinkPad T520/i7-3840QM，coreboot）每次 suspend-to-RAM 后 turbo 永久丢失（停在 2.8GHz 基频直到改 policy limit 或重启），根因是 resume 时固件把 `MSR_IA32_PERF_CTL` 设回基频、内核因缓存/`policy->cur` 跳过重写；Rafael 当日转达 Sashiko 指出的并发 race，需再打磨。
- <a class="article-ref" href="/lkm/2026/10/29/sched-20261029-015-cpufreq-intel-pstate-restore-p-state-request-on-resume-witho.html">sched-20261029-015</a>（今天）：Doug Smythies 给出 **Tested-by**——他实测了 Zak 的 V2 补丁与 Rafael 的补丁，「两者都工作正常」，并明确「尚未 review 代码，未来几天也没时间」。这是该修复向合入迈出的实质一步（有实测背书），但代码 review（尤其 Rafael 之前点名的并发 race）仍未完成。

## 背景与问题
（承接 20261027-015）无 HWP 时 intel_pstate 缓存最后一次写入的 P-state、跳过不变写入；被动模式下 cpufreq core 又因 `policy->cur` 认为频率已设而跳过请求。resume 时固件把每 CPU 的 P-state 请求寄存器设回基频 ratio（28），内核不再写回 turbo ratio（38），turbo 就此丢失。今日无新背景，是实测背书的补充。

## 技术方案
（承接 v1）补丁在 resume 路径恢复 P-state 请求（访问 `MSR_IA32_PERF_CTL`）。今日无新代码；Zak 的 V2 与 Rafael 的补丁两个形态均被 Doug Smythies 实测通过。此前 Rafael 转达的 Sashiko 并发 race 是仍需在 review 中解决的技术点。

## 版本演进与当前进展
*current_version: v2*（Zak 的 V2 补丁；Rafael 亦提供了一版补丁）。今日进展是**实测验证**：Doug Smythies 在真实无 HWP 平台（Ivy Bridge）上分别测试 Zak V2 与 Rafael 补丁，均「worked fine」，给出 `Tested-by: Doug Smythies`。代码 review 与并发 race 处理仍未完成。

## Maintainer 意见与讨论焦点
- **Rafael Wysocki（维护者）**：提供了自己的一版补丁，此前还转达了 Sashiko 指出的并发 race（resume 与其它路径并发写 P-state 的竞态）——该 race 是补丁还需打磨的点。
- **Doug Smythies（今天，测试者）**：`Tested-by`，声明只做了功能验证、未 review 代码。
- 未解决焦点：Sashiko 的并发 race 是否已被 Zak V2 / Rafael 补丁妥善处理，仍需代码 review 定论。

## 合入评估
*likelihood=high*。方向明确、有 Doug Smythies 在真实平台上的 Tested-by 背书、Rafael 亲自参与（给出了自己的补丁形态），收敛路径清晰。*blocking_issues*：Sashiko 点名的并发 race 需在 review 中确认已处理；两个补丁形态（Zak V2 vs Rafael）最终以哪个合入待定。*next_action*：完成对并发 race 的处理与代码 review，择一形态合入。

## 效果评估
Doug Smythies 的验证是功能性（「worked fine」，turbo 恢复）而非量化 benchmark；无性能数字。作者原报告的问题症状（suspend 后停在 2.8GHz 基频、turbo 丢失）即核心证据。

## 我可以参与的点
- **testing**：在其它无 HWP 的 intel_pstate 平台（coreboot/旧 BIOS 的 Ivy Bridge/Sandy Bridge 等）上复现 suspend 后 turbo 丢失，验证补丁后恢复。
- **review**：结合 Rafael 转达的 Sashiko race，核对 resume 写 `MSR_IA32_PERF_CTL` 与其它路径的并发，确认竞态是否已处理。

## 参考链接
- lore thread（v1 补丁）: https://lore.kernel.org/all/20261027143725.3763827-1-zakbrightonknight@gmail.com/
- Doug Smythies 的 Tested-by: https://lore.kernel.org/all/006601dd672b$a7d67f90$f7837eb0$@telus.net/
