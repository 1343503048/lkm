# sched: Make proxy execution compatible with sched_ext

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260924-007：v14 发出，本系列让 proxy execution 与 sched_ext 兼容。
- sched-20260925-011：Andrea Righi 按 Peter 建议重做——把 Shubhang 的 v4 hrtick 补丁前置，新增 `SNT_CONFIRM` 回调确认 donor，删除 `scx_proxy_donor_start()`；Peter 明确表态「I'll apply your patches as is」并问 Tejun 是代收 sched_ext 部分还是等 sched/core 落地后再叠上。
- sched-20260927-004（今天）：Tejun 回复 Peter「I can pull from sched/core and then apply sched_ext parts on top」——分区方式敲定：Peter 收 core 侧、Tejun 自己收 sched_ext 侧。前一天卡住的「Tejun 未回复分区问题」解除，系列离落地只剩各自树上的实际应用。

## 背景与问题

（承接 sched-20260925-011）proxy execution 让阻塞在互斥量上的任务把执行上下文「借」给锁持有者运行。sched_ext 作为可扩展调度类，其 donor 记账、tick 归属、限流语义都与 core 调度路径强耦合，需要一组 sched_ext 侧 hook 才能在 proxy execution 下正确工作。核心张力：Peter 不喜欢 sched_ext 专属 hook，但也不喜欢把 sched_ext 逻辑塞进 core。

## 技术方案

（承接 sched-20260925-011）通过 sched class 回调表达「provisional pick + donor 确认」：新增 `SNT_CONFIRM` 回调，sched_ext 在 `set_next_task_scx()` 里确认 donor，删除 `scx_proxy_donor_start()` 专用入口。今天无新代码，只有收取路径的确认——Tejun 将先 pull sched/core（Peter 应用 core 侧后的结果）再在其上 apply sched_ext 部分。

## 版本演进与当前进展

- v14（2026-09-24 封面相关线程；对应 sched-20260924-007）。
- 09-25：Andrea 重做 donor 确认机制（SNT_CONFIRM）；Peter 表态「I'll apply your patches as is」，并问 Tejun 分区方式（对应 sched-20260925-011）。
- 09-27 03:17：Tejun（`<argaS0_-6V4l9KGq@slm.duckdns.org>`）回复 Peter：自己 pull sched/core 后 apply sched_ext 部分。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（前一日）：照单全收 core 侧（「I'll apply your patches as is」），把「化简 hook」的疑虑后置，核心动作是确认分区。
- **Tejun Heo**（今日）：明确自己收 sched_ext 侧——pull sched/core 后再 apply sched_ext 部分。至此分区方式闭环。
- 分歧仍在代码组织（hook 职责耦合，作者自己也觉得「looks a bit confusing」），但不构成合入障碍。

## 合入评估

*likelihood=high*。Peter 已放行 core 侧、Tejun 今日确认 sched_ext 侧收取路径，昨日唯一的 blocking_issue（Tejun 未回复分区问题）已解除。*blocking_issues*：实际 apply 尚未发生（本日缓存无 tip-bot 合入通知）；hook 职责耦合的「化简」讨论被后置、后续可能再开。*next_action*：跟踪 Peter 对 core 侧、Tejun 对 sched_ext 侧的实际 apply 与 tip 合入通知。

## 效果评估

作者此前自述「passed all my scx proxy exec tests」，未附 benchmark 数字；正确性由自测背书，暂无量化性能数据。

## 我可以参与的点

- `testing`：在 sched_ext + proxy execution 组合下跑调度压力测试（scx 示例调度器 + 互斥锁竞争负载），验证 donor 确认/tick 记账路径，回帖补充实测。
- `review`：`SNT_CONFIRM` 一个 hook 塞两件事（idle tick 记账 + reenqueue retry）的耦合是否值得拆，给出更清晰的拆分建议。

## 参考链接

- Tejun 分区确认: https://lore.kernel.org/all/argaS0_-6V4l9KGq@slm.duckdns.org/
- Peter 照单全收 + 问 Tejun: https://lore.kernel.org/all/20260925075628.GI4121339@noisy.programming.kicks-ass.net/
- 分支: https://git.kernel.org/pub/scm/linux/kernel/git/arighi/linux.git scx-proxy-exec-next

---
id: sched-20260927-004
date: 2026-09-27
subject: "sched: Make proxy execution compatible with sched_ext"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260922165445.943315-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/argaS0_-6V4l9KGq@slm.duckdns.org/"
authors:
  - "Andrea Righi"
maintainers_involved:
  - "Peter Zijlstra"
  - "Tejun Heo"
current_version: v14
patch_series:
  - version: v14
    msgid: "<20260922165445.943315-1-arighi@nvidia.com>"
    date: 2026-09-24
    summary: "重做 donor 确认机制：新增 SNT_CONFIRM 回调、删 scx_proxy_donor_start()，hrtick v4 前置。"
    review_outcome: "Peter 09-25 表态照单全收并问分区；Tejun 09-27 回复自己 pull sched/core 后 apply sched_ext 部分。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "实际 apply 尚未发生（本日无 tip-bot 合入通知）"
    - "hook 职责耦合的「化简」讨论被后置，可能再开"
  next_action: "跟踪 Peter（core 侧）与 Tejun（sched_ext 侧）的实际 apply 与 tip 合入通知"
contribution_opportunities:
  - kind: testing
    description: "在 sched_ext + proxy execution 组合下跑互斥锁竞争压力测试，验证 donor 确认/tick 记账路径"
  - kind: review
    description: "评估 SNT_CONFIRM 一个 hook 塞两件事的耦合是否值得拆分，给出清晰建议"
generated_at: "2026-09-28T09:00:00"
source_email_count: 1
related_articles:
  - sched-20260916-002
  - sched-20260923-002
  - sched-20260924-007
  - sched-20260925-011
tags:
  - sched_ext
  - proxy_execution
---