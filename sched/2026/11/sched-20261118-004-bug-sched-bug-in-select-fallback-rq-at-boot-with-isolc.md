# [BUG] sched: BUG() in select_fallback_rq() at boot with isolcpus=domain on the boot CPU and CONFIG_CPUSETS=n

## TL;DR

Waiman Long 报告：`isolcpus=domain` 指定在 boot CPU 上、且关闭 `CONFIG_CPUSETS` 时，启动阶段 `select_fallback_rq()` 触发 `BUG()`（因 isolcpus=domain 把 boot CPU 从 sched domain 中剥离后，fallback 找不到可运行的 CPU）。今日 Frederic Weisbecker 与 Waiman 就「boot CPU 能否被 nohz_full/isolcpus 隔离」展开讨论——结论是 x86 上 boot CPU 不能被 offline、不推荐把 boot CPU 放进 nohz_full，隔离 boot CPU 属「异端」用法。疑似与 Mathieu Desnoyers 的 deadline 系列（其 patch 28/29 改动 `select_fallback_rq()`）相交。

## 背景与问题

`isolcpus=domain` 会把指定 CPU 从调度域（sched domain）中剥离形成隔离域，但这些 CPU 仍需能从全局 CPU 集合中参与 fallback 选择。当 boot CPU 被指定为 `isolcpus=domain` 且内核编译为 `CONFIG_CPUSETS=n`（无 cpuset 兜底）时，启动早期 `select_fallback_rq()` 在找不到合法 fallback CPU 的情况下触发 `BUG()`。根因在于 boot CPU 在 x86 上无法被 offline（hotplug 不支持），隔离它会让 fallback 路径失去最后的保底 CPU。

## 技术方案

今日缓存仅含两封讨论回帖（Waiman 的 follow-up 与 Frederic 的回复），无补丁：

- **Waiman Long**：指出即将到来的 nohz_full CPU 运行时修改不会支持 boot CPU（x86 上 boot CPU 不能被 offline），不建议把 boot CPU 放进 nohz_full boot 参数，但也「不禁止」。
- **Frederic Weisbecker**：回应「可以试试，但愿没人依赖这个；nohz_full 支持隔离 boot CPU，但这是异端（heresy）用法」。

本质上是在厘清「boot CPU 隔离」这一用法的支持边界，而非给出即时修复。

## 版本演进与当前进展

无版本演进。原始 BUG 报告（2026-11-17，Waiman Long）与今日两封讨论均未给出修复补丁。该报告与 Mathieu Desnoyers 的 deadline 系列（其 patch 28/29 改动 `select_fallback_rq()` 的 fallback 语义）在同一线程上下文中被讨论。

## Maintainer 意见与讨论焦点

- **Frederic Weisbecker（nohz/隔离 维护者）**：「nohz_full supports the boot CPU to be isolated but it's a heresy」——功能上允许，但语义上属不推荐的异端用法。
- **Waiman Long（cpuset 维护者）**：x86 上 boot CPU 不能 offline，nohz_full 运行时修改不会支持 boot CPU；不推荐但也不禁止。
- 双方倾向「这是用法边界问题，boot CPU 隔离不保证支持」，未就「是否在 `select_fallback_rq()` 加防御」表态。

## 合入评估

*likelihood=unknown*。目前只是 BUG 报告 + 用法讨论，未见修复补丁，也无维护者承诺修复。*blocking_issues*：① 无修复方案；② 「boot CPU 是否应支持隔离」的边界未定。*next_action*：明确是否要修（在 `select_fallback_rq()` 里为 `CONFIG_CPUSETS=n` + boot CPU 隔离的极端配置加兜底），或直接声明该配置不受支持。

## 效果评估

无数据；BUG() 为启动期崩溃，触发条件明确（isolcpus=domain on boot CPU + CONFIG_CPUSETS=n），作者未给触发频率/复现统计。

## 我可以参与的点

- **testing**：在 `CONFIG_CPUSETS=n` 下用 `isolcpus=domain=<boot CPU>` 复现该 BUG，并验证「boot CPU 不被隔离」或「开启 cpuset」是否规避，为是否修复提供数据。
- **discussion**：就「isolcpus=domain/nohz_full 作用于 boot CPU 是否应被显式拒绝」给出意见。

## 参考链接

- lore thread（BUG 报告）: https://lore.kernel.org/all/dd335ee6-c879-4bee-9ea8-6d9e9216fb0e@redhat.com/
- Waiman 的后续回复: https://lore.kernel.org/all/c40da4c4-1f70-44f7-983c-3349199b5b68@redhat.com/
- Frederic 的回复: https://lore.kernel.org/all/av26-ojv3LkO2vXH@localhost.localdomain/

---
id: sched-20261118-004
date: '2026-11-18'
subject: "[BUG] sched: BUG() in select_fallback_rq() at boot with isolcpus=domain on the boot CPU and CONFIG_CPUSETS=n"
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<dd335ee6-c879-4bee-9ea8-6d9e9216fb0e@redhat.com>"
lore_url: "https://lore.kernel.org/all/dd335ee6-c879-4bee-9ea8-6d9e9216fb0e@redhat.com/"
authors: [Waiman Long]
maintainers_involved: [Frederic Weisbecker]
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["无修复方案", "boot CPU 隔离是否应受支持未定"]
  next_action: "明确是否在 select_fallback_rq 为极端配置加兜底，或声明该配置不受支持"
contribution_opportunities:
  - kind: testing
    description: "CONFIG_CPUSETS=n + isolcpus=domain=<boot CPU> 复现 BUG，验证规避方式"
  - kind: discussion
    description: "就 boot CPU 是否应被 isolcpus/nohz_full 隔离给出意见"
generated_at: "2026-11-19T09:00:00+08:00"
source_email_count: 2
related_articles: []
tags: [nohz, cgroup, crash]
---
