---
id: sched-20260904-005
date: '2026-09-04'
subject: 'cpufreq: schedutil: convert to kthread_create_worker'
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: b6768a4db5451e90e68befc3a9b498f1dfa52b1c.1788513591.git.brads@mainlining.org
lore_url: https://lore.kernel.org/all/b6768a4db5451e90e68befc3a9b498f1dfa52b1c.1788513591.git.brads@mainlining.org/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Bradley Morgan
maintainers_involved: []
patch_series:
- 'cpufreq: schedutil: convert to kthread_create_worker'
merge_assessment:
  likelihood: unclear
  blocking_issues:
  - 缓存中无任何回帖，cpufreq 维护者（Viresh Kumar / Rafael J. Wysocki）未表态
  - 所属 v2 5 补丁系列的封面与其余 4 个补丁不在缓存中，依赖与排队方式未知
  - 无 Fixes 标签，属清理类，通常需等 merge window
  - 补丁未附自述的验证方式与结果
  next_action: 等 cpufreq 维护者回帖；若长期无回应，可由有兴趣者代为在需要 sugov kthread 的平台上跑 policy 创建/销毁与热插拔压测并回帖
    Tested-by。
contribution_opportunities:
- 确认 sugov_kthread_stop() 中 flush + destroy 是否冗余及 work_lock 销毁顺序
- 核对 sugov_policy_free() 中 sg_policy->thread 的引用释放是否已同步删除（本邮件未含该 hunk）
- 比对 kthread_create_worker() 与旧 kthread_create() 在 freezable / WQ_MEM_RECLAIM 语义上的差异
- 在非 fast_switch 平台跑 cpufreq 模块卸载、CPU 热插拔、governor 切换压测并回帖
source_email_count: 1
related_articles: []
tags:
- cpufreq
- schedutil
- sched/core
title: 'cpufreq: schedutil: convert to kthread_create_worker'
layout: article
---

## TL;DR

把 `kernel/sched/cpufreq_schedutil.c` 里 `sugov_policy` 的 kthread worker 从已废弃的 `kthread_init_worker()` + `kthread_create(kthread_worker_fn, ...)` + `wake_up_process()` 组合换成 `kthread_create_worker()` / `kthread_destroy_worker()`，并顺带用 `worker->task` 取代自持的 `thread` 指针。这是 Bradley Morgan 的 v2 5 补丁系列中的第 4 个，净减少 5 行。本日缓存中只有该补丁本身，没有任何维护者回帖，合入判断只能停留在「不确定」。

## 背景与问题

`cpufreq_schedutil` 的慢路径（非 `fast_switch`）为每个 policy 起一个名为 `sugov:%d` 的 kthread worker 来落地频率变更，历史上用 `kthread_init_worker()` + `kthread_create(kthread_worker_fn, &sg_policy->worker, ...)` + 手动 `wake_up_process()` 拼装，并自己保存 `struct task_struct *thread`。内核已提供 `kthread_create_worker()` 作为标准入口，本补丁的 commit message 只给了一句理由：`"Convert cpufreq_schedutil to use kthread_create_worker() instead of the deprecated kthread_run(kthread_worker_fn) pattern. The new API sets worker->task before the worker starts."`（正文未展开具体的竞态或故障现象）。

注意：该文件位于 `kernel/sched/` 下但属 cpufreq 子系统，与调度器核心逻辑无关，只是 sugov governor 的实现文件。

## 技术方案

- `struct sugov_policy`：`struct kthread_worker worker` + `struct task_struct *thread` 合并为 `struct kthread_worker *worker`。
- `sugov_kthread_create()`：`kthread_init_worker()` + `kthread_create(kthread_worker_fn, ...)` 换成 `kthread_create_worker(0, "sugov:%d", cpumask_first(policy->related_cpus))`；`IS_ERR()` 判定与 `PTR_ERR()` 返回改到 worker 指针上；`sched_setattr_nocheck()`、`set_cpus_allowed_ptr()`、`kthread_bind_mask()`、`wake_up_process()` 全部改用 `sg_policy->worker->task`。
- 错误路径：`sched_setattr_nocheck()` 失败时由 `kthread_stop(thread)` 改为 `kthread_destroy_worker(sg_policy->worker)`。
- `sugov_kthread_stop()`：`kthread_flush_worker()` + `kthread_stop()` 改为 `kthread_flush_worker()` + `kthread_destroy_worker()`。
- `sugov_irq_work()`：`kthread_queue_work(&sg_policy->worker, ...)` → `kthread_queue_work(sg_policy->worker, ...)`。
- 保留原有语义不变的部分：`SCHED_DEADLINE` 的 `sched_attr` 设置、`dvfs_possible_from_any_cpu` 下用 `set_cpus_allowed_ptr()` 否则 `kthread_bind_mask()` 的分支、`fast_switch_enabled` 时的提前返回。改动 14 行新增 / 19 行删除。

## 版本演进与当前进展

- 该补丁是 v2 系列的 4/5（封面 in-reply-to 为 `cover.1788513591.git.brads@mainlining.org`，本日报缓存中未保留封面与其他 4 个补丁），说明作者已按 v1 反馈重发过一轮，但 v1→v2 的具体变化在缓存中未获取到。
- 09-04 17:40 发出后，缓存中（含 09-05、09-06）未见任何人回帖，也未见 cpufreq 维护者（Viresh Kumar / Rafael J. Wysocki）或调度器维护者的动作。

## Maintainer 意见与讨论焦点

未获取到任何维护者意见——本日匹配到的唯一一封邮件就是补丁本身，缓存中不存在对该补丁的回帖、Acked-by 或 Reviewed-by。

可确认的仅有事实：作者用 `[PATCH v2 4/5]` 标签重发过一轮，说明 v1 阶段发生过反馈，但反馈内容不在缓存中，无法判断其性质（是代码意见还是系列拆分/收件人调整）。补丁自身不带 `Fixes:`、不带 `Cc: stable`，作者也未把它描述成 bug 修复，因此更可能被当作 API 清理对待——这类补丁通常需要 cpufreq 维护者经手，而本日报周期内 cpufreq 侧无人回应。

## 合入评估

likelihood: **unclear**。

依据：改动是机械性的 API 迁移，风险低、行数小（+14/-19），且 `kthread_create_worker()` 的上游方向本身就是替换手搓 worker 模式，被接受的可能性不低。

卡点：
- 缓存中零回帖，既无 Acked-by 也无 Reviewed-by，无法判断 cpufreq 维护者是否想要这个改动进入 `cpufreq` 树还是作为 cleanup 排队。
- 它是 5 补丁系列的第 4 个，其余 4 个的内容与 review 状态不在缓存中；系列中前几个补丁的依赖（可能是同一作者的 kthread worker 批量清理）会决定它是独立合入还是随系列合入。
- 无 `Fixes:` 标签，因此不会走 fixes 通道；cleanup 类补丁通常要等 merge window。

## 效果评估

邮件中未提供效果数据。补丁明确定位为 API 迁移（commit message 只说「新 API 在 worker 启动前设置 `worker->task`」），未声称性能或行为变化，也未附任何基准或故障复现。作者自述的验证方式与结果在本日缓存中不可见（v2 封面未保留）。

## 我可以参与的点

- **可复核的具体代码点**（都能只看本 diff 完成）：
  1. `sugov_kthread_stop()` 现在 `kthread_flush_worker()` 后紧接 `kthread_destroy_worker()`，再 `mutex_destroy(&sg_policy->work_lock)`——确认 `kthread_destroy_worker()` 已隐含 flush/stop，两次 flush 是否冗余，以及销毁顺序与 `work_lock` 生命周期的先后。
  2. `sched_setattr_nocheck()` 失败路径改为 `kthread_destroy_worker()`：确认与 `init_irq_work()` / `mutex_init()` 的位置关系（这些在原路径里是 destroy 之后才做的）不会造成资源泄漏或重复销毁。
  3. `sugov_policy_free()` 中原本针对 `sg_policy->thread` 的引用释放是否已同步删除（该 hunk 不在本邮件正文中，需拉完整补丁核对）。
  4. `kthread_create_worker(0, ...)` 未指定 `nice`/flags，与旧路径 `kthread_create()` 的默认行为差异（`WQ_MEM_RECLAIM`、freezable 语义）对 cpufreq 在 suspend/内存回收路径上的影响。
- **可帮跑的验证**：`CONFIG_CPU_FREQ_GOV_SCHEDUTIL` + 非 `fast_switch` 平台（例如带 `dvfs_possible_from_any_cpu` 的 x86 HWP 或需 kthread 落频的平台）上做 policy 反复 create/destroy（`cpufreq` 模块卸载、`CPUHP` 热插拔、`echo performance > scaling_governor` 切换），确认无 `task_struct` 泄漏、无 hung task；这类用例正好补上补丁缺失的验证证据。
- **回合相关性**：属 cpufreq 清理，与 cpuset/cgroup 主线无关；OLK-6.6 若无 kthread API 差异不必单独回合，但若上游已合入而内部树仍用手搓 worker，回合时可一并跟进 `kernel/sched/cpufreq_schedutil.c` 的结构漂移。

## 参考链接

- 邮件线程：
  - v2 4/5 补丁本体: <https://lore.kernel.org/all/b6768a4db5451e90e68befc3a9b498f1dfa52b1c.1788513591.git.brads@mainlining.org/>
  - v2 cover letter 的 msgid（缓存中未保留正文，仅有本补丁的 in-reply-to）: <https://lore.kernel.org/all/cover.1788513591.git.brads@mainlining.org/>
- 相关代码/commit：
  - `kernel/sched/cpufreq_schedutil.c` `sugov_kthread_create()` / `sugov_kthread_stop()` / `sugov_irq_work()`
  - `kernel/kthread.c` `kthread_create_worker()` / `kthread_destroy_worker()`
