# sched: restore preferred CPUs when hotplug removes the last one

## TL;DR

Yury Norov（NVIDIA）7 补丁系列（11/13 发出）的 patch 2/7：当 hotplug 移除最后一颗 preferred CPU 时恢复 preferred CPU 集合，避免任务失去首选 CPU 后行为退化。今日仅捕获到 Shrikanth Hegde（IBM）的一条简短评审「pr_warn instead?」——即建议把该路径的日志级别改用 `pr_warn`。补丁正文与 cover 未在本日缓存中获取到，系列全貌（7 补丁各自内容）证据不足。

## 背景与问题

preferred CPU 机制（Yury 此前的 steal governor / preferred CPU 基础设施的延伸）给任务/负载指定首选 CPU 集合；当 hotplug 把最后一颗首选 CPU 下线时，需要把集合恢复到可用状态，否则任务可能失去首选锚点、调度退化。补丁针对这一边界情形做恢复。

## 技术方案

仅从 review 邮件可推断：补丁在「hotplug 移除最后一颗 preferred CPU」时执行恢复逻辑，并含一处日志打印；Shrikanth 建议该打印用 `pr_warn`（而非当前的 `pr_info`/其他级别），与内核里同类「异常但可恢复」路径的告警惯例一致。具体代码未获取到。

## 版本演进与当前进展

*current_version: v1（2026-11-13，patch 2/7 的 `thread_root_msgid` 见下）*。今日仅捕获 patch 2/7 的一条评审，其余 6 枚补丁与 cover 未获取到。

## Maintainer 意见与讨论焦点

- **Shrikanth Hegde（IBM，社区评审）**：建议日志用 `pr_warn`。
- 无维护者（Peter/Ingo）当日表态；未见 NAK。

## 合入评估

*likelihood=unknown*。证据过少（仅一条日志级别评审、无补丁正文、无维护者表态），不足以判断合入走向。*blocking_issues*：补丁与系列全貌未捕获。*next_action*：作者按 Shrikanth 意见调整日志级别并继续推进；后续需补齐系列上下文再评估。

## 效果评估

无数据（补丁正文未获取到）。

## 我可以参与的点

- **review**：核对「hotplug 移除最后一颗 preferred CPU」的恢复逻辑是否覆盖所有 hotplug 顺序与 `set_affinity` 交错；就日志级别（pr_warn vs 现状）给出判断。

## 参考链接

- lore thread（patch 2/7）: https://lore.kernel.org/all/20261113184257.621707-3-ynorov@nvidia.com/
- Shrikanth 评审: https://lore.kernel.org/all/1da4ec68-6432-4e2d-b435-0761dffb19a1@linux.ibm.com/

---
id: sched-20261119-011
date: '2026-11-19'
subject: "sched: restore preferred CPUs when hotplug removes the last one"
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<20261113184257.621707-3-ynorov@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20261113184257.621707-3-ynorov@nvidia.com/"
authors: [Yury Norov]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261113184257.621707-3-ynorov@nvidia.com>"
    date: '2026-11-13'
    summary: "hotplug 移除最后一颗 preferred CPU 时恢复 preferred CPU 集合"
    review_outcome: "Shrikanth 建议日志用 pr_warn"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["补丁与系列全貌未捕获"]
  next_action: "作者按 Shrikanth 意见调整日志级别；补齐系列上下文再评估"
contribution_opportunities:
  - kind: review
    description: "核对恢复逻辑是否覆盖 hotplug 顺序与 set_affinity 交错"
generated_at: "2026-11-20T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [affinity, topology]
---