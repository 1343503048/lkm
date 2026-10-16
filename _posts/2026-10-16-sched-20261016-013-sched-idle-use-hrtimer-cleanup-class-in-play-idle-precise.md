---
id: sched-20261016-013
date: 2026-10-16
subject: 'sched/idle: Use hrtimer cleanup class in play_idle_precise()'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <eccd97b2003a16291817974798cbe98b25b582a0.1792083743.git.sh_def@163.com>
lore_url: https://lore.kernel.org/all/eccd97b2003a16291817974798cbe98b25b582a0.1792083743.git.sh_def@163.com/
authors:
- Hui Su
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v2
  msgid: <eccd97b2003a16291817974798cbe98b25b582a0.1792083743.git.sh_def@163.com>
  date: 2026-10-16
  summary: 改用 CLASS(hrtimer_on_stack, timer) cleanup class 管理 on-stack timer 生命周期
  review_outcome: 待 Peter 复核
upstream_commit: null
fixes_commit: c1de45ca831a
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等 Peter 复核 v2 的 cleanup class 用法后收取
contribution_opportunities: []
generated_at: '2026-10-17T01:30:00'
source_email_count: 1
related_articles:
- sched-20261015-007
tags:
- idle
title: 'sched/idle: Use hrtimer cleanup class in play_idle_precise()'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-007-sched-idle-destroy-on-stack-hrtimer-in-play-idle-precise.html">sched-20261015-007</a>（原题「sched/idle: Destroy on-stack hrtimer in play_idle_precise()」）：Hui Su 修 `play_idle_precise()` 的 on-stack hrtimer 生命周期——`it.timer` 用 `hrtimer_setup_on_stack()` 初始化但返回前未销毁，`CONFIG_DEBUG_OBJECTS_TIMERS` 下残留 debug 对象。K Prateek 给 R-B/T-B，但 Peter Zijlstra 不喜欢点修复，倾向用 `__cleanup()` 做更优雅的接口。
- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-013-sched-idle-use-hrtimer-cleanup-class-in-play-idle-precise.html">sched-20261016-013</a>（今天）：Hui Su 发 v2，**按 Peter 的方向改用 `CLASS(hrtimer_on_stack, timer)` cleanup class** 管理 on-stack timer 生命周期，题目也相应改为「Use hrtimer cleanup class」。

## 背景与问题
（承接 20261015-007）`play_idle_precise()` 里 `it.timer` 经 `hrtimer_setup_on_stack()` 初始化；`CONFIG_DEBUG_OBJECTS_TIMERS` 下会把 timer 注册为 on-stack debug 对象，必须在分配它的函数离开前移除。原 v1 采用「expiry 循环后再手动 `destroy_hrtimer_on_stack()`」的点修复，被 Peter 评价为打补丁式、易误用。

## 技术方案
v2（`kernel/sched/idle.c`，+10/−6）：改用 `CLASS(hrtimer_on_stack, timer)(&it.timer, ...)` cleanup class，把 setup 与 destruction 配对自动完成；timer 用 `HRTIMER_MODE_REL_PINNED_HARD` 启动（hardirq 在当前 CPU 上回调），回调返回 `HRTIMER_NORESTART` 保证在 cleanup 对象拆除 on-stack debug 对象前不被 requeue。这是对 Peter「用 `__cleanup()` 做对的接口」意见的直接落实。

## 版本演进与当前进展
- v1（2026-10-15）：手动 `destroy_hrtimer_on_stack()` 点修复。
- v2（2026-10-16，<eccd97b2003a16291817974798cbe98b25b582a0.1792083743.git.sh_def@163.com>）：改用 `CLASS(hrtimer_on_stack, timer)` cleanup class，标题同步改为「Use hrtimer cleanup class」。

## Maintainer 意见与讨论焦点
Peter Zijlstra 原立场是「hating on this」点修复、倾向 `__cleanup()` 风格生命周期封装；v2 正是按此方向重写，回应了维护者的核心诉求。K Prateek 此前已 R-B/T-B v1。v2 尚无新的 review。

## 合入评估
*likelihood=high*。v2 直接采纳 Peter 建议的 cleanup class 方向，原有阻塞点已解除。*blocking_issues*：无实质阻塞；v2 刚发、待复核。*next_action*：等 Peter 复核 v2 的 cleanup class 用法后收取。

## 效果评估
v1 曾附 hrtimer setup/free oracle PASS 与 bzImage/modules 构建 PASS；v2 无新增数据，属生命周期/调试正确性修复。

## 我可以参与的点
当前阶段 v2 已对齐维护者方向，参与空间有限；可持续观察是否被收取。

## 参考链接
- v2 patch：https://lore.kernel.org/all/eccd97b2003a16291817974798cbe98b25b582a0.1792083743.git.sh_def@163.com/
- 原 v1：https://lore.kernel.org/all/20261015025029.3356060-1-sh_def@163.com/
