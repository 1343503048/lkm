---
id: sched-20260827-006
date: '2026-08-27'
subject: 'sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff'
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: <20260812054033.95658-1-sshegde@linux.ibm.com>
lore_url: https://lore.kernel.org/all/2e1085f1-82f2-42dc-ae72-0bedffb414f3@arm.com/
authors:
- Dietmar Eggemann
- Shrikanth Hegde
maintainers_involved:
- Dietmar Eggemann
current_version: v11
patch_series:
- version: v10
  msgid: <20260812054033.95658-1-sshegde@linux.ibm.com>
  date: 2026-08-12
  summary: preferred CPUs + steal-driven vCPU backoff 12 补丁
  review_outcome: 0f3307c8 起的多轮讨论延伸到 08-27
- version: v11
  msgid: <20260825103855.721013-1-sshegde@linux.ibm.com>
  date: 2026-08-25
  summary: 含 32-bit Arm 任务的防御性检查改动
  review_outcome: Dietmar 质疑必要性，作者愿删但待确认
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - cpus_ptr ⊆ task_cpu_possible_mask 是否恒成立待 Dietmar 二次确认，决定 v12 是否删防御检查
  next_action: Dietmar 回复 32-bit 场景覆盖结论，作者出 v12
contribution_opportunities:
- kind: testing
  description: 在 arm64 异构/32-bit 兼容环境实测 cpuset 收缩 + preferred mask 的交集行为
- kind: discussion
  description: 回答线程末尾 task_allowed_on_cpu 语义问题（当日无人应答）
generated_at: '2026-09-07T22:05:00'
source_email_count: 2
related_articles:
- sched-20260825-001
- sched-20260817-005
- sched-20260814-004
- sched-20260822-003
tags:
- affinity
- arm64
title: 'sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff'
layout: article
---

## TL;DR
本文为增量更新（完整背景见 related_articles）。08-27 的讨论收敛到一个具体的代码问题：`task_can_sched_on_preferred()` 里针对 32-bit Arm 用户的防御性 `task_cpu_possible()` 检查是否多余。Dietmar Eggemann 给出肯定推理（`p->cpus_ptr` 恒为 `task_cpu_possible_mask(p)` 子集，与 preferred mask 相交不可能引入架构上不可运行的 CPU），作者 Shrikanth Hegde 愿意据此在 v12 删掉该检查，但以"我担心有例外才加的防御"反问，**当日 Dietmar 未回复，问题悬空**。

## 背景与问题
该系列（Shrikanth Hegde, IBM）为虚机场景引入 preferred CPUs 与基于 steal time 的 vCPU 退避。v11（08-25，见 sched-20260825-001）曾加入/讨论过 32-bit 任务的特判。08-27 的线程挂在 v10 cover 下继续：焦点是 preferred mask 与异构架构约束（部分 Arm64 SoC 的 asymmetric AArch32 EL0——32-bit 用户态只能在部分核运行）能否自然组合。

## 技术方案
Dietmar 的分析：若要让 `cpu_preferred_mask` 与 AArch32-EL0 特性配合，需把

```
- return cpumask_intersects(p->cpus_ptr, cpu_preferred_mask);
+ return cpumask_first_and_and(p->cpus_ptr, cpu_preferred_mask,
+                               task_cpu_possible_mask(p)) < nr_cpu_ids;
```

但他认为**不需要**——对 32-bit Arm 用户态任务，`p->cpus_ptr` 本身就是 `task_cpu_possible_mask(p)` 的子集，交集里不可能出现架构上不可运行的 CPU。Shrikanth 08-27 回复确认理解了 `task_allowed_on_cpu()` 的双重检查语义，仍坚持过"怕有漏网 case 才加防御检查"，并表态：如果 Dietmar 确认 `cpumask_intersects()` 覆盖全部 32-bit 场景，v11 里那个特判就去掉，反问"你觉得呢？"。

## 版本演进与当前进展
- v10：2026-08-12（12 补丁，本线程挂靠版本）。
- v11：08-25（含 32-bit 任务的防御性改动，见 sched-20260825-001）。
- 08-27：v10 线程内完成上述"防御检查是否必要"的一来一回；等待 Dietmar 二次确认才能定 v12 内容。

## Maintainer 意见与讨论焦点
- 认可方向：Dietmar 对核心逻辑无异议，问题只在边界正确性；
- 分歧/未决：`p->cpus_ptr ⊆ task_cpu_possible_mask(p)` 是否**恒**成立（作者担心存在反例，典型如 cpuset 与架构 mask 的组合路径），这决定 v12 是否删代码；
- 无 NAK。当日无其他维护者介入。

## 合入评估
**possible**。系列已演进到 v11 且 review 收敛到局部细节级问题，说明大盘无异议；卡点是这个 32-bit 特判的取舍确认（涉及 Arm 异构 SoC 语义，Dietmar 的二次回复是关键）。对 x86/ARM64 服务器场景（无 AArch32-EL0 限制）无影响，回合判断不受此细节牵制。

## 效果评估
当日无新数据；历史 benchmark（含 v10 阶段 3-5% 回归讨论）见 related_articles。

## 我可以参与的点
- 若手里有开启 CONFIG_SCHED_PROXY/异构 arm64 或 32-bit 兼容的测试环境，可以实测 cpuset 收缩 + v11 组合下 preferred mask 是否会越出 possible mask，直接给 Dietmar 的问题提供数据（这比空讨论集合包含关系有用）。
- OLK/华为 arm64 机型若关注虚机 steal 退避行为，v11 已进入收尾期，是开始评估回合的时点。

## 参考链接
- Dietmar 的分析: https://lore.kernel.org/all/2e1085f1-82f2-42dc-ae72-0bedffb414f3@arm.com/
- Shrikanth 的追问: https://lore.kernel.org/all/0a62143d-6d8d-46a4-ac92-f8ca7268e555@linux.ibm.com/
- 被讨论的 v10 cover: https://lore.kernel.org/all/0f3307c8-6fc9-49b6-93e4-7ffd85dd0c16@linux.ibm.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
