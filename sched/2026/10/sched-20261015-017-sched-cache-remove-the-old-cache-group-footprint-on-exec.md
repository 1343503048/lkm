# sched/cache: Remove the old cache group footprint on exec

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261009-007 / 20261010-003：Jemmy Wong 修 `sched_cache_exec_mmap()` 记账遗漏——exec 换掉 cache group 后旧 group 的 footprint 只在 exit 路径被减，共享 mm 任务 exec 后旧贡献残留；v2 抽 helper 让 exec 与 exit 都 drop。
- sched-20261012-008：Chen Yu 指出 footprint 无锁读写竞态；Jemmy 折入 `try_cmpxchg_relaxed()` 等改进，并反问 clamp 是否会掩盖记账 bug。
- sched-20261014-010：Jemmy 回应 clamp 疑问——改走 `atomic_long_t` footprint + `atomic_long_add/sub`、去掉 clamp，并按 Chen Yu 建议「每次 placement pass 只更新一次 footprint」。
- sched-20261015-017（今天）：Chen Yu 认可改名 `sched_cache_switch_grp()` 并请作者发正式版；Jemmy 发 **v3**——`sched_cache_replace_grp()` 改名 `sched_cache_switch_grp()`，subtract 集中一处、exec/exit 共用，footprint 转 `atomic_long_t` 且非返回型原子 add/sub。

## 背景与问题
（承接 20261009-007 → 20261014-010）`grp->footprint` 记录每个任务对 cache group 的 NUMA fault 贡献，退出/exec 时应减掉。exec 换组后旧组贡献只在 exit 路径减，共享 mm（CLONE_VM 而非 CLONE_THREAD）任务 exec 后旧 footprint 残留；且无锁读取会与并发 NUMA placement 竞态。v3 前的讨论已确定：footprint 用 `atomic_long_t`、去 clamp、placement pass 只更新一次。今日焦点是「subtract 放哪」与 helper 职责。

## 技术方案
（承接 v2/discussion）v3（<20261015053604.29927-1-jemmywong512@gmail.com>）：
- `sched_cache_replace_grp()` 改名 `sched_cache_switch_grp()`：语义从「纯指针替换」扩为「离开旧组时 subtract 贡献 + 发布新组指针 + 返回旧组引用供调用方释放」；exec 与 exit 共用（`CONFIG_NUMA_BALANCING` guard 保留一处）。
- footprint 转 `atomic_long_t`，用非返回型原子 add/sub（`atomic_long_sub`）避免返回值的原子序冲突。
- 净增量以 `total_numa_faults` 为基准、每次 placement pass 结算一次，减少共享 cacheline 流量。
- 文档化：exec 的 subtract 必须先于 `task_numa_free()` 重置。

## 版本演进与当前进展
- v2：`try_cmpxchg_relaxed` + clamp 存疑。
- 讨论：Jemmy 尝试把 subtract 移到两个调用方（Chen Yu 建议），发现需要多个小 helper 藏 config guard、代码更碎；遂改为「helper 承担 subtract + 发布 + 返回旧组」的 `switch_grp` 语义。
- v3（今天）：正式落地上述设计。

## Maintainer 意见与讨论焦点
Chen Yu 认可改名与职责整合：「I support this renaming proposal. Please feel free to send a formal version.」分歧点已收敛（subtract 归属从「放调用方」回退到「集中 switch_grp」），Chen Yu 此前还主动提出愿意测试原子更新的性能影响。

## 合入评估
*likelihood=high*。设计经多轮与 Chen Yu 对齐、v3 已发正式版，维护者明确 support。*blocking_issues*：无实质阻塞，待 Chen Yu 对 v3 的最终 Re-view 与测试（原子更新性能影响）。*next_action*：Chen Yu 测试/Reviewed-by v3 后合入。

## 效果评估
暂无量化数据。作者标注该问题为「code inspection 发现，非 workload 复现」；footprint 原子化的性能影响（共享 cacheline 流量）由 Chen Yu 提出验证，尚无结果。

## 我可以参与的点
- *testing*：在 CLONE_VM（无 CLONE_THREAD）场景下验证 exec 后旧 group footprint 正确减掉、无残留；评估原子更新的性能影响。
- *review*：核对 v3 中 subtract 先于 `task_numa_free()` 的时序，以及其他并发 NUMA placement 竞态是否被原子操作覆盖。

## 参考链接
- v3 patch：https://lore.kernel.org/all/20261015053604.29927-1-jemmywong512@gmail.com/
- Chen Yu 的认可：https://lore.kernel.org/all/atBDlr0OvYa-ExeV@chenyu-dev/
- Jemmy 的设计说明：https://lore.kernel.org/all/1174BE6F-35AC-4BBA-BD36-661B6FEC0794@gmail.com/

---
id: sched-20261015-017
date: 2026-10-15
subject: "sched/cache: Remove the old cache group footprint on exec"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261015053604.29927-1-jemmywong512@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261015053604.29927-1-jemmywong512@gmail.com/"
authors: ["Jemmy Wong"]
maintainers_involved: ["Chen Yu"]
current_version: v3
patch_series:
  - version: v1
    msgid: null
    date: null
    summary: "修复 exec 换组后旧 footprint 残留"
    review_outcome: "见 related 文章"
  - version: v2
    msgid: null
    date: 2026-10-10
    summary: "抽 helper 让 exec/exit 都 drop；try_cmpxchg + clamp 存疑"
    review_outcome: "Chen Yu 指出竞态，追问 clamp"
  - version: v3
    msgid: "<20261015053604.29927-1-jemmywong512@gmail.com>"
    date: 2026-10-15
    summary: "改名 sched_cache_switch_grp；footprint 转 atomic_long_t、subtract 集中、去 clamp"
    review_outcome: "Chen Yu 认可改名，待 v3 终审与性能测试"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["待 Chen Yu 终审与原子更新性能测试"]
  next_action: "Chen Yu 测试/Reviewed-by v3 后合入"
contribution_opportunities:
  - kind: testing
    description: "CLONE_VM 场景验证 exec 后 footprint 无残留；评估原子更新性能影响"
  - kind: review
    description: "核对 subtract 先于 task_numa_free() 的时序与并发竞态覆盖"
generated_at: "2026-10-16T01:05:00"
source_email_count: 3
related_articles: ["sched-20261009-007", "sched-20261010-003", "sched-20261012-008", "sched-20261014-010"]
tags: [cfs, numa_balancing]
---