# sched: Convert last bits of deprecated static key usage

## TL;DR

Hongyan Xia 收掉调度器里最后一批已废弃的 static key 用法：`kernel/sched/fair.c` 的 CFS bandwidth `__cfs_bandwidth_used` 从 `struct static_key` + `static_key_false()` / `static_key_slow_inc_cpuslocked()` 迁到 `DEFINE_STATIC_KEY_FALSE()` + `static_branch_unlikely()` / `static_branch_inc_cpuslocked()`；`kernel/sched/core.c` 的 PREEMPT_DYNAMIC 更新宏也一并改用 `static_branch_enable/disable()`。作者称完成后调度器内废弃 static key API 归零。
本日为 v2，明确是「rebase 并修掉 core.c 里一个大冲突」的版本，说明它与同期 PREEMPT_DYNAMIC 改动同抢 `__sched_dynamic_update()` 这一块。09-03 无回帖。

## 背景与问题

raw static key 不带类型信息，无法防止误配（例如对默认为 TRUE 的 key 使用 `static_key_false()`），而且 `static_key_{true/false}()` 这组命名本身有歧义，因此被废弃。调度器内的多数站点已在此前的补丁中转换，本补丁处理剩下的两处，其中 `sk_dynamic_*` 使用的 `static_key_{enable/disable}()` 严格说并未废弃，作者只是顺带统一到新 API。

## 技术方案

- `kernel/sched/fair.c`（`CONFIG_CFS_BANDWIDTH` + `CONFIG_JUMP_LABEL` 分支）：`static struct static_key __cfs_bandwidth_used` -> `DEFINE_STATIC_KEY_FALSE(__cfs_bandwidth_used)`；`static_key_false()` -> `static_branch_unlikely()`；`static_key_slow_inc_cpuslocked()` / `static_key_slow_dec_cpuslocked()` -> `static_branch_inc_cpuslocked()` / `static_branch_dec_cpuslocked()`。
- `kernel/sched/core.c`（PREEMPT_DYNAMIC）：宏 `preempt_dynamic_key_enable(f)` / `preempt_dynamic_key_disable(f)` 改名为 `preempt_dynamic_branch_enable(f)` / `preempt_dynamic_branch_disable(f)`，实现从 `static_key_enable(&sk_dynamic_##f.key)` 改为 `static_branch_enable(&sk_dynamic_##f)`，调用点在 `__sched_dynamic_update()` 的 full/lazy 分支。
- 总计 8 增 8 删，作者声明 "No functional change"。

## 版本演进与当前进展

- v1 不在当日缓存中（仅见于 v2 的 changelog 自述）。
- v2（09-03 19:57）两项改动：补充说明旧 API 为何被废弃；rebase 并修掉 `core.c` 的一个大冲突。
- 09-03 内无回帖、无 tag、未进入任何分支。
- 与 [[sched-20260903-013]]（PREEMPT_DYNAMIC 简化）以及已合入的 [[sched-20260902-002]] 改动同一代码区域；v2 的大冲突正是这一点的直接证据。

## Maintainer 意见与讨论焦点

未获取到维护者意见：本日为 v2 首发于当日缓存，无任何回帖。
值得注意的不是态度而是**冲突面**：作者自己记录 v2 "Rebase and fix a big conflict in core.c"，而冲突位置就是 `__sched_dynamic_update()` 与 `preempt_dynamic_key_*` 宏——同一区域同时是 Mark Rutland 的 PREEMPT_DYNAMIC 精简系列（[[sched-20260903-013]]）的工作对象，且 Mark 在 09-02 已承认该处 `sched_dynamic_show()` 的字符串数组与 enum 不一致问题"probably needs a bit more rework"。也就是说这 4 行改动的最终形态取决于两条线谁先落地。

## 合入评估

likelihood: **possible**。
依据：纯清理、无功能变化、改动面 8 行，且是既有废弃 API 迁移序列的收尾（前序补丁已合入），维护者一般不会有异议；作者已主动 rebase 到当前基线并解决冲突。
卡点：一是零评审、零 tag，本日为 v2 首发；二是与 PREEMPT_DYNAMIC 精简系列存在明确的代码区域竞争，`fair.c` 那半部分基本无风险，`core.c` 那半部分需要与 [[sched-20260903-013]] 的落地顺序协商，很可能被要求等 Mark 的 v3 之后再 rebase；三是这类收尾补丁通常由 maintainer 直接收进 tip 的 cleanup 分支，不会单独催促进度。

## 效果评估

邮件中未提供效果数据，补丁本身也声明 "No functional change"，因此不存在性能指标可评估。可核实的收益是静态的：转换后调度器代码内不再有废弃 static key API 调用（作者原话 "After this fix, scheduler code has zero deprecated static key APIs now"），且 `fair.c` 侧从 `static_key_slow_*_cpuslocked()` 换到 `static_branch_*_cpuslocked()` 后，类型信息与默认方向（FALSE）由 `DEFINE_STATIC_KEY_FALSE` 显式表达，消除了误配可能。无 benchmark、无编译产物尺寸对比。

## 我可以参与的点

1. 最实际的一条：给出与 Mark Rutland 系列的落地顺序意见。若愿意推进，可在 `tip/sched/core` + PREEMPT_DYNAMIC v2 系列之上实测本 v2，回报是否仍有冲突——这直接决定它是独立合入还是被吸收进 Mark 的重做。
2. 可复核代码点：`CONFIG_JUMP_LABEL=n` 分支下 `cfs_bandwidth_used()` 的退化实现是否与新 `DEFINE_STATIC_KEY_FALSE` 语义一致；以及 `static_branch_inc_cpuslocked()` 对调用者持 `cpus_read_lock()` 的要求在 CFS bandwidth 记账路径上是否处处成立。
3. 清理型扫尾：用同样的判据在内核其它子系统查一遍残留 `static_key_true/false()` 用法（本补丁只收了 sched），这属于低风险、易被接受的贡献入口。
4. 回合视角：OLK-6.6 回合该补丁前需确认 `static_branch_*_cpuslocked()` 与 `DEFINE_STATIC_KEY_FALSE` 在目标内核的 `jump_label.h` 中已存在；6.6 的 `preempt_dynamic_*` 宏形态不同，`core.c` 部分通常不可直接 cherry-pick，`fair.c` 部分价值更高。

## 参考链接

- 本补丁 v2：https://lore.kernel.org/all/20260903115728.11864-1-hongyan.xia@transsion.com/
- 相关文章/系列：
  - [[sched-20260902-002]] PREEMPT_DYNAMIC 简化 + static key 迁移（已合入）。
  - [[sched-20260903-013]] Simplify PREEMPT_DYNAMIC v2（同一代码区域的并行系列）。
- 相关代码：
  - `kernel/sched/fair.c` `cfs_bandwidth_used()` / `__cfs_bandwidth_used`
  - `kernel/sched/core.c` `__sched_dynamic_update()` / `preempt_dynamic_branch_{enable,disable}`

---
id: sched-20260903-007
date: '2026-09-03'
subject: 'sched: Convert last bits of deprecated static key usage'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: '<20260903115728.11864-1-hongyan.xia@transsion.com>'
lore_url: https://lore.kernel.org/all/20260903115728.11864-1-hongyan.xia@transsion.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Hongyan Xia
maintainers_involved: []
patch_series:
- "sched: Convert last bits of deprecated static key usage"
merge_assessment:
  likelihood: possible
  blocking_issues:
  - "09-03 内无回帖、无 Acked-by/Reviewed-by"
  - "core.c 部分与 PREEMPT_DYNAMIC 精简系列争用同一区域，v2 已因此需修大冲突"
  next_action: "确认与 Simplify PREEMPT_DYNAMIC 系列的落地顺序，并在最新基线上重测冲突"
contribution_opportunities:
- "在 tip/sched/core + PREEMPT_DYNAMIC v2 之上实测本补丁是否仍冲突并回帖"
- "核对 CONFIG_JUMP_LABEL=n 分支与 cpus_read_lock 前提是否仍成立"
- "把同类 static_key_true/false() 残留扫描推广到 sched 之外的子系统"
source_email_count: 1
related_articles:
- sched-20260902-002
tags:
- sched/core
---
