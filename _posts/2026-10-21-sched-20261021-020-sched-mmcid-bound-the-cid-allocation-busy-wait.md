---
id: sched-20261021-020
date: 2026-10-21
subject: 'sched/mmcid: Bound the CID allocation busy wait'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/4e6dda6c.4dd0b.1a15c14eb2d.Coremail.xujiakai24@mails.ucas.ac.cn/
authors:
- Jiakai Xu
maintainers_involved:
- Peter Zijlstra
- Thomas Gleixner
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 无复现器
  - Peter 的语义质疑未回应
  next_action: 作者构造复现或回应 Peter 的语义质疑
contribution_opportunities:
- kind: discussion
  description: 参与 mm_cid 耗尽场景构造与语义澄清
generated_at: '2026-10-22T01:30:00'
source_email_count: 1
related_articles:
- sched-20260918-003
tags:
- cgroup
- cfs
title: 'sched/mmcid: Bound the CID allocation busy wait'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-003-sched-mmcid-bound-the-cid-allocation-busy-wait.html">sched-20260918-003</a>：Jiakai Xu 提交修复——为 `mm_get_cid()` 的无界自旋加 32 次重试上限，耗尽返回 `MM_CID_UNSET`；Peter Zijlstra 强烈质疑（"horribly wrong"），认为未解释切换为何不发生、如何不破坏用户态，首版未获认可。
- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-020-sched-mmcid-bound-the-cid-allocation-busy-wait.html">sched-20261021-020</a>（今天）：Thomas（Gleixner）此前追问复现器，作者 Jiakai 回复「很遗憾，我没有这个问题的 reproducer」。对依赖「能否复现」来推进的修复而言，这属不利进展。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-003-sched-mmcid-bound-the-cid-allocation-busy-wait.html">sched-20260918-003</a>）`mm_get_cid()` 无可用 CID 时永久自旋，调用者持 rq 锁/`mm::mm_cid::lock` 且关中断，CID bitmap 耗尽时可升级为 RCU stall / 整机 lockup，模式切换期 fixup 线程与自旋任务互相等待成 livelock。补丁加 32 次重试上限。核心未解问题（Peter 提出）是「为何切换不发生」以及「如何不破坏用户态」；作者今日承认无法提供复现器。

## 技术方案
（承接 v1）`MM_CID_GET_RETRIES 32` 上限 + 耗尽返回 `MM_CID_UNSET` + 各调用点 schedule-in 重试。今日无新代码，仅作者对复现器询问的回应。

## 版本演进与当前进展
*current_version: v1*（无新版本）。

## Maintainer 意见与讨论焦点
Peter Zijlstra 此前 "horribly wrong" 的质疑仍未化解；Thomas Gleixner 追问复现器，作者 Jiakai 明确「没有 reproducer」。这意味着支撑修复的异常场景目前无法实证，Peter 要求的「切换为何不发生」的解释也缺少复现依据。

## 合入评估
*likelihood=low*。修复方向被 Peter 强烈质疑，作者又无法提供复现器，推进受阻。*blocking_issues*：无复现器；Peter 的语义质疑（切换为何不发生、是否破坏用户态）未回应。*next_action*：作者尝试构造复现（如定向触发 CID 耗尽）或回应 Peter 的语义质疑。

## 效果评估
无量化数据；修复的有效性依赖一个作者自己都无法复现的场景。

## 我可以参与的点
- `discussion`：CID（mm_cid）耗尽场景的构造——per-task 稳态模式下如何让 bitmap 耗尽，以及 Peter 质疑的「切换为何不发生」，值得有 mm_cid 使用经验的开发者参与澄清。

## 参考链接
- Jiakai 的「无 reproducer」回复：https://lore.kernel.org/all/4e6dda6c.4dd0b.1a15c14eb2d.Coremail.xujiakai24@mails.ucas.ac.cn/
