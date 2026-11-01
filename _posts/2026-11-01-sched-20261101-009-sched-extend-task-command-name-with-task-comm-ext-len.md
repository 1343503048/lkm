---
id: sched-20261101-009
subject: 'sched: Extend task command name with TASK_COMM_EXT_LEN'
date: 2026-11-01
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261030-tonyk-long_name-v8-4-c9b030332254@igalia.com>
lore_url: https://lore.kernel.org/all/20261030-tonyk-long_name-v8-4-c9b030332254@igalia.com/
authors:
- André Almeida
maintainers_involved: []
current_version: v8
patch_series:
- version: v8
  msgid: <20261030-tonyk-long_name-v8-4-c9b030332254@igalia.com>
  date: 2026-10-30
  summary: TASK_COMM_EXT_LEN 扩展任务命令名；treewide 系列第 4/6 个补丁
  review_outcome: kernel test robot 报告 W=1 构建告警（nouveau snprintf 截断）
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - kernel test robot 报告 W=1 构建告警（nouveau snprintf 截断）待处理
  next_action: 修复 nouveau snprintf 截断告警并等待维护者合入表态
contribution_opportunities:
- kind: new_patch
  description: '修复 nouveau 的 snprintf 截断并加 Reported-by: kernel test robot'
- kind: testing
  description: 在更多 config 上做 W=1 构建，排查其它 TASK_COMM_LEN 定长缓冲区调用点
generated_at: '2026-11-02T09:00:00'
source_email_count: 1
related_articles: []
tags: []
title: 'sched: Extend task command name with TASK_COMM_EXT_LEN'
layout: article
---

## TL;DR

André Almeida 的 treewide 系列（v8，第 4/6 个补丁）用 `TASK_COMM_EXT_LEN` 扩展任务命令名长度。本窗口内 kernel test robot 报告该补丁在 W=1 构建下于 nouveau 驱动触发 snprintf 截断告警，需要作者跟进修复。

## 背景与问题

系列目标是用统一的长度宏替换历史遗留的 `TASK_COMM_LEN`（16 字节）限制与分散的 `get_task_comm()` 使用，支持更长的任务 comm 名。作为 treewide 改动（"treewide: Get rid of get_task_comm"），其副作用是会波及依赖 `TASK_COMM_LEN` 定长缓冲区的调用点。

## 技术方案

`TASK_COMM_EXT_LEN` 扩展 comm 存储与拷贝路径。0-day 报告指出一个具体副作用：`drivers/gpu/drm/nouveau/nouveau_chan.c:343` 的 `snprintf(args->name, __member_size(args->name), "%s[%d]", current->comm, task_pid_nr(current))`，当 `current->comm` 变长后输出可达 4–77 字节，超出 `TASK_COMM_LEN + 16 = 32` 字节的目标缓冲区。

## 版本演进与当前进展

v8（当前，系列第 4/6 个补丁）。v1–v7 不在本次分析窗口内。本窗口内为 0-day 的 W=1 构建告警回帖。

## Maintainer 意见与讨论焦点

本窗口内未获取到维护者回帖，仅有 kernel test robot 的自动化构建告警（建议单独修复时加 `Reported-by: kernel test robot` 与 `Closes` 链接）。

## 合入评估

可能性中等（medium）。系列已迭代到 v8，但仍有 0-day 构建告警待处理，且本窗口内无维护者合入表态。阻塞项：nouveau snprintf 截断告警需修复（或确认无害）。

## 效果评估

无性能数据；0-day 给出 W=1 构建告警：`snprintf` 输出 4–77 字节写入 32 字节目标（`nouveau_channel_ctor`）。

## 我可以参与的点

- new_patch：修复 nouveau 的 snprintf 截断（加大缓冲区或改用安全截断），并加 `Reported-by: kernel test robot`。
- testing：在更多 config 上做 W=1 构建，排查其它 `TASK_COMM_LEN` 定长缓冲区调用点。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261030-tonyk-long_name-v8-4-c9b030332254@igalia.com/
- 0-day 告警: https://lore.kernel.org/all/202611010746.Qs8jUny8-lkp@intel.com/
