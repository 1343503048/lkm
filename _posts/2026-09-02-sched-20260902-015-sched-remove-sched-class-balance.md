---
id: sched-20260902-015
date: '2026-09-02'
subject: 'sched: Remove sched_class::balance()'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Peter Zijlstra
- Tejun Heo
- Aaron Lu
- K Prateek Nayak
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: medium_high
  blocking_issues:
  - '同系列 2/7 sched/core: Simplify/fix time updates 中 opt_update_rq_clock()/RQCF_UPDATED
    的处理仍与 Tejun Heo 有分歧'
  - 系列存在 0/2 与 7/7 两种形态，评审对象需对齐
  - sched_ext 侧的实际影响未见独立确认
  next_action: 跟进 2/7 的时间戳简化讨论，并从 sched_ext 使用侧确认移除 balance 回调无功能缺口
contribution_opportunities:
- 从 sched_ext 侧核对移除 sched_class::balance() 后均衡入口是否完整
- 验证 2/7 的 opt_update_rq_clock() 是否放松了 debug 下的 rq clock 更新告警
- 澄清并对齐评审对象（0/2 与 7/7 两种系列形态并存）
source_email_count: 10
related_articles: []
tags:
- sched/core
- load_balance
title: 'sched: Remove sched_class::balance()'
layout: article
---

## TL;DR

Peter Zijlstra 移除 `sched_class::balance()`（7/7 的最后一步）由 sched_ext 维护者 Tejun Heo 在评审。
清理方向没人反对，当天的实际往返发生在同系列的 2/7 `sched/core: Simplify/fix time updates` 上。

## 背景与问题

调度类（sched_class）的 `balance()` 回调历史上用于某个调度类的负载均衡钩子，但现代
实现下已不再需要或被更通用的路径取代。本期（作为 7/7 系列的一部分，Re: UID 72566
对应 `7/7`）移除 `sched_class::balance()`，清理这一遗留接口。

## 技术方案

- `[PATCH 7/7] sched: Remove sched_class::balance()`（UID 72566 Re:），属 7 补丁系列
  的最后一步清理。
- 同日还有相关 `2/7` 的 Re: `sched/core: Simplify/fix time updates`（UID 72934）。

## 版本演进与当前进展

- 当前状态：**under_review**（作为多补丁系列的一部分推进）。
- 合入可能性 medium/high；纯清理，风险低。

## Maintainer 意见与讨论焦点

- Tejun Heo 9/2 07:47 回 7/7（72564，diffstat 可见 `kernel/sched/core.c` 减 23 行，deadline.c、
  fair.c 相应改写）；13:38 又回 2/7（72931），针对新增的 `opt_update_rq_clock()` 与
  `if (!(rq->clock_update_flags & RQCF_UPDATED)) update_rq_clock(rq);` 这段；Peter Zijlstra 22:32 回敬
  （74280）。
- 也就是说真正的意见来自 sched_ext 侧（Tejun），不是 fair/deadline 侧；这与移除 balance 回调会影响
  sched_ext 直接相关。
- 当天无第二种反对声音，无 NAK。

## 合入评估

**中/高**。清理类、Peter 主推、体量小；卡点在 2/7 的时间戳简化与 Tejun 的分歧上，而 2/7 和 7/7 是同一
系列的依赖，必须一起过。另需注意：同一主题在邮件里同时存在 `[PATCH 0/2]` 与 `[PATCH 7/7]` 两种系列形态
（当日各有 Re:），说明 Peter 中途把系列拆过，评审时要认准对象。

## 效果评估

无数据，也不该有——移除未被使用的回调属纯清理，线程内无人报告性能或行为变化。

## 我可以参与的点

- 若你跑 sched_ext：核对移除 `sched_class::balance()` 后 scx 侧的均衡入口是否还完整，这正是 Tejun 关心
  的点， sched_ext 用户目前没人出声。
- 直接看 2/7 的 `opt_update_rq_clock()`：`RQCF_UPDATED` 判断被前置后，debug 下的 clock 更新警告是否会
  变松。这个可以拿实验结论回帖。
- 确认评审对象：`0/2` 与 `7/7` 两种形态并存，避免在错误的版本上回帖。

## 参考链接

- 002 PREEMPT_DYNAMIC 简化 + static key 迁移（同属调度核心清理）
- 007 sched/fair 重做 task_h_load（同属负载均衡相关）
