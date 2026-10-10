# sched_ext: Serialize user DSQ destruction against deferred reenqueues

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20260930-002：Hui Su 修 sched_ext deferred reenqueue 的 use-after-free；v1 用「detach 前先取引用」，Andrea Righi 认可 race 但建议避免反复排队 RCU 回调地持引用。
- sched-20261008-012：按 Tejun 建议放弃引用计数、改在罕见的 DSQ 销毁路径加同步（扫每 CPU deferred 列表 + 检查游标，必要时再推迟一轮 RCU 回收），重命名发 v3，KASAN + LOCKDEP 干净；无显式 R-b/A-b。
- sched-20261010-007（今天）：**Tejun 对该 v3 的处理是「换方案」而非直接收**——「I'd rather cancel the pending requests before the grace period」，请他改测 Tejun 当天另发的 for-7.3-fixes 补丁（见 sched-20261010-006）。这条 v3 线实质被 Tejun 的替代方案 supersede。

## 背景与问题
（承接 sched-20260930-002 → sched-20261008-012）deferred reenqueue 下，被 defer 的用户 DSQ 节点可能在 RCU 回调到达 `exit_dsq()` 前就被 detach，deferred 路径其后仍裸用 DSQ 指针，KASAN 报 `slab-use-after-free in run_deferred`。v3 把修复做成「销毁路径同步」（sweep + 检查游标、必要时再推迟一轮 RCU 回收）。今天的关键是维护者对这条修复路径的取舍——Tejun 认为「取消 pending 请求」比「再推迟回收」更干净。

## 技术方案
（承接 v3 的销毁路径同步）今天 Tejun 明确否定「再推迟回收」的方向，给出替代：在宽限期**之前**取消 pending 请求，让 `exit_dsq()` 的「宽限期已冲刷」假设保持不变、其 `WARN` 继续捕获丢失的调度。该替代已由 Tejun 亲自以 for-7.3-fixes 补丁落地（`<20261009220001.196762128-1-tj@kernel.org>`，见 sched-20261010-006）。

## 版本演进与当前进展
- v1（09-30，见 related_articles）：detach 前取引用；Andrea 建议避免反复排队 RCU 回调。
- v3（10-08，`<20261008024753.4096008-1-sh_def@163.com>`）：改销毁路径同步（重命名「Serialize user DSQ destruction against deferred reenqueues」）。
- 今天（Tejun 回帖 `<6782b5c7b47824ce6a89c506cca1186b@kernel.org>`）：不直接收 v3，改为「cancel pending requests before the grace period」的方案，请 Hui Su 改测 Tejun 的 for-7.3-fixes 补丁。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（维护者）：明确否决 v3 的「再推迟回收」路径——「I'd rather cancel the pending requests before the grace period, so that exit_dsq()'s assumption holds and its WARN keeps catching lost schedules」；请 Hui Su 测他的替代补丁。
- 无 NAK 之外的争议；v3 方向被维护者的替代方案 supersede（见 sched-20261010-006，Tejun 的补丁已 applied）。

## 合入评估
*likelihood=low*（对本 v3 本身）。这条 v3 的修复路径被 Tejun 的替代方案取代，v3 不会独立合入；但 bug 本身已由 Tejun 的 for-7.3-fixes 补丁修复（见 sched-20261010-006）。*blocking_issues*：被维护者的替代方案 supersede。*next_action*：Hui Su 按 Tejun 要求测替代补丁（已完成，见 sched-20261010-006 的 Tested-by）。

## 效果评估
v3 自身的 KASAN/LOCKDEP 验证此前已干净（见 sched-20261010-006 关联）；今天无新增测试数据，仅维护者的方向性裁决。

## 我可以参与的点
- 当前阶段该系列已被替代方案收敛，无独立参与空间；可关注替代补丁（sched-20261010-006）在 stable v7.1+ 的回合。

## 参考链接
- v3: https://lore.kernel.org/all/20261008024753.4096008-1-sh_def@163.com/
- Tejun 的替代补丁: https://lore.kernel.org/all/20261009220001.196762128-1-tj@kernel.org/
- Tejun 今日回帖: https://lore.kernel.org/all/6782b5c7b47824ce6a89c506cca1186b@kernel.org/

---
id: sched-20261010-007
date: '2026-10-10'
subject: 'sched_ext: Serialize user DSQ destruction against deferred reenqueues'
subsystem: sched
type: fix
status: superseded
severity: high
thread_root_msgid: '<20261008024753.4096008-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20261008024753.4096008-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved:
  - 'Tejun Heo'
current_version: v3
patch_series:
  - version: v3
    msgid: '<20261008024753.4096008-1-sh_def@163.com>'
    date: '2026-10-08'
    summary: '销毁路径同步（sweep deferred 列表 + 检查游标，必要时再推迟一轮 RCU）'
    review_outcome: 'Tejun 改为「cancel pending requests before grace period」方案，本 v3 被 supersede'
upstream_commit: null
fixes_commit: '84b1a0ea0b7c'
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - '被维护者 Tejun 的替代方案（sched-20261010-006）supersede'
  next_action: '无需继续推进本 v3；bug 已由 Tejun 的 for-7.3-fixes 补丁修复'
contribution_opportunities: []
generated_at: '2026-10-11T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260930-002
  - sched-20261008-012
tags:
  - sched_ext
  - crash
---