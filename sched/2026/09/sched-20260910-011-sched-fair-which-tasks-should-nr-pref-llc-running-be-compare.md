# sched/fair: which tasks should nr_pref_llc_running be compared against?

## TL;DR
本文为增量更新，完整背景见 related_articles 中的 sched-20260909-015 / sched-20260830-003。09-09 Chen Yu 对「用 cfs.h_nr_queued 作分母」与「Lu Wang 的 ALB guard 是否已覆盖该场景」的两连问，09-10 由 Tim Chen 给出完整回答：用 T1/T2 反例论证 h_nr_queued 作分母会错误触发 active balance，并指出 Lu Wang 的补丁只缓解 migrate_llc 一种迁移原因；Chen Yu 表示接受并已启动 sanity 测试，结果待回报。分母口径之争基本落定，维持 runnable 域计数。

## 背景与问题
cache-aware scheduling 的 alb_break_llc() 需要判断「本 LLC 上偏好该 LLC 的任务占比」来决定是否打破 LLC 亲和做 active balance，分子 nr_pref_llc_running 应与哪个分母比较存在争议：08-28 的改动把 nr_pref_llc_running 移入 runnable 域（与 DELAY_DEQUEUE 对齐，h_nr_runnable 作分母），09-09 Chen Yu 提出 cfs.h_nr_queued 作为候选分母并给出 3 任务反例。

## 技术方案
Tim Chen 的论证（本日核心内容，直接引用其反例）：要避免的常见场景是「任务 T1 在偏好 src LLC 的 CPU 上运行，另一个不偏好 src LLC 的任务 T2 处于 delay queued」：
- runnable 域（当前修法）：h_nr_runnable == 1，nr_pref_llc_running == 1 → 相等 → alb_break_llc() 为 true → 抑制 active balance。正确：唯一真正在跑的任务就想待在这里，不应把它拽走。
- h_nr_queued 方案：h_nr_queued == 2，nr_pref(queued) == 1 → 不等 → alb_break_llc() 为 false → 进入 active balance，打破 T1 的局部性去缓解一个实际上只是「T2 在睡觉」的假 imbalance。
关于 Lu Wang 的 ALB guard：Tim 明确「Lu Wang's patch only mitigate the migrate_llc case but not other migration reasons」——即使有该 guard，非 migrate_llc 原因的 active balance 仍不该在上述场景发生，因此 guard 不能替代正确的分母口径。

## 版本演进与当前进展
讨论线程，无补丁版本。时间线：08-27 作者提问 → 08-28 runnable 域改动 → 08-30/09-09 多轮讨论 → 09-09 Chen Yu 两连问 → 09-10 Tim 完整作答 → Chen Yu 接受（"Got it, I see. Indeed."）并自述已启动 sanity 测试、稍后回报。当前等待 Chen Yu 的测试结果收尾。

## Maintainer 意见与讨论焦点
- Tim Chen：给出 T1/T2 反例与 Lu Wang guard 覆盖范围的判定，是分母口径的最终技术论据。
- Chen Yu：从质疑转为接受，并以实测验证收尾——sanity 测试结果未出，是本线程唯一悬念。
- 无新分歧。遗留的结构性问题（前文已记录）：计数口径、runnable 域改动、ALB guard 三者之间仍没有写进注释的统一不变式。

## 合入评估
不适用（讨论线程，依托的 runnable 域改动已在既有补丁中）。likelihood: unknown——结论倾向维持现状（h_nr_runnable 分母），但正式定论等 Chen Yu 的 sanity 测试结果；若测试印证 Tim 的反例，该问题可关闭。

## 效果评估
本日无 benchmark；论证为构造性反例（T1/T2 场景），Chen Yu 的实测结果未出。暂无效果数据。

## 我可以参与的点
- 复现 Tim 的 T1/T2 场景：构造一个偏好本 LLC 的运行任务加一个不偏好的 delay-queued 任务，在 DELAY_DEQUEUE 开启下用 /proc/sched_debug 对比 h_nr_runnable 与 h_nr_queued 两种分母下 alb_break_llc() 的实际决策，给 Chen Yu 的 sanity 测试提供独立数据（testing）。
- 把三方结论（runnable 域分子分母同域、ALB guard 仅覆盖 migrate_llc）提炼成一段可进代码注释的不变式说明并发出，补上前文指出的「无成文统一不变式」缺口（new_patch）。

## 参考链接
- lore thread（本日 Tim 的回答）: https://lore.kernel.org/all/a1b1d5f9a58895b65217671678c6e02bd711241a.camel@linux.intel.com/
- Chen Yu 的接受与测试承诺: https://lore.kernel.org/all/aqKKrMKaZORqNpwt@three-body/
- 原讨论线程根（09-09 文章记录）: https://lore.kernel.org/all/aqFFu1Xo52cQV3iy@fengwei-dev/

---
id: sched-20260910-011
date: 2026-09-10
subject: "sched/fair: which tasks should nr_pref_llc_running be compared against?"
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: "<20260827135000.735138-1-zhanxusheng@xiaomi.com>"
lore_url: "https://lore.kernel.org/all/a1b1d5f9a58895b65217671678c6e02bd711241a.camel@linux.intel.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: "2026-09-11T10:45:00"
authors:
  - "Xu Sheng Zhan"
maintainers_involved:
  - "Tim Chen"
  - "Chen Yu"
patch_series:
  - version: v1
    msgid: "<20260827135000.735138-1-zhanxusheng@xiaomi.com>"
    date: "2026-08-27"
    summary: "讨论 alb_break_llc() 分母口径；runnable 域改动（h_nr_runnable 分母）为当前方案。"
    review_outcome: "09-10 Tim Chen 用 T1/T2 反例论证 h_nr_queued 分母会把睡眠任务算成 imbalance、错误打破 T1 局部性，并指出 Lu Wang 的 ALB guard 只覆盖 migrate_llc；Chen Yu 接受并已启动 sanity 测试，结果待回报。"
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "Chen Yu 的 sanity 测试结果未出，分母口径未正式关闭"
    - "计数口径/runnable 域/ALB guard 三者仍无写进注释的统一不变式"
  next_action: "等 Chen Yu 回报测试结果；如印证 T1/T2 反例则维持 h_nr_runnable 分母并关闭讨论"
contribution_opportunities:
  - kind: testing
    description: "构造 T1（偏好本 LLC 运行）+T2（不偏好、delay-queued）场景，DELAY_DEQUEUE 开启下对比两种分母下 alb_break_llc() 的实际决策，独立验证 Tim 的反例"
  - kind: new_patch
    description: "把「分子分母同域 + ALB guard 仅覆盖 migrate_llc」提炼为代码注释里的统一不变式并发出补丁"
source_email_count: 2
related_articles:
  - "sched-20260909-015"
  - "sched-20260830-003"
  - "sched-20260828-004"
  - "sched-20260827-018"
tags:
  - load_balance
  - cfs
---
