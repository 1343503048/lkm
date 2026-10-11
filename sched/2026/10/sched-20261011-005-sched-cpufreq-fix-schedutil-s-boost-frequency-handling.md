# sched/cpufreq: fix schedutil's boost frequency handling

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260921-007：Ananthu C V 的 schedutil boost 频率处理修复（v2）回应 Oleg 关于 `cpuinfo->max_freq` 只升不降设计的疑问，接受 Zhongqiu 建议补 `Fixes:`。
- sched-20260922-019：Zhongqiu Han 在 SM8850（SCMI 驱动）上复测，二分定位问题由 `db80ad776cd2` 引入。
- sched-20260929-004：作者发 v3——drop `max_table_freq` 字段、新增从频率表取最大频率的 helper、`policy_set_boost` 判断改「是否有 boost 频率」、2/2 的 `Fixes:` 改为 `db80ad776cd2`；Oleg 对 v2 的 `Tested-by` 因实现变更未被采纳。
- sched-20260930-012：Oleg Keri 基于 v3 在 Lenovo Yoga Slim 7x Gen 11 上复测，给出 `Tested-by`（boost 关闭回 4032000、开启 4723200、再关回 4032000）——此前 v3 缺 `Tested-by` 的阻塞点解除。
- sched-20261011-005（今天）：Zhongqiu Han 基于 v3 2/2 给出新 review——changelog 应描述 `6e39ba4e5a82` 的影响、2/2 应前置且自包含（以便独立回 backport stable）、并建议改用 `has_boost` 标志让频率表无条件成为 `cpuinfo.max_freq` 来源。

## 背景与问题

（承接 sched-20260918-005 / sched-20260921-007）schedutil 在关闭 boost 后频率无法回落到非 boost 值：commit `538b0188da46` 给 `cpuinfo->max_freq` 加了「只向上更新」guard，其后 `db80ad776cd2` 又删掉驱动默认 `policy->max = max_freq` 赋值，使该单向 guard 成为 cpuinfo max（进而 policy max）更新的唯一路径，boost 关闭后两者被钉在 boost 频率。v3 两个缺口：per-CPU capacity 频率参考在 policy 创建时设定一次、boost 之后不再更新；以及「关闭 boost 后回不去」。

## 技术方案

（承接 sched-20260929-004）v3 仍两补丁：1/2 用「频率表最高值」与 `cpuinfo.max_freq` 较大者 seed capacity freq ref，让 schedutil 从 policy 创建起就知道最高可用频率；2/2 无条件跟踪频率表最高非 boost 频率（`max_base_freq`），有 boost 频率时用「频率表最高 / `max_base_freq`」控制 boost 值、关闭 boost 时回落，无 boost 频率时回退 `cpuinfo->max_freq`。`Fixes: db80ad776cd2`。

今日增量（Zhongqiu 对 2/2 的 review）提出三点：

- changelog 应描述 commit `6e39ba4e5a82`（"cpufreq: Add boost_freq_req QoS request"）的影响——v2 时已提过，对理解本 fix 很关键。
- 2/2 目前依赖 1/2 引入的 helper，无法独立 backport；2/2 是应单独回到 stable 的独立修复，应放到 1/2 之前并保持自包含。
- 建议改用另一实现替代「新增仅频率表驱动使用的成员」：若频率表里有 boost entries，该表就是 `cpuinfo.max_freq` 的唯一来源，让 `cpufreq_frequency_table_cpuinfo()` 在这种情况下无条件设置它。其 diff 引入 `bool has_boost`，遍历时记录是否有 `CPUFREQ_BOOST_FREQ` 项，最后 `if (has_boost || policy->cpuinfo.max_freq < max_freq)` 才写回 `max_freq`。

## 版本演进与当前进展

- v2（09-08）：运行时尽量不依赖 `cpuinfo_max_freq` + 修复关闭 boost 后无法回落；Oleg `Tested-by`。
- v3（09-29）：drop `max_table_freq`、新增取频率表最大频率 helper、`policy_set_boost` 判断改「是否有 boost 频率」、`Fixes:` 改 `db80ad776cd2`；Oleg 的 `Tested-by` 因实现变更未沿用。
- 09-30：Oleg 基于 v3 复测并给新 `Tested-by`。
- 10-11：Zhongqiu 对 v3 2/2 提三点意见（changelog 补 `6e39ba4e5a82` 影响、2/2 前置自包含、改用 `has_boost` 方案），倾向需要 v4。

## Maintainer 意见与讨论焦点

- **Zhongqiu Han**（Qualcomm，多次复测/二分定位 `db80ad776cd2`，非 cpufreq 维护者）：今日对 v3 2/2 提出 ① changelog 需描述 `6e39ba4e5a82` 影响；② 2/2 应置前并自包含以便独立 backport；③ 建议以 `has_boost` 标志让「含 boost 频率的频率表」无条件成为 `cpuinfo.max_freq` 来源，避免引入仅频率表驱动使用的新成员。
- **Oleg Keri**（测试者）：09-30 已基于 v3 给 `Tested-by`。
- cpufreq 维护者（Rafael Wysocki / Viresh Kumar）：仍未表态。无 NAK。

## 合入评估

*likelihood=medium*（较 09-30 的 high 下调）。方向正确、已有 Oleg 的 v3 `Tested-by`；但 Zhongqiu 提出替代实现与重排要求，作者需发 v4，且 cpufreq 维护者仍未收取。*blocking_issues*：Zhongqiu 的 v4 修改意见（`has_boost` 替代实现、2/2 前置自包含、changelog 补 `6e39ba4e5a82` 影响）；尚缺 cpufreq 维护者最终收取。*next_action*：作者按 Zhongqiu 意见发 v4，等 Rafael/Viresh review 收取。

## 效果评估

无新增 benchmark。Oleg 的 sysfs 实测（boost 关闭回 4032000、开启 4723200、再关回 4032000）确认「关闭 boost 后频率回落」行为正确（沿用 09-30 数据）。今日无新数字。

## 我可以参与的点

- `review`：评估 Zhongqiu 的 `has_boost` 方案与作者 v3 `max_base_freq` 方案在「频率表只含 boost 频率」「无 boost 频率」边界下的等价性。
- `testing`：在另一带 boost 能力的 cpufreq 驱动（amd-pstate/intel_pstate）上基于下一版验证回落行为，回帖补 `Tested-by`。

## 参考链接

- lore（v3 cover）: https://lore.kernel.org/all/20260929-schedutil-boost-frequency-handling-v3-0-68de169498c7@oss.qualcomm.com/
- lore（Zhongqiu 10-11 review）: https://lore.kernel.org/all/41f328b2-0825-4023-b86c-48136ba6ecd2@oss.qualcomm.com/

---
id: sched-20261011-005
date: '2026-10-11'
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
    review_outcome: '09-30 Oleg 基于 v3 复测给 Tested-by；10-11 Zhongqiu 提 has_boost 替代实现与重排意见'
upstream_commit: null
fixes_commit: 'db80ad776cd2'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'Zhongqiu 的 v4 修改意见（has_boost 替代实现、2/2 前置自包含、changelog 补 6e39ba4e5a82 影响）'
    - '尚缺 cpufreq 维护者最终收取'
  next_action: '作者按 Zhongqiu 意见发 v4，等 Rafael/Viresh review 收取'
contribution_opportunities:
  - kind: review
    description: '评估 has_boost 方案与 max_base_freq 方案在只含 boost 频率/无 boost 频率边界下的等价性'
  - kind: testing
    description: '在 amd-pstate/intel_pstate 上基于下一版验证回落行为并回帖 Tested-by'
generated_at: '2026-10-12T01:00:00'
source_email_count: 1
related_articles:
  - sched-20260930-012
tags:
  - cpufreq
---