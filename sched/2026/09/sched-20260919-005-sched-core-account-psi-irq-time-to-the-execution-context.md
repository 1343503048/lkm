# sched/core: Account PSI IRQ time to the execution context

## TL;DR
增量更新：Zhan Xusheng 的 proxy execution PSI IRQ 记账修复本日获 Hui Su 的 Tested-by——作者实测补丁把 IRQ 时间归属从 donor 移到执行上下文（`rq->curr`），且补上了原测试缺失的 donor != curr 场景。定量的 irq.pressure 归属迁移数据支持修复方向，系列等待维护者收取。

## 背景与问题
背景见 sched-20260918-018：proxy execution 下 `sched_tick()` 把 PSI IRQ 时间记到 `rq->donor`，而 `__schedule()` 记到 `rq->curr`，二者不一致导致 IRQ 时间被记到错误的 cgroup。修复是让 `sched_tick()` 改传 `rq->curr`（恢复 split 之前的语义）。仅影响启用 proxy execution 的配置。

## 技术方案
见 sched-20260918-018：统一 IRQ 时间的记账目标为执行上下文 `rq->curr`。本日无方案变更，仅补充测试证据。

## 版本演进与当前进展
- v1（2026-09-18，`<20260918132915.1236312-1-zhanxusheng@xiaomi.com>`）：修复补丁（见 sched-20260918-018）。
- 本日 Hui Su（`<fe5e2c51f5b90447bbedde4eabf4cfd4.sh_def@163.com>`）给出 Tested-by 与实测数据。

## Maintainer 意见与讨论焦点
本日无维护者直接表态。Hui Su 的测试覆盖了原作者测试缺失的"donor != curr"路径：两个 proxy execution 进程分属两个 cgroup v2，owner 持 CPU0 互斥锁 20s，SCHED_FIFO donor 阻塞其上；x86_64 QEMU（4 vCPU、2GiB）、开启 PSI 与 IRQ 时间记账。无分歧或反对意见。

## 合入评估
*likelihood=high*。修复方向明确、有针对性测试补齐缺口（donor != curr），无反对意见；等待 sched 维护者收取。*blocking_issues*：暂无。*next_action*：维护者 review 后收取。

## 效果评估
Hui Su 实测的 `irq.pressure` 总增量（us）：未打补丁 owner 22,053 / donor 401,127；打补丁后 owner 552,740 / donor 31,566。两次运行均成功完成，归属确实从 donor 移到了执行上下文（owner）。定量印证了"IRQ 时间此前被错记到 donor"。

## 我可以参与的点
当前阶段暂无明显参与空间；如关注 proxy execution + PSI 交互，可在更多负载形态（多 donor、嵌套 mutex）下复测归属正确性。

## 参考链接
- lore（原 patch）: https://lore.kernel.org/all/20260918132915.1236312-1-zhanxusheng@xiaomi.com/
- lore（Hui Su Tested-by）: https://lore.kernel.org/all/fe5e2c51f5b90447bbedde4eabf4cfd4.sh_def@163.com/

---
id: sched-20260919-005
date: '2026-09-19'
subject: 'sched/core: Account PSI IRQ time to the execution context'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260918132915.1236312-1-zhanxusheng@xiaomi.com>'
lore_url: 'https://lore.kernel.org/all/20260918132915.1236312-1-zhanxusheng@xiaomi.com/'
authors:
  - 'Zhan Xusheng'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260918132915.1236312-1-zhanxusheng@xiaomi.com>'
    date: '2026-09-18'
    summary: '让 sched_tick() 把 PSI IRQ 时间记到 rq->curr，与 __schedule() 一致'
    review_outcome: '本日 Hui Su 补齐 donor!=curr 场景测试并给 Tested-by'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '维护者 review 后收取'
contribution_opportunities: []
generated_at: '2026-09-20T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260918-018
tags:
  - proxy_execution
  - psi
---