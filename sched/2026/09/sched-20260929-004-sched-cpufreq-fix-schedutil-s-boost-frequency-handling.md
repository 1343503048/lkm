# sched/cpufreq: fix schedutil's boost frequency handling

> **subject**：`sched/cpufreq: fix schedutil's boost frequency handling`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260921-007：Ananthu C V 的 schedutil boost 频率处理修复（v2）回应 Oleg 关于 `cpuinfo->max_freq` 只升不降设计的疑问，并接受 Zhongqiu 建议给补丁补 `Fixes:` 标签。
- sched-20260922-019：Zhongqiu Han 在 SM8850（SCMI 驱动）上复测，二分定位问题由 `db80ad776cd2`（"cpufreq: Remove driver default policy->min/max init"）引入。
- sched-20260929-004（今天）：作者发 v3——按 v2 反馈重构：放弃 `max_table_freq` 字段、新增从频率表取最大频率的 helper，把 `policy_set_boost` 的判断条件从「是否有时钟表」改为「是否有 boost 频率」，并把第 2 片补丁的 `Fixes:` 标签改为 `db80ad776cd2`。Oleg 对 v2 的 `Tested-by` 因实现变更未被采纳。

## 背景与问题

（承接 sched-20260918-005 / sched-20260921-007）schedutil 在关闭 boost 后频率无法回落到非 boost 值，根因是 commit 538b0188da46 给 `cpuinfo->max_freq` 加了「只向上更新」的 guard，其后 db80ad776cd2 又删掉了驱动默认 `policy->max = max_freq` 的赋值，使该单向 guard 成为 cpuinfo max（进而 policy max）更新的唯一路径，boost 关闭后两者都被钉在 boost 频率。

本系列的两个缺口：per-CPU capacity 频率参考值在 policy 创建时设定一次、boost 之后启用不再更新，导致 schedutil 即使满利用率也到不了 boost 频率；以及上面这个「关闭 boost 后回不去」的问题。

## 技术方案

（承接 sched-20260921-007）v3 仍是两补丁：

1. **1/2**（本日未进入缓存，据 cover 描述）：per-CPU capacity 频率参考在 policy 创建后不再随 boost 更新——新增一个从频率表取最高值的 helper，用它和 `cpuinfo.max_freq` 的较大者来 seed capacity freq ref，让 schedutil 从 policy 创建起就知道最高可用频率。
2. **2/2**（本日进入缓存）：无条件跟踪频率表里最高的非 boost 频率（`max_base_freq`）；若存在 boost 频率，则用「频率表最高值 / max_base_freq」而非 `cpuinfo->max_freq` 来控制 boost 值，使关闭 boost 时频率能降回非 boost 值；无 boost 频率时回退到 `cpuinfo->max_freq` 保持原行为。`Fixes: db80ad776cd2`。

## 版本演进与当前进展

- v2（09-08，`<20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>`）：两补丁，运行时尽量不依赖 `cpuinfo_max_freq` + 修复关闭 boost 后无法回落。
- v3（09-29，`<20260929-schedutil-boost-frequency-handling-v3-0-68de169498c7@oss.qualcomm.com>`），changelog 三点：drop `max_table_freq` 字段、改为新增从频率表取最大频率的 helper；`policy_set_boost` 的判断条件从「是否有时钟表」改为「是否有 boost 频率」；第 2 片补丁的 `Fixes:` 标签改为 `db80ad776cd2`。Oleg Keri 对 v2 的 `Tested-by` 因 v3 实现变更未采纳。

## Maintainer 意见与讨论焦点

- **Oleg Keri**（测试者，v2）：在 Lenovo Yoga Slim 7x Gen 11 上测试 v2 并给出 `Tested-by`，但因 v3 实现变更未被沿用。
- 当日无维护者新表态；cover 的 To 列表包含 Vincent Guittot、Rafael Wysocki、Viresh Kumar 等，但缓存中无他们的当日回复。无 NAK。

## 合入评估

*likelihood=medium*。修复逻辑清晰、`Fixes:` 已按 Zhongqiu 的定位精确到 `db80ad776cd2`、作者积极响应 review 并落地 v3，但仍是迭代期（v3 刚发、`Tested-by` 需在 v3 上重新验证），尚未见维护者最终收取。*blocking_issues*：v3 无新 `Tested-by`；维护者未收取。*next_action*：等维护者 review v3，或测试者基于 v3 重新给出 `Tested-by`。

## 效果评估

无新增 benchmark；cover 附有 v3 前后的 sysfs 对照（`boost` 关闭后 `scaling_max_freq` 从钉在 4723200 变为正确回落到 4454400，`time_in_state` 显示 boost 关闭后高段计数归零）。

## 我可以参与的点

- `testing`：在带 boost 能力的 cpufreq 驱动（amd-pstate/intel_pstate/SCMI）上基于 v3 验证「关闭 boost 后频率回落」及无回归，回帖补 `Tested-by`。
- `review`：核对 v3 新 helper 与 `policy_set_boost` 新判断条件在「频率表只含 boost 频率」等边界下的行为。

## 参考链接

- lore（v3 cover）: https://lore.kernel.org/all/20260929-schedutil-boost-frequency-handling-v3-0-68de169498c7@oss.qualcomm.com/
- lore（v3 2/2）: https://lore.kernel.org/all/20260929-schedutil-boost-frequency-handling-v3-2-68de169498c7@oss.qualcomm.com/

---
id: sched-20260929-004
date: '2026-09-29'
subject: "sched/cpufreq: fix schedutil's boost frequency handling"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260929-schedutil-boost-frequency-handling-v3-0-68de169498c7@oss.qualcomm.com>'
lore_url: 'https://lore.kernel.org/all/20260929-schedutil-boost-frequency-handling-v3-0-68de169498c7@oss.qualcomm.com/'
authors:
  - 'Ananthu C V'
maintainers_involved: []
current_version: v3
patch_series:
  - version: v2
    msgid: '<20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>'
    date: '2026-09-08'
    summary: '两补丁：运行时尽量不依赖 cpuinfo_max_freq + 修复关闭 boost 后无法回落'
    review_outcome: 'Oleg Tested-by；Zhongqiu 定位 db80ad776cd2 引入回归'
  - version: v3
    msgid: '<20260929-schedutil-boost-frequency-handling-v3-0-68de169498c7@oss.qualcomm.com>'
    date: '2026-09-29'
    summary: 'drop max_table_freq 字段改新增取频率表最大频率 helper；policy_set_boost 判断改为是否有 boost 频率；2/2 的 Fixes 改为 db80ad776cd2'
    review_outcome: '无新回帖；v2 的 Tested-by 因实现变更未沿用'
upstream_commit: null
fixes_commit: 'db80ad776cd2'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'v3 无新 Tested-by'
    - '维护者尚未收取'
  next_action: '等维护者 review v3，或测试者基于 v3 重新给出 Tested-by'
contribution_opportunities:
  - kind: testing
    description: '在带 boost 的 cpufreq 驱动上基于 v3 验证关闭 boost 后频率回落并回帖 Tested-by'
  - kind: review
    description: '核对 v3 新 helper 与 policy_set_boost 新条件在「频率表只含 boost 频率」等边界下的行为'
generated_at: '2026-09-30T01:15:00'
source_email_count: 2
related_articles:
  - sched-20260922-019
  - sched-20260921-007
tags:
  - cpufreq
---