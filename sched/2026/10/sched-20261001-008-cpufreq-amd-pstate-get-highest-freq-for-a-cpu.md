# cpufreq/amd-pstate: Get Highest Freq for a CPU

> **subject**：`cpufreq/amd-pstate: Get Highest Freq for a CPU`

## TL;DR

Mario Limonciello（amd-pstate 驱动维护者）的 3 补丁系列 v4：最高频率已知时直接取用（BIOS/quirk 查询 `amd_get_max_frequency()`），替代按 `(nominal_freq * highest_perf) / nominal_perf` 线性插值的 `max_freq` 计算——机器 BIOS 提供的值更准确（此前 TRX40 平台问题即源于此）。1/3 新增 `amd_get_boost_ratio()`/`amd_get_max_frequency()` helper；2/3 acpi-cpufreq 改用 `amd_get_boost_ratio()`（带 K Prateek Nayak R-b/T-b 与 Rafael Acked-by）；3/3 amd-pstate 的 `amd_pstate_init_freq()` 先查 BIOS 再回退插值。v3 的 3/3 曾被 Christian Loehle 指出遗漏（`amd_pstate_update_min_max_limit()` 仍用 nominal-based 转换、BIOS 覆盖值低于插值结果时会得到 `max_limit_perf < highest_perf`），作者称「excellent finding」并在 v4 一并修正。当日无 NAK。

## 背景与问题

amd-pstate 初始化 `max_freq` 时按 `(nominal_freq * highest_perf) / nominal_perf` 线性插值计算；但当机器 BIOS 明确提供每 CPU 最高频率（或平台 quirk 表有值）时，插值结果可能不准——真实最高频率应优先取 BIOS 已知值（本系列同日的另一 amd-pstate 系列「supply nominal/lowest freq for TRX40 based boards」即处理此类平台）。3/3 的 v3 版本只改了 `amd_pstate_init_freq()` 的 max_freq 计算，被 Christian Loehle 发现配套遗漏：`amd_pstate_update_min_max_limit()` 仍对 `policy->max` 用 nominal-based `freq_to_perf()` 转换，BIOS 覆盖值低于插值结果时会出现 `max_limit_perf < highest_perf` 的不一致。

## 技术方案

三片补丁（v4）：

1. **1/3 `x86/amd: Add amd_get_boost_ratio() and amd_get_max_frequency()`**：新增两个 helper——`amd_get_max_frequency()` 从 BIOS/quirk 查每 CPU 最高频率；`amd_get_boost_ratio()` 返回 boost 分子/分母（对齐「频率值应优先于性能值」的系统）。（该 patch 正文未出现在当日缓存，内容依据 2/3、3/3 的调用侧与 v4 cover 线程头推断。）
2. **2/3 `cpufreq/acpi-cpufreq: Use amd_get_boost_ratio()`**：`get_max_boost_ratio()` 改调新 helper（AMD 分支取 `numerator/denominator`，非 AMD 分支沿用 `perf_caps.highest_perf/nominal_perf`），确保 boost ratio 在「应使用频率值而非性能值」的系统上计算正确。带 `Reviewed-by`/`Tested-by: K Prateek Nayak`、`Acked-by: Rafael J. Wysocki`。
3. **3/3 `cpufreq/amd-pstate: Get Highest Freq for a CPU`**：`amd_pstate_init_freq()` 里 `max_freq = amd_get_max_frequency(cpudata->cpu) * 1000`，查不到（0）再回退插值；v4 新增 `amd_pstate_update_min_max_limit()` 对齐——`policy->max >= cpudata->max_freq` 时 `max_limit_perf` 直接取 `perf.highest_perf`，否则仍走 `freq_to_perf()`，消除 Christian 指出的不一致。

## 版本演进与当前进展

- v1/v2：早于 09-24，未获取到具体内容（不在缓存）。
- v3（09-24，`<20260924160052.2858456-1-superm1@kernel.org>`）：3/3 首次实现 BIOS 优先的 max_freq。
- 10-01：Christian 对 v3 3/3 提出对齐遗漏（`<5b748ac7-26da-4010-bfc8-014a0c97abe2@arm.com>`）；Mario 回复「That's an excellent finding, thanks.」（`<ca33c615-e429-49b1-b1f5-fa25a879a6fa@kernel.org>`）；随后发 v4（cover `<20261001142341.2934582-1-mario.limonciello@amd.com>`）：3/3 更新 `amd_pstate_update_min_max_limit()`（changelog 注明「update amd_pstate_update_min_max_limit too (Christian)」），2/3 增加 Rafael 的 Acked-by。当日无 NAK。

## Maintainer 意见与讨论焦点

- **Rafael J. Wysocki**（cpufreq/ACPI 维护者）：对 2/3 给 `Acked-by`（v4 收录）。
- **K Prateek Nayak**（amd-pstate R）：对 2/3 给 `Reviewed-by` + `Tested-by`。
- **Christian Loehle**（Arm，评审者）：指出 v3 3/3 的 `freq_to_perf()` 对齐遗漏——BIOS 覆盖值低于插值时 `max_limit_perf < highest_perf`；意见被 v4 完整采纳。
- 作者本人即 amd-pstate 驱动维护者；无分歧。

## 合入评估

*likelihood=high*。系列由 amd-pstate 驱动维护者本人提交、2/3 已集齐 R-b/T-b/Acked-by（K Prateek + Rafael）、3/3 的技术性遗漏被 Christian 当场发现并在 v4 修正、当日无 NAK；待 cpufreq 维护者（Rafael/Viresh）正式收取。*blocking_issues*：未见 Rafael/Viresh 对整个系列的收取表态；1/3（x86 侧 helper）正文不在当日缓存、其自身评审状态未知。*next_action*：等 Rafael/Viresh 收取整系列；跟踪 1/3 的 x86 侧评审。

## 效果评估

无量化 benchmark。效果属于正确性/准确性范畴：max_freq 从插值估值改为 BIOS 已知值优先（含 `amd_pstate_update_min_max_limit()` 的一致性）；2/3 的 boost ratio 在「应使用频率值」的系统上计算正确。K Prateek 的 Tested-by 覆盖 2/3。

## 我可以参与的点

- `testing`：在 BIOS 提供与不提供最高频率的两类 AMD 平台上验证 `max_freq`/`max_limit_perf`/boost ratio 的一致性（尤其 mixed-slice 异构核上 BIOS 值与插值差异大的场景）。
- `review`：核对 1/3 的 `amd_get_max_frequency()` BIOS 查询失败路径与 3/3 的 0 值回退逻辑是否覆盖 quirk 表为空的机器。

## 参考链接

- v4 cover 线程根: https://lore.kernel.org/all/20261001142341.2934582-1-mario.limonciello@amd.com/
- v4 3/3: https://lore.kernel.org/all/20261001142341.2934582-4-mario.limonciello@amd.com/
- v4 2/3: https://lore.kernel.org/all/20261001142341.2934582-3-mario.limonciello@amd.com/
- Christian 的 v3 3/3 评审: https://lore.kernel.org/all/5b748ac7-26da-4010-bfc8-014a0c97abe2@arm.com/
- Mario 的回应: https://lore.kernel.org/all/ca33c615-e429-49b1-b1f5-fa25a879a6fa@kernel.org/

---
id: sched-20261001-008
date: '2026-10-01'
subject: 'cpufreq/amd-pstate: Get Highest Freq for a CPU'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20261001142341.2934582-1-mario.limonciello@amd.com>'
lore_url: 'https://lore.kernel.org/all/20261001142341.2934582-1-mario.limonciello@amd.com/'
authors:
  - 'Mario Limonciello'
maintainers_involved:
  - 'Rafael J. Wysocki'
current_version: v4
patch_series:
  - version: v3
    msgid: '<20260924160052.2858456-1-superm1@kernel.org>'
    date: '2026-09-24'
    summary: 'amd_pstate_init_freq 的 max_freq 改 BIOS 查询优先、插值回退'
    review_outcome: 'Christian 指出 amd_pstate_update_min_max_limit 的对齐遗漏'
  - version: v4
    msgid: '<20261001142341.2934582-1-mario.limonciello@amd.com>'
    date: '2026-10-01'
    summary: '3/3 补上 amd_pstate_update_min_max_limit 对齐（policy->max >= max_freq 时直取 highest_perf）；2/3 加 Rafael Acked-by'
    review_outcome: '无 NAK；待 Rafael/Viresh 收取'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - '未见 Rafael/Viresh 对整系列的收取表态'
    - '1/3（x86 侧 helper）正文不在当日缓存，评审状态未知'
  next_action: '等 cpufreq 维护者收取整系列，跟踪 1/3 的 x86 侧评审'
contribution_opportunities:
  - kind: testing
    description: '在 BIOS 提供/不提供最高频率的两类 AMD 平台验证 max_freq/max_limit_perf 一致性'
  - kind: review
    description: '核对 amd_get_max_frequency 失败路径与 0 值回退逻辑'
generated_at: '2026-10-09T01:00:00'
source_email_count: 4
related_articles: []
tags:
  - cpufreq
---
