---
subject: 'sched/fair: NOHZ 负载均衡优先选择完全空闲核心'
date: 2026-08-07
series: sched-fair-nohz-fully-idle
version: v4
status: in-review
tags:
- sched/fair
- nohz
- load_balance
related_articles: []
submitter: 社区
emails:
- uid: 26834
  subject: 'Re: [PATCH v4] sched/fair: prefer fully idle cores for NOHZ balancing'
title: sched fair nohz fully idle cores
layout: article
---

## 概述

延续前几日的 "sched/fair: prefer fully idle cores for NOHZ balancing" 系列，本批为 v4 的评审回复（Re），围绕 NOHZ 负载均衡在选择目标核心时如何优先挑选"完全空闲"（核心内所有 SMT 兄弟均空闲）的核心进行讨论。

## 背景

NOHZ 负载均衡在 tickless CPU 上周期性地决定把任务迁往何处。优先选择完全空闲的核心（而非仅部分兄弟空闲）可减少跨 SMT 干扰、提升缓存局部性。

## 状态

v4，已进入评审回复阶段，讨论聚焦于实现细节与对其他负载均衡路径的影响。

## 参考链接

- 邮件：uid 26834
