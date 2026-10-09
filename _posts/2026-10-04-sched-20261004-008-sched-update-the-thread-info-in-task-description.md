---
id: sched-20261004-008
date: '2026-10-04'
subject: 'sched: Update the THREAD_INFO_IN_TASK description'
subsystem: sched
type: discussion
status: stalled
severity: none
thread_root_msgid: <20261004134034.3622868-1-chenhuacai@loongson.cn>
lore_url: https://lore.kernel.org/all/20261004134034.3622868-1-chenhuacai@loongson.cn/
authors:
- Huacai Chen
maintainers_involved: []
current_version: v3
patch_series:
- version: v3
  msgid: <20261004134034.3622868-1-chenhuacai@loongson.cn>
  date: '2026-10-04'
  summary: 仅更新 Cc 列表的第三次重发（内容同 V2）
  review_outcome: 四个月零 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 无 maintainer 回应（两次点名未果）
  next_action: 换通道（-mm/Kconfig）或当面提醒
contribution_opportunities:
- kind: review
  description: 给内容正确的沉睡补丁发 Reviewed-by 助推收取
generated_at: '2026-10-05T01:00:00'
source_email_count: 1
related_articles:
- sched-20260726-006
- sched-20260907-015
tags:
- sched/debug
- documentation
title: 'sched: Update the THREAD_INFO_IN_TASK description'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/07/26/sched-20260726-006-sched-update-the-thread-info-in-task-description.html">sched-20260726-006</a>：Huacai Chen（LoongArch）修正 `THREAD_INFO_IN_TASK` Kconfig help——原文写于 4.9（仅 x86、thread_info 只剩 flags），要求 arch「移除除 flags 外所有字段」；实际 arm64/x86/riscv/powerpc 都保留多字段且工作正常，真实要求只是移除 task_struct 指针字段。V2 于 06-09 发出。
- <a class="article-ref" href="/lkm/2026/09/07/sched-20260907-015-sched-update-the-thread-info-in-task-description.html">sched-20260907-015</a>：作者第二次 ping——直接点名 Ingo/Peter「Could you please spend some time reviewing this?」。无 review、无版本变化，从 06-09 起挂了近三个月。
- <a class="article-ref" href="/lkm/2026/10/04/sched-20261004-008-sched-update-the-thread-info-in-task-description.html">sched-20261004-008</a>（今天）：作者发 **V3**——内容与 V2 相同，唯一变化是「Update the Cc list」（补齐收件人）。四个月未获任何 review 的 4 增 3 删纯文档改动继续换版本号求关注。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/07/sched-20260907-015-sched-update-the-thread-info-in-task-description.html">sched-20260907-015</a>）`THREAD_INFO_IN_TASK` 的 Kconfig help 文本过时且误导：4.9 引入时仅 x86 支持、thread_info 只剩 flags 字段，故描述要求「arch 需移除除 flags 外的所有 thread_info 字段」；但其后 arm64（4.10，多字段）、x86 自身（4.16，加回 status）、riscv/powerpc 等都多字段运行良好——实际约束只是「移除 thread_info 里的 task_struct 指针字段」（该指针在 info 入 task 后可由容器关系推导）。误导性描述抬高 LoongArch 等新架构的接入成本。

## 技术方案

（承接，V3 无内容变化）`init/Kconfig` +4/−3：

- 「remove all thread_info fields except flags」→「remove the task_struct pointer field from thread_info」；
- `try_get_task_stack()`/`put_task_stack()` 的适用说明从 `save_thread_stack_tsk()`、`get_wchan()` 扩展到「及其它 stacktrace 函数」。

零代码逻辑改动、零运行时影响。

## 版本演进与当前进展

- V2（06-09）→ 09-07 第二次 ping → V3（10-04，`<20261004134034.3622868-1-chenhuacai@loongson.cn>`，仅改 Cc 列表）。

## Maintainer 意见与讨论焦点

- 无任何 review 意见。改的是 init/Kconfig 但产权在 sched（THREAD_INFO_IN_TASK 历史上由 sched/core 维护者收）——Ingo/Peter 均未回应两次点名。

## 合入评估

*likelihood=low*。内容零争议、改动极小，但四个月零 review 的记录说明它卡在维护者注意力而非技术；V3 换 Cc 列表能否改变命运未知。*blocking_issues*：无 maintainer 回应。*next_action*：可能需要走 -mm/Kconfig 通道或当面（LPC/CPU 热插拔圈）提醒。

## 效果评估

无（纯文档）。

## 我可以参与的点

- `review`：给该补丁发一条 Reviewed-by（内容确实正确、事实链完整）——多人 R-b 是推动沉睡补丁被收取的少数有效手段之一。

## 参考链接

- lore（V3）: https://lore.kernel.org/all/20261004134034.3622868-1-chenhuacai@loongson.cn/
