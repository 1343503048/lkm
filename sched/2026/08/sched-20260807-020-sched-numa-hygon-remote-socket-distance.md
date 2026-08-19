# sched numa hygon remote socket distance

## 概述

Chaohong Guo 提交 v3 的 2 片系列，为 Hygon model 7 在构建调度域时对远端 socket 节点应用平均距离，修正错误的跨 socket 节点合并。

## 背景

commit `4d6dd05d07d0`（"sched/topology: Fix sched domain build error for GNR, CWF in SNC-3 mode"）在构建调度域时对远端 socket 节点引入平均距离，把远端 socket NUMA 节点归为同一调度组，改善负载均衡决策。Hygon model 7 每个 package 最多 6 个 die，开启 NPS（NUMA per socket）时每 package 暴露 6 个 NUMA 节点，遇到与 GNR/CWF 相同问题：当前域构建会错误地把不同 socket 的节点在更高 NUMA 层级合并，导致负载均衡时远端 socket CPU 选择次优。

## 变更

将 GNR/CWF 的"远端 socket 平均距离"做法扩展到 Hygon model 7，使远端 socket 节点不再被错误合并进同一调度组。

## 状态

v3，处于评审阶段。

## 参考链接

- 系列：uid 25979 / 25980

---
subject: "sched/numa: 为 Hygon model 7 应用远端 socket 距离平均"
date: 2026-08-07
series: "sched-numa-hygon"
version: "v3"
status: "in-review"
tags: [numa_balancing, topology, load_balance]
related_articles: []
submitter: "Chaohong Guo"
emails:
  - uid: 25979
    subject: "[PATCH v3 0/2] sched/numa: apply remote socket distance averaging for Hygon"
  - uid: 25980
    subject: "[PATCH v3 1/2] ... (related)"
---
