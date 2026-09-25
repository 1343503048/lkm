# sched: Make proxy execution compatible with sched_ext

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260924-007：v14 发出，本系列让 proxy execution 与 sched_ext 兼容。
- sched-20260925-011（今天）：Andrea Righi 按 Peter 建议重做——把 Shubhang 的 v4 hrtick 补丁作为前置 commit 合入，新增 `SNT_CONFIRM` 回调，用它在 `set_next_task_scx()` 里确认 donor，删除 `scx_proxy_donor_start()`；Peter 明确表态「I'll apply your patches as is」（照单全收），并问 Tejun 是代收 sched_ext 部分还是等 sched/core 落地后再叠上。

## 背景与问题

（承接 sched-20260924-007）proxy execution 让阻塞在互斥量上的任务把执行上下文「借」给锁持有者运行。sched_ext 作为可扩展调度类，其 donor 记账、tick 归属、限流语义都与 core 调度路径强耦合；要让 sched_ext 在 proxy execution 下正确工作，需要一组 sched_ext 侧的 hook。核心张力：Peter 不喜欢 sched_ext 专属 hook，但也不喜欢把 sched_ext 逻辑塞进 core。

## 技术方案

（承接 sched-20260924-007）通过 sched class 回调表达「provisional pick + donor 确认」：新增 `SNT_CONFIRM` 回调，sched_ext 在 `set_next_task_scx()` 里确认 donor，删除原先的 `scx_proxy_donor_start()` 专用入口。空 stub 签名错误（Peter 之前抓到的）已在新分支修正。05/16 的 hook 同时承担两件事：`next == rq->idle` 时 NO_HZ_FULL tick 记账能看到 proxy 停止并清掉 proxy tick 状态（`find_proxy_task()` 已调用 `proxy_resched_idle()` 把 `rq->donor` 也置 idle），以及 reenqueue retry——作者承认两者塞同一个 hook「looks a bit confusing」，但为免再加一个 core 调用点而保留。

## 版本演进与当前进展

- v14（2026-09-24 封面 `20260924075237.GH2009045@noisy.programming.kicks-ass.net` 相关线程）。
- 09-25：Andrea 重做 donor 确认机制（SNT_CONFIRM），把 hrtick v4 前置、删 scx_proxy_donor_start、修正空 stub 签名；自测 scx proxy exec 全过；分支 `git://git.kernel.org/pub/scm/linux/kernel/git/arighi/linux.git scx-proxy-exec-next`。
- Peter：`I'll apply your patches as is`——即不再纠结「是否化简」，先收下，后续再 noodle 差异；同时问 Tejun 分区方式。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra 明确照单全收**：对「用 sched class 回调统一表达 provisional pick 与 donor 确认」既不完全信服（"I'm not convinced either"），但更不喜欢 sched_ext 专属 hook，因此决定先应用原补丁、再慢慢想差异。这是合入层面的实质放行。
- **待 Tejun 表态**：Peter 把球踢给 Tejun——sched_ext 部分由 Peter 一并代收，还是 Tejun 在 sched/core 落地后把 sched_ext 补丁叠在自己的树上再收。
- 分歧集中在代码组织（hook 的职责耦合），而非正确性；作者已自测通过。

## 合入评估

*likelihood=high*。Peter 已表态「照单全收」，只剩 Tejun 对 sched_ext 部分收取方式的选择，以及最终分区落地。*blocking_issues*：Tejun 未回复分区问题。*next_action*：等 Tejun 决定 sched_ext 部分的收取路径；随后按 Peter 安排落地。

## 效果评估

作者自述「passed all my scx proxy exec tests」，但未附 benchmark 数字；正确性由自测背书。暂无量化性能数据。

## 我可以参与的点

- `testing`：在 sched_ext + proxy execution 组合下跑调度压力测试（如 scx 示例调度器 + 互斥锁竞争负载），验证 donor 确认/tick 记账路径，回帖补充实测。
- `review`：05/16 那个「一个 hook 塞两件事」的耦合是否值得拆，作者自己都觉得 confusing，可以给出更清晰的拆分建议。

## 参考链接

- Andrea 重做说明: https://lore.kernel.org/all/arYm4PPMhevWQWsK@gpd4/
- Peter 照单全收 + 问 Tejun: https://lore.kernel.org/all/20260925075628.GI4121339@noisy.programming.kicks-ass.net/
- Andrea 对 05/16 stub/tick 记账说明: https://lore.kernel.org/all/arYvePmLroZ9G_XI@gpd4/
- 分支: https://git.kernel.org/pub/scm/linux/kernel/git/arighi/linux.git scx-proxy-exec-next

---
id: sched-20260925-011
date: 2026-09-25
subject: "sched: Make proxy execution compatible with sched_ext"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260924075237.GH2009045@noisy.programming.kicks-ass.net>"
lore_url: "https://lore.kernel.org/all/20260924075237.GH2009045@noisy.programming.kicks-ass.net/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v14
generated_at: "2026-09-26T01:15:00"
authors:
  - "Andrea Righi"
maintainers_involved:
  - "Peter Zijlstra"
  - "Tejun Heo"
patch_series:
  - version: v14
    msgid: "<20260924075237.GH2009045@noisy.programming.kicks-ass.net>"
    date: 2026-09-24
    summary: "v14 让 proxy execution 与 sched_ext 兼容"
    review_outcome: "09-25 重做为 SNT_CONFIRM donor 确认机制；Peter 照单全收并问 Tejun 分区方式"
merge_assessment:
  likelihood: high
  blocking_issues:
    - "Tejun Heo 尚未回复 sched_ext 部分的收取路径（Peter 代收 vs Tejun 树上叠）"
  next_action: "等 Tejun 决定 sched_ext 部分收取方式，随后按 Peter 安排落地"
contribution_opportunities:
  - kind: testing
    description: "在 sched_ext + proxy execution 组合下跑互斥锁竞争/调度压力测试，验证 donor 确认与 tick 记账路径"
  - kind: review
    description: "05/16 一个 hook 塞两件事（tick 记账 + reenqueue retry）的耦合作者自己都觉得 confusing，可给拆分建议"
source_email_count: 3
related_articles:
  - "sched-20260924-007"
  - "sched-20260923-002"
  - "sched-20260916-002"
tags:
  - sched_ext
  - proxy_execution
---