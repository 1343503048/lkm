---
id: sched-20260907-015
date: '2026-09-07'
subject: 'sched: Update the THREAD_INFO_IN_TASK description'
subsystem: sched
type: fix
status: stalled
severity: none
thread_root_msgid: <20260609031924.97092-1-chenhuacai@loongson.cn>
lore_url: https://lore.kernel.org/all/CAAhV-H55Lb4mAcubjc6hFka_RJB7pkQkJMzkVWaU4se7jt2-0g@mail.gmail.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Huacai Chen
maintainers_involved: []
patch_series:
- version: v2
  msgid: <20260609031924.97092-1-chenhuacai@loongson.cn>
  date: '2026-06-09'
  summary: init/Kconfig 中 THREAD_INFO_IN_TASK 的 help 文本修正：不再要求 arch 移除除 flags 外的所有
    thread_info 字段，改为仅需移除其中的 task_struct 指针字段并修复运行时 bug；并把 try_get_task_stack()/put_task_stack()
    的适用说明扩展到其它 stacktrace 函数。4 增 3 删，无代码逻辑改动。本日无新版本、无改动，仅作者第二次 ping。
  review_outcome: 06-09 发出后至今零回复：07-26 作者第一次 ping（Gentle ping?），09-07 第二次 ping 并点名
    Ingo 与 Peter（Could you please spend some time reviewing this?）。无 Reviewed-by/Acked-by，无维护者表态。
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无明确接手人：改的是 init/Kconfig 文本，但语义属各 arch 的 thread_info 移植约定，sched 与 arch 两侧都未认领
  - 补丁无争议且风险为零，纯粹卡在无人 pick（已 3 个月、两次 ping、零回复）
  - 邮件中未给出目标合并窗口
  next_action: 若有已转换 THREAD_INFO_IN_TASK 的架构同学，按自家 thread_info 现状核对新 help 文本并回 Reviewed-by；除此之外无需投入跟踪成本
contribution_opportunities:
- kind: review
  description: 用 arm64/x86/riscv/powerpc 的 thread_info 现状核对新 help 文本是否准确，回帖 Reviewed-by
    打破无人签名的停滞
- kind: discussion
  description: 内部涉及 init/Kconfig、Documentation/scheduler/ 等跨子系统归属的文档补丁，提交前先确认 maintainer
    归属并预设升级节奏，以本线程为反面案例
source_email_count: 1
related_articles:
- sched-20260726-006
tags:
- arm64
- x86
- riscv
title: 'sched: Update the THREAD_INFO_IN_TASK description'
layout: article
---

## TL;DR

本文为增量更新，完整背景见 sched-20260726-006（Huacai Chen 的 `THREAD_INFO_IN_TASK` Kconfig 描述修正，V2 于 06-09 发出）。本日唯一一封邮件是**作者自己第二次 ping**：Huacai Chen 直接点名 `Hi, Ingo, Peter, Could you please spend some time reviewing this?`。没有任何 review 意见、没有版本变化（仍是 V2）、没有新代码。补丁从 06-09 起算已经挂了整整三个月无人处理，而它改的内容本身争议为零。

## 背景与问题

补丁要修的是一处**过时且误导的 Kconfig help 文本**：`THREAD_INFO_IN_TASK` 的描述写于 4.9 引入时（当时只有 x86、且 thread_info 只剩 flags），要求 arch「移除除 flags 外的所有 thread_info 字段」；但随后 arm64、x86、riscv、powerpc 等架构都在 thread_info 里保留了多个字段且工作正常，实际要求只是移除 thread_info 中的 task_struct 指针。细节与改动内容见 [[sched-20260726-006]]。

本日没有任何技术层面的新内容，因此这一节的「问题」变成了流程问题：一个 `init/Kconfig` 里的 4 增 3 删文档改动，为什么三个月推不动。

## 技术方案

无变化。仍是 `init/Kconfig` 上 `THREAD_INFO_IN_TASK` help 文本的修正（外加把 `try_get_task_stack()` / `put_task_stack()` 的适用说明从 `save_thread_stack_tsk()`、`get_wchan()` 扩展到其它 stacktrace 函数），零代码逻辑改动、零运行时影响。

## 版本演进与当前进展

- 06-09 03:19（+08:00）V2 发出：`<20260609031924.97092-1-chenhuacai@loongson.cn>`，此后长期无回应。
- 07-26 作者第一次 ping（"Gentle ping?"），仍无回应。
- **09-07 15:38 作者第二次 ping**，直接把 Ingo 与 Peter 两人点名到正文第一行。
- 本日邮件中没有维护者回复、没有 Reviewed-by/Acked-by、没有 V3；目标窗口与是否会被某个 -rc 收走，邮件中均未提及（未获取到）。

## Maintainer 意见与讨论焦点

本日仍**零意见**。可归纳的只有作者侧的姿态变化：第一次是 "Gentle ping?"（不点名），这次直接 `Hi, Ingo, Peter, Could you please spend some time reviewing this?`——点名到具体两个人，说明作者已判断这封补丁不是「邮件太多被漏掉」，而是**没人认为它归自己管**。

这条线程的结构性问题是归属模糊：改的是 `init/Kconfig` 里的一个 `config` 项帮助文本，但它描述的语义属于各 arch 的 thread_info 移植约定，V2 的动机又来自 LoongArch 的适配。线程里没有任何人（包括作者）指明谁对该文本负责，因此它既不会被 sched 维护者当性能/正确性问题处理，也不会被 arch 维护者主动认领。这一点前作已记录为「文档类小补丁容易被淹没在列表中」，本日算是确认了该判断。

## 合入评估

`likelihood=unknown`。改动正确、风险为零、无争议，技术上没有任何反对理由；但它已经三个月推不动且本日没有出现任何维护者动作，因此无法用「会被接受」来给一个更高评级——停滞的原因不在补丁质量，在于没有人 pick。`severity=none`、`status=stalled` 不变。

卡点清单（相对前作无新增）：
1. 缺一个明确的接手人：sched/core 与 arch 两侧都没有表态；
2. 无任何 tag，作者也没尝试扩大 Cc 名单或改用 `scripts/get_maintainer.pl` 指向的其他维护者；
3. 无目标窗口，因而也不会进入任何 merge window 的检查视野。

## 效果评估

无数据，也不需要数据：纯 Kconfig help 文本改动，无运行时效果。收益仍是「降低新架构支持 `THREAD_INFO_IN_TASK` 的理解门槛」——即避免下一个 arch（本例是 LoongArch）在移植时按错误的描述去删掉不该删的字段。本日没有可观测的进展指标，唯一量化事实是时间：**V2 已存在 3 个月、被 ping 过 2 次、得到 0 条回复**。

## 我可以参与的点

- **一条回贴就能推动的事**：任何已完成 `THREAD_INFO_IN_TASK` 转换的架构（arm64、x86、riscv、powerpc）维护者/开发者，按自家 `thread_info` 现状核对新 help 文本是否准确，然后回一个 `Reviewed-by`。这是本补丁唯一真正的瓶颈——它缺的不是讨论而是第二个签名。若我们内部有 arch 移植文档沿用了旧描述，也顺手能确认这处修正是否与我们自己的经验一致。
- **把它转成内部流程检查项**：这条线程是「文档/Kconfig 类补丁在跨子系统归属处会长期停滞」的典型样本。内部提交涉及 `init/Kconfig`、`Documentation/scheduler/` 这类既属 sched 又属 arch 的内容时，应在发出前先确认 maintainer 归属（`get_maintainer.pl` + 直接点名），并预设「若无回应 2 周后升级」的节奏——作者的 3 个月 / 两次 ping 是反面教材。
- **值得顺带核对的一处**：help 文本里提到的 `try_get_task_stack()` / `put_task_stack()` 使用点（`save_thread_stack_tsk()`、`get_wchan()` 及其它 stacktrace 函数）在我们自己分支上是否也仍然成立。若内部有 out-of-tree 的 stacktrace/wchan 相关改动，这是少数能与该描述直接对上或冲突的地方；本线程中无人验证过这一点。
- 不需要跟进的部分：本补丁没有性能、没有调度决策影响，不必按调度器补丁的评审强度处理，也不必安排测试资源。

## 参考链接

- 相关文章：[[sched-20260726-006]] 前作（背景、改动内容与第一次 ping）。
- 本日作者的第二次 ping: https://lore.kernel.org/all/CAAhV-H55Lb4mAcubjc6hFka_RJB7pkQkJMzkVWaU4se7jt2-0g@mail.gmail.com/
- V2 补丁本体（06-09）: https://lore.kernel.org/all/20260609031924.97092-1-chenhuacai@loongson.cn/
- tip-bot commit: 未获取到
- stable backport: 未获取到
- 相关代码：`init/Kconfig` 中 `THREAD_INFO_IN_TASK` 的 help 文本；`save_thread_stack_tsk()` / `get_wchan()`
