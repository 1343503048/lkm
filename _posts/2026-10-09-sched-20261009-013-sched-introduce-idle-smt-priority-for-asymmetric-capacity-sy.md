---
id: sched-20261009-013
date: '2026-10-09'
subject: 'sched: Introduce idle SMT priority for asymmetric capacity systems'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com>
lore_url: https://lore.kernel.org/all/CAKfTPtCianGNWSu0s2J_B_aO_rtKWO17k9guYmwgXXLUHQE+SA@mail.gmail.com/
authors:
- Mete Durlu
maintainers_involved:
- Vincent Guittot
- Tim Chen
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com>
  date: '2026-10-08'
  summary: SCHED_IDLE_SMT_PRIO 静态分支 + arch_needs_idle_smt_prio()，s390 启用
  review_outcome: Tim/Vincent/Andrea/Shrikanth 就前提与分层展开，作者未回应
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - Vincent 对非对称容量起点的质疑待回应
  - Tim 要求的前提显式化/enforce 未落地
  - 两级模型 vs 简化选择序未收敛
  - 无跨平台收益数据
  next_action: 作者回应前提质疑与契约要求，明确触发条件
contribution_opportunities:
- kind: discussion
  description: 两级分层模型 vs 简化选择序的分析
- kind: review
  description: 审 SMT 兄弟同核前提在 LPAR vs KVM 下的 enforce
- kind: testing
  description: x86/arm64 非对称容量+SMT 平台实测负载打包
generated_at: '2026-10-10T01:30:00'
source_email_count: 5
related_articles:
- sched-20261008-001
tags:
- cfs
- topology
- hyperthreading
title: 'sched: Introduce idle SMT priority for asymmetric capacity systems'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-001-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261008-001</a>：Mete Durlu（IBM/s390）发 RFC：非对称容量 + SMT 系统上调度器「宁可整核空闲，也不占忙碌高容量核的空闲 SMT 兄弟线程」，引入 `SCHED_IDLE_SMT_PRIO` 静态分支 + `arch_needs_idle_smt_prio()` 钩子。Andrea Righi 与 Shrikanth Hegde 建议改走「扩展 `cpu_preferred_mask` 做 soft preference」，路线未收敛。
- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-013-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261009-013</a>（今天）：评审密集展开——**Tim Chen** 要求把「SMT 兄弟必须真在同一物理核」这一前提显式化并写进 Kconfig/钩子契约（KVM 客户机的 sibling mask 只是描述、无打包收益）；**Vincent Guittot**（mainline 维护者）质疑前提本身——若 s390 视所有 CPU 等容量则 `SD_ASYM_CPUCAPACITY_FULL` 永不置位、`select_idle_capacity()` 根本不会用到；**Andrea** 提出「hard affinity + entitlement-based soft affinity」两级模型；**Shrikanth** 澄清 PowerVM entitlement 语义并给出「全空闲 preferred 核 → idle preferred CPU → 任意 idle CPU」的简化选择序。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-001-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261008-001</a>）调度器持续往「优先整核空闲、避免 SMT 惩罚」方向演进（commit `25a32e400a14`），打破了 s390 依赖的行为：s390 的 CPU capacity 代表 hypervisor 分配的运行时 entitlement，整机接近满载时忙碌高容量核的空闲 SMT 兄弟线程开始胜过完全空闲的低容量核。今天的增量把讨论从「实现路线」推向「前提是否成立」与「分层模型」两个更深的问题。

## 技术方案

（承接）v1 方案：patch 1 在 `kernel/sched` 引入 `SCHED_IDLE_SMT_PRIO` 配置项 + `sched_idle_smt_prio` 静态分支 + `arch_needs_idle_smt_prio()` 钩子（逐架构 opt-in）；patch 2 在 s390 硬件拓扑下打开静态分支。今天的评审对其前提与分层提出修正：

- **Tim Chen**：① 该方案只在「客户机看到的 SMT 兄弟真跑在同一物理核」时才成立（LPAR 上 hypervisor 整核派发成立；KVM `threads=2` 等按 vCPU 派发的客户机不成立，sibling mask 只是描述）。② 系列目前没有任何检查/文档化这一前提。③ 主张**保留钩子**（这是唯一能 enforce 该前提的地方），要求：Kconfig help 与钩子上方写明契约（「只有 SMT 兄弟总是派发到同一物理核时才 select 此特性」）；s390 钩子改成测试 `machine_is_lpar() && topology_mode == TOPOLOGY_MODE_HW && smp_cpu_mtid`。
- **Vincent Guittot**：质疑拓扑前提——「如果 s390 视所有 CPU 等容量」，`SD_ASYM_CPUCAPACITY_FULL` 就永不置位、`select_idle_capacity()` 根本不会用到；若 hypervisor 越过阈值降容量，steal time 已通过 irq 从任务可用容量里扣除（原始容量不变）。这直击系列「非对称容量」的起点。
- **Andrea Righi**：同意被 steal governor 排除的 CPU 应始终规避；提议**两级模型**——`cpu_preferred_mask` 作 hard affinity 约束，mask 内再做 entitlement 软偏好（先全空闲核、再 idle SMT 兄弟，忙则 spill 到 mask 内低 entitlement CPU），软偏好永不越过 governor 的限制。
- **Shrikanth Hegde**：澄清 PowerVM 的 entitlement 语义（VP=虚拟核、EC=entitled 核，hypervisor 保证 EC 量，entitlement 内无优先级）；高 steal 时 preferred 内通常没有全空闲核；`find_new_ilb()` 本就从开头遍历、会先选到 preferred 内的空闲核；建议采用简化的选择序「全空闲 preferred 核 → idle preferred CPU → 任意 idle CPU」，并认为 Andrea 的两级模型会让 `find_new_ilb()` 过复杂、可能不值。

## 版本演进与当前进展

v1（RFC）当日无新版。今天评审从「实现路线」深入到「前提显式化」与「分层模型」，作者尚未对今天这批意见回应。

## Maintainer 意见与讨论焦点

- **Vincent Guittot（mainline sched 维护者，今天首次表态）**：对系列「非对称容量」的起点提出质疑——s390 要么等容量（则该机制无触发条件）、要么靠 steal time 降容量（已被现有 irq 记账覆盖）。
- **Tim Chen（Intel）**：聚焦「SMT 兄弟同物理核」前提必须显式化 + 保留钩子做 enforce。
- **Andrea Righi**：两级（hard + soft）分层模型。
- **Shrikanth Hegde（s390）**：entitlement 语义澄清 + 简化选择序，对 Andrea 两级模型的价值存疑。
- **Mete Durlu（作者）**：尚未回应今天的意见。
- 分歧核心：① 系列前提（非对称容量 + SMT 同核）是否成立/如何 enforce；② 是否需要两级分层模型还是简化选择序即可。

## 合入评估

*likelihood=unknown*。仍为早期 RFC；Vincent 对前提的质疑若成立会动摇系列根基，作者需先回应这一层再谈实现。*blocking_issues*：① Vincent 对「非对称容量起点」的质疑待作者回应；② Tim Chen 要求的前提显式化/enforce 未落地；③ 两级模型 vs 简化选择序未收敛；④ 无跨平台收益数据。*next_action*：作者回应 Vincent 的前提质疑与 Tim 的契约要求，明确触发条件与 enforce 方式。

## 效果评估

（承接）作者未附 benchmark；本日仍无新量化数据。可引用的间接经验仍是 Shrikanth 此前 `find_new_ilb()` 优先挑 preferred CPU 时真实负载未见显著提升的个人经验判断。

## 我可以参与的点

- `discussion`：就「两级（hard + soft）分层模型 vs 简化选择序」以及 Vincent 对触发条件（等容量则无需、降容量则已被 irq 记账）的质疑给出分析。
- `review`：审「SMT 兄弟同物理核」前提在不同虚拟化（LPAR vs KVM）下的 enforce 可行性。
- `testing`：x86/arm64 非对称容量 + SMT 平台实测负载打包与邻分区噪声——当前最缺 s390 之外的实测。

## 参考链接

- 系列封面: https://lore.kernel.org/all/20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com/
- Tim Chen 前提质疑: https://lore.kernel.org/all/76e09124223f7adb7f486fd861ead3bdbf595016.camel@linux.intel.com/
- Vincent Guittot 回复: https://lore.kernel.org/all/CAKfTPtCianGNWSu0s2J_B_aO_rtKWO17k9guYmwgXXLUHQE+SA@mail.gmail.com/
