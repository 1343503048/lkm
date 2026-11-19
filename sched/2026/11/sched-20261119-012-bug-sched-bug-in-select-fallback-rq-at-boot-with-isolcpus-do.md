# [BUG] sched: BUG() in select_fallback_rq() at boot with isolcpus=domain on the boot CPU and CONFIG_CPUSETS=n

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261118-004：Waiman Long 报告 `isolcpus=domain` 指定在 boot CPU 上、且关闭 `CONFIG_CPUSETS` 时，启动阶段 `select_fallback_rq()` 触发 `BUG()`；Frederic Weisbecker 与 Waiman 就「boot CPU 能否被隔离」讨论（x86 上 boot CPU 不可 offline，隔离 boot CPU 属异端用法）。
- sched-20261119-012（今天）：**Mathieu Desnoyers 加入并定性为回归**——同一命令行在 `CONFIG_CPUSETS=y` 下可启动；`CONFIG_CPUSETS=n` 下 revert `bf5b0c27fad2`（"sched: Switch the fallback task allowed cpumask to HK_TYPE_DOMAIN"）即可启动。他支持 Waiman「拒绝把 boot CPU 域隔离」的修法（要求拒绝时打印信息并继续启动），并主动提出可在同样 VM（含/不含 CONFIG_CPUSETS）里帮忙测补丁。

## 背景与问题

（承接 sched-20261118-004）`isolcpus=domain` 会把指定 CPU 从调度域剥离形成隔离域，但这些 CPU 仍需参与全局 fallback 选择。当 boot CPU 被指定为 `isolcpus=domain` 且 `CONFIG_CPUSETS=n` 时，启动早期 `select_fallback_rq()` 找不到合法 fallback CPU 而触发 `BUG()`（日志里没有任何指向 isolcpus 的线索，只报 BUG）。Mathieu 今日确认这是一个回归：罪魁是 `bf5b0c27fad2`（把 fallback 任务允许 cpumask 切到 `HK_TYPE_DOMAIN`），revert 后即可启动。

## 技术方案

今日为讨论、无补丁落定：

- Mathieu 认可 Waiman「在 cpuset 卸载/隔离 boot CPU 时拒绝域隔离」的方案，前提是拒绝时打印可理解的信息、启动继续下去（而不是静默或重启）。
- 该方案的代价：会改变一个今天能工作的配置——`isolcpus=domain,0,1` + `CONFIG_CPUSETS=y`。
- Mathieu 主动提供测试资源（同样的 VM、含/不含 CONFIG_CPUSETS）。

## 版本演进与当前进展

*current_version: 无补丁（bug 报告阶段）*。今日无补丁发出，讨论从「是否允许隔离 boot CPU」推进到「回归责任 commit + 修法取舍 + 测试承诺」。

## Maintainer 意见与讨论焦点

- **Mathieu Desnoyers**：定性为回归（`bf5b0c27fad2`）、支持 Waiman 的拒绝方案并附加「打印信息 + 继续启动」的要求，愿测补丁。
- **Waiman Long**（此前，20261118-004）：主张 cpuset 侧拒绝域隔离 boot CPU。
- **Frederic Weisbecker**（此前）：参与 boot CPU 是否可被隔离的讨论。
- 无 NAK；分歧点是「拒绝 boot CPU 域隔离」会牺牲一个现有可用配置（isolcpus=domain,0,1 + CONFIG_CPUSETS=y）。

## 合入评估

*likelihood=medium*。修法方向（拒绝 boot CPU 域隔离）已有人支持、作者愿意测，但需在「修回归」与「保留现有可用配置」之间取舍，且需 Peter（select_fallback_rq/hotplug 侧）把最终方案定下来。*blocking_issues*：修法取舍未定（拒绝隔离 vs 保留配置）。*next_action*：Waiman 出补丁，Mathieu 测试（含/不含 CONFIG_CPUSETS），Peter 定夺。

## 效果评估

无性能数据；现象为启动阶段 BUG()。Mathieu 给出的可复现证据：`CONFIG_CPUSETS=y` 可启动、`=n` revert `bf5b0c27fad2` 可启动。

## 我可以参与的点

- **testing**：在 x86 + `isolcpus=domain,0` + `CONFIG_CPUSETS=n` 上复现 BUG，并验证 Waiman 拒绝方案（补丁发出后）的启动日志清晰、能继续启动。
- **review**：评估「拒绝 boot CPU 域隔离」对 `isolcpus=domain,0,1 + CONFIG_CPUSETS=y` 这一现有配置的破坏面。

## 参考链接

- lore thread（首次报告）: https://lore.kernel.org/all/dd335ee6-c879-4bee-9ea8-6d9e9216fb0e@redhat.com/
- Mathieu 的回归定性: https://lore.kernel.org/all/64f061ff-5a1d-44b3-a759-7daedfd67996@efficios.com/

---
id: sched-20261119-012
date: '2026-11-19'
subject: "[BUG] sched: BUG() in select_fallback_rq() at boot with isolcpus=domain on the boot CPU and CONFIG_CPUSETS=n"
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<dd335ee6-c879-4bee-9ea8-6d9e9216fb0e@redhat.com>"
lore_url: "https://lore.kernel.org/all/dd335ee6-c879-4bee-9ea8-6d9e9216fb0e@redhat.com/"
authors: [Waiman Long]
maintainers_involved: [Mathieu Desnoyers]
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: "bf5b0c27fad2"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["修法取舍未定（拒绝隔离 vs 保留现有配置）"]
  next_action: "Waiman 出补丁，Mathieu 测试，Peter 定夺"
contribution_opportunities:
  - kind: testing
    description: "isolcpus=domain,0 + CONFIG_CPUSETS=n 复现并验证拒绝方案"
  - kind: review
    description: "评估拒绝 boot CPU 域隔离对现有可用配置的破坏面"
generated_at: "2026-11-20T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261118-004]
tags: [affinity, topology, regression]
---