# sched/psi: Prevent stale timer rearm after rtpoll teardown

## 概述

修复 PSI 的 rtpoll（基于 hrtimer 的轮询）在拆除（teardown）后，陈旧定时器仍可能被重新武装的问题。

## 问题

rtpoll 路径依赖 hrtimer 周期性刷新 PSI 状态。若在 teardown 后仍因某些引用/状态未清理而重新武装定时器，会导致已拆除的 PSI 轮询继续触发，可能访问已释放/无效的 poll 状态，造成行为异常或资源未释放。

## 变更

补丁确保 rtpoll teardown 后相关定时器不再被重新武装（正确清理轮询状态与定时器关联）。

## 状态

作为 3 片 PSI 系列的一部分（1/3 与本片），处于评审阶段。

## 参考链接

- 邮件：uid 26538 / 26539

---
subject: "psi: 防止 rtpoll 拆除后陈旧定时器被重新武装"
date: 2026-08-07
series: "psi-rtpoll-teardown"
version: "v1"
status: "in-review"
tags: [psi]
related_articles: []
submitter: "社区"
emails:
  - uid: 26538
    subject: "[PATCH 1/3] psi: prevent stale timer rearm after rtpoll teardown"
  - uid: 26539
    subject: "[PATCH 2/3] ... (related psi fix)"
---
