---
id: sched-20261119-005
date: '2026-11-19'
subject: 'sched: Limit sysctl sched_rt_{period|runtime}_us to RT_GROUP_SCHED'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261113-sched_dl-v3-6-a76ffa1cdeee@linutronix.de>
lore_url: https://lore.kernel.org/all/20261113-sched_dl-v3-6-a76ffa1cdeee@linutronix.de/
authors:
- Sebastian Andrzej Siewior
maintainers_involved: []
current_version: v3
patch_series:
- version: v3
  msgid: <20261113-sched_dl-v3-6-a76ffa1cdeee@linutronix.de>
  date: '2026-11-13'
  summary: patch 6/8：!RT_GROUP_SCHED 时移除 sched_rt_{period|runtime}_us sysctl
  review_outcome: LKP 报 ltp.proc_sched_rt01.fail；作者澄清为有意为之
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - LTP proc_sched_rt01 失败需对齐处理
  next_action: 与测试侧对齐文件缺失即预期，或同步更新 LTP
contribution_opportunities:
- kind: review
  description: 排查是否还有其他工具依赖这两个 sysctl 在 !RT_GROUP_SCHED 下存在
- kind: discussion
  description: 就删除 vs 保留并文档化的接口取舍与 LTP 适配方式讨论
generated_at: '2026-11-20T09:00:00+08:00'
source_email_count: 2
related_articles: []
tags:
- rt
- rt_bandwidth
title: 'sched: Limit sysctl sched_rt_{period|runtime}_us to RT_GROUP_SCHED'
layout: article
---

## TL;DR

Sebastian Andrzej Siewior 的 v3 8 补丁系列（cover 主题「sched/deadline: Reject debugfs dl_server writes for not-active CPUs」，11/13 发出）里的 patch 6/8：在未开启 `RT_GROUP_SCHED` 时删除 `sched_rt_period_us`/`sched_rt_runtime_us` 两个 sysctl——因为向它们写值「毫无作用」，但人们普遍误以为写它们能关闭 RT 限流。Intel 0day（kernel test robot）跑出 `ltp.proc_sched_rt01.fail`：LTP 往这两个文件写、文件已不存在而报错。Sebastian 回应这正是删除的预期副作用、倾向让测试适配而非保留文件。系列其余上下文（cover 全文）未在本日缓存中获取到。

## 背景与问题

`/proc/sys/kernel/sched_rt_period_us` 与 `sched_rt_runtime_us` 这两个全局 sysctl 只在开启 `RT_GROUP_SCHED` 时才真正参与 RT 带宽记账；未开启该 config 时，写它们不产生任何效果。但用户/测试常「以为写这两个文件能关闭 RT throttling」，Sebastian 主张这种误导性接口应当移除，于是 patch 在 `!RT_GROUP_SCHED` 构型下不再创建这两个文件。

## 技术方案

patch 6/8 将两个 sysctl 的注册限定到 `RT_GROUP_SCHED` 开启时；关闭时文件不出现。作为副作用，LTP 的 `proc_sched_rt01` 用例（`kirk -f sched`，x86_64-rhel-9.4 环境，8 线程 Haswell）因 `open/write` 目标文件不存在而 fail——这正是 Sebastian 预期的行为变化：移除无用且误导的 tunable，代价是要下游测试/用户适配。

## 版本演进与当前进展

*current_version: v3（2026-11-13，patch 6/8 的 `thread_root_msgid` 见下）*。本日在缓存中仅有 patch 6/8 的 LKP 回归报告与 Sebastian 的回应，cover 与其它 7 个补丁正文未获取到（系列上下文仅能由 lkp 链接中的分支名「sched-deadline-Reject-debugfs-dl_server-writes-for-not-active-CPUs」佐证）。

## Maintainer 意见与讨论焦点

- **Sebastian Andrzej Siewior（作者，PREEMPT_RT 维护者）**：明确删除是有意为之——「写这些文件毫无用处，人们不知道这一点，反而以为能关闭 RT 限流」；对 LKP 的 fail 未表达改回文件的意向。
- **kernel test robot**：报告 `ltp.proc_sched_rt01.fail`（commit `4f1021f29368`），附 `Closes` 链接，属预期行为变化的回归告警。
- 未见其他维护者（Peter/Ingo）当日表态。潜在分歧：下游测试（LTP）是否应随内核行为变化适配。

## 合入评估

*likelihood=medium*。移除误导性 tunable 的动机合理、且是 PREEMPT_RT 侧维护者一贯的「收紧 RT 接口」方向，但会引起已知的 LTP 用例失败，通常需同步更新测试或确认「文件缺失」为可接受行为后方可合入。*blocking_issues*：LTP `proc_sched_rt01` 失败需处理（改测试或接受行为变化）。*next_action*：作者与测试侧对齐「文件缺失即预期」后提交，或给 LTP 打补丁跳过该场景。

## 效果评估

无性能数据；可见效果为 LTP `proc_sched_rt01.fail`（预期内的接口删除副作用），无其他回归数据。

## 我可以参与的点

- **review**：确认除 LTP 外，是否有其他用户态工具/发行版脚本依赖这两个全局 sysctl 在 `!RT_GROUP_SCHED` 下的存在。
- **discussion**：就「删除 vs 保留并文档化」的接口取舍在列表上发表看法，帮助收敛 LTP 适配方式。

## 参考链接

- lore thread（patch 6/8）: https://lore.kernel.org/all/20261113-sched_dl-v3-6-a76ffa1cdeee@linutronix.de/
- LKP 回归报告: https://lore.kernel.org/all/202611192004.cca8bf73-lkp@intel.com/
- Sebastian 回应: https://lore.kernel.org/all/20261119142348.MkPQ2Fby@linutronix.de/
