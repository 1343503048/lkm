---
id: sched-20261001-009
date: '2026-10-01'
subject: 'cpufreq: CPPC: Add ospm_nominal_freq attribute'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260807214837.863209-1-sumitg@nvidia.com>
lore_url: https://lore.kernel.org/all/d6d8912d-cc39-4af7-bb78-4d8095fb094b@amd.com/
authors:
- Sumit Gupta
maintainers_involved:
- Mario Limonciello
current_version: v7
patch_series:
- version: v7
  msgid: <20260807214837.863209-1-sumitg@nvidia.com>
  date: '2026-08-07'
  summary: ACPI 寄存器 + ospm_nominal_freq sysfs + policy 反映三片
  review_outcome: 09-28 Christian 质疑 write-only 接口、Pierre 提初值时机与 rebase；10-01 Mario
    支持 Christian 的读回建议
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 作者尚未回应 v7 评审（接口形态、初值时机、rebase）
  - Rafael 最终 Ack 未给
  next_action: 按可读回方向（或辩护 write-only）改出 v8 并处理 rebase
contribution_opportunities:
- kind: review
  description: 就未设置返回错误+设置后返回最后值的具体语义给接口设计意见
- kind: testing
  description: 在 PCC/共享内存 CPPC 平台验证接口改型后的读写一致性
generated_at: '2026-10-09T01:00:00'
source_email_count: 1
related_articles:
- sched-20260928-010
tags:
- cpufreq
title: 'cpufreq: CPPC: Add ospm_nominal_freq attribute'
layout: article
---

> **subject**：`cpufreq: CPPC: Add ospm_nominal_freq attribute`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-010-acpi-cpufreq-cppc-add-ospm-nominal-perf-support.html">sched-20260928-010</a>：Sumit Gupta 的 v7 三片 CPPC 系列（新增 OSPM nominal perf 支持，把 OS 电源管理设定的标称性能如实反映到 cpufreq 的 boost 与频率上限）在 Rafael Wysocki 催稿后获得首批实质评审——Christian Loehle 质疑 patch 2/3 的 `ospm_nominal_freq` write-only 接口形态（建议能返回 `-EOPNOTSUPP`/requested_val/未设置值），Pierre Gondois 问初值设置时机并建议 rebase。
- <a class="article-ref" href="/lkm/2026/10/01/sched-20261001-009-cpufreq-cppc-add-ospm-nominal-freq-attribute.html">sched-20261001-009</a>（今天）：Mario Limonciello（amd-pstate 驱动维护者）加入讨论并**支持 Christian 的读回建议**——该值在 OSPM set/save/restore 表中被跟踪，Christian 的观点成立；接口可设计为「未设置时返回错误、设置后返回最后一次设置的值」，多软件交互时还能「检查是否设置成功」。write-only 接口争议从「一对一」变为「二对一」倾向可读，但作者 Sumit Gupta 尚未回应。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-010-acpi-cpufreq-cppc-add-ospm-nominal-perf-support.html">sched-20260928-010</a>）CPPC 允许 OS 直接写性能寄存器设定目标。系列 patch 2/3 在 cpufreq 侧新增 `ospm_nominal_freq` sysfs 属性（kHz、write-only、软件侧跟踪），patch 1/3（ACPI）加 `ospm_nominal_perf` 寄存器支持、patch 3/3 把 OSPM nominal 反映到 policy 的 boost 与 limits。Christian 09-28 的质疑：write-only 接口别扭，用户态写入后无法读回核对（尤其多软件交互时），建议返回 `-EOPNOTSUPP`/requested_val/未设置值。今天 Mario 给出支撑该建议的新论据：该值本来就「tracked in the OSPM set/save/restore table」。

## 技术方案

（承接）系列 v7 三片：ACPI 寄存器 + cpufreq `ospm_nominal_freq` sysfs + policy 反映。今天无新代码；Mario 建议的接口语义：未设置时返回错误（如 `-EOPNOTSUPP` 或错误码）、设置后返回最后一次写入的值——「a 'check that it got set properly' in case multiple software interact with the file」。

## 版本演进与当前进展

- v1–v6：早于 08-07，未获取到（不在缓存）。
- v7（08-07，`<20260807214837.863209-1-sumitg@nvidia.com>`）：三片；09-26 Rafael 催稿（无人评审则不合入）；09-28 Christian 与 Pierre 给出实质评审（见 <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-010-acpi-cpufreq-cppc-add-ospm-nominal-perf-support.html">sched-20260928-010</a>）。
- 10-01：Mario Limonciello 回帖支持 Christian 的读回建议（`<d6d8912d-cc39-4af7-bb78-4d8095fb094b@amd.com>`）。作者未回应。

## Maintainer 意见与讨论焦点

- **Mario Limonciello**（amd-pstate 驱动维护者）：「I guess since it's tracked in the OSPM set/save/restore table your point is valid. It could return an error until it's set and then the value that was last set a 'check that it got set properly' in case multiple software interact with the file. So to that point I agree with your suggestion.」——明确站在 Christian 一边。
- **Christian Loehle**（09-28，评审者）：write-only 形态质疑，被 Mario 响应。
- **Rafael Wysocki**（cpufreq 维护者，09-26）：催稿门槛仍在——无人评论则不合入；现在有评论了，但 Rafael 本人尚未对接口形态表态。
- **Pierre Gondois**（09-28，评审者）：初值设置时机、rebase 建议，尚无下文。
- 焦点：`ospm_nominal_freq` 是否改为可读接口（write-only → 可读回），两位评审者已同向，待作者定夺。

## 合入评估

*likelihood=medium*。接口争议获得第二位（且是维护者角色）评审者的同向支持，收敛方向清晰；但作者尚未回应任何 v7 评审意见、v8 未发、Rafael 未表态，且 Pierre 的 rebase 建议也未处理。*blocking_issues*：作者需按「可读回」方向改出 v8（或说明坚持 write-only 的理由）；Pierre 的 rebase/初值时机意见待处理；Rafael 最终 Ack 未给。*next_action*：作者回应 Christian/Mario（改接口为可读或辩护现状）、处理 rebase 后发 v8。

## 效果评估

本日无新数据；系列整体也尚无性能数据（属电源管理寄存器语义一致性改进）。

## 我可以参与的点

- `review`：就「未设置返回错误 + 设置后返回最后值」的具体语义（错误码选择、是否区分 v1/v2 模式）给出接口设计意见，帮助 Christian/Mario/作者三方收敛。
- `testing`：在 arm64 PCC 或 x86 共享内存 CPPC 平台上验证接口改型后的读写一致性与 OSPM save/restore 表的交互。

## 参考链接

- Mario 的支持回复: https://lore.kernel.org/all/d6d8912d-cc39-4af7-bb78-4d8095fb094b@amd.com/
- Christian 的接口意见: https://lore.kernel.org/all/e539dce2-1b2a-45cc-9ea8-1ab0e0f11972@arm.com/
- v7 封面: https://lore.kernel.org/all/20260807214837.863209-1-sumitg@nvidia.com/
