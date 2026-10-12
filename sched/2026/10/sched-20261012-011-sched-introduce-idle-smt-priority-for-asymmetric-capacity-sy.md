# sched: Introduce idle SMT priority for asymmetric capacity systems

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261008-001 / 20261009-013：Mete Durlu（IBM/s390）发 RFC——非对称容量 + SMT 系统上调度器「宁可整核空闲也不占忙碌高容量核的空闲 SMT 兄弟线程」，引入 `SCHED_IDLE_SMT_PRIO` 静态分支 + `arch_needs_idle_smt_prio()` 钩子；Andrea/Shrikanth 建议改走扩展 `cpu_preferred_mask` 做 soft preference。
- sched-20261012-011（今天）：Vincent Guittot 明确反对「运行期容量可变」的假设（steal time 是系统压力不是容量变化，`arch_scale_cpu_capacity` 不应运行期变），指向 Shrikanth 的 preferred-core 工作；Mete 澄清 s390 极化/hiperdispatch 机制并提出三档（steal time=0 / 低于阈值 / 高于阈值）的 `cpu_preferred_mask + soft affinity` 方案，请 Shrikanth/Andrea 评估。

## 背景与问题

（承接 20261008-001/20261009-013）s390 上 vCPU 有「极化」概念（高低 entitlement），无争用时所有 vCPU 容量几乎一致、对称；steal time 越过阈值后才给低 entitlement vCPU 降容量。此时「低容量但整核空闲」的核不再值得优先——应先把负载打包到高容量核的 SMT 兄弟。作者想让调度器在非对称容量阶段优先填充高容量核的 SMT 兄弟，而非死守「整核空闲优先」。

## 技术方案

（承接 20261008-001）原 RFC 是静态分支 + 架构钩子。今日 Mete 提出更细的三档方案（结合 steal governor 的 `low_threshold` 与极化）：(1) steal time==0 → `cpu_preferred_mask = active_cpus`、无 soft affinity，维持整核空闲优先；(2) 0 < steal ≤ 初始阈值 → soft affinity=entitled cpus，先填满 entitled 核的 SMT 兄弟再外溢；(3) steal > 阈值 → preferred mask 收缩到 entitled + steal governor 的调整。作者并同意把「虚拟拓扑无法反映到 KVM 全核调度」的限制写进 Kconfig 帮助文本。Vincent 则坚持：容量不应运行期变，steal time 属系统压力（不 rebuild sched domain），应走 Shrikanth 已开发的 preferred-core 机制而非新静态分支。

## 版本演进与当前进展

v1（10-08）→ 今日（10-12）方案讨论深化，Mete 给出三档 soft-affinity 设计并请 Shrikanth/Andrea 评估；尚未发 v2。

## Maintainer 意见与讨论焦点

- **Vincent Guittot**：如果 vCPU 起点容量一致就不该开 asym_capacity；steal time 是系统压力而非容量变化，`arch_scale_cpu_capacity` 不应运行期变（否则 misfit 检测会失效），建议走 Shrikanth 的 preferred-core 工作。
- **Shrikanth Hegde**：区分「idle load balance 选核」与「任务放置」两个层面；soft affinity 与负载均衡「尽力打散」的目标相悖、较棘手；提示 steal governor 有 `low_threshold` 可把低 steal 视作 0。
- **Mete Durlu**：澄清 s390 极化/hiperdispatch，承认「全虚拟拓扑时 vCPU 是独立实体」的局限并同意写进 Kconfig。

## 合入评估

*likelihood=medium*。需求（s390/非对称 SMT 打包）真实，但技术路线分歧明显，可能从新静态分支转向 cpu_preferred_mask 扩展。*blocking_issues*：容量 vs 压力语义分歧、路线未定。*next_action*：作者回应 Vincent、与 Shrikanth/Andrea 收敛到 cpu_preferred_mask 方向后重发。

## 效果评估

无 benchmark 数字；讨论集中在架构/语义层面，作者未提供实测数据（属主观判断，未见测试数据）。

## 我可以参与的点

- `discussion`：就「容量变化 vs steal-time 压力」的建模方式，以及 cpu_preferred_mask soft-affinity 与负载均衡打散倾向的冲突发表意见。
- `review`：评估虚拟化（无全核调度的 KVM）下该机制的语义边界与文档化。

## 参考链接

- lore（cover）: https://lore.kernel.org/all/20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com/
- lore（Vincent 质疑）: https://lore.kernel.org/all/CAKfTPtAGiesy0FZQ3aOny_1QkqaX0P2MCOdkE42ERdihRJL99g@mail.gmail.com/
- lore（Mete 三档方案）: https://lore.kernel.org/all/6c4fcef6-6ff8-4733-a451-53744d2c821d@linux.ibm.com/

---
id: sched-20261012-011
date: '2026-10-12'
subject: 'sched: Introduce idle SMT priority for asymmetric capacity systems'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com>
lore_url: https://lore.kernel.org/all/20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com/
authors:
- Mete Durlu
maintainers_involved:
- Vincent Guittot
- Shrikanth Hegde
current_version: v1
patch_series:
- version: v1
  msgid: <20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com>
  date: '2026-10-08'
  summary: 引入 SCHED_IDLE_SMT_PRIO 静态分支 + arch 钩子，允许覆盖「宁可整核空闲」偏好
  review_outcome: Vincent 质疑容量运行期可变假设、指向 cpu_preferred_mask 方向
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Vincent 认为 steal time 是系统压力而非容量变化，不该用 asym_capacity 表达
  - 方案可能转向扩展 Shrikanth 的 cpu_preferred_mask 做 soft preference
  next_action: 作者澄清 s390 极化/hiperdispatch 语义并回应是否改走 cpu_preferred_mask 路线
contribution_opportunities:
- kind: discussion
  description: 就「容量变化 vs steal-time 压力」与 cpu_preferred_mask soft-affinity 路线发表意见
- kind: review
  description: 评估 vCPU 拓扑完全虚拟时（KVM 无全核调度）该配置的语义边界
generated_at: '2026-10-13T01:40:00'
source_email_count: 5
related_articles:
- sched-20261008-001
- sched-20261009-013
tags:
- topology
- hyperthreading
---
