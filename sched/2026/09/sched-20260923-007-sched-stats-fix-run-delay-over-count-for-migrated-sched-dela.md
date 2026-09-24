# sched/stats: Fix run_delay over-count for migrated sched_delayed tasks

## TL;DR
- sched-20260921-006：Wei Yang 的 run_delay 多计数修复 v2 又获 K Prateek Nayak 的 Reviewed-by + Tested-by，评审背书加强，合入概率高。更早 v1 时该修复即被定位为「sched_delayed 任务跨 CPU 迁移时 run_delay 重复累计」。
- sched-20260922-015：Wei Yang 发出 v3——新增收集 Kayra Cizmeci、K Prateek Nayak 的 Reviewed-by 与 K Prateek 的 Tested-by。Peter Zijlstra 回帖提出新问题：proxy execution 是否也存在同类 over-count（是否该用 `t->is_blocked` 判断更合适）。补丁集齐多组 review/test，但 Peter 的问题待回应。
- sched-20260923-007（今天）：针对 Peter 上轮问题，Wei Yang 与 Kayra Cizmeci 给出回应——确认 `proxy_migrate_task()` 经 `activate_task()`（无 `ENQUEUE_RESTORE`）重挂 blocked donor 是同类问题，但 `is_blocked` 不能直接门控（会误伤 `ttwu_runnable()` 的真实唤醒重挂）；作者倾向先复现 proxy 场景再决定是否纳入本补丁。

## 背景与问题
- sched-20260921-006：任务在被迁移且处于 `sched_delayed`（延迟出队）状态时，`run_delay` 统计会被重复累计，导致 `/proc/<pid>/sched` 等接口里 run_delay 数据偏大失真。
- sched-20260922-015：细化根因——DELAY_DEQUEUE 下被迁移的 sched_delayed 任务，`sched_info_enqueue()` 在迁移时错误重挂 `last_queued`，导致真实唤醒时被抑制，整段「迁移→唤醒」睡眠时长被计入 run_delay。
- sched-20260923-007（今天）：Peter 上轮追问 proxy execution 是否同类，本日聚焦此点展开。

## 技术方案
- sched-20260921-006：修复思路为对迁移到别的 CPU 的 sched_delayed 任务正确结算 run_delay 增量，避免跨 CPU 迁移路径上的重复计数。
- sched-20260922-015：`sched_info_enqueue()` 对 sched_delayed 任务不重挂 `last_queued`（唤醒路径清掉 sched_delayed 后才到该函数，故真实唤醒仍正确重挂，普通 runnable 任务不受影响）。
- sched-20260923-007（今天）：补丁方案不变，聚焦 proxy 场景记账判定——**Wei Yang** 确认 proxy 侧有类似问题（`proxy_migrate_task()` 经 `activate_task()` 无 `ENQUEUE_RESTORE` 重挂 blocked donor 是「假 enqueue」），但 `t->is_blocked` 不能直接门控（`ttwu_runnable()` 里 delayed 任务真实唤醒在 `if (p->is_blocked)` 分支内做 `enqueue_task(ENQUEUE_DELAYED)`，`is_blocked` 要到 `ttwu_do_wakeup()` 才清掉，用 `!is_blocked` 抑制会恰好压制本补丁依赖的重挂）；`task_is_blocked()` 可作 proxy 场景附加条件、但不能替代 `se.sched_delayed`。**Kayra Cizmeci** 确认 `is_blocked` 只在 `try_to_block_task()` 置 1，倾向用 `task_is_blocked()`，但自陈「proxy + delayed 把脑子绕晕了」请他人校正。

## 版本演进与当前进展
- v3（09-22）之后，本日无新版；讨论仍在澄清 proxy 场景的记账语义。

## Maintainer 意见与讨论焦点
Peter 上轮的问题（proxy 同类问题、`is_blocked` 是否更合适）本日得到作者与测试者的正面回应，确认「proxy 侧确有同类 over-count」，但对「是否、如何把 proxy 场景纳入本补丁」尚未定论，Wei Yang 明确想先复现确认。无 NAK。

## 合入评估
likelihood=high（delayed 场景部分）：补丁本身集齐 Chen Yu/Kayra/K Prateek 的 Reviewed-by 与 K Prateek 的 Tested-by，delayed 修复路径清晰；唯一悬而未决的是是否要在同一补丁里顺带处理 proxy 场景。blocking_issues：proxy 场景是否纳入本补丁未定；若纳入需先复现确认 donor run_delay 语义。next_action：作者决定 delayed-only 或扩到 proxy 场景，回应 Peter 后即可合。

## 效果评估
无本日新增 benchmark；为统计记账正确性修复（修复使 sched_delayed 任务迁移期间的睡眠时长不再被误计入 run_delay）。

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
    review_outcome: 'v2 收 Chen Yu Reviewed-by；获 K Prateek Reviewed-by + Tested-by'
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