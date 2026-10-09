---
id: sched-20261009-017
date: '2026-10-09'
subject: 'cpufreq/amd-pstate: Don''t fail active mode init on read-only auto_sel'
subsystem: sched
type: fix
status: superseded
severity: medium
thread_root_msgid: <20261008040705.10600-1-akram02st@gmail.com>
lore_url: https://lore.kernel.org/all/20261009001022.6660-1-akram02st@gmail.com/
authors:
- Akram Boulahia
maintainers_involved:
- Mario Limonciello
current_version: v1
patch_series:
- version: v1
  msgid: <20261008040705.10600-1-akram02st@gmail.com>
  date: '2026-10-08'
  summary: -EOPNOTSUPP 且 auto_sel 已是目标态时视为无害，继续 active 初始化
  review_outcome: 根因是 BIOS bug，作者更新 BIOS 后主动请弃
upstream_commit: null
fixes_commit: 9dfd13f80c85
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
  - 根因在固件（BIOS 308），更新 BIOS 后问题消失，补丁被放弃
  next_action: 无，系列终结
contribution_opportunities: []
generated_at: '2026-10-10T01:30:00'
source_email_count: 2
related_articles:
- sched-20261008-008
tags:
- cpufreq
- x86
title: 'cpufreq/amd-pstate: Don''t fail active mode init on read-only auto_sel'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-008-cpufreq-amd-pstate-don-t-fail-active-mode-init-on-read-only.html">sched-20261008-008</a>：Akram Boulahia 发补丁修 amd-pstate 在一个特定固件形态（`_CPC` 的 Autonomous Selection Enable 项是常量而非寄存器）下的初始化失败——`shmem_init_perf()` 无条件 `cppc_set_auto_sel()` 返回 `-EOPNOTSUPP`、导致回退 acpi-cpufreq。带 `Fixes:`，在华硕 GA403UV 实测修复。
- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-017-cpufreq-amd-pstate-don-t-fail-active-mode-init-on-read-only.html">sched-20261009-017</a>（今天）：**补丁被放弃**。AMD 维护者 Mario Limonciello 判定该固件形态疑似严重 BIOS bug（8945HS 本是 MSR 平台、不该走共享内存），要求先更新 BIOS；作者 Akram 更新 BIOS（308→311）后确认未打补丁的 7.2.8 内核上 amd-pstate 已正常工作，补丁只是对旧 BIOS 的 workaround 且不处理 passive 模式，主动请弃。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-008-cpufreq-amd-pstate-don-t-fail-active-mode-init-on-read-only.html">sched-20261008-008</a>）自 commit `9dfd13f80c85` 起，active 模式 `shmem_init_perf()` 无条件调用 `cppc_set_auto_sel()`，在 Autonomous Selection Enable 项为常量的固件上写被拒、返回 `-EOPNOTSUPP`，导致每个 CPU 初始化失败、回退 acpi-cpufreq。今天的增量确认：根因不是内核代码，而是固件（BIOS 308）形态异常。

## 技术方案

（承接）原补丁在「写被拒但 active 模式要的 auto_sel 本就是启用态」时视为无害、继续初始化。今天 Mario 否决了这一 workaround 的方向——8945HS 应使用 MSR 访问、走共享内存是异常路径，属「severe BIOS bug」，应先修固件再判断；作者更新 BIOS 后确认问题消失，且原补丁不处理 passive 模式，故主动撤回。

## 版本演进与当前进展

v1 发出次日即被放弃（作者主动请弃）。系列终结（status=superseded）。

## Maintainer 意见与讨论焦点

- **Mario Limonciello（AMD，amd-pstate 维护者）**：判断「一个 8945HS 走共享内存是极怪异的路径，该系统有 MSR 访问」，疑为 severe BIOS bug；要求在改代码前先理解固件为何如此表现，建议更新 BIOS 后若仍失败再提交 acpidump（如 kernel bugzilla）。
- **Akram Boulahia（作者）**：更新 BIOS 308→311 后，未打补丁的 7.2.8 内核上 amd-pstate 正常工作（active 加载为 amd-pstate-epp、`amd_pstate=passive` 加载为 amd-pstate，「CPPC feature is supported but currently disabled by the BIOS」行消失）。确认 BIOS 更新才是真正修复，补丁仅为旧 BIOS 的 workaround、且不处理 passive 模式，请弃。

## 合入评估

*likelihood=rejected*。作者主动请弃、维护者已确认根因在固件，补丁不再合入。*next_action*：无，系列终结。

## 效果评估

作者实测：BIOS 308→311 后 amd-pstate 在未打补丁内核上恢复正常加载。原补丁本身无 benchmark（属初始化路径 workaround），其「效果」被固件修复取代。

## 我可以参与的点

当前阶段暂无明显参与空间，系列已终结（固件修复替代了补丁）。若同类「`_CPC` 常量 auto_sel」固件在其它机型复现且 BIOS 无法修复，可再议是否重提 workaround。

## 参考链接

- Mario Limonciello 回复: https://lore.kernel.org/all/851316da-2cfa-4a22-947c-1838532d05cf@amd.com/
- 作者放弃: https://lore.kernel.org/all/20261009001022.6660-1-akram02st@gmail.com/
- 原补丁: https://lore.kernel.org/all/20261008040705.10600-1-akram02st@gmail.com/
