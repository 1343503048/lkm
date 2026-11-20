---
id: sched-20261120-018
date: '2026-11-20'
subject: 'sched: Limit sysctl sched_rt_{period|runtime}_us to RT_GROUP_SCHED'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261113-sched_dl-v3-6-a76ffa1cdeee@linutronix.de>
lore_url: https://lore.kernel.org/all/awBiDzEvUch_5ZJn@jlelli-thinkpadt14gen4.remote.csb/
authors:
- Sebastian Andrzej Siewior
maintainers_involved:
- Juri Lelli
current_version: v3
patch_series:
- version: v3
  msgid: <20261113-sched_dl-v3-6-a76ffa1cdeee@linutronix.de>
  date: '2026-11-13'
  summary: v3 系列 patch 6/8：!RT_GROUP_SCHED 下删除两个 sysctl
  review_outcome: Juri 提议保留文件仅 DL 生效 + pr_warn_once，作者接受并承诺 respin
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 需按折中方案 respin
  - LTP 场景最终行为待确认
  next_action: Sebastian 出 v4（保留文件 + 仅 DL + pr_warn_once）并重验 LTP
contribution_opportunities:
- kind: review
  description: 核对改由 sched_dl_try_boundary 支撑后既有校验语义是否逐位保持兼容
- kind: testing
  description: LTP proc_sched_rt01 于新语义下确认写成功但仅对 DL 生效
generated_at: '2026-11-21T09:00:00+08:00'
source_email_count: 216
related_articles:
- sched-20261119-005
tags:
- deadline
- rt_bandwidth
title: 'sched: Limit sysctl sched_rt_{period|runtime}_us to RT_GROUP_SCHED'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/19/sched-20261119-005-sched-limit-sysctl-sched-rt-period-runtime-us-to-rt-group-sc.html">sched-20261119-005</a>：Sebastian Andrzej Siewior 的 v3 系列 patch 6/8 在 `!RT_GROUP_SCHED` 下删除 `sched_rt_period_us`/`sched_rt_runtime_us` 两个 sysctl；Intel 0day 报 LTP `proc_sched_rt01.fail`。
- <a class="article-ref" href="/lkm/2026/11/20/sched-20261120-018-sched-limit-sysctl-sched-rt-period-runtime-us-to-rt-group-sc.html">sched-20261120-018</a>（今天）：**方案反转**——Juri Lelli 提出「保留文件、改为只作用于 DEADLINE admission control、写时 `pr_warn_once` 提示」的折中；Sebastian 接受（「Doesn't sound bad. Let me respin it with these changes.」）。

## 背景与问题

（承接）两个全局 sysctl 只在 `RT_GROUP_SCHED` 开启时才真正参与 RT 带宽记账；未开启时写它们无效果，但用户普遍误以为能关闭 RT 限流。Sebastian 原方案是删除文件，但 LTP `proc_sched_rt01` 因此 fail，且正如 Juri 指出：删除会让现有用户「失去的是还在工作的旋钮」——5/8 已把 RT 限流功能挪到 sysfs，用户并非省下无用物。

## 技术方案

Juri 的折中（被 Sebastian 接受）：

- 对 `!RT_GROUP_SCHED`，保留 `sched_rt_{period,runtime}_us`，但由新的 `sched_dl_try_boundary()` 同款代码支撑，只对 DEADLINE admission control 起作用；
- 保留现有校验语义（LTP 检查 EINVAL 用例，0 是合法的 runtime）；
- 写时 `pr_warn_once()` 说明「只控制 DEADLINE admission control、RT throttling 由 fair_server 处理」并指向新旋钮位置；
- 文档同步；将来新接口成熟后再讨论废弃 procfs 名。

## 版本演进与当前进展

*current_version: v3（2026-11-13，patch 6/8 的 `thread_root_msgid` 见下）*。今日为方案反转：从「删除文件」改为「保留 + 仅 DL 生效 + 写时告警」。

## Maintainer 意见与讨论焦点

- **Juri Lelli（sched/deadline 维护者）**：同意 RT throttling 部分，但反对直接删除——5/8 已把功能挪到 sysfs，「现有用户失去的是仍在工作的旋钮」；给出「保留 + 仅 DL + pr_warn_once」的具体方案。
- **Sebastian Andrzej Siewior（作者，PREEMPT_RT 维护者）**：接受并承诺据此 respin。
- 无 NAK；此为接口兼容性争议的实质解决。

## 合入评估

*likelihood=medium*。方案已获双方一致（作者 + deadline 维护者），但还需按新方案 respin 系列、且 LTP 用例需随「写仍生效（对 DL）」的新语义重新验证。*blocking_issues*：作者需按折中方案 respin；LTP 场景的最终行为待确认。*next_action*：Sebastian 出 v4（保留文件 + 仅 DL + pr_warn_once），重验 LTP。

## 效果评估

无性能数据；可见效果从「删除文件导致 LTP fail」转为「文件保留但仅对 DEADLINE 生效、写时告警」，对外接口兼容性更好。

## 我可以参与的点

- **review**：核对 `sched_rt_{period,runtime}_us` 改由 `sched_dl_try_boundary()` 支撑后在 `!RT_GROUP_SCHED` 下的既有校验语义（EINVAL、0 合法 runtime）是否逐位保持兼容。
- **testing**：跑 LTP `proc_sched_rt01` 于新语义下确认「写 value 成功但仅对 DL 生效」的预期行为。

## 参考链接

- lore thread（Juri 回复）: https://lore.kernel.org/all/awBiDzEvUch_5ZJn@jlelli-thinkpadt14gen4.remote.csb/
