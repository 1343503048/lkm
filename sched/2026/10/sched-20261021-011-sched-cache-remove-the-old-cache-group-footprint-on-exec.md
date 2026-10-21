# sched/cache: Remove the old cache group footprint on exec

## TL;DR
本文为增量更新，完整脉络见相关文章，要点如下。

- sched-20261009-007 → sched-20261014-010：Jemmy Wong 修 `sched_cache_exec_mmap()` 记账遗漏——exec 换 cache group 后旧 group 的 footprint 只在 exit 路径减；经多轮演进确定 footprint 转 `atomic_long_t`、去 clamp、placement pass 只更新一次，v3 把 `sched_cache_replace_grp()` 改名 `sched_cache_switch_grp()` 并让 exec/exit 共用 subtract。
- sched-20261015-017：Chen Yu 认可改名并请作者发正式版；Jemmy 发 v3。
- sched-20261021-011（今天）：Chen Yu 在多 LLC per node 的 Xeon 上跑完整 hackbench 后给出 *Reviewed-by* + *Tested-by*——无「超出 run-to-run 方差」之外的明显差异；仅要求一处注释措辞微调（`unsigned long` → `atomic_long_t`）。Jemmy 回复 v4 将恢复收敛注释、按建议改类型并重排文本，并纳入两个 tag。

## 背景与问题
（承接 sched-20261009-007 → sched-20261015-017）`grp->footprint` 记录每个任务对 cache group 的 NUMA fault 贡献，退出/exec 时应减去；exec 换组后旧组贡献只在 exit 路径减，共享 mm 任务 exec 后旧 footprint 残留，且无锁读取与并发 NUMA placement 竞态。v3 已确定：footprint 用 `atomic_long_t`、去 clamp、placement pass 只更新一次。今日无背景新增，进展集中在获得维护者级实测背书与 v4 定稿。

## 技术方案
（承接 v3）v3（`<20261015053604.29927-1-jemmywong512@gmail.com>`）：`sched_cache_switch_grp()` 语义扩为「离开旧组时 subtract + 发布新组指针 + 返回旧组引用」，exec/exit 共用；footprint 转 `atomic_long_t` 非返回型原子 add/sub；净增量以 `total_numa_faults` 为基准每次 placement pass 结算一次。今日 v4 计划：恢复 batched 更新旁的收敛注释、类型按 Chen Yu 建议写 `atomic_long_t`、重排文本。

## 版本演进与当前进展
*current_version: v3*（v4 待发）。

## Maintainer 意见与讨论焦点
Chen Yu（Intel，cache-aware 工作核心开发者）：多 LLC per node Xeon 上完整 hackbench 无超方差之外的明显差异，仅个别大 run-to-run 方差的「假阳性回退」；认可「把 footprint 变成准确计数器」的方向，给 Reviewed-by + Tested-by，并要求注释措辞微调（不能写成 `unsigned long`）。Jemmy 已确认 v4 会落实。无分歧。

## 合入评估
*likelihood=high*。方向已获核心开发者 Reviewed-by + Tested-by，仅剩注释措辞与 v4 定稿。*blocking_issues*：近乎无，仅 v4 关键词微调待发。*next_action*：作者发 v4（改注释 + 类型措辞）后即可推动收取。

## 效果评估
Chen Yu 的完整 hackbench（Xeon 多 LLC per node）显示大部分条项 IMPROVED（如 process 4 2 提升 15.60%、threads 8 4 提升 43.15%），但存在一批大 stderr% 的 REGRESSED 点；Chen Yu 复测后认为「系统饱和时数据并不稳定，可能是另一个问题，我后续再查」——即这些回退更可能来自饱和噪声，非本补丁引入。

## 我可以参与的点
- `discussion`：Chen Yu 提到的「系统饱和时 hackbench 数据不稳定」值得深挖，可帮定位该稳定问题（与本补丁正交）。
- `review`：v4 发出后核对注释措辞与 `atomic_long_t` 类型表述是否满足 Chen Yu 的要求。

## 参考链接
- Chen Yu 的 Reviewed/Tested-by + hackbench：https://lore.kernel.org/all/atiP8TwaDDtbImRn@chenyu-dev/
- Jemmy 的 v4 计划回帖：https://lore.kernel.org/all/A81AB6C4-6821-454D-9C2D-716A3D0DFE6B@gmail.com/

---
id: sched-20261021-011
date: 2026-10-21
subject: "sched/cache: Remove the old cache group footprint on exec"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261015053604.29927-1-jemmywong512@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261015053604.29927-1-jemmywong512@gmail.com/"
authors: ["Jemmy Wong"]
maintainers_involved: []
current_version: v3
patch_series:
  - version: v3
    msgid: "<20261015053604.29927-1-jemmywong512@gmail.com>"
    date: 2026-10-15
    summary: "sched_cache_switch_grp() 统一 exec/exit 的 footprint subtract，转 atomic_long_t"
    review_outcome: "Chen Yu 多 LLC Xeon 实测 Reviewed-by + Tested-by，要求注释措辞微调"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "作者发 v4（改注释 + atomic_long_t 措辞）后推动收取"
contribution_opportunities:
  - kind: discussion
    description: "深挖 Chen Yu 观察到的饱和 hackbench 数据不稳定问题"
  - kind: review
    description: "v4 发出后核对注释与 atomic_long_t 类型表述"
generated_at: "2026-10-22T01:30:00"
source_email_count: 2
related_articles: ["sched-20261015-017"]
tags: [cfs, numa_balancing]
---