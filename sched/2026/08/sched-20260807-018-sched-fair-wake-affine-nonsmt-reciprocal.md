# sched/fair: Preserve wake-affine CPU for non-SMT reciprocal sync wakeups

## 概述

延续 "sched/fair: preserve wake-affine CPU for non-SMT reciprocal scenario" 系列，本批为 v4 的评审回复（Re）。围绕唤醒亲和性（wake-affine）在非 SMT 互逆（prev 与 curr 分属不同、非超线程对称 CPU）场景下，如何保留此前选定的 wake-affine CPU 进行讨论。

## 背景

wake-affine 倾向于把被唤醒任务放到与 waker 同缓存/同核的 CPU 上，以利用缓存热度。但在非 SMT 且互逆（waker 与上次被唤醒者 CPU 关系反转）的场景，原有逻辑可能错误地迁移，损失局部性。本系列旨在修正该行为、保留更优的 wake-affine CPU 选择。

## 状态

v4，处于评审回复阶段。

## 参考链接

- 邮件：uid 25792

---
subject: "sched/fair: 在非 SMT 互逆关系下保留 wake-affine CPU"
date: 2026-08-07
series: "sched-fair-wake-affine"
version: "v4"
status: "in-review"
tags: [sched/fair, affinity]
related_articles: []
submitter: "社区"
emails:
  - uid: 25792
    subject: "Re: [PATCH v4] sched/fair: preserve wake-affine CPU for non-SMT reciprocal scenario"
---
