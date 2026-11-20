# sched: restore preferred CPUs when hotplug removes the last one

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261119-011：Yury Norov 的 7 补丁系列 patch 2/7 在 hotplug 移除最后一颗 preferred CPU 时恢复集合；Shrikanth Hegde 建议日志用 `pr_warn`。
- sched-20261120-019（今天）：**Yury 拒绝 pr_warn**——「Warning 暗示需要用户调查的异常，Notice 才是值得注意但正常的事」；从调度视角这是完全可恢复情形，消息本就是描述它，没什么好 warn 的。

## 背景与问题

（承接）preferred CPU 机制的边界情形：hotplug 把最后一颗首选 CPU 下线后需要恢复集合。补丁正文未在当日缓存，仅从 review 邮件可推断其含一处日志打印；Shrikanth 建议改用 `pr_warn` 与内核「异常但可恢复」路径的告警惯例一致。

## 技术方案

今日为日志级别之辩、无代码：Yury 从语义上区分 warning（异常、可能需用户调查）与 notice（值得注意但正常），主张该 hotplug 恢复属后者，维持 notice 级别即可。

## 版本演进与当前进展

*current_version: v1（2026-11-13，patch 2/7，系列 cover `<20261113184257.621707-1-ynorov@nvidia.com>`）*。今日仅日志级别的一条往返，无新版本。

## Maintainer 意见与讨论焦点

- **Yury Norov（作者）**：拒绝 `pr_warn`，主张 notice 语义。
- **Shrikanth Hegde（IBM，社区评审）**：建议 `pr_warn`。
- 无维护者（Peter/Ingo）当日表态；无 NAK。

## 合入评估

*likelihood=unknown*。日志级别之争不影响方案本身，但补丁/系列正文仍未捕获、无维护者表态，合入走向证据不足。*blocking_issues*：补丁与系列全貌未捕获。*next_action*：日志级别达成一致后作者继续推进；后续补齐系列上下文再评估。

## 效果评估

无数据（补丁正文未获取到）。

## 我可以参与的点

- **review**：核对「hotplug 移除最后一颗 preferred CPU」的恢复逻辑是否覆盖所有 hotplug 顺序与 `set_affinity` 交错；就日志级别（notice vs warn）给出判断。

## 参考链接

- lore thread（Yury 回复）: https://lore.kernel.org/all/av8n5_x8WghrGbTb@yury

---
id: sched-20261120-019
date: '2026-11-20'
subject: "sched: restore preferred CPUs when hotplug removes the last one"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261113184257.621707-1-ynorov@nvidia.com>"
lore_url: "https://lore.kernel.org/all/av8n5_x8WghrGbTb@yury"
authors: [Yury Norov]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261113184257.621707-1-ynorov@nvidia.com>"
    date: '2026-11-13'
    summary: "7 补丁系列：hotplug 移除最后一颗 preferred CPU 时恢复集合"
    review_outcome: "Shrikanth 建议 pr_warn，Yury 拒绝（notice 语义）"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["补丁与系列全貌未捕获"]
  next_action: "日志级别一致后作者继续推进；后续补齐系列上下文"
contribution_opportunities:
  - kind: review
    description: "核对恢复逻辑覆盖所有 hotplug 顺序与 set_affinity 交错，判断日志级别"
generated_at: "2026-11-21T09:00:00+08:00"
source_email_count: 216
related_articles: [sched-20261119-011]
tags: [affinity, topology]
---