---
id: sched-20260919-007
date: '2026-09-19'
subject: 'sched/topology: Add asymmetric SMT packing override'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260917140707.3807229-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260917140707.3807229-3-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Vincent Guittot
current_version: v4
patch_series:
- version: 09-17 迭代
  msgid: <20260917140707.3807229-1-arighi@nvidia.com>
  date: '2026-09-17'
  summary: 重构为 1/2（fair idle 选择）+ 2/2（topology SMT packing override）
  review_outcome: Vincent 质疑 2/2 的 auto/off 取值，作者同意简化为仅 force
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 2/2 内核参数需简化为仅 force 选项并补 changelog 说明
  next_action: 作者重发简化后的 2/2，说明其为 ACPI 固件属性标准化前的过渡方案
contribution_opportunities:
- kind: review
  description: 就内核参数 override vs 固件 ACPI 属性取舍给出跨架构视角
- kind: testing
  description: 在需命令行覆盖的非对称 SMT 硬件上验证 force 项
generated_at: '2026-09-20T09:00:00'
source_email_count: 3
related_articles:
- sched-20260918-008
tags:
- topology
- idle
- hyperthreading
title: 'sched/topology: Add asymmetric SMT packing override'
layout: article
---

## TL;DR
增量更新：Andrea Righi 非对称 SMT 系列 2/2（新增内核参数覆盖 asymmetric SMT packing）本日收到 Vincent Guittot 的质疑——`auto` 取值冗余、仅 `on` 强制项有意义；Andrea 两度回应，说明该参数是 ACPI 固件属性标准化前的过渡方案，并同意按 Vincent 建议砍掉 `auto`/`off`、只保留显式强制项。

## 背景与问题
背景见 sched-20260918-008：在大小核/非对称 SMT 平台上，idle 选择希望优先选择高优先级 SMT sibling。系列重构后 2/2 把"是否启用 SMT 打包 override"拆成独立内核参数，允许在固件无法描述 SMT 偏好时由命令行显式覆盖。

## 技术方案
2/2（`sched/topology: Add asymmetric SMT packing override`）：新增内核参数，原设计含 `auto`/`off`/`on` 三档，用于显式开启 SMT 层 asymmetric packing。本日讨论聚焦该参数取值设计。

## 版本演进与当前进展
- 09-17 迭代（`<20260917140707.3807229-1-arighi@nvidia.com>`）：重构为 1/2 + 2/2（见 sched-20260918-008）。
- 本日 Vincent Guittot（`<CAKfTPtD6i7BMpfnj4pEPJMMOSXyMWL63YDX00d+jRTn0x+ot7A@mail.gmail.com>`）质疑 `auto` 必要性。
- Andrea Righi（`<aq2B612KT5JGdsaf@gpd4>`、`<aq2CqGXjH_lrZVnS@gpd4>`）回应并同意简化接口。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**：`auto` 等价于命令行不加参数，为何还需要？是否仅为调试用途？"只有 `sched_smt_asym_packing=on` 对强制开启（固件不提供信息时）真正有用"。
- **Andrea Righi**：解释固件描述的 ACPI 属性是长期首选，但跨固件/Linux/其他 OS 定义并验证接口、完成 ACPI 标准化需要时间；命令行选项是过渡 workaround 与"固件无法升级的已部署系统"的兜底。Will Deacon 不喜欢用 Olympus CPU quirk 探测、要求固件描述属性，故改走 boot-time override。作者同意 Vincent 的意见：`auto` 冗余、省略参数即保留架构/固件提供的拓扑；无具体用例需要暴露 `off`；将把接口简化为"仅显式 force 选项"。

## 合入评估
likelihood=medium（收敛中）。1/2 已获多位 reviewer 认可，2/2 的接口正在按 Vincent 意见简化（去 auto/off 留 force）。blocking_issues：2/2 参数接口待按"仅 force"重发并补 changelog 说明。next_action：作者重发简化后的 2/2，说明该参数为 ACPI 固件属性标准化前的过渡方案。

## 效果评估
本日无新增 benchmark；讨论为接口设计收敛，无性能数据。

## 我可以参与的点
- kind=review：就"内核参数 override vs 固件 ACPI 属性"的取舍给出跨架构视角（尤其非 x86/arm64 平台的 asym packing 需求）。
- kind=testing：在有非对称 SMT 且固件未提供属性、需靠命令行覆盖的硬件上验证 `force` 项。

## 参考链接
- lore（09-17 系列 cover）: https://lore.kernel.org/all/20260917140707.3807229-1-arighi@nvidia.com/
- lore（2/2 patch）: https://lore.kernel.org/all/20260917140707.3807229-3-arighi@nvidia.com/
- lore（Vincent 质疑）: https://lore.kernel.org/all/CAKfTPtD6i7BMpfnj4pEPJMMOSXyMWL63YDX00d+jRTn0x+ot7A@mail.gmail.com/
