# sched/mmcid: Bound the CID allocation busy wait

## TL;DR
Jiakai Xu 提交修复：为 `mm_get_cid()` 的无界自旋加 32 次重试上限，耗尽时返回 `MM_CID_UNSET` 让任务无 CID 运行、下次调度再重试。这避免了 CID 耗尽时 rq 锁 + 关中断自旋导致的 RCU stall / 整机 lockup 以及模式切换 fixup 线程的 livelock。Peter Zijlstra 强烈质疑——"horribly wrong"，认为未解释切换为何不发生、以及如何不破坏用户态。首版未获认可，需大改。

## 背景与问题
`mm_get_cid()` 在无可用 CID 时会永远自旋。所有调用者都持有 runqueue 锁或 `mm::mm_cid::lock` 且关中断，所以该循环依赖另一个 CPU 在短窗口内释放 CID。该假设在两种情况下失效：
1. per-task 稳态模式下 CID 被任务终身持有、只在 exit/execve 时释放；CID bitmap 耗尽时，自旋任务关中断阻塞本 CPU 一切，升级为 RCU stall，甚至当 text_poke IPI 命中该 CPU 时整机 lockup。
2. 模式切换期间 fixup 线程需获取自旋任务 CPU 的 rq 锁来释放 per-CPU 持有的 CID，而该锁正被自旋任务持有，二者互相等待形成 livelock。

## 技术方案
- 新增 `MM_CID_GET_RETRIES 32` 上限，重试耗尽返回 `MM_CID_UNSET`。
- 所有调用点均可处理该返回值：`mm_cid_from_task()`/`mm_cid_from_cpu()` 在 schedule-in 路径把 per-CPU 与 task 存储置为 `MM_CID_UNSET` 并在下次 schedule-in 重试；`sched_mm_cid_fork()` 同样存储未设置 CID。
- 同时避免耗尽时把 `MM_CID_UNSET` 误当位号喂给 `clear_bit()`。改动集中在 `kernel/sched/sched.h`（45 增 6 删）。

## 版本演进与当前进展
- v1（2026-09-17，`<20260918013454.1850369-1-xujiakai24@mails.ucas.ac.cn>`）：首版，仅此一封；本日 Peter 给出负面 review，暂无后续版本。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：整体否定——"这听起来非常不对（horribly wrong）。它既没解释为什么 transition 没有发生，也没解释它如何不彻底违反/破坏用户态"。另指出注释风格破损、与作者早前注释不一致（两处 "broken comment style"）。
- 核心分歧：Peter 认为返回 `MM_CID_UNSET` 让任务无 CID 运行可能破坏用户态语义，且作者没有论证"为什么不能正常完成 CID 分配/切换"。

## 合入评估
likelihood=low。方向（避免无界自旋）合理，但 Peter 的质疑直指方案正确性与用户态影响，当前版本不足以合入。blocking_issues：需解释为何 transition 无法推进、以及无 CID 运行对用户态的正确性影响；注释风格需统一。next_action：作者回帖说明切换卡住的根因与 `MM_CID_UNSET` 对用户态的兼容性（或改用其他收敛方案），修复注释风格后重发。

## 效果评估
邮件未附性能/复现数据。作者描述了 CID 耗尽导致 RCU stall / lockup / livelock 的机理（推理，未见实测数据）。修正确实消除了一类潜在整机 hang，但 Peter 对其正确性存疑。

## 我可以参与的点
- kind=review：帮助论证"返回 MM_CID_UNSET 无 CID 运行"对用户态/RCU 读路径是否安全，或指出更稳妥的收敛方式（如受控释放而不是放弃分配）。
- kind=discussion：澄清 per-task 与 per-CPU CID 模式切换的时序，回应 Peter 关于"transition 为何不发生"的疑问。

## 参考链接
- lore（patch）: https://lore.kernel.org/all/20260918013454.1850369-1-xujiakai24@mails.ucas.ac.cn/

---
id: sched-20260918-003
date: '2026-09-18'
subject: 'sched/mmcid: Bound the CID allocation busy wait'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260918013454.1850369-1-xujiakai24@mails.ucas.ac.cn>'
lore_url: 'https://lore.kernel.org/all/20260918013454.1850369-1-xujiakai24@mails.ucas.ac.cn/'
authors:
  - 'Jiakai Xu'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260918013454.1850369-1-xujiakai24@mails.ucas.ac.cn>'
    date: '2026-09-17'
    summary: '为 mm_get_cid 自旋加 32 次上限，耗尽返回 MM_CID_UNSET'
    review_outcome: 'Peter 质疑正确性与用户态影响、注释风格，未获认可'
upstream_commit: null
fixes_commit: '9a723ed7facff'
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - '需解释 transition 无法推进的根因'
    - '需论证 MM_CID_UNSET 无 CID 运行不破坏用户态'
  next_action: '作者回应 Peter 质疑并修复注释风格后重发'
contribution_opportunities:
  - kind: review
    description: '论证无 CID 运行对用户态/RCU 读路径的安全性'
  - kind: discussion
    description: '澄清 per-task/per-CPU CID 模式切换时序'
generated_at: '2026-09-19T09:00:00'
source_email_count: 2
related_articles: []
tags:
  - mm
  - cgroup
---
