---
id: sched-20261026-001
date: 2026-10-26
subject: 'sched/stats: Fix run_delay over-count for proxy-migrated blocked donors'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261025130740.3324391-1-albin_yang@163.com>
lore_url: https://lore.kernel.org/all/20261025130740.3324391-1-albin_yang@163.com/
authors:
- Wei Yang
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261025130740.3324391-1-albin_yang@163.com>
  date: 2026-10-25
  summary: 新增 !task_is_blocked() 门控，任务仍阻塞在 mutex 上时不 re-arm last_queued
  review_outcome: Kayra/Prateek 质疑判据与 proxy v33 叠加的边界，作者计划重构为 v5 两补丁
upstream_commit: null
fixes_commit: b049b81bdff6
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - blocked_on 在 waiter 单独 enqueue 路径仍置位导致 !task_is_blocked() 门控欠计
  - Prateek 的 is_blocked 单一判据实测不成立
  next_action: 作者重构重发 v5 两补丁，并就 blocked_on 四选一给出结论
contribution_opportunities:
- kind: review
  description: 核对 blocked_on 在 waiter 单独 enqueue 路径是否置位、DEQUEUE_SAVE/ENQUEUE_RESTORE
    方案副作用
- kind: testing
  description: 启用代理执行的构建上复现 owner 睡眠 + waiter 单独 enqueue 场景验证欠计
generated_at: '2026-10-27T01:00:00'
source_email_count: 5
related_articles:
- sched-20261025-002
tags:
- cfs
- sched_debug
- proxy_execution
title: 'sched/stats: Fix run_delay over-count for proxy-migrated blocked donors'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-002-sched-stats-fix-run-delay-over-count-for-proxy-migrated-bloc.html">sched-20261025-002</a>：Wei Yang 在 run_delay v4（delayed dequeue 迁移多计修复）基础上补发独立单补丁，修 proxy execution 下被迁移的 blocked donor 的 run_delay 多计：mutex owner 在别的 CPU 上跑时，`find_proxy_task()` 把仍在阻塞的 donor 迁到 owner 的 CPU，迁移用 `activate_task(ENQUEUE_NOCLOCK)`（不带 `ENQUEUE_RESTORE`）re-arm 了 `last_queued`，导致阻塞时长被误算成等 CPU 时长。补丁新增 `!task_is_blocked()` 门控，2 CPU VM 实测同 ~170ms 阻塞从 ~167ms 降到 0.01ms。
- <a class="article-ref" href="/lkm/2026/10/26/sched-20261026-001-sched-stats-fix-run-delay-over-count-for-proxy-migrated-bloc.html">sched-20261026-001</a>（今天）：Kayra Cizmeci 与 K Prateek Nayak 密集 review。Kayra 指出补丁与 John Stultz proxy v33 系列（`20261023220431.1106611-8-jstultz@google.com`）叠加后，waiters 会被拖到 owner 的列表、`on_rq` 可能为 false，`ttwu_runnable()` 可能早返回而不清 `blocked_on`，导致门控欠计；Prateek 提议用 `p->is_blocked` 作单一判据并给了 diff，Wei Yang 实测该重构在 enqueue/dequeue 两侧都出错（普通 runnable 任务 counter 归零、阻塞任务 delta 变成整个 uptime）。作者将重构为 `[PATCH v5 1/2]`（DELAY_DEQUEUE）+ `[PATCH v5 2/2]`（本补丁），并待确认 `blocked_on` 在单独 enqueue 路径是否仍置位（Kayra 认为「看代码是置位的」）。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-002-sched-stats-fix-run-delay-over-count-for-proxy-migrated-bloc.html">sched-20261025-002</a>）proxy exec（v7.1 合入）下任务阻塞在内核 mutex 上（proxy donor），其 mutex owner 在另一 CPU 运行。`find_proxy_task()` 在「donor 被选为 next 但非 current、owner on_rq 且未 delayed」时，经 `proxy_migrate_task()` 把仍阻塞的 donor 迁到 owner 的 CPU。该迁移用 `attach_task()` → `activate_task(rq, p, ENQUEUE_NOCLOCK)`（不带 `ENQUEUE_RESTORE`）re-attach donor，于是 `sched_info_enqueue()` re-arm `last_queued`，尽管 donor 根本不 runnable——一次「假 enqueue」。真实唤醒不会纠正：donor 仍 on_rq 且非 `sched_delayed`，`ttwu_runnable()` 不调 `enqueue_task()`，`last_queued` 停留在迁移时刻；`sched_info_arrive()` 于是把迁移到真正运行之间的整个阻塞时长计为等 CPU 时间。`Fixes: b049b81bdff6`（"sched: Handle blocked-waiter migration (and return migration)"）。

今日无新背景，为对门控正确性的深度 review：焦点从「要不要修」转向「用哪个判据修才不引入新 bug」。

## 技术方案
（承接 <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-002-sched-stats-fix-run-delay-over-count-for-proxy-migrated-bloc.html">sched-20261025-002</a>）单补丁：任务仍阻塞在 mutex 上时不再 re-arm `last_queued`。delayed dequeue 睡眠者没有 `blocked_on`，所以这是对 `se.sched_delayed` 检查的**附加条件**而非替代（`!sched_delayed && !task_is_blocked()`）。不能用 `!p->is_blocked` 门控：`ttwu_runnable()` 的真实唤醒 enqueue 在 `if (p->is_blocked)` 分支内、`is_blocked` 之后才在 `ttwu_do_wakeup()` 中清除，`!is_blocked` 会压掉本补丁依赖的 re-arm。

今日方案演进的实质交锋：

- **K Prateek Nayak** 提议反向思路——不用「堆砌例外」，而是让 sched info 全面改用 `p->is_blocked` 作单一判据（类似 PSI 信号的处理），给出 diff：`sched_info_dequeue()` 遇 `is_blocked` 直接返回、`sched_info_enqueue()` 只在 `is_blocked` 时 arm、`sched_info_depart()` 里 blocked 任务额外 `__sched_info_dequeue()`。
- **Wei Yang** 实测该 diff（rebuild 后跑自己的 sanity check），报告**两处都不成立**：(1) `__sched_info_dequeue()` 丢掉了原来的 `if (!last_queued) return` 守卫，blocking 任务的 `last_queued==0`（`sched_info_arrive()` 在 switch-in 时已清），于是 delta = `rq_clock - 0` 即整个 uptime——cross-cpu blocked 169.80ms 却计 run_delay 169047.52ms、same-cpu 168.70ms 计 185515.00ms，且对照也受影响、非 proxy 专属；(2) `sched_info_enqueue()` 只在 `is_blocked` 时 arm，普通 runnable 任务完全没 counter，sanity check 从 +39ms 掉到 0.00ms。作者给出结论：`is_blocked` 能 gate 计费侧，但 arm 侧需要一个在唤醒时已被清除的判据（`task_is_blocked()` 或 `sched_delayed`）。
- 作者另报告：`!sched_delayed && !task_is_blocked()` 组合在 proxy 用例上给 0.01ms（sanity +39ms 保持）、delayed 复现器 0/20。

## 版本演进与当前进展
*current_version: v1*（`<20261025130740.3324391-1-albin_yang@163.com>`）。当日无新版本，但作者明确计划重构：将把 DELAY_DEQUEUE 修复与本补丁合并重发为 **`[PATCH v5 1/2]` + `[PATCH v5 2/2]`** 两补丁系列（此前二者分开单发）。

## Maintainer 意见与讨论焦点
无维护者（Peter）当日直接表态，但两位资深 reviewer 给出实质意见：

- **Kayra Cizmeci**：指出「这不是一个孤立 bug」——与 John Stultz 的 sleeping-owner v33 叠加后，waiters 会被拖到 owner 的列表、`on_rq` 可能为 false、`ttwu_runnable()` 会早返回而不清 `blocked_on`，届时门控会欠计。他倾向「单独一个 fix，在该路径显式 clear `blocked_on`（任务确实是在等 CPU）」，并问作者是否 `blocked_on` 在那条路径仍置位。他也认为「这应该是个系列而不是独立补丁」。
- **K Prateek Nayak**：主张用 `p->is_blocked` 作单一判据取代堆例外，给了 build-tested 的 diff（on top of sched-core-2026-10-18），并说「与 PSI 信号处理方式一致」。
- **Wei Yang（作者）**：回应 Kayra 的第一个疑点——「不，你说得对：假 enqueue 在迁移时刻启动计时，~167ms 就是我测到的那个 delta；我之前把 `sched_info_arrive()` 直接计费写错了描述，会修正」。对 Kayra 的 blocked_on 疑问，他先承认自己的 sanity check 没覆盖「waiter 与 owner 分开 enqueue」的情形，并列出四选一（a. 在该路径也清 predicate；b. 在那里清 `blocked_on`（proxy 领地）；c. 等到 John 系列合入再重估；d. 从源头给 `proxy_migrate_task()` 加 `DEQUEUE_SAVE/ENQUEUE_RESTORE` 让迁移完全不碰 sched_info）。他倾向「先收本补丁，欠计只在 John 系列合入后才出现」，并追加 John 到 CC。
- **Kayra Cizmeci（二次）**：回「AFAICT 从代码看，是的（blocked_on 仍置位）」；重申单独 clear `blocked_on` 的 fix 更好；并说「这由 Peter 决定收不收」。

分歧点：门控判据用 `is_blocked`（Prateek）还是 `!task_is_blocked()`（作者实测可行），以及 blocked_on 在单独 enqueue 路径的处理——均未收敛。

## 合入评估
*likelihood=medium*。修复方向无异议且带明确 `Fixes:`，但判据仍在多方拉扯：Prateek 的单一判据方案被作者实测证伪，作者坚持的 `!task_is_blocked()` 又被 Kayra 指出与 proxy v33 叠加后的欠计边界。*blocking_issues*：`blocked_on` 在 waiter 单独 enqueue 路径仍置位导致 `!task_is_blocked()` 门控欠计（Kayra 已确认代码上置位）；Prateek 的 `is_blocked` 单一判据实测不成立；系列尚未重发。*next_action*：作者按计划重构重发 v5 两补丁，并就 blocked_on 的 a/b/c/d 四选一给出结论（或与 John/Kayra 敲定再推进）。

## 效果评估
作者今日补测数据（`run_delay` 为 `/proc/<tid>/schedstat` 第 2 字段）：Prateek 版 diff 的 cross-cpu 用例「blocked 169.80ms / run_delay delta 169047.52ms」、same-cpu「blocked 168.70ms / delta 185515.00ms」（证伪该 diff）；而 `!sched_delayed && !task_is_blocked()` 组合在 proxy 用例上 0.01ms、delayed 复现器 0/20。此前的 `!task_is_blocked()` 门控在 2 CPU VM 上把同 ~170ms 阻塞的误计从 ~167ms 降到 0.01ms。

## 我可以参与的点
- *kind: review*：核对 `blocked_on` 在「waiter 与 owner 分开 enqueue」路径是否确实仍置位、以及 a/b/c/d 四选一里 `DEQUEUE_SAVE/ENQUEUE_RESTORE` 对 psi/rt/dl/sched_ext 的副作用——这是当前卡点，作者已明确征求 Kayra/John 意见。
- *kind: testing*：在启用 `SCHED_PROXY_EXECUTION` 的构建上复现「owner 睡眠 + waiter 被 kill 信号唤醒后单独 enqueue」场景，验证门控是否欠计。

## 参考链接
- patch（v1）: https://lore.kernel.org/all/20261025130740.3324391-1-albin_yang@163.com/
- Kayra 首次 review: https://lore.kernel.org/all/at5JrmlnEXPQftDe@scheduler.schedules/
- Prateek diff: https://lore.kernel.org/all/72a6eb77-0461-477b-a0e9-c06a486e3e0e@amd.com/
- 作者实测回复: https://lore.kernel.org/all/20261026133831.4111227-1-albin_yang@163.com/
- 作者四选一回复: https://lore.kernel.org/all/20261026135352.4120064-1-albin_yang@163.com/
- 前文: <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-002-sched-stats-fix-run-delay-over-count-for-proxy-migrated-bloc.html">sched-20261025-002</a>
