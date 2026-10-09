# sched_ext: Add ops.sub_cid_sched_updated()

> **subject**：`sched_ext: Add ops.sub_cid_sched_updated()`
> 本文为增量更新，完整脉络见下。

## TL;DR

- sched-20261006-001：Tejun Heo 为 sub-scheduler 委派模型补上**用量可观测性**——新增 `ops.sub_cid_sched_updated()`：某调度器视角下「跑在一个 cid 上的调度器」变化时通知它（NONE/SELF/直接子 cgroup id，子树内部变化不上报）；开销控制在调度器不变时每次上下文切换一次指针比较、整体挂 static key。3 补丁（+352/−11），2/3、3/3 为 scx_qmap 配套（cid 区间 buffer 修正 + 参与者 cid 时间/分配额对照展示）。当日刚发出、无回帖。
- sched-20261007-007（今天）：**Tejun 回帖「Applied to sched_ext/for-7.4.」**——作者即维护者的自我收取，系列落地 7.4 特性分支。

## 背景与问题

（承接 sched-20261006-001）sub-scheduler 分层里父调度器把 cid 委派给子级后，实际用量是黑盒：按需定尺寸的父级无法度量、想转移 cid 的父级看不到当前占用者。grant/revoke 已有 caps 通知，占用状态此前没有。今天无新背景，事件是收取落地。

## 技术方案

（承接）3 补丁不变：1/3 `ops.sub_cid_sched_updated()`（上下文切换路径埋点、NONE/SELF/子 cgroup id 通知、static key 门控、指针比较级开销）；2/3 scx_qmap cid 区间 buffer 尺寸修正；3/3 scx_qmap 展示每参与者 cid 时间与分配额对照。本日无代码改动。

## 版本演进与当前进展

- v1（10-05 发出，10-06 见报，sched-20261006-001）：3 补丁系列，无第三方 review。
- 10-07：Tejun「Applied to sched_ext/for-7.4.」——进 7.4 特性分支，等 7.4 合并窗口开进主线。

## Maintainer 意见与讨论焦点

无新增意见。作者即 maintainer 的自我收取，一句「Thanks.」收尾；无第三方 review（sub-scheduler 生态当前参与者极少，Tao Cui 一类早期使用者未涉及此 API）。

## 合入评估

*likelihood=merged*（进 `sched_ext/for-7.4`）。该分支为 7.4 合并窗口的暂存地，无意外将随 7.4 进主线。*blocking_issues*：无。*next_action*：关注 7.4 窗口开启后的 pull；sub-scheduler 使用者可开始基于该 API 写「委派用量感知」的父调度器。

## 效果评估

无新数据。机制的量化收益（上下文切换开销）此前已论证为指针比较级；scx_qmap 的对照展示是可观测性收益的载体。

## 我可以参与的点

- `extend`：API 已落地但无消费者示范——写一个按 `sub_cid_sched_updated()` 统计量动态收缩/扩张子级委派的示例调度器（scx_qmap 只做了展示，未做控制回路），这是该特性兑现价值的下一步。
- `testing`：大机器（多子调度器 + 频繁委派变动）上验证通知风暴不会随子级数量放大（设计声称只通知看到变化者）。

## 参考链接

- Applied 回帖: https://lore.kernel.org/all/3871af99ba63dafea637284830f7a399@kernel.org/
- 系列封面: https://lore.kernel.org/all/20261005175520.2756986-1-tj@kernel.org/
- 相关文章：[[sched-20261006-001]]（系列首发）

---
id: sched-20261007-007
date: '2026-10-07'
subject: 'sched_ext: Add ops.sub_cid_sched_updated()'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: '<20261005175520.2756986-1-tj@kernel.org>'
lore_url: 'https://lore.kernel.org/all/3871af99ba63dafea637284830f7a399@kernel.org/'
authors:
  - 'Tejun Heo'
maintainers_involved:
  - 'Tejun Heo'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261005175520.2756986-1-tj@kernel.org>'
    date: '2026-10-05'
    summary: 'ops.sub_cid_sched_updated() + scx_qmap 可观测配套，3 补丁'
    review_outcome: '10-07 Applied to sched_ext/for-7.4（作者即维护者自我收取）'
upstream_commit: null
fixes_commit: null
merged_branch: 'sched_ext/for-7.4'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '随 7.4 合并窗口进主线'
generated_at: '2026-10-08T01:00:00'
contribution_opportunities:
  - kind: extend
    detail: '基于该 API 写委派用量感知的示例父调度器（控制回路）'
  - kind: testing
    detail: '多子调度器场景验证通知不随子级数量放大'
source_email_count: 1
related_articles:
  - sched-20261006-001
tags:
  - sched_ext
  - cgroup
---
