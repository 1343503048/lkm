---
id: sched-20260920-001
date: '2026-09-20'
subject: 'sched/stats: Fix run_delay over-count for migrated sched_delayed tasks'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260909133345.1572954-1-albin_yang@163.com>
lore_url: https://lore.kernel.org/all/20260920043116.1298017-1-albin_yang@163.com/
authors:
- Wei Yang
maintainers_involved: []
current_version: v2
patch_series:
- version: v1
  msgid: <20260909133345.1572954-1-albin_yang@163.com>
  date: '2026-09-09'
  summary: 迁移 delayed 任务时不更新 last_queued，避免 run_delay 虚增
  review_outcome: 本日 Kayra 纠正迁移路径描述，作者确认并承诺 v2 修正
- version: v2
  msgid: <20260920043116.1298017-1-albin_yang@163.com>
  date: '2026-09-20'
  summary: 修正 commit message 迁移路径论证，加 Chen Yu Reviewed-by
  review_outcome: Kayra Reviewed-by，并指出 sched_info_enqueue 注释待修
upstream_commit: null
fixes_commit: 152e11f6df29
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 sched/stats 维护者收取入 tip
contribution_opportunities:
- kind: testing
  description: 复测 active load balance / NUMA balancing 压力下的迁移路径
- kind: review
  description: 跟进 Kayra 即将发出的 sched_info_enqueue 注释修正补丁
generated_at: '2026-09-21T09:00:00'
source_email_count: 3
related_articles:
- sched-20260919-004
tags:
- eevdf
- load_balance
title: 'sched/stats: Fix run_delay over-count for migrated sched_delayed tasks'
layout: article
---

## TL;DR
增量更新：Wei Yang 的 run_delay 虚增修复发布 v2——按 Kayra Cizmeci 的纠正重写了 commit message 中「负载均衡迁移不受影响」的错误论断（active load balance 的 lb_env 不设置 migration_type、恒为 0==migrate_load，delayed 任务仍可能被迁移），并纳入 Chen Yu 的 Reviewed-by。Kayra 在 v2 上给出 Reviewed-by，同时指出 `sched_info_enqueue()` 上方注释有误（实际有两处调用点），表示后续会单独发补丁修注释。

## 背景与问题
背景见 sched-20260919-004 / sched-20260909-017：EEVDF 的 delayed-dequeue 任务（`se.sched_delayed` 置位、`last_queued` 已清零）在睡眠期间被迁移时，普通迁移路径 `activate_task(dst, 0)` 不含 ENQUEUE_RESTORE，会在迁移时刻重设 `last_queued`，把「迁移到唤醒」这段仍处于睡眠的时长虚算进 run_delay。

v1 的 commit message 声称「load-balance 迁移不受影响」，本日被 Kayra 证实有误：`can_migrate_task()` 仅在 `env->migration_type != migrate_load` 时才跳过 delayed 任务；而 active load balance（`active_load_balance_cpu_stop()` 的 lb_env 不设置 migration_type，恒为 0==migrate_load）以及普通 load balance 经 `calculate_imbalance()` 的 migrate_load 分支都能命中该路径，迁移后经 `attach_task() -> activate_task(rq, p, ENQUEUE_NOCLOCK)` 重挂载，同样不含 ENQUEUE_RESTORE，都会重设 `last_queued` 并虚增 run_delay。修复本身不变，只是描述需更正。

## 技术方案
修复逻辑不变（见 sched-20260919-004）：在 `kernel/sched/stats.h` 的 `sched_info_enqueue()` 中，对仍处于 sched_delayed 状态的任务不再重设 `last_queued`：

```c
static inline void sched_info_enqueue(struct rq *rq, struct task_struct *t)
{
-	if (!t->sched_info.last_queued)
+	if (!t->sched_info.last_queued && !t->se.sched_delayed)
		t->sched_info.last_queued = rq_clock(rq);
}
```

唤醒路径在进入 `sched_info_enqueue()` 前已清除 sched_delayed，故真实唤醒时仍会重设 `last_queued`，普通 runnable 任务不受影响。本版仅修订 commit message 描述，代码 diff 与 v1 一致（1 文件 1 增 1 删）。

## 版本演进与当前进展
- v1（09-09，`<20260909133345.1572954-1-albin_yang@163.com>`）：修复补丁（见 sched-20260919-004）。
- 本日作者回帖（`<20260920025206.1237461-1-albin_yang@163.com>`）回应 Kayra：确认 migrate_load==0、`active_load_balance_cpu_stop()` 的 lb_env 不设置 migration_type，并补充普通 load balance 经 `calculate_imbalance()` 也可命中，承认 v1 描述有误、修复覆盖这些路径、将更正 commit message。
- v2（09-20，`<20260920043116.1298017-1-albin_yang@163.com>`）：按 Kayra 意见修正描述，并加 Chen Yu 的 Reviewed-by；changelog 记录 v1 链接。
- Kayra（`<20260920111535.117996-1-kayracizmeci@gmail.com>`）在 v2 上给 Reviewed-by，并指出 `sched_info_enqueue()` 注释有误。

## Maintainer 意见与讨论焦点
（以下为 reviewer 意见，无维护者表态）
- **Chen Yu**：Reviewed-by（v2 已收录），此前从 `last_queued`/`sched_info_arrive` 语义给出机理说明。
- **Kayra Cizmeci**：v2 上 Reviewed-by；同时指出 `sched_info_enqueue()` 实际有两处调用点（`sched_info_depart()` 与 `enqueue_task()`），其上方注释声称仅一处是错误的，并表示会另行发补丁修注释；还分析第二条调用链存在 `task_is_running` 保护、delayed 任务不会在该路径运行，故补丁的判断在该路径不会误触发。
- 分歧/未决：无明显对立；遗留一个小问题——`sched_info_enqueue()` 的注释待修正（Kayra 已表示会补，不阻塞本补丁）。

## 合入评估
likelihood=high。v2 已获 Chen Yu、Kayra 双 Reviewed-by，修复为一行条件判断、带 `Fixes:` 标签与 reproducer 支撑，无否决意见。blocking_issues：暂无实质性阻塞，仅 `sched_info_enqueue()` 注释错误待 Kayra 单独补丁修正。next_action：等待 sched/stats 维护者收取入 tip。

## 效果评估
本版无新增 benchmark 数据；reproducer 实测见 sched-20260919-004（迁移落在 delayed 睡眠期间 run_delay 虚增约 148ms、打补丁后归零）。

## 我可以参与的点
- kind=testing：用 reproducer 在自身环境复测，重点覆盖 active load balance / NUMA balancing 等迁移路径。
- kind=review：跟进 Kayra 即将发出的 `sched_info_enqueue()` 注释修正补丁，帮忙 review。

## 参考链接
- lore（v2 patch）: https://lore.kernel.org/all/20260920043116.1298017-1-albin_yang@163.com/
- lore（作者回应 Kayra）: https://lore.kernel.org/all/20260920025206.1237461-1-albin_yang@163.com/
- lore（Kayra Reviewed-by v2）: https://lore.kernel.org/all/20260920111535.117996-1-kayracizmeci@gmail.com/
- lore（v1）: https://lore.kernel.org/all/20260909133345.1572954-1-albin_yang@163.com/
