---
id: sched-20260921-010
date: '2026-09-21'
subject: 'cpufreq: Use a non-boost reference frequency for pressure calculation'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260915065747.1671965-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/20260915065747.1671965-1-wujianyong@hygon.cn/
authors:
- Jianyong Wu
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260915065747.1671965-1-wujianyong@hygon.cn>
  date: '2026-09-15'
  summary: 用非 boost 参考频率做 pressure 计算，恢复 cache aware 调度聚合
  review_outcome: 作者以 Hygon + AMD 双平台实测回应维护者追问并给 Tested-by
upstream_commit: null
fixes_commit: d2d5c129d07e
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待 cpufreq/schedutil 维护者最终 pickup
contribution_opportunities:
- kind: testing
  description: 在 intel_pstate/amd-pstate 等其它 governor 与平台上复测 pressure 归零与 cache aware
    聚合恢复
- kind: review
  description: 核查非 boost 参考频率选取在不同 boost 配置下的边界正确性
generated_at: '2026-09-22T01:10:00'
source_email_count: 1
related_articles:
- sched-20260919-006
tags:
- cpufreq
- load_balance
title: 'cpufreq: Use a non-boost reference frequency for pressure calculation'
layout: article
---

## TL;DR
增量更新：Jianyong Wu 的"cpufreq 用非 boost 参考频率计算 pressure"修复（v1）昨日获作者本人补强的 Tested-by——在 Hygon 与 AMD（acpi-cpufreq）平台上实测 CPU pressure 重新归零，cache aware 调度恢复把任务聚合到 50% LLC 容量（与 d2d5c129d07e 引入回归前一致）。实测背书到位，合入概率较高。

## 背景与问题
背景见 <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-010-cpufreq-use-a-non-boost-reference-frequency-for-pressure-cal.html">sched-20260918-010</a> / <a class="article-ref" href="/lkm/2026/09/19/sched-20260919-006-cpufreq-use-a-non-boost-reference-frequency-for-pressure-cal.html">sched-20260919-006</a>：cpufreq 的 pressure 计算把 boost 频率当作参考频率，导致 CPU pressure 计算失真，进而破坏依赖该信号的 cache aware 调度聚合。回归由 commit d2d5c129d07e 引入。

## 技术方案
本日无新代码。修复为改用非 boost 参考频率来做 pressure 计算（详见 <a class="article-ref" href="/lkm/2026/09/19/sched-20260919-006-cpufreq-use-a-non-boost-reference-frequency-for-pressure-cal.html">sched-20260919-006</a>）。昨日回复是对此前维护者（Rafael J. Wysocki）追问的确认，并补充了双平台实测数据。

## 版本演进与当前进展
- v1（09-15，thread root `<20260915065747.1671965-1-wujianyong@hygon.cn>`）。
- 09-21：作者 RE: 回复维护者，确认"（方案）确实有帮助"，并给出 Hygon + AMD 双平台 Tested-by。

## Maintainer 意见与讨论焦点
- 此前维护者（Rafael J. Wysocki）追问过方案的有效性（原邮件不在本日缓存），作者昨日以实测数据正面回应。当前无 NAK 或未解决分歧。

## 合入评估
*likelihood=medium*。修复方向明确、有双平台实测验证、能恢复既有（d2d5c129d07e 之前）的 cache aware 调度聚合行为；仍处 v1 讨论期，未见维护者最终 pickup。

## 效果评估
作者实测（Hygon 与 AMD 平台，acpi-cpufreq）：CPU pressure 重新归零，cache aware 调度恢复把任务聚合到最高 50% 的 LLC 容量，与回归前（d2d5c129d07e 之前）一致。

## 我可以参与的点
- **testing**：在 intel_pstate / amd-pstate 等其它 governor 与平台上复测 pressure 归零与 cache aware 调度聚合恢复情况。
- **review**：核查"非 boost 参考频率"的选取在不同 boost 配置下的边界正确性。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260915065747.1671965-1-wujianyong@hygon.cn/
