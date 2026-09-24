# sched/core: Alternate approach to sleeping-owner handling in PROXY_EXEC

## TL;DR
增量更新：K Prateek Nayak 的 proxy execution「sleeping-owner 处理替代方案」PoC（00/16）在 John Stultz 的 torture 压力测试中触发 `sched_change_begin` 的 WARNING，随后 kernel BUG（rt.c:1020）。K Prateek 已认领排查。该系列仍是 PoC（RFC），非合入候选。

## 背景与问题
背景见 sched-20260916-003：这是对 proxy execution 中 sleeping-owner 处理机制的替代设计 PoC（K Prateek Nayak 提出）。本次新增的是正确性 bug 报告。

## 技术方案
当日无方案变化，焦点转为 bug 复现。John Stultz 在 7.2.0-rc4-00032-gf14e36dcc837（QEMU, PREEMPT full）上跑 torture_shuffle 时：先触发 `WARNING: kernel/sched/sched.h:1645 at sched_change_begin`（栈：`__set_cpus_allowed_ptr_locked` ← `torture_shuffle`），随后 `kernel BUG at kernel/sched/rt.c:1020`。

## 版本演进与当前进展
PoC（00/16，`<20260826062901.2137-1-kprateek.nayak@amd.com>`）无新版本。09-17 新增：John Stultz 报告 WARNING+BUG，K Prateek 回复"让我去查我哪里弄坏了"。

## Maintainer 意见与讨论焦点
- **John Stultz**：压力测试复现 WARNING 与 BUG，给出完整栈与内核版本，未做根因判断。
- **K Prateek Nayak**（作者）：认领排查，承诺查找。
- 无 NAK，但也无人认可该 PoC 方向；系列仍停留在 PoC 阶段。

## 合入评估
*likelihood=unknown*。PoC 尚未进入正式评审，本次还出现可复现的正确性 bug，短期内无合入可能。*blocking_issues*：sleeping-owner 处理机制 bug 待修；与既有 PE 系列的关系待明确。*next_action*：作者先修复 stress 测试暴露的 sched_change_begin/rt.c 崩溃。

## 效果评估
无性能数据；出现负面的正确性回归（WARNING + kernel BUG）。

## 我可以参与的点
- kind=testing：按 John Stultz 的复现方式（torture_shuffle + PREEMPT full）复测，帮助定位 rt.c:1020 BUG 的触发条件。
- kind=discussion：分析该 PoC 与 John Stultz/Suleiman 主线 PE 系列（sleeping-owner v31 等）的关系，判断哪条路线更值得投入。

## 参考链接
- lore（PoC cover）: https://lore.kernel.org/all/20260826062901.2137-1-kprateek.nayak@amd.com/
- John Stultz 报告: https://lore.kernel.org/all/CANDhNCoVzHqS627Vv55E==VsJfnDMwvEnvYMxBt5Euu8PRUP3Q@mail.gmail.com/

---
id: sched-20260917-004
date: '2026-09-17'
subject: 'sched/core: Alternate approach to sleeping-owner handling in PROXY_EXEC'
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: '<20260826062901.2137-1-kprateek.nayak@amd.com>'
lore_url: 'https://lore.kernel.org/all/20260826062901.2137-1-kprateek.nayak@amd.com/'
authors:
  - 'K Prateek Nayak'
maintainers_involved:
  - 'John Stultz'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260826062901.2137-1-kprateek.nayak@amd.com>'
    date: '2026-08-26'
    summary: 'sleeping-owner 处理替代方案 PoC（00/16）'
    review_outcome: 'John Stultz 压力测试触发 WARNING+BUG，作者排查中'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - 'PoC 尚未正式评审，且存在可复现的正确性 bug'
  next_action: '作者修复 sched_change_begin/rt.c 崩溃后再谈评审'
contribution_opportunities:
  - kind: testing
    description: '复测 torture_shuffle + PREEMPT full 定位 rt.c:1020 BUG 触发条件'
  - kind: discussion
    description: '分析该 PoC 与主线 PE 系列的关系，评估路线取舍'
generated_at: '2026-09-18T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260916-003
tags:
  - proxy_execution
---
