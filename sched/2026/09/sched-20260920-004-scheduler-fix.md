# scheduler fix

## TL;DR
增量更新：Andrea Righi 的 proxy donor 误报迁移告警修复（sched/core: Avoid false migration warning for proxy donors）已随 sched/urgent 进入 Ingo Molnar 今日发给 Linus 的拉取请求（sched-urgent-2026-09-20，HEAD fe3c73d7bc76），等待进入主线；kernel test robot 对 tip/sched/urgent 分支报 BUILD SUCCESS（178 个 config 构建通过）。

## 背景与问题
背景见 sched-20260918-020：proxy execution 会把被阻塞 donor 的调度上下文搬到锁 owner 的 CPU，`set_task_cpu()` 对 migration-disabled 任务无条件告警，导致误报。该修复此前已合入 tip/sched/urgent，本日 Ingo 正式把 sched/urgent 树打包向 Linus 拉取。

## 技术方案
本次拉取仅含一条调度修复（`kernel/sched/core.c`，8 增 1 删）：在 `set_task_cpu()` 告警中排除被阻塞的 proxy donor。具体代码改动见 sched-20260918-020，本日无新代码变更，仅是合入主线前的拉取动作。

## 版本演进与当前进展
- 修复（09-15，Andrea Righi）：已合入 tip/sched/urgent（commit fe3c73d7bc769e7afc252f867a3421fe168b898d）。
- 09-20：Ingo Molnar 发 [GIT PULL] scheduler fix（`<aq-rDdJ7JlxW7gMZ@gmail.com>`），请 Linus 拉取 `sched-urgent-2026-09-20`（fetch up to fe3c73d7bc76）。
- 09-20：kernel test robot 报 [tip:sched:urgent] BUILD SUCCESS（`<202609201741.NLli0TP7-lkp@intel.com>`），178 个 config 构建通过、10 个跳过，耗时 1100 分钟。

## Maintainer 意见与讨论焦点
- **Ingo Molnar**：作为 sched/urgent 维护者整理并发送拉取请求，无异议。

## 合入评估
*likelihood=merged*。已合入 tip/sched/urgent，正等待 Linus 拉取进入主线。*blocking_issues*：无。*next_action*：跟踪 sched-urgent 拉取在主线落地。

## 效果评估
无性能数据；kernel test robot 对 tip/sched/urgent 分支 BUILD SUCCESS（178 config 通过），构建层面无回归。

## 我可以参与的点
当前阶段暂无明显参与空间（已合入待主线拉取），可持续观察 proxy execution 相关后续修复。

## 参考链接
- lore（GIT PULL）: https://lore.kernel.org/all/aq-rDdJ7JlxW7gMZ@gmail.com/
- lore（BUILD SUCCESS）: https://lore.kernel.org/all/202609201741.NLli0TP7-lkp@intel.com/
- tip gitweb: https://git.kernel.org/tip/fe3c73d7bc769e7afc252f867a3421fe168b898d

---
id: sched-20260920-004
date: '2026-09-20'
subject: 'scheduler fix'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: '<aq-rDdJ7JlxW7gMZ@gmail.com>'
lore_url: 'https://lore.kernel.org/all/aq-rDdJ7JlxW7gMZ@gmail.com/'
authors:
  - 'Andrea Righi'
maintainers_involved:
  - 'Ingo Molnar'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260915184101.2621252-1-arighi@nvidia.com>'
    date: '2026-09-15'
    summary: 'set_task_cpu 告警排除被阻塞 proxy donor'
    review_outcome: '已合入 tip/sched/urgent，本日发 GIT PULL 向主线拉取'
upstream_commit: 'fe3c73d7bc769e7afc252f867a3421fe168b898d'
fixes_commit: null
merged_branch: 'tip/sched/urgent'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '跟踪 sched-urgent 拉取在主线落地'
contribution_opportunities: []
generated_at: '2026-09-21T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260918-020
tags:
  - proxy_execution
---