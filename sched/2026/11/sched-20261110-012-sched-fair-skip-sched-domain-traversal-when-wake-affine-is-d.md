# sched/fair: Skip sched-domain traversal when wake affine is disabled

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261109-010：Srikar Dronamraju 发单补丁，把 `select_task_rq_fair()` 里 `want_affine == false`（`wake_wide()` 为真或醒来的 CPU 不在任务允许 mask 内）的 TTWU wakeup 直接跳入既有快路径、省掉「进入 sched-domain 遍历随即 break」的无谓开销。Kayra 当日指出 `SD_BALANCE_WAKE` 实际从未被设置，并给出一个更直接的替代改法。
- sched-20261110-012（今天）：**Kayra 深化质疑**——找到一个反例：prev_cpu 落在第一个域、该域设 `SD_WAKE_AFFINE|SD_BALANCE_FORK` 而下一域只设 `SD_WAKE_AFFINE` 时，补丁会把 sd 置 NULL 直接返回 new_cpu，而旧代码会进入该域的慢路径；作者认可「fair point」并解释代码其实是用 `WF_TTWU` 代指 SD_BALANCE_WAKE（`WF_TTWU=0x08 /* maps to SD_BALANCE_WAKE */`），当 WF_TTWU 置位时本就该走快路径、慢路径是留给 WF_FORK/WF_EXEC 的。

## 背景与问题

（承接 sched-20261109-010）`select_task_rq_fair()` 里 `want_affine == false` 的 wakeup 已按快路径处理，但仍会进入 sched-domain 遍历后几乎立即 break。补丁把这类 wakeup 完全跳过遍历。今日的讨论焦点是「跳过遍历是否改变既有慢路径行为」——Kayra 构造了「第一个域只设 SD_BALANCE_FORK、下一个域才设 SD_WAKE_AFFINE」的场景来验证。

## 技术方案

（承接）补丁四点清理：把 `want_affine` 移进使用它的 WF_TTWU 块；`want_affine == false` 时跳过 sched-domain 遍历；删掉 SD_WAKE_AFFINE 检查里冗余的 `want_affine` 判断；删对应 `!want_affine` 循环终止逻辑。今日 Kayra 的反例提示：旧代码在 WF_TTWU 块之前还有一个「寻找到 SD_BALANCE_WAKE 域」的循环，若跳过遍历导致「本应落在慢路径（WF_FORK/WF_EXEC）的 wakeup 被一并快路径化」，行为就不只「去掉无用遍历」。作者澄清 WF_TTWU 与 SD_BALANCE_WAKE 的映射关系，主张快/慢路径由 WF_* 标志决定、补丁不改变语义。

## 版本演进与当前进展

*current_version: v1（2026-11-09，`<20261109120522.1704752-2-srikar@linux.ibm.com>`）*。今日无新版本，为作者与 Kayra 的语义澄清回合；作者尚未出新版。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci**：连续两日紧盯 `SD_BALANCE_WAKE` 未被设置这一前提，并给出跨域慢路径反例，要求作者澄清跳遍历是否改变 WF_FORK/WF_EXEC 慢路径行为。
- **Srikar Dronamraju（作者）**：认可 Kayra 的「fair point」，并用 `WF_TTWU==SD_BALANCE_WAKE` 的宏定义做辩护，主张快路径判定由 WF_* 决定。作者是否据此改补丁或补说明尚未明确。
- 无维护者（Peter/Vincent）表态；分歧集中在语义是否守恒，仍在澄清。

## 合入评估

*likelihood=unknown*。优化动机小（少一次几乎立刻 break 的遍历），但 Kayra 连续质疑其语义前提，尚无维护者背书，是否值得合入存疑。*blocking_issues*：① Kayra 的跨域慢路径反例未获作者用改补丁方式回应；② 无维护者表态确认优化价值。*next_action*：作者就 Kayra 反例澄清或修订补丁（明确 WF_TTWU/WF_FORK/WF_EXEC 下跳过遍历的行为不变），并争取维护者评审。

## 效果评估

无性能数据。作者未给出跳过遍历的可测量收益，属「微小 hot path 优化」且收益存疑。

## 我可以参与的点

- **review**：验证 Kayra 构造的反例（第一个域只 SD_BALANCE_FORK、下一域才 SD_WAKE_AFFINE）下补丁是否真的改变慢路径行为——这是当前唯一未决的正确性问题。

## 参考链接

- Kayra 的反例: https://lore.kernel.org/all/avH3rQ4W6d4jfny2@scheduler.schedules/
- 作者对 WF_TTWU 的澄清: https://lore.kernel.org/all/avH1WCeG9_O83U7N@linux.ibm.com/
- 作者认可 fair point: https://lore.kernel.org/all/avJzqQEpKdU-GPrQ@linux.ibm.com/

---
id: sched-20261110-012
date: '2026-11-10'
subject: "sched/fair: Skip sched-domain traversal when wake affine is disabled"
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<avH3rQ4W6d4jfny2@scheduler.schedules>"
lore_url: "https://lore.kernel.org/all/avH3rQ4W6d4jfny2@scheduler.schedules/"
authors: [Srikar Dronamraju]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261109120522.1704752-2-srikar@linux.ibm.com>"
    date: '2026-11-09'
    summary: "want_affine==false 的 wakeup 跳过 sched-domain 遍历"
    review_outcome: "Kayra 给出跨域慢路径反例，作者澄清 WF_TTWU 语义"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "Kayra 的跨域慢路径反例未获改补丁回应"
    - "无维护者表态确认优化价值"
  next_action: "作者澄清/修订补丁，并争取维护者评审"
contribution_opportunities:
  - kind: review
    description: "验证 Kayra 构造的跨域反例下补丁是否改变慢路径行为"
generated_at: "2026-11-11T09:00:00+08:00"
source_email_count: 3
related_articles: [sched-20261109-010]
tags: [cfs, load_balance, affinity]
---