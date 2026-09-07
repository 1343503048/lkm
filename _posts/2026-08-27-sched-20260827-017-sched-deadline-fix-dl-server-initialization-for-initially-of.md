---
id: sched-20260827-017
date: '2026-08-27'
subject: 'sched/deadline: Fix DL server initialization for initially offline CPUs'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260811100612.1408592-2-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20260827102238.2671839-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved:
- Juri Lelli
current_version: v1
patch_series:
- version: v1
  msgid: <20260811100612.1408592-2-sh_def@163.com>
  date: 2026-08-11
  summary: 修复初始离线 CPU 的 DL server 初始化（方案细节未获取到）
  review_outcome: Juri Lelli Acked-by；08-27 作者 ping，待收取
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 维护者收取进 tip
contribution_opportunities:
- kind: testing
  description: 在 CPU 初始离线 + dl_server 配置下验证初始化路径
generated_at: '2026-09-07T22:05:00'
source_email_count: 1
related_articles:
- sched-20260827-016
tags:
- deadline
- dl_server
title: 'sched/deadline: Fix DL server initialization for initially offline CPUs'
layout: article
---

## TL;DR
同作者的姊妹 ping：针对"初始离线 CPU 上 DL server 初始化"的修复（8 月 11 日发出）同样**已有 Juri Lelli 的 Acked-by**，08-27 作者催办，等 Peter/Ingo 收取。与 sched-20260827-016 一起构成 deadline server 在 CPU 热插拔/离线生命周期下的两个正确性补丁。补丁正文细节不在本日缓存，未获取到。

## 背景与问题
DL server 的初始化路径在 CPU 自启动起就处于离线状态时处理不正确（具体症状——是崩溃、还是状态未初始化——原文未在本线程重述）。references 根 `<20260811100612.1408592-2-sh_def@163.com>`。

## 技术方案
本日邮件未重述方案细节。

## 版本演进与当前进展
- 2026-08-11：发出补丁；
- 随后：Juri Lelli Acked-by（父消息 `<anw7IML1xzHys6re@jlelli-thinkpadt14gen4.remote.csb>`）；
- 08-27：ping，无跟进。

## Maintainer 意见与讨论焦点
Juri 已背书；无分歧、无 NAK。

## 合入评估
**likely**。与 016 同一状态机：Ack 在手、待收取。两封大概率同一批进 tip。`next_action`：维护者收取。

## 效果评估
无数据；初始化路径缺陷的可触发性细节未获取到。

## 我可以参与的点
- 与 016 相同：热插拔密集的虚拟化/隔离场景（cpu offline + dl_server）是天然验证田，OLK-6.6 回合时两封成对处理。

## 参考链接
- 本日 ping: https://lore.kernel.org/all/20260827102238.2671839-1-sh_def@163.com/
- Juri 的 Acked-by 回帖: https://lore.kernel.org/all/anw7IML1xzHys6re@jlelli-thinkpadt14gen4.remote.csb/
- 原补丁（08-11，据 references 还原）: https://lore.kernel.org/all/20260811100612.1408592-2-sh_def@163.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
