# [GIT PULL] scheduler fixes

## TL;DR

Ingo Molnar 于 09-27 16:04（北京时间）向 Linus 发出 `tip/sched/urgent` 拉取请求（分支 `sched-urgent-2026-09-27`，顶端 a0bb6fac53fa7cf1cadb487b43d4c9276a6b82e3），共 7 条修复、6 位作者、10 个文件 +388/-134，全部集中在 **sched/cache（cache-aware 调度）** 与一条 **sched/core PSI IRQ 记账**修复：LLC 误调度（Tim Chen、Lu Wang）、cache 分组统计 UAF（Tim Chen 两条）、跳过 kthread 加固 cache-aware（Chen Yu）、热插拔刷新 LLC capacity（Davi Chaves Azevedo）、PSI IRQ 记到执行上下文（Zhan Xusheng）。这批是此前跟踪过的多个 cache-aware 系列与 PSI 记账系列的合入节点。

## 背景与问题

拉取内容与既有跟踪系列的对应关系（除 Chen Yu 一条外均有前文）：

- **sched/cache: Keep nr_pref_llc_running in the runnable domain**（Tim Chen）——修 LLC 误调度，对应 sched-20260916-011。
- **sched/cache: Decouple sched_cache_group from mm to fix UAF**（Tim Chen）——对应 sched-20260916-012。
- **sched/cache: Introduce task_struct->sched_cache_grp to fix UAF**（Tim Chen）——对应 sched-20260916-013。
- **sched/cache: Honor migrate_llc_task semantics in active load balance**（Lu Wang）——对应 sched-20260903-011。
- **sched/cache: Refresh LLC capacity across CPU hotplug**（Davi Chaves Azevedo）——对应 sched-20260916-010。
- **sched/core: Account PSI IRQ time to the execution context**（Zhan Xusheng）——对应 sched-20260924-012。
- **sched/cache: Skip kernel threads for cache aware scheduling to rubustify the code**（Chen Yu）——本日缓存与前文均未找到独立跟踪文章（未获取到对应前文）。

本日邮件是 pull request 正文，不含新讨论；「背景」是身份变化：这批修复从评审线程进入 `tip/sched/urgent` 祖先图，成为下游分支与 stable 回合可对齐的事实。

## 技术方案

无新代码。diffstat 显示改动集中在 cache-aware 调度主路径：`kernel/sched/fair.c | 417 +++++++++++++++++++++++++++++++++--------`（LLC 误调度 + UAF 修复合计），`include/linux/sched.h +20/-`、`include/linux/mm_types.h +15/-`（`sched_cache_grp` 结构迁移，配合 mm 解耦 UAF），`kernel/exit.c 28 +--`、`kernel/fork.c +2`（任务生命周期挂钩），`drivers/base/cacheinfo.c +11/-`（LLC capacity 热插拔刷新），`kernel/sched/topology.c 22 +--`。`kernel/sched/core.c | 2 +-` 是 Zhan Xusheng PSI IRQ 记账修复的落点。

## 版本演进与当前进展

- 各修复各自发出并被本报逐篇跟踪（见 related_articles，时间跨度 09-03 至 09-24）。
- 09-27 16:04（北京时间）：Ingo 汇总拉取，按「LLC 误调度 → 统计 UAF → kthread 加固 → 热插拔 capacity → PSI 记账」组织描述。
- 进 Linus 树时点：本日缓存无 pr-tracker-bot 回执，未获取到。

## Maintainer 意见与讨论焦点

线程内只有 Ingo 的 pull request 本身。可读出的信号：这批修复被归为 urgent（针对 v7.3-rc4 窗口），其中 cache-aware 调度（sched/cache）占了 6/7，说明 cache-aware 的 LLC 误调度与 UAF 正确性问题被当作 -rc 阶段重点；Zhan Xusheng 的 PSI IRQ 记账修复从「09-24 发出」到「09-27 进 tip」仅约 3 天。pull 正文无任何反对或保留意见。

## 合入评估

*likelihood=merged*（已成事实）：`status=merged_tip`，合入分支 `tip/sched/urgent`（`sched-urgent-2026-09-27`，顶端 a0bb6fac53fa7cf1cadb487b43d4c9276a6b82e3）。*blocking_issues*：进 Linus 树的合并 commit 与 -rc 归属未获取到；各条修复的 stable 回合情况未获取到。*next_action*：跟踪 pr-tracker-bot 合并回执确认进主线时点；按 commit 与内部分支/OLK 分支逐条比对回合状态。

## 效果评估

pull request 无 benchmark 数据。可量化信息是规模与时延：7 条修复、10 文件、+388/-134，最后一批（PSI 记账，09-24 发出）到进 tip 约 3 天。收益属正确性一类：LLC 误调度消除、cache 分组统计 UAF 修复、热插拔后 LLC capacity 不再低估、PSI IRQ 时间记到真正执行的上下文。

## 我可以参与的点

- `new_patch`：回合自查——7 条修复与内部分支/OLK 逐条比对是否已带。其中 `sched_cache_grp` 解耦改动涉及 `mm_types.h`/`sched.h`/`exit.c`/`fork.c`，凡在内部分支动过 cache-aware 或任务生命周期代码的都要留意 rebase 冲突。
- `testing`：`sched/core: Account PSI IRQ time to the execution context` 影响 proxy execution 下 PSI 统计口径，可在 proxy 调度压测场景验证 `/proc/pressure/irq` 与实际执行任务的归属一致性。

## 参考链接

- 本日 pull request: https://lore.kernel.org/all/arjOHApB_TyTUsCY@gmail.com/
- 相关文章/系列：
  - [[sched-20260903-011]] sched/cache: Honor migrate_llc_task semantics in active load balance
  - [[sched-20260916-010]] sched/cache: Refresh LLC capacity across CPU hotplug
  - [[sched-20260916-011]] sched/cache: Keep nr_pref_llc_running in the runnable domain
  - [[sched-20260916-012]] sched/cache: Decouple sched_cache_group from mm to fix UAF
  - [[sched-20260916-013]] sched/cache: Introduce task_struct->sched_cache_grp to fix UAF
  - [[sched-20260924-012]] sched/core: Account PSI IRQ time to the execution context
- 进 Linus 树的合并点: 未获取到（无 pr-tracker-bot 回执）
- stable backport: 未获取到

---
id: sched-20260927-009
date: 2026-09-27
subject: "[GIT PULL] scheduler fixes"
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<arjOHApB_TyTUsCY@gmail.com>"
lore_url: "https://lore.kernel.org/all/arjOHApB_TyTUsCY@gmail.com/"
authors:
  - "Ingo Molnar"
maintainers_involved:
  - "Ingo Molnar"
current_version: v1
patch_series:
  - version: v1
    msgid: "<arjOHApB_TyTUsCY@gmail.com>"
    date: 2026-09-27
    summary: "Ingo 向 Linus 拉取 tip/sched/urgent（sched-urgent-2026-09-27，顶端 a0bb6fac53fa7cf1cadb487b43d4c9276a6b82e3）：7 条修复、6 位作者、10 files +388/-134。sched/cache 6 条（LLC 误调度、统计 UAF×2、kthread 加固、热插拔 capacity）+ sched/core PSI IRQ 记账 1 条。逐条细节见 related_articles。"
    review_outcome: "无讨论回帖；除 Chen Yu 一条外均为既有跟踪系列的合入节点，进 tip 后各自系列状态变为 merged_tip。"
upstream_commit: null
fixes_commit: null
merged_branch: "tip/sched/urgent（sched-urgent-2026-09-27）"
merge_assessment:
  likelihood: merged
  blocking_issues:
    - "进 Linus 树的合并 commit 与 -rc 归属未获取到（无 pr-tracker-bot 回执）"
    - "各条修复的 stable 回合情况未获取到"
  next_action: "跟踪 pr-tracker-bot 合并回执；按 commit 与内部分支/OLK 逐条比对回合状态"
contribution_opportunities:
  - kind: new_patch
    description: "回合自查：7 条修复与内部分支/OLK 逐条比对；sched_cache_grp 解耦涉及 mm_types.h/sched.h/exit.c/fork.c，注意 rebase 冲突面"
  - kind: testing
    description: "在 proxy 调度压测场景验证 PSI IRQ 时间记到执行上下文后 /proc/pressure/irq 与执行任务归属一致性"
generated_at: "2026-09-28T09:00:00"
source_email_count: 1
related_articles:
  - sched-20260903-011
  - sched-20260916-010
  - sched-20260916-011
  - sched-20260916-012
  - sched-20260916-013
  - sched-20260924-012
tags:
  - load_balance
  - psi
  - cgroup
---