# sched: Expose writable interface for preferred CPUs mask

## TL;DR

Yury Norov 发 6-patch 系列，为 "preferred CPUs" 提供**运行时可写**的 sysfs 接口（`/sys/devices/system/cpu/cpuN/preferred`），用于在物理 CPU 竞争时手动预留 CPU、把 fair 任务导流到其余 CPU。Peter Zijlstra 明确 NAK 了整个方向（「We already have cpusets... Don't bother trying again, this isn't happening」），系列判为 rejected；但其中 patch 1（把 PREFERRED_CPU 从 PARAVIRT 解耦）得到 s390 侧 Ilya/Shrikanth 认可，Peter 另给出 `HAVE_CPUTIME_STEAL` 的替代方案，该 Kconfig 解耦可独立推进。

## 背景与问题

现有 preferred CPU mask 只供 steal governor 在 vCPU 抢占时动态缩减 vCPU 需求；作者希望增加手动控制以覆盖更多场景（例如运行时为选定 fair 任务留 CPU、并把其它 fair 任务导流到其余 CPU，类似 `isolcpus=domain` 的运行时版）。手动设置无需特权、可被后续 governor 更新覆盖；首 patch 放宽 PREFERRED_CPU 对 PARAVIRT 的依赖——动机是 IBM s390 LPAR 硬件辅助虚拟化不启用 PARAVIRT，且 preferred cpumask 并不依赖 PARAVIRT 门控的任何特性。

## 技术方案

系列结构（作者 6 补丁）：1) 把 PREFERRED_CPU 从 `PARAVIRT && SMP` 解耦为独立可配选项（steal governor 默认只在 PARAVIRT 下启用）；2) 新增 `reset_preferred_cpumask()` helper；3) hotplug 移除最后一个 preferred CPU 时在 `sched_cpu_deactivate()` 恢复所有 active CPU 为 preferred；4) 引入 `cpu_preferred_mutex` 串行化多模块并发访问（并修掉 steal governor 采样与 hotplug 之间的既有竞态）；5) steal_governor 对意外 mask 状态告警；6) driver core 增加 per-CPU `preferred` sysfs。

## 版本演进与当前进展

v1 刚发出即被拒。Peter Zijlstra 在 cover 与 patch 1 上双重表态：方向上「Sceptical, I am... This isn't happening」，认为 cpusets 已完全能干这件事、手写接口是灾难配方。对 patch 1（Kconfig 解耦）他另发一段示例代码，引入 `HAVE_CPUTIME_STEAL`（s390 直接 `select`、PPC pseries 经 `PPC_SPLPAR` select），把解耦方向从「删 PARAVIRT」改为「按 steal time 记账能力表达」。Ilya Leoshkevich 给 patch 1 `Reviewed-by` 并补 `depends on SMP && HAVE_CPUTIME_STEAL`；Shrikanth Hegde 追问能否直接用 `PARAVIRT_TIME_ACCOUNTING`（随后认可 Peter 的方案）。

## Maintainer 意见与讨论焦点

主要分歧：Peter Zijlstra 对整个「writable preferred mask 手动接口」方向明确 NAK（改用 cpusets），属于方向性拒绝而非补丁质量争议；但对「PREFERRED_CPU 与 PARAVIRT 解耦」这一子目标持开放态度，并主动给出更合理的 Kconfig 表达（`HAVE_CPUTIME_STEAL`）。s390 侧（Ilya/Shrikanth）对解耦有明确需求并已 review。

## 合入评估

likelihood=rejected（手动 sysfs 接口方向）。blocking：Peter 的 NAK 是根本障碍。next_action：作者若想推进，应放弃 writable 接口、仅提交「PREFERRED_CPU 解耦 PARAVIRT」这一被认可的子 patch（并采纳 `HAVE_CPUTIME_STEAL` 方案）。

## 效果评估

无性能数据；这是接口/控制面改动，未涉及效果测量。

## 我可以参与的点

- new_patch：基于 Peter 的 `HAVE_CPUTIME_STEAL` 示例，把「PREFERRED_CPU ↔ PARAVIRT 解耦」整理为独立补丁（含 s390/PPC `select`），这是唯一有合入可能的部分。
- discussion：就「手动 preferred 接口 vs cpusets/isolation」的边界与 Peter 讨论用例（但方向已被否，投入产出低）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261101192203.6979-1-ynorov@nvidia.com/

---
type: feature
status: stalled
severity: none
thread_root_msgid: <20261101192203.6979-1-ynorov@nvidia.com>
authors:
- Yury Norov
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261101192203.6979-1-ynorov@nvidia.com>
  date: '2026-11-01'
  summary: 6-patch：writable preferred mask sysfs + PREFERRED_CPU 解耦 PARAVIRT + 热插拔恢复
    + cpu_preferred_mutex
  review_outcome: Peter 对整体 NAK，仅认可 Kconfig 解耦并给出 HAVE_CPUTIME_STEAL 替代；Ilya Reviewed-by
    patch 1
merge_assessment:
  likelihood: rejected
  blocking_issues:
  - Peter Zijlstra 明确 NAK 手动 writable preferred 接口方向，认为 cpusets 已覆盖
  next_action: 放弃 writable 接口，仅推进 PREFERRED_CPU↔PARAVIRT 解耦（采纳 HAVE_CPUTIME_STEAL）
contribution_opportunities:
- kind: new_patch
  description: 把 PREFERRED_CPU↔PARAVIRT 解耦按 HAVE_CPUTIME_STEAL 方案整理成独立补丁
- kind: discussion
  description: 讨论手动 preferred 接口的替代方案（cpusets/isolation）
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 9
related_articles: []
tags:
- cgroup
- topology
- affinity
id: sched-20261102-004
subject: 'sched: Expose writable interface for preferred CPUs mask'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
