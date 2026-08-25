---
id: sched-20260819-010
date: 2026-08-19
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: <unknown>
lore_url: 未获取到
authors:
- Tao Cui
- Tejun Heo
- Liang Luo
maintainers_involved:
- Tejun Heo
- Changwoo Lee
current_version: RFC
patch_series:
- version: RFC
  msgid: <unknown>
  date: 2026-08-19
  summary: 原 RFC 提议：当 cgroup 配了有限 cpu.max 配额但当前 BPF 调度器未实现 cgroup_set_bandwidth 回调时，打印一次性警告（实测
    scx_simple 下 cpu.max=50% 配额仍占满 9946ms/10s、nr_throttled=0）。Tejun 反对：cpu.weight
    当年类似警告弊大于利，BPF 调度器可能整体忽略 nice 等多个 knob，单点警告武断；应以文档说明。Tao Cui 接受，改为去 sched-ext.rst
    加说明：cgroup CPU knob 仅当加载的调度器实现了对应回调才生效，调度器也可能忽略其它 knob。
  review_outcome: Tejun NAK 了运行时警告思路，明确倾向文档方案；作者同意改投文档补丁（与 article 008 同源）。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 方向已从'运行时警告'转向'文档说明'，需把文档补丁写清并获 ack
  next_action: 等待作者发出 sched-ext.rst 的 cgroup knob 依赖文档补丁并获 Tejun/Changwoo ack。
contribution_opportunities:
- kind: discussion
  description: 可帮忙草拟 sched-ext.rst 中关于'cgroup CPU knob 依赖调度器回调实现'的准确表述，或举例哪些 in-tree
    调度器实现了哪些回调。
generated_at: '2026-08-20T00:30:00'
source_email_count: 3
related_articles:
- sched-20260818-004
- sched-20260818-005
- sched-20260819-008
tags:
- sched_ext
- cgroup
- documentation
title: 关于 "sched_ext 下 cpu.max 配额未被 BPF 调度器强制时是否告警" 的讨论：Tejun NAK 了运行时一次性警告（参照 cpu.w...
layout: article
---

## TL;DR
关于 "sched_ext 下 cpu.max 配额未被 BPF 调度器强制时是否告警" 的讨论：Tejun NAK 了运行时一次性警告（参照 cpu.weight 前车之鉴），倾向用文档说明 "knob 仅当调度器实现对应回调才生效"。作者改为投文档补丁。属 08-18 带宽讨论的延续。

## 背景与问题
内核把 `cpu.max` 带宽参数存进 `task_group` 并通过 `ops.cgroup_set_bandwidth()` / `scx_cgroup_init_args` 透传给 BPF 调度器，但内核自身不强制配额。若加载的 BPF 调度器未实现该回调，`cpu.max` 被静默忽略——实测 `scx_simple` 下 `cpu.max="50000 100000"`（单核 50%）配一个忙任务，10s 内用了 9946ms CPU 且 `nr_throttled` 始终为 0。in-tree 示例调度器仅 `scx_qmap` 实现了回调，且只是 `bpf_printk` 打印参数，无人真正强制配额。

## 技术方案（讨论中的取舍）
- **原 RFC（Tao Cui）**：配了有限配额但调度器缺回调时，打印一次性警告，提示用户/编排器配额未生效。
- **Tejun 反对**：cpu.weight 当年加类似警告是 "created more annoyances than helping anything"；cgroup 带宽控制不是 BPF 调度器唯一可能跳过的事，它也可能整体忽略 nice 等级等，无法检测；单点警告武断。应以文档处理。
- **作者接受**：改为在 `sched-ext.rst` 加说明——cgroup CPU knob（如 cpu.max）仅在加载的调度器实现了对应回调时才生效，且调度器也可能忽略其它 knob。

## 版本演进与当前进展
- 8/18 Tao Cui 发 RFC（打印警告）。
- 8/19 Tejun 回复 NAK 警告、建议文档；Tao Cui 同意转文档方案（与同日 Liang Luo 的 cgroup-v2.rst 措辞修正 article 008 同源）。

## Maintainer 意见与讨论焦点
**核心分歧已 resolved 为方向性 NAK**：Tejun 明确不想要运行时警告，理由是与 cpu.weight 历史一致（警告弊大于利）、且无法覆盖调度器可能忽略的全部 knob。社区一致倾向文档化。

## 合入评估
合入可能性 medium：方向已从代码改为文档，文档补丁需写清并获 Tejun/Changwoo ack。无技术风险。

## 效果评估
无性能数据。实测数据（scx_simple 下 9946ms/10s、nr_throttled=0）支撑 "配额被忽略" 的现象描述，但属文档/认知问题而非性能优化。

## 我可以参与的点
- 帮忙草拟 `sched-ext.rst` 中准确的 knob-依赖-回调 表述，或列一张 in-tree 调度器实现各回调的对照表补进文档。

## 参考链接
- lore thread: 未获取到
