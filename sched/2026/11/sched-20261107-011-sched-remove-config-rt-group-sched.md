# sched: Remove CONFIG_RT_GROUP_SCHED

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261106-009：Sebastian Andrzej Siewior 提议删除 `CONFIG_RT_GROUP_SCHED`（-1438 行）。讨论结果是**不直接删除**——Peter Zijlstra 想删但记得有人用过、需先有 HCBS 替代；Tejun Heo 建议渐进弃用；最终 Peter 提出「先标记 BROKEN，看这次谁叫」，Sebastian 同意先这么试。
- sched-20261107-011（今天）：**Qais Yousef 回应「我也很想让它被删掉」并给 Pointless-Acked-By**，还透露自己正修 RT throttling 的另一处坏坑却卡在「让 systemd mount cgroup v1 跑测试」上。方向不变：删方向仍 blocked 于 HCBS，先走「标记 BROKEN 试探」。

## 背景与问题

（承接 sched-20261106-009）`RT_GROUP_SCHED` 实现早已腐坏：启用后设 SCHED_FIFO/RR 因 cgroup 无 runtime 而失败、cgroup v2 无法分配 runtime、SCHED_DEADLINE 准入卡死。Sebastian 判断不值得修——DL fair server 已承担 RT throttling，专职 HCBS 工作也在推进。Peter 记得有真实用户、需 HCBS 替代。

今日 Qais Yousef 的补充强化了「腐坏」的证据面：他正尝试修另一处由 RT throttling 引发的坏坑，却被「让 systemd mount cgroup v1 以便跑测试」卡住——侧面印证该功能在真实环境里已难以为继。

## 技术方案

（承接）补丁直接移除 `CONFIG_RT_GROUP_SCHED`（17 文件 +15/-1438 行）。讨论后方向调整为渐进式：改发「标记 BROKEN」版本（先 BROKEN 试探是否有人依赖，再考虑删除）。今日无技术变更。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出，移除版）*。删除版实质被搁置，作者将改发 BROKEN 版本；今日无新版本，仅 Qais 追加背书。

## Maintainer 意见与讨论焦点

- 今日 **Qais Yousef**：「FWIW 我在修另一处 RT throttling 引发的坏坑，却在让 systemd mount cgroup v1 跑测试上撞墙。我也很想让它被删掉 :-)。对整个删除：Pointless-Acked-By: Qais Yousef。」（自嘲「Pointless」是因为删除方向已不在此轮直接推进。）
- 前日 Peter（需 HCBS、改 BROKEN）、Tejun（渐进弃用）、Sebastian（接受 BROKEN 路线）的格局未变。

无 NAK，删除仍被推迟为「标记 BROKEN + 等 HCBS」。

## 合入评估

*likelihood=low*（针对「直接删除」而言）。删除方向未被采纳，改为「标记 BROKEN」渐进方案；今日 Qais 的 Ack 不影响该判断。*blocking_issues*：① Peter 记得有真实用户、删除需 HCBS 替代；② 需通过标记 BROKEN 试探依赖方。*next_action*：作者改发「标记 CONFIG_RT_GROUP_SCHED 为 BROKEN」补丁，等待 HCBS 成熟。

## 效果评估

无运行时效果数据。动议价值诉求是「删除腐坏代码 -1438 行」，对「是否有人真实依赖」仍无硬数据——Sebastian 自述无人回来说明坏在哪，Peter 凭记忆认为有人用过，Qais 的遭遇是间接佐证而非量化证据。

## 我可以参与的点

- **discussion**：如果所在团队/产品依赖 `CONFIG_RT_GROUP_SCHED`，在「标记 BROKEN」期间发声是社区明确想要的信号——这是 Peter 与 Tejun 留给依赖方的窗口。
- **testing/review**：Qais 卡在的「systemd mount cgroup v1 跑 RT throttling 测试」本身是可帮忙的环境问题，可从工具链角度协助。

## 参考链接

- lore thread（Qais Ack）: https://lore.kernel.org/all/au6Ln7JYI1lZll3A@aerith/
- lore thread（系列）: https://lore.kernel.org/all/20261105164724.yxONBd03@linutronix.de/

---
id: sched-20261107-011
date: '2026-11-07'
subject: "sched: Remove CONFIG_RT_GROUP_SCHED"
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: "<20261105164724.yxONBd03@linutronix.de>"
lore_url: "https://lore.kernel.org/all/au6Ln7JYI1lZll3A@aerith/"
authors: [Sebastian Andrzej Siewior]
maintainers_involved: [Peter Zijlstra, Tejun Heo, Qais Yousef]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261105164724.yxONBd03@linutronix.de>"
    date: '2026-11-06'
    summary: "移除 CONFIG_RT_GROUP_SCHED（-1438 行）"
    review_outcome: "删除搁置，改标记 BROKEN + 等 HCBS；Qais 今日 Pointless-Acked-By"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - "Peter 记得有真实用户，删除需 HCBS 替代"
    - "需通过标记 BROKEN 试探依赖方"
  next_action: "作者改发标记 BROKEN 补丁，等 HCBS 成熟"
contribution_opportunities:
  - kind: discussion
    description: "若团队依赖 CONFIG_RT_GROUP_SCHED，在标记 BROKEN 期间发声"
  - kind: testing
    description: "协助解决 systemd mount cgroup v1 跑 RT throttling 测试的环境问题"
generated_at: "2026-11-08T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261106-009]
tags: [rt, rt_bandwidth, cgroup]
---