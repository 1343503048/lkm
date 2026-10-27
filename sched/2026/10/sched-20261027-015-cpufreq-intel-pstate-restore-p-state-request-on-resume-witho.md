# cpufreq: intel_pstate: Restore P-state request on resume without HWP

## TL;DR
Zak Brighton Knight 报告并修一个 intel_pstate 被动模式的 resume 缺陷：无 HWP 的 Ivy Bridge（ThinkPad T520/i7-3840QM，coreboot）每次 suspend-to-RAM 后 turbo 永久丢失（停在 2.8GHz 基频直到改 policy limit 或重启），原因是 resume 时固件把 `MSR_IA32_PERF_CTL` 设回基频、内核因缓存/`policy->cur` 跳过重写。补丁在 resume 时恢复 P-state 请求。Rafael 当日转达 Sashiko 指出的并发 race，需再打磨。

## 背景与问题
无 HWP 时 intel_pstate 缓存最后一次写入的 P-state、跳过不变写入；被动模式下 cpufreq core 又因 `policy->cur` 认为频率已设而跳过请求（`intel_cpufreq` 只在 HWP 下设 `CPUFREQ_NEED_UPDATE_LIMITS`）。resume 时固件把每 CPU 的 P-state 请求寄存器设回基频 ratio（28），内核不再写回 turbo ratio（38），turbo 就此丢失。

## 技术方案
补丁在 resume 路径恢复 P-state 请求（访问 `MSR_IA32_PERF_CTL`）。具体实现细节未在摘要正文展开。

## 版本演进与当前进展
*current_version: v1*（`<20261027143725.3763827-1-zakbrightonknight@gmail.com>`），当日新发。

## Maintainer 意见与讨论焦点
Rafael J. Wysocki（PM/cpufreq 维护者）当日回应：转达 Sashiko 的意见——该补丁引入与 `cpu->cpu` 上并发 P-state 更新的 race（`sashiko.dev` 链接），「要避免这个 race 还需要更多工作」。

## 合入评估
*likelihood=medium*。问题真实、方向对，但存在并发 race 需解决。*blocking_issues*：并发 P-state 更新 race。*next_action*：作者按 Sashiko/Rafael 意见规避 race 后发 v2。

## 效果评估
作者描述症状（无 HWP 机型 resume 后 turbo 丢失），未附定量数据。

## 我可以参与的点
- *kind: review*：评估 resume 期间 P-state 恢复与并发频率更新的加锁方案。
- *kind: testing*：在无 HWP 且带 coreboot 的机型上复现 resume 后 turbo 丢失。

## 参考链接
- patch: https://lore.kernel.org/all/20261027143725.3763827-1-zakbrightonknight@gmail.com/

---
id: sched-20261027-015
date: 2026-10-27
subject: 'cpufreq: intel_pstate: Restore P-state request on resume without HWP'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: '<20261027143725.3763827-1-zakbrightonknight@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20261027143725.3763827-1-zakbrightonknight@gmail.com/'
authors:
  - 'Zak Brighton Knight'
maintainers_involved:
  - 'Rafael J. Wysocki'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261027143725.3763827-1-zakbrightonknight@gmail.com>'
    date: 2026-10-27
    summary: 'resume 时恢复 P-state 请求，避免无 HWP 机型 turbo 丢失'
    review_outcome: 'Rafael 转达 Sashiko 的并发 race 意见'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '并发 P-state 更新 race'
  next_action: '作者规避 race 后发 v2'
contribution_opportunities:
  - kind: review
    description: '评估 resume 期间 P-state 恢复的加锁方案'
  - kind: testing
    description: '无 HWP + coreboot 机型复现 resume 后 turbo 丢失'
generated_at: '2026-10-28T09:00:00'
source_email_count: 2
related_articles: []
tags:
  - cpufreq
---