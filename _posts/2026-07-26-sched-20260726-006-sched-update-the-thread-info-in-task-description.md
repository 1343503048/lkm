---
id: sched-20260726-006
date: 2026-07-26
subsystem: sched
type: fix
status: stalled
severity: low
thread_root_msgid: <uid-637@qq-imap>
lore_url: unknown
authors:
- Huacai Chen
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <uid-637@qq-imap>
  date: 2026-06-09
  summary: 更新 THREAD_INFO_IN_TASK 的 Kconfig 描述：不再要求 arch 删除除 flags 外的所有 thread_info
    字段，改为仅需移除 thread_info 中的 task_struct 指针字段；并完善 try_get_task_stack()/put_task_stack()
    说明覆盖所有 stacktrace 函数。
  review_outcome: 6/9 发出后无人回复，7/26 作者发 'Gentle ping?' 催促。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 自 6/9 发出以来无维护者回应，7/26 的 ping 仍未见答复，处于无人 review 的停滞状态
  next_action: 需要 sched core 维护者（或 init/Kconfig 相关）确认描述修改无误并 pick，作者可考虑抄送更精确的 reviewer
contribution_opportunities:
- kind: review
  description: 核对补丁描述是否与各架构（arm64/x86/riscv/powerpc/loongarch）thread_info 现状一致，回帖
    Reviewed-by 帮助推进
- kind: discussion
  description: 帮忙 Cc 合适的维护者或在列表回帖，避免这个小修复继续被淹没
generated_at: '2026-07-27T01:10:00'
source_email_count: 1
related_articles: []
tags:
- arm64
- x86
- riscv
title: 'sched: Update the THREAD_INFO_IN_TASK description'
layout: article
---

## TL;DR
Huacai Chen 更新 `THREAD_INFO_IN_TASK` 的 Kconfig 描述，纠正一处过时且误导的说明（并非要删除除 flags 外的所有字段，实际只需移除 task_struct 指针字段）。补丁自 6/9 发出后一直无人 review，7/26 作者发出 "Gentle ping?" 催促，目前停滞。

## 背景与问题
`THREAD_INFO_IN_TASK` 用于把 thread_info 从内核栈移入 task_struct。其 Kconfig help 文本源自 4.9 引入时（当时只有 x86、thread_info 仅含 flags 字段），描述称"arch 需要移除除 flags 外的所有 thread_info 字段"。但后续 arm64（4.10）、x86 重新加回 status（4.16）、以及 riscv/powerpc 等架构的 thread_info 都含多个字段且工作正常，说明原描述是错误且误导的，会给 LoongArch 等新架构支持该特性制造不必要的困惑。

## 技术方案
把 help 文本从"移除除 flags 外的所有字段"改为准确表述——"移除 thread_info 中的 task_struct 指针字段并修复运行时 bug"；同时把 `try_get_task_stack()`/`put_task_stack()` 的使用说明从仅 `save_thread_stack_tsk()` 和 `get_wchan()` 扩展为"以及其他 stacktrace 函数"。改动仅涉及 `init/Kconfig`（4 增 3 删），无代码逻辑变化。

## 版本演进与当前进展
当前 v2，2026-06-09 发出。此后长期无 review 回应，2026-07-26 作者发出 "Gentle ping?"。进展停滞在等待维护者关注。

## Maintainer 意见与讨论焦点
截至当日窗口，无任何维护者对本补丁发表意见——既无认可也无反对，纯粹是无人 review。讨论焦点其实"缺失"本身就是问题：文档类小补丁容易被淹没在列表中。

## 合入评估
合入可能性中等。改动正确、风险极低、无争议，理论上很容易被接受，但卡在无人 pick。需要 sched core 或 init/Kconfig 相关维护者确认后 apply；作者也可尝试 Cc 更精确的 reviewer 以打破停滞。

## 效果评估
纯文档描述修正，无运行时效果，无需效果数据。收益为降低新架构支持该特性的理解门槛。

## 我可以参与的点
- 核对补丁描述与各架构 thread_info 现状是否一致，回帖 Reviewed-by 帮助推进
- 帮忙 Cc 合适维护者或在列表回帖，避免这个小修复继续被淹没

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
