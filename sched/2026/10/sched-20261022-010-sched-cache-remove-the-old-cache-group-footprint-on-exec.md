# sched/cache: Remove the old cache group footprint on exec

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20261009-007 → sched-20261014-010：Jemmy Wong 修 `sched_cache_exec_mmap()` 记账遗漏——exec 换 cache group 后旧 group 的 footprint 只在 exit 路径减；经多轮演进确定 footprint 转 `atomic_long_t`、去 clamp、placement pass 只更新一次，v3 把 `sched_cache_replace_grp()` 改名 `sched_cache_switch_grp()` 并让 exec/exit 共用 subtract。
- sched-20261015-017：Chen Yu 认可改名并请作者发正式版；Jemmy 发 v3。
- sched-20261021-011：Chen Yu 在多 LLC per node 的 Xeon 上跑完整 hackbench 后给出 Reviewed-by + Tested-by——无「超出 run-to-run 方差」之外的明显差异；仅要求一处注释措辞微调（`unsigned long` → `atomic_long_t`）。
- sched-20261022-010（今天）：作者发 v4——恢复 batched 更新旁的收敛注释、纳入 Chen Yu 的 Reviewed-by/Tested-by/Assisted-by、压缩提交描述；Chen Yu 回帖「looks good to me」。本系列带 `Fixes: b636fef85bda`。

## 背景与问题
（承接 sched-20261009-007 → sched-20261015-017）`grp->footprint` 记录每个任务对 cache group 的 NUMA fault 贡献，退出/exec 时应减去；exec 换组后旧组贡献只在 exit 路径减，共享 mm 任务（如较长命的 CLONE_VM 任务）exec 后旧 footprint 残留，且无锁读取与并发 NUMA placement 竞态。v3 已确定：footprint 用 `atomic_long_t`、去 clamp、placement pass 只更新一次。今日无背景新增，进展到 v4 定稿与维护者级背书齐备。

## 技术方案
（承接 v3）v4（`<20261022031933.46869-1-jemmywong512@gmail.com>`）：`sched_cache_switch_grp()`（原 `sched_cache_replace_grp()`）语义为「离开旧组时 subtract + 发布新组指针 + 返回旧组引用」，exec/exit 共用，exec 的 subtract 必须先于 `task_numa_free()` 清零 `total_numa_faults`；footprint 转 `atomic_long_t` 非返回型原子 add/sub；净增量以 `total_numa_faults` 为基准每次 placement pass 结算一次。v4 相对 v3：恢复 batched 更新旁的收敛注释（按 Chen Yu 要求提 `atomic_long_t`）、加入 Chen Yu 的 Reviewed/Tested/Assisted-by、缩短提交描述。

## 版本演进与当前进展
*current_version: v4*（`<20261022031933.46869-1-jemmywong512@gmail.com>`）。v1: `<20261009151215.62878-1-jemmywong512@gmail.com>`，v2: `<20261010111612.31345-1-jemmywong512@gmail.com>`，v3: `<20261015053604.29927-1-jemmywong512@gmail.com>`。当日 Chen Yu 回帖「looks good to me」。

## Maintainer 意见与讨论焦点
Chen Yu（Intel）此前已给 Reviewed-by + Tested-by，并对 v4 表示「looks good」。无反对意见；此前已就「去 clamp、原子记账、注释措辞」达成一致。

## 合入评估
*likelihood=high*。v4 定稿且获 Chen Yu 的 Reviewed-by + Tested-by，方向无异议、带明确 Fixes；*blocking_issues*：无实质卡点；*next_action*：等待维护者收取。

## 效果评估
无新量化数据；此前 Chen Yu 在多 LLC per node Xeon 上的 hackbench 实测无超出方差之外的差异（此系列为记账正确性修复，无性能提升预期）。

## 我可以参与的点
- *kind: review*：审读 v4 的 exec/exit 共用 subtract 与失败 exec 路径的记账正确性。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261022031933.46869-1-jemmywong512@gmail.com/
- Chen Yu 今日回帖：https://lore.kernel.org/all/20261015053604.29927-1-jemmywong512@gmail.com/

---
id: sched-20261022-010
date: 2026-10-22
subject: "sched/cache: Remove the old cache group footprint on exec"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261015053604.29927-1-jemmywong512@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261022031933.46869-1-jemmywong512@gmail.com/"
authors: ["Jemmy Wong"]
maintainers_involved: []
current_version: v4
patch_series:
  - version: v4
    msgid: "<20261022031933.46869-1-jemmywong512@gmail.com>"
    date: 2026-10-22
    summary: "恢复收敛注释、纳入 Chen Yu 三 tag、缩短描述"
    review_outcome: "Chen Yu 认可（looks good），Reviewed+Tested 已给"
upstream_commit: null
fixes_commit: "b636fef85bda"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待维护者收取"
contribution_opportunities:
  - kind: review
    description: "审读 exec/exit 共用 subtract 与失败 exec 路径记账正确性"
generated_at: "2026-10-23T01:20:00"
source_email_count: 2
related_articles: ["sched-20261021-011"]
tags: [cfs, numa_balancing]
---