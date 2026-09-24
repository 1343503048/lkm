# cpufreq: intel_pstate: Fix max_freq fallback in cpufreq_update_pressure()

## TL;DR
- sched-20260922-009：Rafael Wysocki 修复 `d2d5c129d07e` 引入的回归——`cpufreq_update_pressure()` 在 `arch_scale_freq_ref()` 返回 0 时无条件回落到 `policy->cpuinfo.max_freq`，导致负载均衡器意外出现 cpufreq 压力信号；补丁新增 `.scale_freq_ref()` 回调让 intel_pstate 仅在容量参考频率已知时才回落。
- sched-20260924-014（今天，增量更新）：Chen Yu 在 4LLCs/节点 Xeon 上跑 cache-aware-scheduling sanity test 未观察到问题，给出 `Tested-by`；Rafael 简短回复「Thanks!」。补丁继续积累正向确认，待收取。

## 背景与问题
- sched-20260922-009：`d2d5c129d07e`（"cpufreq: Make cpufreq_update_pressure() fall back to cpuinfo.max_freq"）后，某些此前不出现 cpufreq pressure 的场合压力信号意外出现在 CPU 负载均衡器中；调度器本假设「只有 CPU 容量参考频率已知时才设置 cpufreq pressure」，该 commit 违反了这个假设。`Fixes: d2d5c129d07e`，`Reported-by/Tested-by: Jianyong Wu <wujianyong@hygon.cn>`。
- 本日无新增背景。

## 技术方案
- 沿用 sched-20260922-009 的方案（新增 `.scale_freq_ref()` driver 回调，`cpufreq_update_pressure()` 在 `arch_scale_freq_ref()==0` 时改调该回调）。本日无代码变化。

## 版本演进与当前进展
- v1（09-22）当日发出。本日（09-24）新增 Chen Yu 的 `Tested-by`（4LLCs/节点 Xeon 上的 cache-aware sanity test 无异常）与 Rafael 的「Thanks!」。

## Maintainer 意见与讨论焦点
- **Chen Yu（Intel）**：`Tested-by`——「在 4LLCs/节点 Xeon 服务器上跑 cache-aware-scheduling sanity test 未观察到任何问题」。
- **Rafael J. Wysocki（Intel，作者兼 cpufreq 维护者）**：简短「Thanks!」。
- 无争议、无 NAK。

## 合入评估
*likelihood=high*。作者即 cpufreq 子系统维护者、带 Fixes 与多个 Tested-by（Jianyong、Chen Yu），改动小而聚焦；尚未见正式合入通知（如 tip/power 分支收取），故取 high 而非 merged。*blocking_issues*：无明确项。*next_action*：合入 cpufreq 维护者分支并回合。

## 效果评估
无量化 benchmark；本质是正确性修复——避免 cpufreq pressure 信号在容量参考频率未知时误报进负载均衡。Chen Yu 的 sanity test 佐证了无回归。

## 我可以参与的点
- kind=testing：在 intel_pstate 平台（scale-invariant capacity 已/未设置两种路径）验证 pressure 信号行为与负载均衡无异常。
- kind=review：核查 `.scale_freq_ref()` 回调语义与其它 cpufreq driver 的 pressure 假设一致。

## 参考链接
- lore thread: https://lore.kernel.org/all/12975163.O9o76ZdvQC@rafael.j.wysocki/
- Chen Yu Tested-by: https://lore.kernel.org/all/arP8Fv9z0ozmVP1t@chenyu-dev/

---
id: sched-20260924-014
date: '2026-09-24'
subject: 'cpufreq: intel_pstate: Fix max_freq fallback in cpufreq_update_pressure()'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<12975163.O9o76ZdvQC@rafael.j.wysocki>'
lore_url: 'https://lore.kernel.org/all/12975163.O9o76ZdvQC@rafael.j.wysocki/'
authors:
  - 'Rafael J. Wysocki'
maintainers_involved:
  - 'Rafael J. Wysocki'
current_version: v1
patch_series:
  - version: v1
    msgid: '<12975163.O9o76ZdvQC@rafael.j.wysocki>'
    date: '2026-09-22'
    summary: '新增 .scale_freq_ref() 回调，修正 pressure 的 max_freq 回落条件'
    review_outcome: 'Chen Yu Tested-by（Xeon sanity 无异常），Rafael Thanks'
upstream_commit: null
fixes_commit: 'd2d5c129d07e'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '合入 cpufreq 维护者分支并回合'
contribution_opportunities:
  - kind: testing
    description: 'intel_pstate 两路径验证 pressure 信号与负载均衡'
  - kind: review
    description: '核查 .scale_freq_ref() 语义与其它 cpufreq driver 一致性'
generated_at: '2026-09-25T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260922-009
tags:
  - cpufreq
  - load_balance
---