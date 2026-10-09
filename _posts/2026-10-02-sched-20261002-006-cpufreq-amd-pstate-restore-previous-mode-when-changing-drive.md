---
id: sched-20261002-006
date: '2026-10-02'
subject: 'cpufreq: amd-pstate: Restore previous mode when changing driver mode fails'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261001202254.1679976-1-superm1@kernel.org>
lore_url: https://lore.kernel.org/all/20261001202254.1679976-1-superm1@kernel.org/
authors:
- Mario Limonciello
- K Prateek Nayak
maintainers_involved: []
current_version: v2
patch_series:
- version: v1
  msgid: <20260921190235.3651688-1-mario.limonciello@amd.com>
  date: '2026-09-21'
  summary: 4 补丁：模式切换恢复、auto_sel 错误传播、EPP 别名容错、max_freq 断言
  review_outcome: 10-02 Prateek 对 3/4 给出更严格方案
- version: v2
  msgid: <20261001202254.1679976-1-superm1@kernel.org>
  date: '2026-10-02'
  summary: 3 补丁：3/4+4/4 换成 Prateek 的 energy_perf_strings 真值源 + raw EPP 校验方案
  review_outcome: Mario Tested-by；无人对 v2 回帖
upstream_commit: null
fixes_commit: 3ca7bc818d8c
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Rafael/Viresh 尚未对 v2 表态
  next_action: 等 Rafael/Viresh 经 cpufreq tree 收取
contribution_opportunities:
- kind: testing
  description: Zen6 平台跑 amd-pstate-ut 验证 EPP 容错与错误检测边界
- kind: review
  description: 核对 EXPORT_SYMBOL_FOR_PSTATE_UT 在 y/m 配置下的链接行为
generated_at: '2026-10-03T01:00:00'
source_email_count: 6
related_articles: []
tags:
- cpufreq
- amd_pstate
title: 'cpufreq: amd-pstate: Restore previous mode when changing driver mode fails'
layout: article
---

> **subject**：`cpufreq: amd-pstate: Restore previous mode when changing driver mode fails`

## TL;DR

Mario Limonciello（AMD，amd-pstate 维护者）的 3 补丁 v2（前身 09-21 的 4 补丁 v1，v1 未在既往分析窗口覆盖）：修复 amd-pstate 模式切换的两个健壮性缺口与 Zen6 上两个单元测试失败。1/3：`amd_pstate_change_driver_mode()` 注册新模式失败后什么也不恢复、系统失去 scaling driver，改为记住旧模式并在失败时重注册（两处均由 Sashiko bot 报告、`Fixes: 3ca7bc818d8c`）；2/3：`cppc_set_auto_sel()` 返回值被丢弃、固件拒绝时软件模式与硬件实际状态脱节，改为传播首个错误；3/3：把 v1 的 3/4+4/4 换成 K Prateek Nayak 的方案——max_freq 断言放宽到 `lowest_nonlinear_freq`（Zen6 低功耗核最高频可低于共享 nominal），EPP 测试改用 `energy_perf_strings` 为唯一真值源、字符串不匹配时校验硬件 raw EPP 值以容忍 Zen6 的 EPP 别名。v2 的 3/3 正是当日凌晨 Prateek 与 Mario 讨论的直接产物。

## 背景与问题

三个独立缺陷：

1. **模式切换失败后无兜底**：`amd_pstate_change_driver_mode()` 先 unregister 当前驱动再 register 请求的模式；新模式注册失败时直接返回错误，系统停留在「无 scaling driver」状态，直到手动再写一个合法模式。由 Sashiko（kernel.org 的 bug 收集 bot，sashiko.dev）报告。
2. **固件拒绝被静默吞掉**：`amd_pstate_change_mode_without_dvr_change()` 遍历在线 CPU 调 `cppc_set_auto_sel()` 开关硬件自治选择，但不看返回值、无条件返回 0——固件拒绝时 cpufreq core 记录「切换成功」而硬件留在旧自治状态，软件模式与实际频率行为不一致。同样 Sashiko 报告。
3. **Zen6 打破两个 amd-pstate-ut 断言**：(a) 低功耗核的 max_freq 可低于共享的 nominal_freq，`max_freq >= nominal_freq` 断言失败；(b) 多个 EPP 命名偏好可别名到同一 raw 值，`show()` 回读报告的是匹配该值的名字，字符串比对失败。Prateek 对 (b) 的初始 v1 方案（直接容忍别名）「feels a bit hacky since it may be possible an epp may be programmed incorrectly in hardware and as a result it aliases with a different string」——容错不能掩盖硬件编程错误。

## 技术方案

v2 三片（`<20261001202254.1679976-{1,2,3}-superm1@kernel.org>`，3 文件 +85/−57）：

1. **1/3 Restore previous mode**：`old_mode = cppc_state` 先存；`amd_pstate_register_driver(mode)` 失败时 `pr_err` 并重注册 `old_mode`（连恢复失败也分级报错），原始错误仍返回给 sysfs 写入方。
2. **2/3 Propagate auto_sel errors**：`for_each_online_cpu` 循环里检查 `cppc_set_auto_sel()` 返回值，首个错误直接上抛。
3. **3/3 amd-pstate-ut Zen6 fixes**（Prateek 的 patch，Mario Tested-by）：
   - 频率断言改为 `max_freq >= lowest_nonlinear_freq`（注释说明：多数部件 boost 最高即 `max >= nominal`，异构设计低功耗核可低于共享 nominal，故只要求高于最低非线性频率）。
   - EPP 测试：测试内的 `epp_strings[]` 本地副本删除，改用驱动的 `enum energy_perf_value_index` + `energy_perf_strings[]`（从 amd-pstate.c 移到 amd-pstate.h、`EXPORT_SYMBOL_FOR_PSTATE_UT(amd_pstate_cpu_epp_values)` 供模块化 UT 使用）；字符串不匹配时 `FIELD_GET(AMD_CPPC_EPP_PERF_MASK, cppc_req_cached)` 取硬件实际 EPP 值与 `amd_pstate_cpu_epp_values(cpu_type)[mode]` 比对——匹配则 continue（容忍别名、同时验证硬件编程正确），不匹配才报错。注释明确「some platforms (e.g. Zen6) program the same raw EPP value for more than one named preference, so show() reports the first name that matches that value」。

v1→v2 关键变化：3/4+4/4 被 Prateek 方案替换（Mario 10-02 01:20 回复「That does sound like a better approach. I'll test the below」后 04:22 即发 v2，间隔约 3 小时）。

## 版本演进与当前进展

- v1（09-21，`<20260921190235.3651688-1-mario.limonciello@amd.com>`，4 补丁）：1/4、2/4 与 v2 1/3、2/3 同源；3/4「Tolerate aliased EPP preferences」为字符串级容错；4/4 推断为 max_freq 断言放宽的原始版本。
- 10-02（今天）：
  - 00:52 Prateek（`<b3ed027f-8c7b-4ac5-aac6-95d47ac0c41d@amd.com>`）对 3/4 给出完整 diff：以 `energy_perf_strings` 为真值源 + raw 值校验，并把枚举/字符串表迁到 amd-pstate.h 导出。
  - 01:20 Mario（`<472a05d5-f078-46ec-98e7-99cb2f1cd134@amd.com>`）：「That does sound like a better approach. I'll test the below.」
  - 04:22 v2 三补丁发出，3/3 即 Prateek 的 patch（`Signed-off-by: K Prateek Nayak`、`Tested-by: Mario Limonciello`）。
- 当日无人对 v2 回帖。

## Maintainer 意见与讨论焦点

- **Mario Limonciello**（AMD PSTATE DRIVER 维护者，作者）：对 Prateek 方案的反应速度极快（3 小时内吸收重发）；1/3、2/3 维持 v1 设计。
- **K Prateek Nayak**（AMD，评审者）：实质贡献了 3/3 的设计——其核心理念「用驱动自己的字符串表做唯一真值源、用硬件 raw 值兜底校验」比 v1 的朴素容错更严格（不会放过真正编程错误的硬件）。
- 无 NAK、无维护者（Rafael/Viresh）对 v2 表态。

## 合入评估

*likelihood=high*。作者即驱动维护者、两片带 `Fixes:` + Sashiko 报告链接、第三片经维护者实测（Tested-by）且设计经共同作者打磨；amd-pstate 修复通常经 Rafael 的 cpufreq 树收取，门槛主要是流程性的。*blocking_issues*：Rafael/Viresh 尚未对 v2 表态（amd-pstate 修复一般走 cpufreq tree）。*next_action*：等 Rafael/Viresh 收取；无其它已知卡点。

## 效果评估

无 benchmark 数据（行为正确性 + 单元测试修复）。正确性证据：Mario 对 3/3 给出 `Tested-by`（Zen6 平台）；1/3、2/3 的场景（注册失败、固件拒绝）由 Sashiko 报告链接佐证。频率断言放宽后未给出「具体哪款 Zen6 部件 max < nominal」的实例数据。

## 我可以参与的点

- `testing`：在 Zen6 异构平台（低功耗核）跑 `insmod amd-pstate-ut.ko`，确认 3/3 后 EPP/max_freq 测试通过且人为注入错误 EPP raw 值时仍能报错（验证「容错不掩盖硬件错误」的边界）。
- `review`：核对 `EXPORT_SYMBOL_FOR_PSTATE_UT` 的模块导出方式（`EXPORT_SYMBOL_FOR_MODULES` 带 "amd-pstate-ut" 目标白名单）在 CONFIG_X86_AMD_PSTATE_UT=y/m 两种配置下的链接行为。

## 参考链接

- v2 1/3: https://lore.kernel.org/all/20261001202254.1679976-1-superm1@kernel.org/
- v2 3/3（Prateek 方案）: https://lore.kernel.org/all/20261001202254.1679976-3-superm1@kernel.org/
- Prateek 的评审 diff: https://lore.kernel.org/all/b3ed027f-8c7b-4ac5-aac6-95d47ac0c41d@amd.com/
- v1（09-21）: https://lore.kernel.org/all/20260921190235.3651688-1-mario.limonciello@amd.com/
