# sched: Replace nr_iowait_cpu() with a bool accessor

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261014-004：Christian Loehle 发清理补丁——menu governor 已不再消费 per-CPU iowait 计数的大小，剩余调用方只关心「零/非零」，故把 `nr_iowait_cpu()` 改成返回 `bool` 的 `cpu_has_iowait()`，纯重构、无行为变更，当日无 review。
- sched-20261015-014（今天）：Peter Zijlstra 回「So I like this」，但困惑为何把 coccinelle 脚本写进 commit message；Christian 发 v2，把 cocci 片段从 commit message 挪走（保留转换说明）。

## 背景与问题
（承接 20261014-004）`nr_iowait_cpu()` 返回 per-CPU iowait 计数的大小，其唯一需要大小值的消费者（menu governor）已删除（`38f83090f515`）。所有 per-CPU 调用方如今只做 `> 0` 的零/非零判定，却仍拿着一个「大小」接口——这是把聚合计数当 per-CPU 状态判据的误用温床（Peter 在同日 cputime 线程批评的正是这一点）。

## 技术方案
（承接 v1）`nr_iowait_cpu()` → `bool cpu_has_iowait(int cpu)`，返回 `atomic_read(&cpu_rq(cpu)->nr_iowait) != 0`；`nr_iowait()` 直接求和保留全局总量。更新 generic 与 s390 idle 记账调用方，替换过时 menu 注释。v2 改动：把 coccinelle 片段从 commit message 挪走（Peter 的疑问），仅保留对转换规则的文字说明。

## 版本演进与当前进展
- v1（2026-10-14）：含 coccinelle 片段于 commit message。
- v2（2026-10-15，<20261015083317.3733733-1-christian.loehle@arm.com>）：按 Peter 意见把 cocci 片段移出 commit message。

## Maintainer 意见与讨论焦点
Peter Zijlstra：「So I like this; but I'm confused about including the cocci script. Why is this?」——认可方向，仅对 commit message 里放 cocci 脚本有疑问，v2 已回应。

## 合入评估
*likelihood=high*。维护者明示喜欢该重构，v2 已消除唯一点疑问，无实质阻塞。*blocking_issues*：无。*next_action*：等 Peter 收取 v2。

## 效果评估
无行为/性能变化（纯接口重构）。无量化数据。

## 我可以参与的点
当前阶段暂无明显参与空间，方向已获维护者认可、等待收取；可持续观察后续。

## 参考链接
- v2 patch：https://lore.kernel.org/all/20261015083317.3733733-1-christian.loehle@arm.com/
- Peter 的回复：https://lore.kernel.org/all/20261015073750.GI4121339@noisy.programming.kicks-ass.net/

---
id: sched-20261015-014
date: 2026-10-15
subject: "sched: Replace nr_iowait_cpu() with a bool accessor"
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<20261015083317.3733733-1-christian.loehle@arm.com>"
lore_url: "https://lore.kernel.org/all/20261015083317.3733733-1-christian.loehle@arm.com/"
authors: ["Christian Loehle"]
maintainers_involved: ["Peter Zijlstra"]
current_version: v2
patch_series:
  - version: v1
    msgid: null
    date: 2026-10-14
    summary: "nr_iowait_cpu() 改 bool cpu_has_iowait()，commit message 含 cocci 片段"
    review_outcome: "Peter 认可方向但困惑 cocci 入 commit message"
  - version: v2
    msgid: "<20261015083317.3733733-1-christian.loehle@arm.com>"
    date: 2026-10-15
    summary: "把 cocci 片段移出 commit message"
    review_outcome: "待 Peter 收取"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等 Peter 收取 v2"
contribution_opportunities: []
generated_at: "2026-10-16T01:05:00"
source_email_count: 2
related_articles: ["sched-20261014-004"]
tags: [cfs, cpufreq]
---