# sched/deadline: check start_dl_timer expiry with ktime_before()

## TL;DR
Liang Hao 的 v1 小品：把 `start_dl_timer()` 的"过去到期"检测从 `ktime_us_delta(act, now) < 0` 改为 `ktime_before(act, now)`，使判定与 `act`/`now` 使用同一分辨率（ktime_t），避免微秒取整导致的边界误差。纯清理/正确性改进。

## 背景与问题
`start_dl_timer()` 在 DL 任务设置 hrtimer 前，需判断是否 deadline 已过（落在过去），若是则直接返回 0 不启动定时器。原代码用 `ktime_us_delta(act, now) < 0`，即把 ktime_t 先转成微秒再比较。由于 `ktime_us_delta` 会做除法取整，`act == now` 或两者差距在亚微秒量级时，取整可能让 `< 0` 判定与真实 `act` 早于 `now` 的语义不一致（边界毛刺）。

## 技术方案
直接用 `ktime_before(act, now)` 比较 ktime_t，与 `act`/`now` 同分辨率，消除取整误差。单文件单行（+1/-1），无逻辑结构变化。

## 版本演进与当前进展
v1（41925）于 2026-08-16 发出。暂无 review 意见。

## Maintainer 意见与讨论焦点
v1 刚发出，DL 维护者（Peter/Juri/Daniel）尚未回复。

## 合入评估
合入可能性高。改动极小且语义更严谨，通常直接收。需确认 `ktime_before` 在 `act == now` 时返回 false（不视为"过去"），与原 `ktime_us_delta < 0` 在边界一致性。

## 效果评估
消除亚微秒级边界判定误差；无性能数据，纯正确性/整洁性修复。

## 我可以参与的点
- 评审边界相等行为一致性（`ktime_before` 在 `act==now` 返回 false，与原逻辑是否完全等价）。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched/deadline: check start_dl_timer expiry with ktime_before()"
id: sched-20260816-001
date: 2026-08-16
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<uid-41925@qq-imap>"
lore_url: "未获取到"
authors: [Liang Hao]
maintainers_involved: [Peter Zijlstra, Juri Lelli, Daniel Bristot de Oliveira]
current_version: v1
patch_series:
  - version: v1
    msgid: "<uid-41925@qq-imap>"
    date: 2026-08-16
    summary: "start_dl_timer() 过期检测改用 ktime_before()，使过去到期判定与 act/now 同分辨率。"
    review_outcome: "v1 刚发出，暂无 review 意见。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: [单文件单行改动，需 DL 维护者确认语义等价]
  next_action: "等待 DL 维护者 review/apply。"
contribution_opportunities:
  - kind: review
    description: "评审 ktime_before(act, now) 与 ktime_us_delta(act, now) < 0 在边界（恰好相等）行为是否一致。"
generated_at: "2026-08-17T00:10:00"
source_email_count: 1
related_articles: []
tags: [deadline]
---
