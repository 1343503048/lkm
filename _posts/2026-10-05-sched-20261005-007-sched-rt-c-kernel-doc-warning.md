---
id: sched-20261005-007
date: '2026-10-05'
subject: 'sched: rt.c: kernel-doc warning'
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: <20261005072738.2902503-2-manuelebnerli@mailbox.org>
lore_url: https://lore.kernel.org/all/20261005072738.2902503-2-manuelebnerli@mailbox.org/
authors:
- Manuel Ebner
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: 无补丁、无回帖
  next_action: 回帖解释 config 门控成因；可选发清理补丁
generated_at: '2026-10-06T01:00:00'
title: 'sched: rt.c: kernel-doc warning'
layout: article
---

> **subject**：`sched: rt.c: kernel-doc warning`

## TL;DR

Manuel Ebner 在 `make W=1` 构建时遇到告警并公开求解：`kernel/sched/rt.c:12:18: warning: 'max_rt_runtime' defined but not used [-Wunused-const-variable=]`——他困惑于该变量「明明在文件后面被用了两处」（`tg_set_rt_bandwidth()` 的 quota 上限检查、`sched_rt_global_validate()` 的全局校验），为何编译器仍报未使用。结合主线代码可解：这两处使用**全部被 config 门控**——`tg_set_rt_bandwidth()` 在 `#ifdef CONFIG_RT_GROUP_SCHED` 内，`sched_rt_global_validate()`/`sched_rt_handler` 在 `#ifdef CONFIG_SYSCTL` 内（rt.c:2849 起）；其 tinyconfig 构建把两者都关掉，`static const u64 max_rt_runtime = MAX_BW` 就成了无引用定义，`-Wunused-const-variable=` 随之触发。当日无人回帖。

## 背景与问题

- 触发条件：tinyconfig + `make W=1`（`-Wunused-const-variable=` 在 W=1 才启用）。
- 现象：`kernel/sched/rt.c:12` 的 `static const u64 max_rt_runtime = MAX_BW`（MAX_BW 即 4 小时量级的带宽上限，注释「More than 4 hours if BW_SHIFT equals 20」）报 unused。
- 疑点来源：文件内确实存在两处使用——`tg_set_rt_bandwidth()` 的 `if (rt_runtime != RUNTIME_INF && rt_runtime > max_rt_runtime) return -EINVAL`（quota 溢出防御）与 `sched_rt_global_validate()` 的 `sysctl_sched_rt_runtime * NSEC_PER_USEC > max_rt_runtime`（sysctl 写入校验）——但提问者没注意到两者的编译条件。
- 注意：邮件标题写 kernel-doc warning，实际是 `-Wunused-const-variable=`（普通编译告警），与 kernel-doc 无关；提问者附的 diff 只是把自己加的两段注释贴出来佐证「used」。

## 技术方案

主线代码（/home/zq/code/linux）核实：

- `tg_set_rt_bandwidth()` 位于 `#ifdef CONFIG_RT_GROUP_SCHED` 区域（rt.c:2639 起）——tinyconfig 无 RT 组调度。
- `sched_rt_global_validate()` 与 `sched_rt_handler()` 位于 `#ifdef CONFIG_SYSCTL` 区域（rt.c:2849 起），注册进 `sched_rt_sysctls[]`（`/proc/sys/kernel/sched_rt_period_us`、`sched_rt_runtime_us`、`sched_rr_timeslice_ms`）——tinyconfig 无 proc sysctl。
- 两条路径全灭 → 定义成为孤儿 → W=1 告警。这不是 bug 而是配置组合下的告警噪音；类似的「config 门内使用」型 unused 告警在 tinyconfig 构建下并不罕见。

候选修法（当日未有人提出，按常规做法）：

- 把 `max_rt_runtime` 定义移进 `#ifdef CONFIG_SYSCTL`（或 `#if defined(CONFIG_RT_GROUP_SCHED) || defined(CONFIG_SYSCTL)`）；
- 或对定义加 `__maybe_unused`。

## 版本演进与当前进展

- 10-05 首问（`<20261005072738.2902503-2-manuelebnerli@mailbox.org>`），无回帖。非补丁系列，纯求解邮件。

## Maintainer 意见与讨论焦点

- 无维护者回帖。
- 焦点即「为什么 used 变量报 unused」——答案是 config 门控（见技术方案），尚无人给出。

## 合入评估

*likelihood=unknown*。尚无补丁；若发一个「定义加 config 门或 `__maybe_unused`」的清理补丁，属典型低风险 trivia 修正，走 sched 维护者正常通道。*blocking_issues*：无补丁、无回帖。*next_action*：有人回帖解释 + 视情况发清理补丁。

## 效果评估

无数据。问题本身为构建告警（噪音级别），不影响运行时行为。

## 我可以参与的点

- `discussion`：直接回帖解释 config 门控成因（`CONFIG_RT_GROUP_SCHED` 与 `CONFIG_SYSCTL` 双关），附两处 `#ifdef` 的行号证据——当下就能闭环这个问答。
- `new_patch`：顺手续一个最小清理补丁（定义移入 `#ifdef CONFIG_SYSCTL` 或加 `__maybe_unused`），tinyconfig W=1 验证告警消失——典型的新人友好型首 patch。

## 参考链接

- 提问邮件: https://lore.kernel.org/all/20261005072738.2902503-2-manuelebnerli@mailbox.org/
