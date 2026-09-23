# sched/stats: Fix run_delay over-count for migrated sched_delayed tasks

## TL;DR
本文为增量更新，完整背景见 sched-20260922-015（v3）。针对 Peter Zijlstra 上轮提出的「proxy execution 是否也有同类 over-count、是否该用 `t->is_blocked` 判断」，Wei Yang 与 Kayra Cizmeci 今日给出回应：确认 `proxy_migrate_task()` 经 `activate_task()`（无 `ENQUEUE_RESTORE`）重挂 blocked donor 是同类问题，但 `is_blocked` 不能直接门控（会误伤 `ttwu_runnable()` 的真实唤醒重挂）；作者倾向先复现 proxy 场景再决定是否纳入本补丁。

## 背景与问题
背景见 sched-20260922-015：DELAY_DEQUEUE 下被迁移的 sched_delayed 任务，`sched_info_enqueue()` 在迁移时错误重挂 `last_queued`，导致真实唤醒被抑制、整段「迁移→唤醒」睡眠时长被计入 run_delay。Peter 上轮追问 proxy execution 是否同类。

## 技术方案
补丁本身方案不变（见 sched-20260922-015）。本日聚焦 proxy 场景的记账判定：

- **Wei Yang**：确认 proxy 侧有类似问题——`proxy_migrate_task()` 经 `activate_task()`（无 `ENQUEUE_RESTORE`）重挂 blocked donor，是一次「不应更新 `last_queued` 的假 enqueue」。但 `t->is_blocked` 不能直接门控：`ttwu_runnable()` 里 delayed 任务的真实唤醒在 `if (p->is_blocked)` 分支内做 `enqueue_task(ENQUEUE_DELAYED)`，`is_blocked` 要到之后的 `ttwu_do_wakeup()` 才清掉；若用 `!is_blocked` 抑制，会恰好压制本补丁依赖的重挂、导致 run_delay 永不被记账。
- **Wei Yang** 同时指出 `task_is_blocked()` 可用于 proxy 场景（每个 waker 唤醒前都清 `blocked_on`，真实唤醒 enqueue 上不应置位），但它不能替代 `se.sched_delayed`（delayed sleeper 根本没有 `blocked_on`），只能作附加条件。作者倾向先复现 proxy 场景、确认 donor 的 run_delay 该如何记账（blocked on mutex 的时长应像 delayed sleep 一样丢弃，还是另算），再决定本补丁是否只聚焦 delayed 场景。
- **Kayra Cizmeci**：确认 `is_blocked` 只在 `try_to_block_task()`（仅 `__schedule` 调用）置 1，并附 `!task_is_blocked()` 的 `should_block` 参数逻辑；倾向用 `task_is_blocked()` 判断，但也自陈「proxy + delayed 把脑子绕晕了」，请他人校正。

## 版本演进与当前进展
- v3（09-22）之后，本日无新版；讨论仍在澄清 proxy 场景的记账语义。

## Maintainer 意见与讨论焦点
Peter 上轮的问题（proxy 同类问题、`is_blocked` 是否更合适）本日得到作者与测试者的正面回应，确认「proxy 侧确有同类 over-count」，但对「是否、如何把 proxy 场景纳入本补丁」尚未定论，Wei Yang 明确想先复现确认。无 NAK。

## 合入评估
likelihood=high（delayed 场景部分）：补丁本身集齐 Chen Yu/Kayra/K Prateek 的 Reviewed-by 与 K Prateek 的 Tested-by，delayed 修复路径清晰；唯一悬而未决的是是否要在同一补丁里顺带处理 proxy 场景。blocking_issues：proxy 场景是否纳入本补丁未定；若纳入需先复现确认 donor run_delay 语义。next_action：作者决定 delayed-only 或扩到 proxy 场景，回应 Peter 后即可合。

## 效果评估
无本日新增 benchmark；为统计记账正确性修复（见 sched-20260922-015）。

## 我可以参与的点
- kind=review：帮助厘清 proxy donor 的 run_delay 应如何记账（blocked-on-mutex 时长是否应像 delayed sleep 一样丢弃），这是作者明确「想先复现确认」的悬置点。
- kind=testing：验证 DELAY_DEQUEUE + proxy execution 组合下的 run_delay 数值（承 sched-20260922-015）。

## 参考链接
- lore（Wei Yang 回复）: https://lore.kernel.org/all/20260923020302.3581908-1-albin_yang@163.com/
- lore（Kayra Cizmeci 回复）: https://lore.kernel.org/all/20260922210819.11803-1-kayracizmeci@gmail.com/
- lore（v3 补丁）: https://lore.kernel.org/all/20260922082432.2987855-1-albin_yang@163.com/

---
id: sched-20260923-007
subject: 'sched/stats: Fix run_delay over-count for migrated sched_delayed tasks'
date: '2026-09-23'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260922082432.2987855-1-albin_yang@163.com>'
lore_url: 'https://lore.kernel.org/all/20260922082432.2987855-1-albin_yang@163.com/'
authors:
  - 'Wei Yang'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v3
patch_series:
  - version: v1
    msgid: null
    date: '2026-09-09'
    summary: '初版'
    review_outcome: '未获取到 v1 原帖细节'
  - version: v2
    msgid: '<20260920043116.1298017-1-albin_yang@163.com>'
    date: '2026-09-20'
    summary: '修正负载均衡描述，收 Chen Yu Reviewed-by'
    review_outcome: '见 sched-20260921-006'
  - version: v3
    msgid: '<20260922082432.2987855-1-albin_yang@163.com>'
    date: '2026-09-22'
    summary: '收集 Kayra、K Prateek Reviewed-by 与 K Prateek Tested-by'
    review_outcome: 'Peter 提出 proxy exec 同类问题，本日作者回应确认同类问题但判定未定'
upstream_commit: null
fixes_commit: '152e11f6df29'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - 'proxy 场景是否纳入本补丁未定，若纳入需先复现确认 donor run_delay 语义'
  next_action: '作者决定 delayed-only 或扩到 proxy 场景并回应 Peter'
contribution_opportunities:
  - kind: review
    description: '厘清 proxy donor run_delay 记账语义（blocked-on-mutex 是否应丢弃）'
  - kind: testing
    description: '验证 DELAY_DEQUEUE + proxy execution 组合下的 run_delay 数值'
generated_at: '2026-09-24T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260922-015
  - sched-20260921-006
tags:
  - cfs
  - sched_debug
---