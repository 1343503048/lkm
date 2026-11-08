# sched: core-sched fixes and balancing

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261107-001：Peter Zijlstra 的 v2 系列（12 补丁）发出，核心是 rq_clock/rq_lock 语义整体重做——cover 明说「主差异是 rq_clock 的重做，因为 TJ（Tejun Heo）指出上一版把它彻底搞错了」。新增 `rq_drop_lock()`、分解 `update_rq_clock()`、引入 `RQCF_NOP_MASK` 让已 UPDATED 的 rq 跳过重复更新，取代 v1 靠 `core_clock_updated` 布尔量猜时钟的绕路逻辑；补丁 1 也补了「锁间隙兄弟 CPU 建立 core-wide cookie 时重启」的 fast-path 检查。当日无人回帖。
- sched-20261108-005（今天）：**Kayra Cizmeci 评审 patch 02/12（`Introduce rq_drop_lock()`）并给出 Reviewed-by**——除了一处拼写 nit（`prepration` → `preparation`）外「找不到 1 处漏改」，自嘲「sadly I couldn't find anything aside from a nit」。系列评审开始启动，但 rq_clock 重做（02–07）是否过 Tejun 这一关仍待定。

## 背景与问题

（承接 sched-20261107-001，源头 sched-20260828-001）Peter Zijlstra 修自己 6/11 引入的 core scheduling 回归，一路修补，与 Tejun Heo 面向 sched_ext 的 core-sched 修复存在重叠。v2 的动机是 Tejun 对 v1 的 review：v1 的 rq_clock 重做方向错了，于是 v2 把时间更新拆成 6 个补丁重做，并把系列扩到 12 补丁。今日新进展是评审开始回流——首个收到的是 patch 02/12 的 Reviewed-by。

## 技术方案

（承接）今日无代码变更，为 patch 02/12 的评审确认：`rq_drop_lock()` 把 `rq_unpin_lock()` 身兼的「临时放锁」与「最终放锁」两职拆开，用于 `rq_pin_lock() → rq_drop_lock() → rq_repin_lock() → rq_unpin_lock()` 里的临时 drop。Kayra 逐点核对后确认「未找到一处漏改到 `rq_drop_lock()` 的调用点」，仅指出 commit message 的拼写 nit。

## 版本演进与当前进展

*current_version: v2（2026-11-07 发出，msgid 20261107115913.261163891）*。

- v1（2026-08-28，7 补丁）：无回帖；自留 XXX。
- v2（2026-11-07，12 补丁）：响应 Tejun 对 rq_clock 重做的批评，patch 02–07 重做时间更新，patch 1 补 cookie 竞态检查。当日无人回帖。
- 今日（2026-11-08）：patch 02/12 获 Kayra Reviewed-by，无新版本。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci**（评审者，非维护者）：对 patch 02/12 给 `Reviewed-by`，仅一处拼写 nit，明确「找不到漏改点」。
- 关键分歧点未变：Tejun Heo 对 v1 rq_clock 重做「all wrong」的批评仍是本系列最大门槛，v2 的 02–07 是否覆盖到位需 Tejun 复看。Peter/Ingo 未在本窗口直接表态。

无 NAK。评审刚起步，01/12（`pick_next_task()` 自重入）与 08–12（newidle/balance 重构）尚无评审。

## 合入评估

*likelihood=medium*。作者是 sched/core 主要维护者、修的是自己引入的回归，今日 02/12 已获 Reviewed-by；但系列动 `pick_next_task()`/`pick_task_fair()` 最热路径，rq_clock 重做仍需 Tejun 确认，且 11/12 的性能数据是否补上仍未确认。*blocking_issues*：① rq_clock 重做（02–07）需 Tejun 复看；② 01、08–12 尚无评审；③ 11/12 benchmark 未确认。*next_action*：等 Tejun 复看 rq_clock 重做，Aaron Tomlin / K Prateek Nayak 跑回归，确认 11/12 数据。

## 效果评估

今日无性能数据。v1 阶段唯一功能证据是「these patches survive both Aaron's test case and Prateek's」（崩溃不复现，非性能结论）。rq_clock 重做与 patch 1 cookie 竞态检查的收益/开销仍未量化。

## 我可以参与的点

- **testing**：在启用 `CONFIG_SCHED_CORE` 的平台跑 core-sched 复现用例与 schbench/wakeup-latency，回帖 Tested-by——core-wide 状态机改动上游最需要实测背书。
- **review**：核对 v2 的 rq_clock 重做（patch 02–07）是否真正覆盖 Tejun 指出的 v1 错误点，以及 `task_on_core()` 是否遗漏其它以 `task_on_cpu()` 作「不可搬动」判据的路径。

## 参考链接

- lore thread（v2 cover）: https://lore.kernel.org/all/20261107115913.261163891@infradead.org/
- 今日 Kayra 对 02/12 的评审: https://lore.kernel.org/all/avA36psY6pULqy8X@scheduler.schedules/
- 前一版（v1，2026-08-28）: https://lore.kernel.org/all/20260828101659.812011872@infradead.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20261108-005
date: '2026-11-08'
subject: "sched: core-sched fixes and balancing"
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: "<20261107115913.261163891@infradead.org>"
lore_url: "https://lore.kernel.org/all/20261107115913.261163891@infradead.org/"
authors: ["Peter Zijlstra"]
maintainers_involved: ["Tejun Heo"]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20260828101659.812011872@infradead.org>"
    date: '2026-08-28'
    summary: "7 补丁：core_task_seq 重入检测、RQCF_UPDATED 直测、task_on_core() 防偷、rt/dl 早退、重新启用 core-sched newidle、删除 sched_class::balance()"
    review_outcome: "无回帖；Tejun 后续指出 rq_clock 重做方向错误"
  - version: v2
    msgid: "<20261107115913.261163891@infradead.org>"
    date: '2026-11-07'
    summary: "12 补丁：rq_clock/rq_lock 语义重做（rq_drop_lock、update_rq_clock 分解、RQCF_NOP_MASK、pin/drop/repin/unpin 新语义），patch 1 补 cookie 竞态检查"
    review_outcome: "patch 02/12 获 Kayra Reviewed-by；rq_clock 重做待 Tejun 复看"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "rq_clock 重做（patch 02-07）需 Tejun 复看确认方向"
    - "patch 01、08-12 尚无评审"
    - "patch 11 性能数据是否已补上未确认"
  next_action: "等 Tejun 复看 rq_clock 重做，Aaron Tomlin / K Prateek Nayak 跑回归，确认 patch 11 benchmark"
contribution_opportunities:
  - kind: testing
    description: "在启用 CONFIG_SCHED_CORE 的平台跑 core-sched 复现用例与 schbench/wakeup-latency，回帖 Tested-by"
  - kind: review
    description: "核对 v2 rq_clock 重做是否覆盖 Tejun 指出的 v1 错误点，及 task_on_core() 的覆盖面"
generated_at: "2026-11-09T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261107-001]
tags: [core_sched, cfs, load_balance]
---