---
id: sched-20261115-008
date: '2026-11-15'
subject: 'sched/preempt: fix duplicate extern declarations'
subsystem: sched
type: discussion
status: stalled
severity: none
thread_root_msgid: <20261114165612.368785-10-safocl88@gmail.com>
lore_url: https://lore.kernel.org/all/20261114165612.368785-10-safocl88@gmail.com/
authors:
- Safocl Stollmannovic
maintainers_involved:
- Arnd Bergmann
current_version: v3
patch_series:
- version: v1
  msgid: <20261113001432.128201-10-safocl88@gmail.com>
  date: '2026-11-13'
  summary: 删除 preempt.h 两个声明的 extern 关键字
  review_outcome: changelog 乱码，Arnd 反对
- version: v2
  msgid: <20261113010631.139191-10-safocl88@gmail.com>
  date: '2026-11-13'
  summary: 重写 changelog
  review_outcome: Arnd 再次反对：内核不支持 C++、纯风格偏好
- version: v3
  msgid: <20261114165612.368785-10-safocl88@gmail.com>
  date: '2026-11-15'
  summary: 系列扩至 14 补丁，本篇 diff 不变，changelog 补充 bugzilla 链接
  review_outcome: 当日无新维护者回应
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
generated_at: '2026-11-16T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261113-008
tags:
- preempt
title: 'sched/preempt: fix duplicate extern declarations'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/13/sched-20261113-008-sched-preempt-fix-duplicate-extern-declarations.html">sched-20261113-008</a>：Safocl Stollmannovic 在「去除重复 extern 声明」系列里删除 `include/asm-generic/preempt.h` 两个声明的 extern（理由是 C++ 编译模块时 `extern asmlinkage` 因 asmlinkage 展开成 `extern "C"` 而报重复 extern）；Arnd Bergmann 明确反对（内核不以 C++ 为支持目标、非用户可见头、纯风格偏好），v1/v2 当日先后发出均被否决。
- <a class="article-ref" href="/lkm/2026/11/15/sched-20261115-008-sched-preempt-fix-duplicate-extern-declarations.html">sched-20261115-008</a>（今天）：作者把系列扩到 14 补丁并发出 v3（本缓存仅见昨天落地的 09/14 这篇 sched/preempt），changelog 补上 bugzilla 链接与 C++ 编译论证；diff 内容与 v2 相同。当日无新维护者回应。

## 背景与问题

`asmlinkage` 在 `__cplusplus` 下展开为 `extern "C"`，与声明前的 `extern` 重复，用 C++ 编译器编译内核模块时报 "duplicate extern specifier" 错误。作者认为既然代码里已有响应 C++ 编译器的片段，删除 extern（改为 `asmlinkage void preempt_schedule(void);`）是让模块逐步可被 C++ 编译的一步（附 bugzilla 222257）。

## 技术方案

删除 `include/asm-generic/preempt.h` 中 `preempt_schedule()` / `preempt_schedule_notrace()` 声明前的 `extern` 关键字（`#ifdef CONFIG_PREEMPTION` 内 4 行）。v3 该补丁 diff 与 v2 相同。

## 版本演进与当前进展

- v1（11-13）：changelog 有乱码式占位文本，被 Arnd 反对。
- v2（11-13）：重写 changelog，说明 asmlinkage 展开机制；Arnd 仍反对。
- *current_version: v3（2026-11-15，`<20261114165612.368785-10-safocl88@gmail.com>`）*：系列扩至 14 补丁（标题 `[PATCH v3 09/14]`），本篇 diff 不变、changelog 补上 bugzilla 链接与 C++ 编译论证；当日无新维护者回复。

## Maintainer 意见与讨论焦点

- **Arnd Bergmann**（前两版的反对意见仍生效）：内核不以 C++ 为支持目标、非用户可见头文件、省略声明里的 extern 纯属编码风格偏好，不必为此发补丁——实质为否决（NAK）。
- v3 当日无新维护者表态。

## 合入评估

*likelihood=rejected*。Arnd 的 NAK 理由充分且未因 v3 消除，方向未获接受。*blocking_issues*：Arnd 明确反对（内核不支持 C++、纯风格偏好）。*next_action*：作者需放弃该方向，或发起关于内核头文件 C++ 兼容性的更广泛共识讨论。

## 效果评估

无性能数据；作者未给出可度量的收益，仅引用 C++ 编译报错。

## 我可以参与的点

- **discussion**：参与内核头文件是否应逐步兼容 C++ 编译的讨论，提供维护者或工具链视角（注意 Arnd 已明确当前方向不被接受）。

## 参考链接

- lore thread (v3): https://lore.kernel.org/all/20261114165612.368785-10-safocl88@gmail.com/
- 前序 (v2): https://lore.kernel.org/all/20261113010631.139191-10-safocl88@gmail.com/
