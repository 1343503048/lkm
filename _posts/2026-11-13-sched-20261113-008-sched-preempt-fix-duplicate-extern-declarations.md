---
id: sched-20261113-008
subject: 'sched/preempt: fix duplicate extern declarations'
date: 2026-11-13
subsystem: sched
type: discussion
status: stalled
severity: none
thread_root_msgid: <20261113010631.139191-10-safocl88@gmail.com>
lore_url: https://lore.kernel.org/all/20261113010631.139191-10-safocl88@gmail.com/
authors:
- Safocl Stollmannovic
maintainers_involved:
- Arnd Bergmann
current_version: v2
patch_series:
- version: v1
  msgid: <20261113001432.128201-10-safocl88@gmail.com>
  date: 2026-11-13
  summary: 删除 preempt.h 中两个声明的 extern 关键字
  review_outcome: changelog 文本乱码，Arnd 表示反对
- version: v2
  msgid: <20261113010631.139191-10-safocl88@gmail.com>
  date: 2026-11-13
  summary: 重写 changelog，说明 asmlinkage 展开机制
  review_outcome: Arnd 再次反对：内核不支持 C++、纯风格偏好，不必发补丁
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
  - Arnd Bergmann 明确反对：内核不以 C++ 为支持目标，省略 extern 属编码风格偏好
  next_action: 作者需放弃该方向，或发起关于头文件 C++ 兼容性的更广泛共识讨论
contribution_opportunities:
- kind: discussion
  description: 参与内核头文件是否应逐步兼容 C++ 编译的讨论
generated_at: '2026-11-14T01:30:00'
source_email_count: 6
related_articles: []
tags:
- preempt
title: 'sched/preempt: fix duplicate extern declarations'
layout: article
---

## TL;DR
Safocl Stollmannovic 提交（作为 10 补丁「去除重复 extern 声明」系列的一篇，v1 与 v2 当日先后发出）删除 `include/asm-generic/preempt.h` 中 `preempt_schedule()` / `preempt_schedule_notrace()` 的 `extern` 关键字，理由是 C++ 编译内核模块时 `extern asmlinkage` 因 `asmlinkage` 展开成 `extern "C"` 而报重复 extern。Arnd Bergmann 明确反对：内核不支持 C++ 编译、这不是用户可见头文件，纯属编码风格偏好，不必为此发补丁。

## 背景与问题
作者描述：用 C++ 编译器编译内核模块会因 `extern asmlinkage` 报「duplicate extern specifier」错误——`asmlinkage` 在 `__cplusplus` 下展开为 `extern "C"`，与前面的 `extern` 重复。作者认为既然代码里已有响应 C++ 编译器的片段，逐步让内核模块可被 C++ 编译是合理方向（附 bugzilla 链接 222257）。

## 技术方案
删除 `preempt_schedule(void)` 与 `preempt_schedule_notrace(void)` 声明前的 `extern` 关键字（`include/asm-generic/preempt.h`，4 处改动）。v2 仅重写了 changelog 措辞（v1 的 changelog 有乱码式占位文本）。

## 版本演进与当前进展
- v1（当日 00:14 发出）：changelog 文本有明显占位乱码。
- v2（当日 01:06 发出）：重写 changelog，说明 `asmlinkage` 展开机制与 bugzilla 链接。
- Arnd Bergmann 两轮回帖反对；作者试图回应（"asmlinkage 含 extern \"C\""）与建议（"可移除全部 extern 或只移除其一"）。

## Maintainer 意见与讨论焦点
- **Arnd Bergmann**：明确指出「changelog 文不对题」「内核不支持 C++ 编译、这不是用户可见头文件」「省略声明里的 extern 只是编码风格偏好，不必发补丁」——实质为否决（NAK）。
- 作者 Safocl 回应尝试论证 C++ 编译路径，但未获认可。

## 合入评估
被 Arnd 明确否决（NAK），且理由充分（内核不以 C++ 为支持目标、非用户可见头、纯风格偏好），合入可能性低，方向应转向更广泛的「extern 声明清理」共识或放弃该改动。

## 效果评估
无性能数据；作者未给出可度量的收益，仅引用 C++ 编译报错。

## 我可以参与的点
- **discussion**：参与「内核头文件是否应逐步兼容 C++ 编译」的讨论，提供维护者视角或数据——但需注意 Arnd 已明确当前方向不被接受。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261113010631.139191-10-safocl88@gmail.com/
