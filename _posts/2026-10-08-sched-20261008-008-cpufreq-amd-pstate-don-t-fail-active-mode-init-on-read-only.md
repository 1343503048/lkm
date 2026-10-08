---
id: sched-20261008-008
subject: 'cpufreq/amd-pstate: Don''t fail active mode init on read-only auto_sel'
date: '2026-10-08'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261008040705.10600-1-akram02st@gmail.com>
lore_url: https://lore.kernel.org/all/20261008040705.10600-1-akram02st@gmail.com/
authors:
- Akram Boulahia
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261008040705.10600-1-akram02st@gmail.com>
  date: '2026-10-08'
  summary: -EOPNOTSUPP 且 auto_sel 已是目标态时视为无害，继续 active 模式初始化
  review_outcome: 当日无回帖
upstream_commit: null
fixes_commit: 9dfd13f80c85
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无维护者 review
  - -EOPNOTSUPP 豁免条件的边界语义待确认
  next_action: 等 amd-pstate 维护者审阅豁免条件后合并
contribution_opportunities:
- kind: review
  description: 审 -EOPNOTSUPP 豁免条件是否误放边界固件形态
- kind: testing
  description: 在其它 _CPC 常量化机型验证 active/passive 初始化行为
generated_at: '2026-10-09T01:00:00'
source_email_count: 1
related_articles: []
tags:
- cpufreq
- x86
- regression
title: 'cpufreq/amd-pstate: Don''t fail active mode init on read-only auto_sel'
layout: article
---

## TL;DR

Akram Boulahia 修掉 amd-pstate 在一个特定固件形态下的初始化失败：commit `9dfd13f80c85` 起，active 模式里 `shmem_init_perf()` 不再提前返回、总会调用 `cppc_set_auto_sel()`（为共享内存系统所需）；但在 `_CPC` 的 Autonomous Selection Enable 项是「常量整数而非寄存器」的固件上，这次写返回 `-EOPNOTSUPP`，导致所有 CPU 初始化失败、`cpufreq_register_driver()` 找不到 policy，最终回退到 acpi-cpufreq。补丁在「写被拒但 active 模式要的 auto_sel 本就已是启用态」时视为无害继续初始化。带 `Fixes:` 标签、在华硕 GA403UV 实测修复。

## 背景与问题

自 commit `9dfd13f80c85`（"cpufreq/amd-pstate: Toggle auto_sel in active mode on shared memory systems"）起，active 模式下 `shmem_init_perf()` 不再提前返回，而是无条件调用 `cppc_set_auto_sel()`。这对共享内存系统是必要的，但在 Autonomous Selection Enable 项为常量（非寄存器）的固件上，该写会返回 `-EOPNOTSUPP`。这个错误被一路返回：每个 CPU 都初始化失败 → `cpufreq_register_driver()` 找不到 policy、返回 `-ENODEV` → 内核回退到 acpi-cpufreq。日志形如：

```
amd_pstate: failed to set auto_sel, ret: -95
amd_pstate: Failed to initialize CPU 0: -95
amd_pstate: failed to register with return -19
```

复现机型为 ASUS ROG Zephyrus G14（GA403UV，Ryzen 9 8945HS，BIOS 308），其 `_CPC` 为 revision 3、该 entry 固定为 1，`cppc_get_auto_sel()` 在所有 CPU 上读回 1。

## 技术方案

当写返回 `-EOPNOTSUPP`、且请求的是 active 模式、且 `auto_sel` 当前读值已为启用态（恰是 active 模式所需）时，这个被拒绝的写是无害的，初始化可继续；任何其它失败（包括「被拒但当前值与请求模式不符」）仍按原样返回。这样 `amd-pstate-epp` 在该机 16 个 CPU 上都能加载、无告警。`amd_pstate=passive` 行为不变：仍回退 acpi-cpufreq 并报同样 -95（因为 auto_sel 恒为 1、无法改动）。

## 版本演进与当前进展

v1 首发（`<20261008040705.10600-1-akram02st@gmail.com>`），当日无回帖。作者标注在 Linux 7.3.0-rc6 上实测。

## Maintainer 意见与讨论焦点

当日无维护者（Mario Limonciello 等 amd-pstate 维护者）表态。潜在关注点在于：把 `-EOPNOTSUPP` 且「当前值已是目标态」特判为无害是否普适——即是否存在 auto_sel 读值语义与 active 模式期望不一致的边界固件。

## 合入评估

*likelihood=medium*。明确的初始化回归修复、带 `Fixes:` 与真实机实测（amd-pstate-epp 恢复加载）；但尚无维护者 review，且 `-EOPNOTSUPP` 豁免条件（当前值已为目标态）的普适性需维护者确认。*blocking_issues*：无维护者 review；豁免条件的边界语义待确认。*next_action*：等 amd-pstate 维护者（Mario）审阅，确认豁免条件是否普适后合并。

## 效果评估

作者实测：打补丁后 `amd-pstate-epp` 在华硕 GA403UV 全部 16 核加载、无告警；被动模式行为不变（仍回退 acpi-cpufreq，符合预期，因为 auto_sel 恒 1 无法改）。无性能对比数据（属「能否加载」的正确性修复）。

## 我可以参与的点

- `review`：审 `-EOPNOTSUPP` 豁免条件是否可能误放「当前 auto_sel 恰为 1 但语义非 active 所需」的固件形态。
- `testing`：在其它 `_CPC` 常量化（revision 3、auto_sel 固定值）的机型上验证 active/passive 两种模式的初始化行为是否与作者描述一致。

## 参考链接

- 补丁: https://lore.kernel.org/all/20261008040705.10600-1-akram02st@gmail.com/
