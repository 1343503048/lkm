# sched/cache: Honor asym packing over cache aware scheduling on hybrid system

> **subject**：`sched/cache: Honor asym packing over cache aware scheduling on hybrid system`

## TL;DR

Tim Chen 针对「cache-aware 调度在 AMD big/little 混合平台上的性能回退」发出的修复补丁：asym packing 想把任务放到最高优先级 CPU，cache-aware 调度想把同一进程的任务都聚到一个 LLC（不管 LLC 内 CPU 优先级）。补丁让 asym packing 在「要把任务迁到一个优先级更高的空核」时**优先于** cache-aware 策略——迁到更高性能的空核比 cache 共置更划算。带 `Fixes:` 与双 `Tested-by`（Klaus Kusche、Ricardo Neri）、`Cc: stable # 7.2.x`，Tim 同日表示会给 Peter 发一版 cleaned-up 补丁进 `sched/urgent`。

## 背景与问题

这是「Cache-aware scheduling does not work well with amd big/little cores」讨论串（见相关文章 sched-20260927-005）的收口补丁。回归场景：AMD Ryzen AI HX 370 上跑 cache 密集的 Clang full-LTO 链接。小核频率低得多（3.3 GHz vs 5.1 GHz）、L3 只有一半（8 MB vs 16 MB），把这种任务钉到小核 LLC 会双重受损，full-LTO 构建相比 cache-aware 调度之前的內核显著变慢。

冲突根源：asym packing 与 cache-aware 表达的是**相反**的放置策略——前者要任务跑在最高优先级 CPU，后者要把进程任务共置到同一个 LLC、不管 LLC 内 CPU 优先级高低。

## 技术方案

在 `kernel/sched/fair.c`（+18/−3）两处优先化 asym packing：

1. `can_migrate_llc_task()` 里，在进入「too many threads / exceed LLC capacity」检查**之前**，先判断 `sched_asym(env->sd, dst_cpu, src_cpu)`，若 dst_cpu 相对 src_cpu 优先级更高（asym packing 方向），直接返回 `mig_unrestricted`，跳过 cache-aware 的 LLC 迁移限制。
2. `llc_balance()` 里，在 asym packing 域上，若目标 CPU 优先级高于源组所有 CPU，也优先走 asym packing 的迁移路径。

核心原则：当 asym packing 想迁到一个更高优先级的空核时，让 asym packing 赢——迁到更高性能的空闲核带来的收益大于 cache 共置。

`Fixes: 23b2b5ccc45c ("sched/cache: Introduce helper functions to enforce LLC migration policy")`，`Reported-by: Klaus Kusche`，`Tested-by: Klaus Kusche` / `Tested-by: Ricardo Neri`，`Cc: stable@vger.kernel.org # 7.2.x`。

## 版本演进与当前进展

v1 刚发出（`<221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com>`）。当日 Tim Chen 另在讨论串回帖「Thank you for testing and sharing the results so quickly. I will send a cleaned up patch for sched/urgent branch shortly for Peter」，即本补丁将整理后投 `sched/urgent`。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci**（同日 review）：举了一个边界反例——进入 `can_migrate_llc_task()` 时 dst_cpu=CPU0、src_cpu=CPU1、CPU0 的 asym_prio 更高、无 SMT；此时 `sched_use_asym_prio()` 在不检查 core 是否完全空闲的情况下就返回 true，`sched_asym_prefer()` 也 true，于是 `sched_asym()` 返回 true、直接 `mig_unrestricted`。他质疑这是否有意，若是则补丁说明文字（「asym packing tries to migrate task to an empty core / higher performing idle core」）与实现不一致，需要改注释。
- 无 NAK。作者尚未回应 Kayra 的这一注释与语义问题。

## 合入评估

*likelihood=high*。有 `Fixes:` 指向、两位测试者 `Tested-by`（含最初报告者 Klaus Kusche）、明确 `Cc: stable # 7.2.x`、作者已表态将投 `sched/urgent`，方向无异议。*blocking_issues*：Kayra 指出的注释/语义不一致待作者澄清；尚未见 Peter 的收取或 tip 合入通告。*next_action*：作者回应 Kayra 的语义问题后发 cleaned-up 版进 sched/urgent。

## 效果评估

本补丁无新增 benchmark 数字；回归本身（full-LTO 构建显著变慢）与此前的讨论串证据见 sched-20260927-005（Klaus 复测「looks good」、两个编译任务 wallclock 优于所有 cache-aware 版本且不差于关掉 cache-aware 的基线）。Tested-by 表示复测通过，但未见本补丁独立的量化数字。

## 我可以参与的点

- `review`：回应/分析 Kayra 的边界反例——`sched_asym()` 在「dst 优先级更高但非空闲」时是否也应放行迁移，注释与实现的语义一致性。
- `testing`：在带 big/little + cache-aware 的平台（或关 cache-aware 对照）上验证该补丁的编译负载回归消失、且无新的 LLC 抖动。

## 参考链接

- lore（补丁）: https://lore.kernel.org/all/221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com/
- Kayra 回复: https://lore.kernel.org/all/20260928195232.61319-1-kayracizmeci@gmail.com/
- Tim 的「cleaned up patch for sched/urgent」回帖: https://lore.kernel.org/all/2e64c909e48087b188b8220344ef6576bd273373.camel@linux.intel.com/
- 相关讨论串: [[sched-20260927-005]]

---
id: sched-20260929-003
date: '2026-09-29'
subject: 'sched/cache: Honor asym packing over cache aware scheduling on hybrid system'
subsystem: sched
type: regression
status: under_review
severity: high
thread_root_msgid: '<221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com>'
lore_url: 'https://lore.kernel.org/all/221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com/'
authors:
  - 'Tim Chen'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com>'
    date: '2026-09-29'
    summary: '在 can_migrate_llc_task()/llc_balance() 里让 asym packing 优先于 cache-aware，修复 hybrid 平台 cache-aware 性能回退'
    review_outcome: 'Kayra 指出注释与实现语义不一致并给边界反例；Tim 表示将发 cleaned-up 版进 sched/urgent'
upstream_commit: null
fixes_commit: '23b2b5ccc45c'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - 'Kayra 指出的注释/语义不一致待作者澄清'
  next_action: '作者回应 Kayra 语义问题后发 cleaned-up 版进 sched/urgent'
contribution_opportunities:
  - kind: review
    description: '分析 Kayra 边界反例，澄清 sched_asym 放行条件与注释语义'
  - kind: testing
    description: '在 big/little + cache-aware 平台验证编译负载回归消失且无新 LLC 抖动'
generated_at: '2026-09-30T01:15:00'
source_email_count: 3
related_articles: []
tags:
  - load_balance
  - topology
  - regression
---