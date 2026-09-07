# sched/deadline: Fix DL server divide-by-zero for inactive CPUs

## TL;DR
Hui Su 对 8 月 12 日发出的 DL server 除零修复发出 gentle ping：该补丁**已获 Juri Lelli 的 Acked-by**，正等 Peter/Ingo 收取。当日线程无新增技术内容，信息价值集中在合入状态——deadline server 激活路径在 CPU 非活跃时除零的问题已被维护者背书。补丁本体与复现细节不在本日缓存（原文 08-12 发出），此处不重复转述。

## 背景与问题
DL server（sched_dl_entity 承载 RT 任务的 deadline 服务）在 CPU inactive/离线场景下，`replenish_dl_entity()` 相关预算计算存在除零路径。完整背景见原帖（references 根 `<20260812123252.2355986-3-sh_def@163.com>`，未获取到正文）。

## 技术方案
本日邮件未重述方案。仅知修复针对"inactive CPUs"的除零。

## 版本演进与当前进展
- 2026-08-12：作者发出补丁（同系列似为多补丁，msg 尾号 -3-）。
- 此前：Juri Lelli 给出 Acked-by（其回帖即本 ping 的父消息 `<an2BH9a8PWlZUGj6@jlelli-thinkpadt14gen4.remote.csb>`）。
- 08-27：作者 ping "Gentle ping on this fix. Juri has provided an Acked-by."，无其他人跟进。

## Maintainer 意见与讨论焦点
Juri（deadline 侧维护者之一）已 Ack；Peter/Ingo 未动作。无未解决分歧。

## 合入评估
**likely**。单点正确性修复 + 领域维护者 Ack + 无 NAK，处于待收取状态；若两周内无动作，作者的下一封 ping 或他人补 Reviewed-by 是常规推进方式。`next_action`：进 tip/sched（或 urgent，若被定性为可触发崩溃）。

## 效果评估
无数据。除零属可判定的正确性问题，是否已有真实崩溃报告在缓存内未获取到。

## 我可以参与的点
- OLK-6.6 若启用 dl_server（RT 走 deadline server 的架构），该修复与姊妹补丁（sched-20260827-017）是明确的回合候选；等 tip 落地后按 Fixes 标签对号回合即可。
- 补 Reviewed-by/Tested-by 空间不大——已有 Ack。

## 参考链接
- 本日 ping: https://lore.kernel.org/all/20260827101613.2664218-1-sh_def@163.com/
- Juri 的 Acked-by 回帖: https://lore.kernel.org/all/an2BH9a8PWlZUGj6@jlelli-thinkpadt14gen4.remote.csb/
- 原补丁（08-12，据 references 还原）: https://lore.kernel.org/all/20260812123252.2355986-3-sh_def@163.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260827-016
date: '2026-08-27'
subject: "sched/deadline: Fix DL server divide-by-zero for inactive CPUs"
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: "<20260812123252.2355986-3-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/20260827101613.2664218-1-sh_def@163.com/"
authors: [Hui Su]
maintainers_involved: [Juri Lelli]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260812123252.2355986-3-sh_def@163.com>"
    date: 2026-08-12
    summary: "修复 DL server 在 inactive CPU 上的除零（方案细节未获取到）"
    review_outcome: "Juri Lelli Acked-by；08-27 作者 ping，待 Peter/Ingo 收取"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "维护者收取进 tip"
contribution_opportunities:
  - kind: testing
    description: "OLK-6.6 启用 dl_server 的机型验证该除零路径是否存在"
generated_at: "2026-09-07T22:05:00"
source_email_count: 1
related_articles: [sched-20260827-017]
tags: [deadline, dl_server]
---
