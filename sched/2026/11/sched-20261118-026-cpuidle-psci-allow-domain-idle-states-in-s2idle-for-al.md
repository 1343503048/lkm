# cpuidle: psci: Allow domain idle states in s2idle for all CPU idle states

## TL;DR

Kevin Hilman（TI）发 v2：s2idle 期间只为「最深 CPU idle 状态」设域感知的 `->enter_s2idle()` 回调，其余状态绕过 PM domain，导致 QoS 限值排除了最深状态时整个 CPU PM domain 层级永不掉电。v2 把域感知回调赋给除 WFI 外的所有 CPU idle 状态（仅 s2idle 路径），使 genpd governor 在 `cpu_system_power_down_ok()` 里用同一 QoS 限值选域 idle 状态。v2 相对 v1 的改动是只改 s2idle、regular idle 路径保持不变（回应 Ulf 指出的 genpd 契约问题）。

## 背景与问题

当前只有最深的 CPU idle 状态把 `->enter_s2idle()` 设为域感知的 `psci_enter_s2idle_domain_idle_state()`，其余状态用 `psci_enter_idle_state()` 直接绕过 PM domain。s2idle 时 CPU idle 状态由 `find_deepest_state()` 按 CPU wakeup latency QoS 限值选出——若限值排除了最深状态，就选了较浅状态，PM domain 层级永不掉电，即使某些域 idle 状态本在 QoS 限值内。v1 把域感知回调赋给所有状态（含 regular idle），Ulf 指出这破坏 genpd 对 regular idle 的契约（genpd governor 不知道 cpuidle governor 选的 CPU 状态，可能用更深 composite state 覆盖较浅状态）。

## 技术方案

v2 只改 s2idle 路径：把域感知 `->enter_s2idle()` 赋给除 WFI 外的所有 CPU idle 状态。安全性依据：① genpd governor 在 `cpu_system_power_down_ok()` 里用与 CPU idle 选择相同的 QoS 限值（或域内设备有 resume latency 约束时更严）选域状态；② s2idle 无 idle 时长预测，CPU 与域状态都只是 QoS 允许的最深态，genpd 无法覆盖 cpuidle 决定。域状态的 `arm,psci-suspend-param` 是 composite，exit latency 须计入完整 composite。regular idle 保持「仅最深 CPU 状态可触发域状态」。

## 版本演进与当前进展

*current_version: v2（2026-11-17 发出，`<20261117-topic-lpm-psci-domain-callbacks-v2-1-744884105846@baylibre.com>`）*。v1→v2 只保留 s2idle 改动（回应 Ulf）。当日无 review。

## Maintainer 意见与讨论焦点

- 此前 Ulf Hansson 指出 v1 破坏 genpd regular idle 契约，v2 已收敛到仅 s2idle。当日无新回帖。
- 无 NAK；等待 cpuidle/genpd 维护者 review。

## 合入评估

*likelihood=medium*。v2 已按前轮意见收敛范围、论证充分，但当日无维护者表态。*blocking_issues*：无实质分歧，等待 review。*next_action*：等 Ulf/arm64 cpuidle 维护者 review。

## 效果评估

无量化数据；修复 s2idle 下 PM domain 层级无法掉电的功耗问题（正确性/功耗修复）。

## 我可以参与的点

- **testing**：在 PSCI 平台（含 QoS 限值排除最深状态的场景）验证 s2idle 下域 idle 状态能被正确进入、退出 latency 无异常。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261117-topic-lpm-psci-domain-callbacks-v2-1-744884105846@baylibre.com/

---
id: sched-20261118-026
date: '2026-11-18'
subject: "cpuidle: psci: Allow domain idle states in s2idle for all CPU idle states"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261117-topic-lpm-psci-domain-callbacks-v2-1-744884105846@baylibre.com>"
lore_url: "https://lore.kernel.org/all/20261117-topic-lpm-psci-domain-callbacks-v2-1-744884105846@baylibre.com/"
authors: [Kevin Hilman]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: null
    date: null
    summary: "域感知回调赋给所有 CPU idle 状态（含 regular idle）"
    review_outcome: "Ulf 指出破坏 genpd regular idle 契约"
  - version: v2
    msgid: "<20261117-topic-lpm-psci-domain-callbacks-v2-1-744884105846@baylibre.com>"
    date: '2026-11-17'
    summary: "仅 s2idle 路径赋给除 WFI 外所有状态"
    review_outcome: "当日无 review"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: "等 cpuidle/genpd 维护者 review"
contribution_opportunities:
  - kind: testing
    description: "PSCI 平台验证 s2idle 下域 idle 状态进入正确、latency 无异常"
generated_at: "2026-11-19T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [idle, nohz]
---
