---
id: sched-20261106-009
date: 2026-11-06
subject: 'sched: Remove CONFIG_RT_GROUP_SCHED'
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: <20261105164724.yxONBd03@linutronix.de>
lore_url: https://lore.kernel.org/all/20261105164724.yxONBd03@linutronix.de/
authors:
- Sebastian Andrzej Siewior
maintainers_involved:
- Peter Zijlstra
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261105164724.yxONBd03@linutronix.de>
  date: 2026-11-06
  summary: 移除 CONFIG_RT_GROUP_SCHED（-1438 行）。
  review_outcome: 删除被搁置，改为标记 BROKEN + 等 HCBS。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - Peter 记得有真实用户，删除需 HCBS 替代就位
  - 需通过标记 broken 试探依赖方
  next_action: 作者改发标记 CONFIG_RT_GROUP_SCHED 为 BROKEN 的补丁
contribution_opportunities:
- kind: discussion
  description: 依赖 CONFIG_RT_GROUP_SCHED 的团队在标记 broken 窗口期发声
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 9
related_articles: []
tags:
- rt
- rt_bandwidth
- cgroup
title: 'sched: Remove CONFIG_RT_GROUP_SCHED'
layout: article
---

## TL;DR

Sebastian Andrzej Siewior 提议删除 `CONFIG_RT_GROUP_SCHED`（-1438 行）：它「broken beyond repair」，启用后无法给任务设 SCHED_FIFO/RR（cgroup 无 runtime 可分配、cgroup v2 根本不能分配 runtime）、SCHED_DEADLINE 准入也卡死，主流发行版（Debian/OpenSuse/Fedora/Arch）全部默认关闭。讨论结果是**不直接删除**——Peter Zijlstra 想删但记得有人用过、需先有 HCBS 替代；Tejun Heo 建议渐进弃用。最终 Peter 提出「先标记 BROKEN，看这次谁叫」，Sebastian 同意先这么试。方向从「删除」收敛为「标记 broken + 等 HCBS」。

## 背景与问题

`RT_GROUP_SCHED` 允许按 cgroup 层级限制 RT 任务的 CPU 带宽，但实现早已腐坏：启用后设 SCHED_{FIFO,RR} 会因 cgroup 无 runtime 分配而失败；cgroup v2 下无法分配 runtime；root group 占满 runtime 导致 `sched_rt_runtime_us` 全局 sysctl 也无法下调。SCHED_DEADLINE 能设，但准入控制卡死、只能靠 `-1` 禁用。Sebastian 的判断是不值得修：DL fair server 已经承担了 RT throttling，专职的 Hierarchical Constant Bandwidth Server（HCBS）工作也在进行中，用于把多个 RT 任务收进一个 deadline 配置。

## 技术方案

补丁直接移除 `CONFIG_RT_GROUP_SCHED`：删 `kernel/sched/rt.c` 的 925 行、autogroup/deadline/debug 侧的关联代码，以及 `sched-rt-group.rst` 文档，共 17 文件 +15/-1438。讨论后方向调整为渐进式：Sebastian 将改发「标记 BROKEN」的版本（先 `BROKEN` 试探是否有人依赖，再考虑删除），Peter 认可「先标记 broken、看谁叫」。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出，移除版）*。当日即转为「标记 broken」路线，删除版实质被搁置，作者将改发 BROKEN 版本。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：「我很想真的删掉它，但 IIRC 确实有人用过……我们需要用『那个东西』（HCBS）替代它」。对 Sebastian「没人能用」的质疑，他回「For some definition of 'work'」，最终松口「We can try marking it broken; see who screams this time ;-)」。
- **Tejun Heo**：不反对，但建议渐进——先 DEPRECATED + 藏到 EXPORT 一段时间，再 BROKEN，最后删除，给依赖方发声的机会。
- **Sebastian**：质疑「留着这个没人能用的东西」的意义，澄清其 SMP 下记账错位/抢占不正常的现象，最终接受「标记 broken」路线。

无 NAK，但删除被推迟为「标记 broken + 等 HCBS」。

## 合入评估

*likelihood=low*（针对「直接删除」而言）。删除方向未被采纳，改为「标记 BROKEN」的渐进方案。*blocking_issues*：① Peter 记得有真实用户、删除需 HCBS 替代就位；② 需通过「标记 broken」试探依赖方。*next_action*：作者改发「标记 CONFIG_RT_GROUP_SCHED 为 BROKEN」的补丁，等待 HCBS 工作成熟。

## 效果评估

无运行时效果数据。动议的价值诉求是「删除腐坏代码、-1438 行」，但对「是否有人真实依赖」无数据支撑——Sebastian 自述「没有人回来说明坏在哪」，Peter 则凭记忆认为有人用过。双方均无硬数据。

## 我可以参与的点

- **discussion**：如果你所在团队/产品依赖 CONFIG_RT_GROUP_SCHED（哪怕个别配置），在「标记 broken」期间发声是社区明确想要的信号——这是 Peter 与 Tejun 留给依赖方的窗口。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261105164724.yxONBd03@linutronix.de/
- 前置讨论（补丁内引用）: https://lore.kernel.org/all/20261023161348.t3lpPLQZ@linutronix.de/
