---
id: sched-20260726-004
date: 2026-07-26
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <uid-499@qq-imap>
lore_url: unknown
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <uid-499@qq-imap>
  date: 2026-07-26
  summary: sched_ext sparse 注解清理三连：新增 scx_cgroup_sched() 读取 cgrp->scx_sched、收敛大部分残留的
    scx_root 直接访问、first_task 比较改用 rcu_access_pointer()。
  review_outcome: 维护者直接应用 1-3 到 sched_ext/for-7.3。
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.3
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已应用到 sched_ext/for-7.3，随该分支进入后续合并窗口即可
contribution_opportunities: []
generated_at: '2026-07-27T01:10:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Sparse annotation cleanups'
layout: article
---

## TL;DR
Tejun Heo 的 sched_ext sparse 注解清理三连补丁，消除 RCU/锁注解告警，已被直接应用到 `sched_ext/for-7.3`。纯代码质量整理，无需额外跟进。

## 背景与问题
sched_ext 中对 `scx_root`、`cgrp->scx_sched` 等 RCU 保护指针存在若干直接访问，未使用规范的 RCU 访问原语，导致 sparse 静态检查报注解告警。这类问题不影响功能，但长期会掩盖真正的 RCU 使用错误，需要清理以保持代码整洁与检查通过。

## 技术方案
三个 patch 分别：新增 `scx_cgroup_sched()` 辅助函数集中处理 `cgrp->scx_sched` 的读取路径；收敛掉大部分残留的 `scx_root` 直接访问，改走带注解的访问方式；把 first_task 的比较改用 `rcu_access_pointer()`（仅比较指针值、不解引用，语义上正是该处需要的原语）。取舍上以最小改动满足 sparse 的注解要求，不改变运行时行为。

## 版本演进与当前进展
单版提交，维护者 Tejun 直接回复 "Applied 1-3 to sched_ext/for-7.3"，已进入分支。

## Maintainer 意见与讨论焦点
无争议。作为 SCX 维护者，Tejun 本人提交并直接 apply，无其他讨论焦点或分歧。

## 合入评估
已合入 `sched_ext/for-7.3`。无阻塞项，随分支推进即可，无需额外动作。

## 效果评估
纯注解/代码质量清理，无运行时行为变化，暂无也无需效果数据。收益为 sparse 检查通过、RCU 使用更规范。

## 我可以参与的点
当前阶段暂无明显参与空间——补丁已合入且为一次性清理，可持续观察 SCX 后续是否还有类似注解债务。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到（已 apply 到 sched_ext/for-7.3）
- stable backport: 未获取到
