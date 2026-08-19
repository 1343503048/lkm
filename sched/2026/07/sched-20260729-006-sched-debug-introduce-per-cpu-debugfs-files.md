# sched/debug: Introduce per-CPU debugfs files

## TL;DR
Aaron Tomlin 的 v2 补丁在 debugfs 下为每个 CPU 增加独立的调度调试文件 `/sys/kernel/debug/sched/cpu/cpu<N>/debug`，避免排查单 CPU 问题时读全量 `/sys/kernel/debug/sched/debug`。v2 已回应 v1 全部意见，等待维护者表态，可关注但非紧急。

## 背景与问题
目前查看某个 CPU 的调度器调试信息只能读 `/sys/kernel/debug/sched/debug`，它会输出所有 online CPU 的信息。在大规模 SMP 拓扑上排查孤立于单个 CPU 的延迟异常或调度问题时，全量输出既慢又难以定位。这是纯调试便利性改进，不修复功能 bug。

## 技术方案
单个 patch，仅改 kernel/sched/debug.c（+43 行）：
- 新增 `debugfs_cpu_init()`，在 `debugfs_sched` 下建 `cpu/` 目录，对 `for_each_possible_cpu` 逐个建 `cpu<N>/debug` 只读文件；
- 读文件走 `sched_debug_cpu_show()` → 复用现有 `print_cpu()` 只打印目标 CPU 的 runqueue 详情；
- 目标 CPU offline 时返回 -ENODEV（v2 新增）。
方案上没有引入新的信息，只是把已有 print_cpu() 的输出按 CPU 切分暴露，实现保守。

## 版本演进与当前进展
- v1（2026-07-28）：基础实现。Peter Zijlstra 和 Zhan Xusheng 认为 commit message 动机不够充分；Zhan 指出未处理 CPU offline。
- v2（2026-07-28，当前）：动机重写为"大规模 SMP 拓扑上的定向交互式调试"；加 `cpu_online()` 检查返回 -ENODEV。
- v2 发出后作者追帖：自动化分析（sashiko.dev）发现了与本 patch 无关的 pre-existing issues，作者问维护者是否希望在本系列一并处理，暂无人答复。

## Maintainer 意见与讨论焦点
v1 阶段 Peter Zijlstra 的核心质疑是动机——为什么需要这个接口，这类"便利性 debugfs 接口"历来需要说服维护者其价值大于维护成本。v2 是否化解了这个质疑还没有回音。目前没有明确 NAK，也没有 Reviewed-by。

## 合入评估
likelihood: medium。改动小、无功能风险、v1 意见均已回应，这些是加分项；但 debugfs 接口扩充需要 PeterZ 认可动机，v1 他的态度偏保留，v2 重写后尚未表态，这是主要不确定性。pre-existing issues 的处理边界如果被要求扩大范围，系列可能拖长。

## 效果评估
暂无效果数据（该类改动无性能语义，价值在于调试体验，作者未给量化对比）。

## 我可以参与的点
- review v2：重点可看 offline CPU 返回 -ENODEV 的语义选择、for_each_possible_cpu 建目录（possible vs online）在 CPU 热插拔下的行为，回帖提供意见。
- 作者关于 pre-existing issues 的提问无人回应，可帮忙分析这些 issue 的性质并建议单独成 patch，属于低门槛的 discussion 参与机会。

## 参考链接
- lore thread: https://lore.kernel.org/lkml/20260728205238.18447-1-atomlin@atomlin.com
- v1: https://lore.kernel.org/lkml/20260728020309.6169-1-atomlin@atomlin.com/
- tip-bot commit: 未获取到

---
subject: "sched/debug: Introduce per-CPU debugfs files"
id: sched-20260729-006
date: 2026-07-29
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260728205238.18447-1-atomlin@atomlin.com>"
lore_url: "https://lore.kernel.org/lkml/20260728205238.18447-1-atomlin@atomlin.com"
authors: [Aaron Tomlin]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: "<20260728020309.6169-1-atomlin@atomlin.com>"
    date: 2026-07-28
    summary: "首版：在 debugfs 下新增 /sys/kernel/debug/sched/cpu/cpu<N>/debug 按 CPU 输出 print_cpu()"
    review_outcome: "Peter Zijlstra 与 Zhan Xusheng 认为动机描述不充分；Zhan 指出缺少 CPU offline 处理"
  - version: v2
    msgid: "<20260728205238.18447-1-atomlin@atomlin.com>"
    date: 2026-07-28
    summary: "重写 commit message 动机（面向大规模 SMP 拓扑的定向交互式调试）；sched_debug_cpu_show() 增加 cpu_online() 检查，offline CPU 返回 -ENODEV"
    review_outcome: "暂无维护者对 v2 的 review；作者追帖询问是否要在本系列处理 sashiko.dev 发现的 pre-existing issues"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "维护者尚未对 v2 表态；v1 的动机质疑是否被 v2 的重写说服还未确认"
    - "自动化工具发现的 pre-existing issues 是否需要随本系列处理，作者在等维护者答复"
  next_action: "等待 Peter Zijlstra / Ingo / Juri / Vincent 对 v2 review，并答复 pre-existing issues 的处理边界"
contribution_opportunities:
  - kind: review
    description: "review v2 的 -ENODEV 语义：offline CPU 返回 -ENODEV 是否合适（对比 cpufreq 等子系统惯例），可回帖给意见"
  - kind: discussion
    description: "作者关于 pre-existing issues 处理边界的提问目前无人回应，可帮忙分析这些 issue 是否值得单独成 patch"
generated_at: "2026-07-30T11:20:00"
source_email_count: 2
related_articles: []
tags: [sched_debug]
---
