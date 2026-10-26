---
id: sched-20261026-008
date: 2026-10-26
subject: 'sched/idle: Use hrtimer cleanup class in play_idle_precise()'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <179296483981.4109677.4627894100325642362.tip-bot2@tip-bot2>
lore_url: https://lore.kernel.org/all/179296483981.4109677.4627894100325642362.tip-bot2@tip-bot2/
authors:
- Hui Su
maintainers_involved:
- Thomas Gleixner
current_version: v1
patch_series:
- version: v1
  msgid: <eccd97b2003a16291817974798cbe98b25b582a0.1792083743.git.sh_def@163.com>
  date: 2026-10-16
  summary: 用 hrtimer_on_stack cleanup class 配对 play_idle_precise() 的 timer setup/destroy
  review_outcome: 2026-10-25 Thomas Gleixner 合入 tip/timers/urgent
upstream_commit: bd091346971c88fccd44afd2547d28366f824572
fixes_commit: c1de45ca831a
merged_branch: tip/timers/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 timers/urgent 合入主线
contribution_opportunities: []
generated_at: '2026-10-27T01:00:00'
source_email_count: 1
related_articles: []
tags:
- idle
title: 'sched/idle: Use hrtimer cleanup class in play_idle_precise()'
layout: article
---

## TL;DR
Hui Su 的 `sched/idle` 清理补丁已被 Thomas Gleixner 合入 tip 的 `timers/urgent` 分支（commit `bd091346971c88fccd44afd2547d28366f824572`）：用 `hrtimer_on_stack` cleanup class（`CLASS()`）把 `play_idle_precise()` 里 on-stack hrtimer 的「初始化 + 销毁」配对起来，消除手动 `hrtimer_start` 与 debug 对象销毁之间的生命周期缝隙。属正确性/健壮性改进，已合入 tip，无参与空间。

## 背景与问题
`play_idle_precise()` 用于「任务注入 idle」（idle injection）场景：在栈上建立一个 `hrtimer`（`hrtimer_setup_on_stack`），以 `HRTIMER_MODE_REL_PINNED_HARD` 启动一个定时器，让 CPU 在定时器到期前持续 `do_idle()`。原实现手工配对「栈上 timer 的 setup 与销毁」，其中 hrtimer 的 on-stack debug 对象的销毁时机需要与 timer 的生命周期精确匹配，否则容易留下 on-stack debug 对象未释放或提前释放的隐患。这是内核里正在进行的「用 cleanup class 取代手写 init/destroy 配对」整理工作的一部分。`Fixes: c1de45ca831a`（"sched/idle: Add support for tasks that inject idle"）。

## 技术方案
用 `CLASS(hrtimer_on_stack, timer)(&it.timer, idle_inject_timer_fn, CLOCK_MONOTONIC, HRTIMER_MODE_REL_HARD)` 建立 cleanup 对象，把其作用域（scope）包住「timer 启动 + idle 等待」这段：定时器仍以 `HRTIMER_MODE_REL_PINNED_HARD` 启动，使回调在当前 CPU 上以 hardirq 运行；被中断的任务只在回调返回后才观察到 `it.done`。由于回调返回 `HRTIMER_NORESTART`，timer 不会在 cleanup 对象拆除其 on-stack debug 对象之前被重新入队，保证销毁时机安全。改动仅 `kernel/sched/idle.c` 一个文件，+10/−6。

## 版本演进与当前进展
*current_version: v1*（`<eccd97b2003a16291817974798cbe98b25b582a0.1792083743.git.sh_def@163.com>`，2026-10-16 作者署名）。2026-10-25 由 Thomas Gleixner 提交、2026-10-26 tip-bot 通知合入 `timers/urgent`。

## Maintainer 意见与讨论焦点
Thomas Gleixner 作为 committer 直接收取（签名 `Signed-off-by: Thomas Gleixner`），无分歧、无 NAK、无待解决问题。

## 合入评估
*likelihood=merged*。已合入 tip `timers/urgent`（commit `bd091346971c88fccd44afd2547d28366f824572`），属 cleanup class 等价重构，风险低。*blocking_issues*：无。*next_action*：随 timers/urgent 合入主线（等待并入合并窗口）。

## 效果评估
无运行时 benchmark；属 cleanup class 等价重构（把手动 init/destroy 配对改为 RAII 风格），功能语义不变、无量化收益。

## 我可以参与的点
补丁已合入，当前阶段暂无明显参与空间。自家分支回合时留意 `hrtimer_on_stack` cleanup class 是否已存在于目标内核版本（较老分支无此 helper 时需做等价适配）。

## 参考链接
- tip-bot 合入通知: https://lore.kernel.org/all/179296483981.4109677.4627894100325642362.tip-bot2@tip-bot2/
- gitweb: https://git.kernel.org/tip/bd091346971c88fccd44afd2547d28366f824572
- v1 补丁: https://patch.msgid.link/eccd97b2003a16291817974798cbe98b25b582a0.1792083743.git.sh_def@163.com
