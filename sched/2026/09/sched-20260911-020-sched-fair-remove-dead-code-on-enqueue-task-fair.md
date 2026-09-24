# sched/fair: remove dead code on enqueue_task_fair()

## TL;DR
Kayra Cizmeci 当日深夜独立投递的清理补丁：删除 enqueue_task_fair() 中不可达的 `cfs_rq->curr == se` 分支（-13/+3）。它与 Peter Zijlstra 在 place_entity 系列讨论（sched-20260911-015）中给出的删除 diff 内容完全一致——可视为作者按 PeterZ 方向把 v3 的落点单独成篇，两条线索正在合流。当日无回帖。

## 背景与问题
enqueue_task_fair() 中 `curr = (cfs_rq->curr == se)` 为真时走 place_entity(cfs_rq, se, flags) 独立分支、跳过常规入队路径。补丁说明该路径「seems to be unachievable」：enqueue 时 se 不可能是 cfs_rq->curr。这一前提在当日 place_entity 系列讨论中被 PeterZ 论证（08-13 即有此说）并由作者的 WARN_ON_ONCE 测试佐证。

## 技术方案
- 删除 `bool curr` 变量与 `curr = (cfs_rq->curr == se);` 判定及 `if (curr) place_entity(...)` 调用；
- `if (!curr) { reweight_eevdf(); place_entity(ENQUEUE_QUEUED); __enqueue_entity(); }` 的包裹解除，三条语句成为无条件顺序执行；
- 顺带删除上方遗留的 `/* XXX comment on the curr thing */` 注释；requeue_delayed_entity() 调用与 dl_server_start() 检查不动。

## 版本演进与当前进展
*current_version: v1（msgid `<20260911155449.1249726-1-kayracizmeci@gmail.com>`，09-11 23:54 入缓存）*，v1 刚发出、暂无 review 意见。

与 sched-20260911-015 的关系：PeterZ 在该讨论中贴出的 diff 与本补丁逐行等价（基线索引略有差异：4d0b94465d19 vs ade1eceb39b8）；作者在该线程承诺「今天或明天发 v3」——本补丁或即为该方向的独立实现，两线如何归并（本补丁吸收进 v3、或 v3 不再包含该清理）待后续确认。

## Maintainer 意见与讨论焦点
本补丁自身当日无回帖；但同一改动在 place_entity 线程已有 PeterZ 的明确支持（给出 diff）与作者接受（承诺发 v3）。潜在关注点：place_entity() 的 curr 分支语义是否有调用方依赖、以及 `/* XXX comment on the curr thing */` 的历史疑问随代码删除而消散。

## 合入评估
*likelihood=medium*：改动方向已有 PeterZ 的 diff 背书，作者测试（WARN_ON_ONCE 长跑未命中）佐证不可达；风险在于与 place_entity 系列 v3 的归并关系未明——若 v3 一并删除，本补丁可能被标记 superseded。*blocking_issues*：独立投稿与 v3 的重复投递需作者自行去重；「不可达」论证还需在更多配置（core-sched 等）下确认。*next_action*：等待维护者对独立补丁或 v3 的收取表态，避免同一清理双线推进。

## 效果评估
无性能数据；效果为代码可读性与路径简化（enqueue 热路径少一个分支判定）。与 place_entity 系列的定位一致：性能影响作者自评不可测量，属清理性质。

## 我可以参与的点
- kind=testing：core-sched/异常 enqueue 配置下长跑 WARN_ON_ONCE(cfs_rq->curr == se)，为删除提供作者之外的不可达证据（与 sched-20260911-015 的验证点共享）。
- kind=review：对照 PeterZ 在 015 线程的 diff 核对等价性，并跟进两条线索的归并结果（防止主线收到重复/冲突的清理）。

## 参考链接
- 补丁：https://lore.kernel.org/all/20260911155449.1249726-1-kayracizmeci@gmail.com/
- PeterZ 在 place_entity 线程的等价 diff：https://lore.kernel.org/all/20260911124256.GZ776954@noisy.programming.kicks-ass.net/

---
id: sched-20260911-020
subject: 'sched/fair: remove dead code on enqueue_task_fair()'
date: '2026-09-11'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260911155449.1249726-1-kayracizmeci@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20260911155449.1249726-1-kayracizmeci@gmail.com/'
authors:
  - 'Kayra Cizmeci'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260911155449.1249726-1-kayracizmeci@gmail.com>'
    date: 2026-09-11
    summary: '删除 enqueue_task_fair() 不可达的 cfs_rq->curr == se 分支（-13/+3），与 PeterZ 在 place_entity 线程给出的 diff 等价。'
    review_outcome: '当日无回帖；同一改动的归宿取决于 place_entity 系列 v3 的形态。'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '与 place_entity 系列 v3 的归并关系未明，存在重复推进风险'
    - '不可达论证需更多配置下的测试佐证'
  next_action: '作者澄清本补丁与 v3 的关系；维护者择一收取'
contribution_opportunities:
  - kind: testing
    description: 'core-sched 等配置下长跑 WARN_ON_ONCE 验证不可达'
  - kind: review
    description: '核对与 PeterZ diff 的等价性并跟进两线归并结果'
generated_at: '2026-09-14T11:35:00'
source_email_count: 1
related_articles:
  - 'sched-20260911-015'
tags:
  - cfs
---
