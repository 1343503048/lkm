# cpufreq: Use a non-boost reference frequency for pressure calculation

## TL;DR
Jianyong Wu 提交修复：cpufreq 的 CPU pressure 计算改用"非 boost 参考频率"，避免 boost 开关时 pressure 无谓变化、进而干扰负载均衡（cache-aware scheduling 无法按预期聚合 LLC 任务）。本日讨论集中在参考频率的命名与语义：Rafael Wysocki 追问"什么可持续、可持续多久"，Mario Limonciello 建议复用 `cpuinfo.nominal_freq`，作者认同改用 nominal_freq 命名。

## 背景与问题
`cpufreq_update_pressure()` 用 `freq_table[0]` 作为参考频率计算 CPU pressure，但 `freq_table[0]` 被赋给 `policy->max`，与含 boost 的 `cpuinfo.max_freq` 存在差异。作者在 amd/intel/hygon 实测：使用 acpi-cpufreq 且 boost 开启、无频率上限时，会出现本不该有的 CPU pressure。该错误 pressure 直接影响负载均衡——例如 cache-aware scheduling 想按 LLC 容量的 50% 聚合任务，却因 LLC 内 CPU capacity 被错误降低而无法聚合（作者指出这是 commit d2d5c129d07e 之后引入的行为）。

## 技术方案
让 pressure 计算的参考频率在 boost 开关下保持固定，即改用非 boost 参考频率（低于 boost 的最大频率：acpi-cpufreq 的 P0、amd-pstate 的 nominal 频率）。参考 Vincent Guittot 的口径："只要参考频率在 boost 开关下保持固定即可，我们不希望 pressure 随 boost 开关变化、只在 policy->max 变化时才变。"

## 版本演进与当前进展
- v1（09-15，`<20260915065747.1671965-1-wujianyong@hygon.cn>`）：首版，用 "max_sustainable_freq" 命名；本日讨论后作者同意改用 "nominal_freq"。

## Maintainer 意见与讨论焦点
- **Rafael J. Wysocki**：追问"什么频率可持续、可持续多久"是关键；指出 `freq_table[0]` 可能给处理器进入 turbo/boost 的许可；反问"这在何时何地 matter"；提到 intel_pstate 会随 `cpuinfo.max_freq` 一起更新 capacity，因而 pressure 相对新 capacity 计算就无碍，暗示不同驱动行为不统一。
- **Mario Limonciello**：建议直接 `policy->cpuinfo.nominal_freq = freq_table[0].frequency` 并统一使用 `cpuinfo.nominal_freq`。
- **Jianyong Wu（作者）**：承认 "sustainable" 表述易混淆（本意是"boost 以下的最大频率"）；强调错误 pressure 来自 `freq_table[0]`(=policy->max) 与 `cpuinfo.max_freq` 的差值；希望给不同 cpufreq 驱动一个统一行为；认同 "nominal_freq" 优于 "max_sustainable_freq"。
- 分歧点：参考频率的命名与语义（nominal vs sustainable）；是否应统一到 `cpuinfo.nominal_freq`。

## 合入评估
*likelihood=medium*。问题真实（作者三平台复现 + 影响 cache-aware 负载均衡），方向获 Vincent 既有口径背书；但命名/实现方式仍在收敛（Rafael 对语义的追问未完全闭合）。*blocking_issues*：参考频率命名与实现方式（nominal_freq 复用 vs 独立字段）待定；Rafael 的语义追问待回应。*next_action*：作者按 nominal_freq 方向改版，回应 Rafael 关于"可持续频率"语义的疑问后重发。

## 效果评估
作者实测（amd/intel/hygon）：acpi-cpufreq + boost 开启 + 无频率上限时出现本不应有的 CPU pressure；影响 cache-aware scheduling 无法按 50% LLC 容量聚合任务。为定性描述 + 行为复现，未见具体量化 benchmark 数据。

## 我可以参与的点
- kind=review：确认 intel_pstate 之外的驱动（acpi-cpufreq/amd-pstate）pressure 计算口径，帮助收敛统一的参考频率语义。
- kind=testing：在 cache-aware scheduling + 大小核平台复测"boost 开关是否改变 LLC 聚合结果"，为修复提供量化数据。

## 参考链接
- lore（patch）: https://lore.kernel.org/all/20260915065747.1671965-1-wujianyong@hygon.cn/

---
id: sched-20260918-010
date: '2026-09-18'
subject: 'cpufreq: Use a non-boost reference frequency for pressure calculation'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260915065747.1671965-1-wujianyong@hygon.cn>'
lore_url: 'https://lore.kernel.org/all/20260915065747.1671965-1-wujianyong@hygon.cn/'
authors:
  - 'Jianyong Wu'
maintainers_involved:
  - 'Rafael J. Wysocki'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260915065747.1671965-1-wujianyong@hygon.cn>'
    date: '2026-09-15'
    summary: 'pressure 计算改用非 boost 参考频率（max_sustainable_freq）'
    review_outcome: 'Rafael 追问语义；Mario 建议用 nominal_freq；作者同意改名'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '参考频率命名与实现方式（nominal_freq 复用）待定'
    - 'Rafael 关于可持续频率语义的追问待回应'
  next_action: '作者按 nominal_freq 方向改版并回应语义疑问'
contribution_opportunities:
  - kind: review
    description: '收敛不同 cpufreq 驱动的 pressure 参考频率语义'
  - kind: testing
    description: '在 cache-aware + 大小核平台量化 boost 开关对 LLC 聚合的影响'
generated_at: '2026-09-19T09:00:00'
source_email_count: 4
related_articles: []
tags:
  - cpufreq
  - load_balance
  - schedutil
---