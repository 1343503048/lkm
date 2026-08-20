---
id: sched-20260816-004
date: 2026-08-16
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <uid-41637@qq-imap>
lore_url: 未获取到
authors:
- Hui Su
- Rafael J. Wysocki
maintainers_involved:
- Rafael J. Wysocki
- Viresh Kumar
current_version: v3
patch_series:
- version: v3
  msgid: <uid-41637@qq-imap>
  date: 2026-08-16
  summary: 新增 sugov_update_rate_limit_us() 在乘 NSEC_PER_USEC 前把 rate_limit_us 转 s64，修复
    32 位平台乘溢出导致 schedutil 频率更新过频。
  review_outcome: 'Rafael 已 apply 为 7.3 material（Reviewed-by: Zhongqiu Han）。'
upstream_commit: null
fixes_commit: '9bdcb44e391d (cpufreq: schedutil: New governor based on scheduler utilization
  data)'
merged_branch: cpufreq/7.3 (pm tree)
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已 apply 为 7.3 material；关注 stable 回传。
contribution_opportunities:
- kind: testing
  description: 在 32 位平台写大值到 rate_limit_us，验证 freq_update_delay_ns 不再溢出为极小值。
generated_at: '2026-08-17T00:10:00'
source_email_count: 1
related_articles:
- sched-20260807-006
tags:
- cpufreq
- schedutil
title: 'cpufreq: schedutil: Fix rate limit overflow'
layout: article
---

## TL;DR
Hui Su 的 v3（延续 08-07 系列 006）修复 `schedutil` 在 32 位平台的频率限制溢出：`rate_limit_us`（unsigned int）乘 `NSEC_PER_USEC`(1000L) 在 32 位下以 32 位无符号算术进行，写大值（如 4294968）会让 `freq_update_delay_ns` 从 4294968000ns 溢出为 704ns，使 schedutil 远超预期频率更新。Rafael 已 apply 为 7.3 material（Reviewed-by: Zhongqiu Han）。

## 背景与问题
`rate_limit_us` 是 `unsigned int`，`NSEC_PER_USEC` 定义为 `1000L`（long）。在 32 位系统，`rate_limit_us * NSEC_PER_USEC` 先用 32 位无符号算术相乘，再把结果赋给 `freq_update_delay_ns`(s64)。例如写 `4294968` 到 `rate_limit_us`：4294968 * 1000 = 4294968000，超过 32 位无符号上限（~4294967295），溢出 wraparound 为 704ns，导致 schedutil 以远超预期的频率更新（每 ~704ns 一次，而非配置的 ~4.29s）。

## 技术方案
新增 `sugov_update_rate_limit_us()`，在相乘前把 `rate_limit_us` 显式 cast 为 `s64` 再乘 `NSEC_PER_USEC`，强制 64 位算术。两个调用点（sysfs `rate_limit_us_store` 与 `sugov_start` governor 启动）均改用该 helper。`kernel/sched/cpufreq_schedutil.c +13/-2`。v3 相对 v2 仅新增注释说明为何必须先 cast。

## 版本演进与当前进展
- v1（20260805）：首版。
- v2（20260806）：澄清 32 位无符号算术原因；把 `rate_limit_us` cast 为 s64；加 Zhongqiu Han `Reviewed-by`。
- v3（本日 41637 引用的版本）：新增 cast 原因注释。Rafael 于 2026-08-16 回复 "Applied as 7.3 material, thanks!"。
`Fixes: 9bdcb44e391d`，`Cc: stable@vger.kernel.org`。

## Maintainer 意见与讨论焦点
- Rafael J. Wysocki：apply 为 7.3 material（pm tree）。
- Zhongqiu Han：v2 给出 `Reviewed-by`。

## 合入评估
已 apply 为 7.3 material。带 `Fixes` + stable，预期随 7.3 进入主线并回合 stable。

## 效果评估
修复 32 位平台 schedutil 频率更新严重过频（功耗/抖动异常）。无基准数据，属正确性修复。

## 我可以参与的点
- 在 32 位平台写大值到 `rate_limit_us`，验证 `freq_update_delay_ns` 不再溢出为极小值。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
