# sched: Restart hrtick after same-task repicks

## TL;DR
Shubhang Kaushik（Ampere）按 Peter Zijlstra 的设计发出 v2：把 set_next_task() 的 `bool first` 换成 SNT_NORMAL/SNT_PICK/SNT_REPICK 枚举，same-task repick 时 fair 与 DL 都重启 hrtick，并删除 fair 特有的 rq 状态与 runnable 计数条件。首份量化数据同步到来：CPU-bound 任务最大运行时长从 5.227ms 降到 3.386ms、>4ms 样本从 6 个降到 0。本文为增量更新，v1 与 09-11 讨论见 sched-20260911-004。

## 背景与问题
hrtick 到期 → task_tick 触发 resched_curr() → schedule() 里 pick_task_fair() 再次选中当前任务 → put_prev_set_next_task() 在 next == prev 时直接返回、不调用 set_next_task()——hrtick_start_fair() 被跳过，下一个抢占点没有被武装。DL 同理（set_next_task_dl()/start_hrtick_dl() 被跳过）。v1 用 fair 特有的 rq flag + runnable 计数修复，被 Zhan Xusheng 与 PeterZ 指出缺陷与冗余。

## 技术方案
- 枚举化：set_next_task() 参数从 `bool first` 改为 `enum snt_e`（SNT_NORMAL/SNT_PICK/SNT_REPICK），next == prev 路径显式传 SNT_REPICK；修改面覆盖 core.c、deadline.c、ext.c、fair.c、idle.c、rt.c、stop_task.c（+46/-17）；
- fair/DL 的 SNT_REPICK 分支跳过正常任务切换记账、只重启各自 hrtick；SCX 的 repick 直接 return；
- 时序保持：调用发生在 schedule() 内、rq->hrtick_sched 处于 deferred 状态，hrtick_start() 只记录新 delay，hrtick_schedule_exit() 在调度完成后统一重编 hrtimer——保留「不从 hrtick 回调直接编程」的原有规则；
- 作者确认 Vincent 的意见：SNT_REPICK 不调用 set_protect_slice()（否则每次 repick 都会延长保护性最小 slice），该点保留为独立修复；
- 测试：基线 08df884136f1 与 v2 均开 CONFIG_HIGH_RES_TIMERS/CONFIG_SCHED_HRTICK，HRTICK+DELAY_DEQUEUE、base_slice_ns=3ms，CPU 0 上钉 2 个 CPU-bound nice-0 fair 任务 + 周期性 sleeper，各采 5 次 10 秒 perf sched trace。

## 版本演进与当前进展
current_version: v2（msgid `<20260911-sched-fair-hrtick-restart-v2-1-0d34db26ecd1@gentwo.org>`，09-12 06:08 入缓存；另含作者 02:56 对 PeterZ 方案的确认回帖）。

- v1（08-13）→ Zhan Xusheng 08-26 review → 作者 09-11 承诺 v2；
- 09-12：作者先回帖认可 SNT_REPICK 设计（"Yes, this works for me"、"cleaner than the fair specific rq flag"、补上 DL 缺失），随后发出 v2——与 PeterZ 的提案同构。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（承 09-11）：SNT_REPICK 设计的提出者，v2 即按其方案实现；
- **Vincent Guittot**（承 09-11）：SNT_REPICK 不应调用 set_protect_slice 的意见被作者采纳，拆为独立修复（无人认领）；
- 当日缓存内未见 PeterZ/Vincent 对 v2 的复核——枚举化跨 6 个调度类文件，评审面仍在。无分歧记录。

## 合入评估
likelihood=medium：v2 采用了维护者提出的架构方向、带首份量化数据；但跨类接口变更需要 PeterZ 亲自复核，且 set_protect_slice 拆分项悬空。blocking_issues：v2 尚无维护者复核；DL hrtick 场景的验证只有作者承诺（"will test ... a DL hrtick case"）。next_action：等 PeterZ 对 v2 的复核与 DL 场景测试结果；独立修复（repick 不延长 protect slice）需另起补丁。

## 效果评估
作者一手数据（5 次 10 秒 perf sched trace，条件见上）：CPU-bound fair 任务最大运行时长 baseline 5.227ms → v2 3.386ms；>4ms 样本 6 → 0。方向与幅度自洽（base_slice_ns 3ms 下 hrtick 缺失会让任务跑到 4ms+ 才被抢占），暂无第三方复现。

## 我可以参与的点
- kind=testing：作者承诺的 delayed dequeue 混合负载与 DL hrtick 场景仍未回填数据，可在对应配置下复测（ftrace 验证 repick 路径 hrtick 重启，承 sched-20260826-009 的验证点）。
- kind=new_patch：认领「SNT_REPICK 不调用 set_protect_slice」的独立修复——作者与 Vincent 已就语义达成一致，只剩实现。

## 参考链接
- v2 补丁：https://lore.kernel.org/all/20260911-sched-fair-hrtick-restart-v2-1-0d34db26ecd1@gentwo.org/
- 作者对 SNT_REPICK 方案的确认：https://lore.kernel.org/all/b962cd29-f2fc-7081-8565-95640e2621d4@gentwo.org/
- v1 补丁：https://lore.kernel.org/r/20260813-sched-fair-hrtick-restart-v1-1-4230d1e18fbb@gentwo.org/
- PeterZ 的设计提案（09-11）：https://lore.kernel.org/all/20260911112056.GY776954@noisy.programming.kicks-ass.net/

---
id: sched-20260912-004
subject: 'sched: Restart hrtick after same-task repicks'
date: '2026-09-12'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260911-sched-fair-hrtick-restart-v2-1-0d34db26ecd1@gentwo.org>'
lore_url: 'https://lore.kernel.org/all/20260911-sched-fair-hrtick-restart-v2-1-0d34db26ecd1@gentwo.org/'
authors:
  - 'Shubhang'
maintainers_involved:
  - 'Peter Zijlstra'
  - 'Vincent Guittot'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260813-sched-fair-hrtick-restart-v1-1-4230d1e18fbb@gentwo.org>'
    date: 2026-08-13
    summary: 'fair 特有 rq flag + runnable 计数条件的 hrtick 重启修复。'
    review_outcome: 'Zhan Xusheng 指出条件缺陷与冗余；PeterZ 09-11 提出跨类 SNT 枚举方案。'
  - version: v2
    msgid: '<20260911-sched-fair-hrtick-restart-v2-1-0d34db26ecd1@gentwo.org>'
    date: 2026-09-12
    summary: '采纳 SNT_REPICK 枚举方案：fair+DL 同任务重选均重启 hrtick，删 fair 特有状态；附 baseline 5.227ms→v2 3.386ms、>4ms 样本 6→0 的实测。'
    review_outcome: '当日无维护者复核；作者与 Vincent 一致同意 SNT_REPICK 不调 set_protect_slice（拆独立修复）。'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'v2 尚无 PeterZ 复核（跨 6 个调度类文件的接口变更）'
    - 'DL hrtick 场景测试只有作者承诺，未回填'
    - 'set_protect_slice 拆分项无人认领'
  next_action: '等 PeterZ 复核 v2 与 DL 测试结果；set_protect_slice 修复另起补丁'
contribution_opportunities:
  - kind: testing
    description: 'delayed dequeue 混合负载与 DL hrtick 场景复测并回帖'
  - kind: new_patch
    description: '实现 SNT_REPICK 不调 set_protect_slice 的独立修复（语义已定）'
generated_at: '2026-09-14T12:40:00'
source_email_count: 2
related_articles:
  - 'sched-20260911-004'
  - 'sched-20260826-009'
tags:
  - cfs
  - sched_clock
---
