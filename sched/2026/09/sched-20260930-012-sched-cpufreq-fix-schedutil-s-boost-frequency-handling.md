# sched/cpufreq: fix schedutil's boost frequency handling

> **subject**：`sched/cpufreq: fix schedutil's boost frequency handling`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260921-007：Ananthu C V 的 schedutil boost 频率处理修复（v2）回应 Oleg 关于 `cpuinfo->max_freq` 只升不降设计的疑问，接受 Zhongqiu 建议补 `Fixes:`。
- sched-20260922-019：Zhongqiu Han 在 SM8850（SCMI 驱动）上复测，二分定位问题由 `db80ad776cd2` 引入。
- sched-20260929-004：作者发 v3——drop `max_table_freq` 字段、新增从频率表取最大频率的 helper、`policy_set_boost` 判断改「是否有 boost 频率」、2/2 的 `Fixes:` 改为 `db80ad776cd2`；Oleg 对 v2 的 `Tested-by` 因实现变更未被采纳。
- sched-20260930-012（今天）：Oleg Keri 基于 **v3** 在 Lenovo Yoga Slim 7x Gen 11 上复测，给出 `Tested-by`（boost 关闭回 4032000、开启 4723200、再关回 4032000）——此前 v3 缺 `Tested-by` 的阻塞点解除。

## 背景与问题

（承接 sched-20260918-005 / sched-20260921-007）schedutil 在关闭 boost 后频率无法回落到非 boost 值：commit 538b0188da46 给 `cpuinfo->max_freq` 加了「只向上更新」guard，其后 db80ad776cd2 又删掉驱动默认 `policy->max = max_freq` 赋值，使该单向 guard 成为 cpuinfo max（进而 policy max）更新的唯一路径，boost 关闭后两者被钉在 boost 频率。v3 两个缺口：per-CPU capacity 频率参考在 policy 创建时设定一次、boost 之后不再更新；以及「关闭 boost 后回不去」。

## 技术方案

（承接 sched-20260929-004）v3 仍两补丁：1/2 用「频率表最高值」与 `cpuinfo.max_freq` 较大者 seed capacity freq ref，让 schedutil 从 policy 创建起就知道最高可用频率；2/2 无条件跟踪频率表最高非 boost 频率（`max_base_freq`），有 boost 频率时用「频率表最高 / max_base_freq」控制 boost 值、关闭 boost 时回落，无 boost 频率时回退 `cpuinfo->max_freq`。`Fixes: db80ad776cd2`。今日无新代码，增量是 Oleg 基于 v3 的 `Tested-by`。

## 版本演进与当前进展

- v2（09-08）：运行时尽量不依赖 `cpuinfo_max_freq` + 修复关闭 boost 后无法回落；Oleg `Tested-by`。
- v3（09-29）：drop `max_table_freq`、新增取频率表最大频率 helper、`policy_set_boost` 判断改「是否有 boost 频率」、`Fixes:` 改 `db80ad776cd2`；Oleg 的 `Tested-by` 因实现变更未沿用。
- 09-30：Oleg 基于 v3 复测并给新 `Tested-by # Lenovo Yoga Slim 7x Gen 11`。

## Maintainer 意见与讨论焦点

- **Oleg Keri**（测试者，今日）：基于 v3 在 Lenovo Yoga Slim 7x Gen 11 上验证——boost off 4032000、boost on 4723200、再关回 4032000，给出 `Tested-by`。
- cover 的 To 列表含 Vincent Guittot、Rafael Wysocki、Viresh Kumar 等，但缓存中当日无他们的回复。无 NAK。

## 合入评估

*likelihood=high*。修复逻辑清晰、`Fixes:` 精确到 `db80ad776cd2`、作者积极响应 review 并落地 v3，今日又补齐了 v3 上的 `Tested-by`（此前唯一阻塞点「v3 无新 Tested-by」解除）。*blocking_issues*：仍缺维护者（cpufreq 侧）最终收取。*next_action*：等 Rafael/Viresh 等 cpufreq 维护者 review 并收取 v3。

## 效果评估

无新增 benchmark；Oleg 的 sysfs 实测（boost 关闭回 4032000、开启 4723200、再关回 4032000）确认「关闭 boost 后频率回落」的行为正确。

## 我可以参与的点

- `testing`：在另一带 boost 能力的 cpufreq 驱动（amd-pstate/intel_pstate）上基于 v3 验证回落行为，回帖补更多 `Tested-by`。
- `review`：核对 v3 新 helper 与 `policy_set_boost` 新条件在「频率表只含 boost 频率」「无 boost 频率」边界下的行为。

## 参考链接

- lore（v3 cover）: https://lore.kernel.org/all/20260929-schedutil-boost-frequency-handling-v3-0-68de169498c7@oss.qualcomm.com/
- Oleg 的 v3 Tested-by: https://lore.kernel.org/all/179069242536.2121.14601372514436460845@gmail.com/

---
id: sched-20260930-012
date: '2026-09-30'
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
    summary: 'drop max_table_freq 改新增 helper；policy_set_boost 判断改是否有 boost 频率；Fixes 改 db80ad776cd2'
    review_outcome: '09-30 Oleg 基于 v3 复测并给 Tested-by'
upstream_commit: null
fixes_commit: 'db80ad776cd2'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - '尚缺 cpufreq 维护者最终收取'
  next_action: '等 Rafael/Viresh 等 cpufreq 维护者 review 并收取 v3'
contribution_opportunities:
  - kind: testing
    description: '在 amd-pstate/intel_pstate 上基于 v3 验证回落行为并回帖 Tested-by'
  - kind: review
    description: '核对 v3 新 helper 与 policy_set_boost 新条件在边界（只含 boost 频率/无 boost 频率）下的行为'
generated_at: '2026-10-01T01:00:00'
source_email_count: 1
related_articles:
  - sched-20260921-007
  - sched-20260922-019
  - sched-20260929-004
tags:
  - cpufreq
---