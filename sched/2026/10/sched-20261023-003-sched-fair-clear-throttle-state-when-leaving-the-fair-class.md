# sched/fair: Clear throttle state when leaving the fair class

## TL;DR
Daehyeon Ko 发往 sched 的单补丁修复：CFS 带宽节流在任务从 fair 类迁出（`DEQUEUE_CLASS`）时只把 `p->throttled` 从 `throttled_limbo_list` 里移除却**不清位**；若期间最后一份有限配额被禁用、之后再回到 fair 类，陈旧的 `p->throttled` 会让类切换 dequeue 跳过 `__dequeue_task()`，导致 `p->se.on_rq` 残留、`put_prev_task_fair()` 把实体放回 EEVDF 树，最终 fair picker 选中 `TASK_DEAD` 任务、`do_task_dead()` 触发 `BUG()`。作者在 KASAN/LOCKDEP/DEBUG_LIST 的 v7.3 内核以 CapPrm=CapEff=0 复现（3/3 root、3/3 委派）。已获 Aaron Lu `Reviewed-by`。

## 背景与问题
基于任务的 CFS 带宽节流（task-based throttling）在任务被节流时把它的 fair `sched_entity` 移除，但调度核心仍认为任务在队；`p->throttled` 这一 fair 专属状态会跨 dequeue/enqueue 存续。触发链：

1. `DEQUEUE_CLASS` 把任务从 `cfs_rq->throttled_limbo_list` 移除，但**保留** `p->throttled` 位。
2. 若此时最后一份有限 CFS 配额被禁用（`cfs_bandwidth_used()` 变为 false），而任务在另一个类（RT 等）运行，它就缺席 unthrottle 遍历，`p->throttled` 位残留。
3. 任务回到 fair 类且 `cfs_bandwidth_used()==false` 时走真实 fair enqueue，`p->throttled` 仍被置位。
4. 带宽重启后，一次类切换 dequeue 把这个陈旧位当作 limbo 状态，跳过 `__dequeue_task()`，`p->se.on_rq` 残留；`put_prev_task_fair()` 把实体放回 EEVDF 树，任务却迁去 RT。
5. 退出时 fair picker 可能选中 `TASK_DEAD` 任务，`__schedule()` 返回 `do_task_dead()` → `BUG()`。

## 技术方案
单补丁（`kernel/sched/fair.c`）：把清除 `p->throttled` 的时机从「dequeue 时」改为**只在 `DEQUEUE_CLASS` 时清除**——迁移与 group 移动（`DEQUEUE_SAVE`/`DEQUEUE_MOVE` 类）时保留该位，因为 fair 专属状态不应在离开 fair 类之后继续存续；之后再回到 fair 类时走正常 enqueue 路径（该路径仍会尊重被节流的 cfs_rq）。

## 版本演进与当前进展
*current_version: v1*（`<20261022235234.150957-1-4ncienth@gmail.com>`）。当日 Aaron Lu 给出 Reviewed-by，暂无其他 review。

## Maintainer 意见与讨论焦点
Aaron Lu 给出 *Reviewed-by*（「Thanks!」）。暂无异议或分歧；该补丁尚未被 Peter/Vincent 明确表态是否收取。

## 合入评估
*likelihood=high*。清晰的多步复现（含委派/root 多种配置）+ KASAN/LOCKDEP/DEBUG_LIST 验证，改动点小而语义明确，已获 Aaron Lu Reviewed-by。*blocking_issues*：暂无实质卡点，待 sched 维护者收取。*next_action*：等 Peter/Vincent 收取（可考虑补 `Fixes:` 与 `Cc: stable` 标签，当前邮件未带）。

## 效果评估
正确性修复，无性能数据。作者在 KASAN、LOCKDEP、DEBUG_LIST 的 v7.3 内核上 3/3 root、3/3 委派（uid-1000，CapPrm=CapEff=0）复现 `do_task_dead()` 的 `BUG()`，修复后不再触发（邮件正文未给修复后的轮数，仅描述复现配置）。

## 我可以参与的点
- *kind: review*：核对补丁对 `DEQUEUE_CLASS`/`DEQUEUE_SAVE`/`DEQUEUE_MOVE` 各 dequeue 路径是否都正确（哪些该清、哪些该留），并建议是否补 `Fixes:`/`Cc: stable`。
- *kind: testing*：构造「CFS 带宽配额在任务离开 fair 类期间被禁用再重启」场景验证不再触发 `BUG()`。

## 参考链接
- patch: https://lore.kernel.org/all/20261022235234.150957-1-4ncienth@gmail.com/
- Aaron Lu 回帖: https://lore.kernel.org/all/20261023115201.GA1775284@bytedance.com/

---
id: sched-20261023-003
date: 2026-10-23
subject: "sched/fair: Clear throttle state when leaving the fair class"
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: "<20261022235234.150957-1-4ncienth@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261022235234.150957-1-4ncienth@gmail.com/"
authors: ["Daehyeon Ko"]
maintainers_involved: ["Aaron Lu"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261022235234.150957-1-4ncienth@gmail.com>"
    date: 2026-10-23
    summary: "仅在 DEQUEUE_CLASS 时清除 p->throttled，避免离开 fair 类后残留节流状态"
    review_outcome: "Aaron Lu Reviewed-by"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等 Peter/Vincent 收取；可建议补 Fixes/Cc stable"
contribution_opportunities:
  - kind: review
    description: "核对各 dequeue 路径 DEQUEUE_CLASS/SAVE/MOVE 的清位语义，建议补 Fixes/stable"
  - kind: testing
    description: "构造配额在任务离开 fair 类期间被禁用再重启的场景验证不再 BUG"
generated_at: "2026-10-24T09:02:00"
source_email_count: 2
related_articles: []
tags: [cfs, crash]
---