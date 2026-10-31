# sched/deadline: total_bw leak when a task leaves SCHED_DEADLINE while not queued

## TL;DR
Tejun Heo 报告一个 SCHED_DEADLINE 的带宽泄漏 bug：任务在「未入队」（睡眠或被 SIGSTOP 暂停）状态下切换到其它调度策略时，其在 root domain 的 `total_bw` 中的带宽不会被归还，任务退出后依然残留；反复触发可把 `total_bw` 填满到准入上限，之后 `sched_setattr(SCHED_DEADLINE)`、CPU offline、以及启用 sched_ext（挂 ext dl_server）都会以 `-EBUSY` 失败。Juri Lelli 当日给出一个 inline 修复补丁（在 `switched_from_dl()` 的「无 pending inactive timer」分支直接 `__dl_sub()` 归还带宽）。

## 背景与问题
Tejun 给出的三段式泄漏机制（另有完整可复现脚本，需 root + debugfs，x86-64 syscall 314）：

1. `sched_dl_overflow()` 不扣减离开 DEADLINE 任务的带宽，把归还留给 `switched_from_dl()`。
2. `switched_from_dl()` 只对**已入队**的任务调 `task_non_contending()`——它会立即或在 inactive timer 到期后经 `inactive_task_timer()` 归还带宽。
3. 对**未入队**的任务，带宽只有在「dequeue 时遗留的 inactive timer 仍 pending」时才归还；若任务从未作为 DEADLINE 运行过、或 timer 在它睡眠期间已触发（此时任务仍是 DEADLINE，只丢了 `running_bw`），则没有任何路径归还 `total_bw`。

症状：泄漏累积后，`sched_setattr(SCHED_DEADLINE)` 与 CPU offline 报 `-EBUSY`，启用 sched_ext 也失败（`sched_ext: failed to attach ext_server on CPU 0 (-16)`）。这是一个真实的正确性/资源泄漏 bug，影响 DEADLINE 准入控制与 sched_ext 的 dl_server 带宽挂载。

## 技术方案
Juri Lelli 在 `kernel/sched/deadline.c` 的 `switched_from_dl()` 里，把原「仅当 `p->dl.dl_non_contending` 时 `sub_running_bw()`」的逻辑扩展为一个 else 分支：

- 若 `dl_non_contending` 为真（inactive timer 已 armed）：维持原逻辑——inactive timer 之后会看到 `!dl_task(p)` 并经 `__dl_sub()` 归还 `total_bw`，此处只 `sub_running_bw()`。
- 否则（无 pending inactive timer：任务从未以 DEADLINE 运行，或 timer 已触发只掉了 running_bw）：**此刻直接** `raw_spin_lock(&dl_b->lock)` + `__dl_sub(dl_b, p->dl.dl_bw, dl_bw_cpus(task_cpu(p)))` + unlock，主动归还 `total_bw`。

改动共 `24 insertions, 7 deletions`，紧贴现有 `sub_rq_bw()` 之前，逻辑最小化。

## 版本演进与当前进展
*current_version: 无（仅 bug 报告 + 维护者 inline 修复提案）*。Tejun 当日发报（含完整可复现脚本）；Juri Lelli 回帖「Thanks for reporting and for the reproducer! Does the below help?」并附 inline 补丁。尚无正式 PATCH 系列成型，也未有人真实跑该补丁验证。

## Maintainer 意见与讨论焦点
- **Juri Lelli（DEADLINE maintainer）**：认可 bug 与复现脚本，直接给出修复方向，未提出异议。
- **未解决/待确认**：尚无第二人 review 该 inline 补丁；`__dl_sub()` 需要 `dl_b->lock` 保护，Juri 的锁粒度与 `dl_bw_cpus(task_cpu(p))` 的使用是否与现有 overflow 路径完全一致，尚未经过讨论；也无测试数据确认泄漏归零。

## 合入评估
*likelihood=medium*。bug 真实、方向明确、mechanism 清晰，且已由对应子系统维护者给出补丁；但目前还停在「inline 提议」，未形成正式 patch、无 Tested-by/Reviewed-by，亦需确认是否要 `Fixes:` 标签（正文未给出触发该泄漏的原始 commit）与是否进 stable。*blocking_issues*：inline 补丁需转正并过一轮 review + 验证。*next_action*：Juri（或 Tejun）把补丁正式成串、补 `Fixes:` 标签并附复现前后的 `total_bw` 归零验证。

## 效果评估
正文未给出补丁应用后的量化数据；但 Tejun 提供了泄漏复现脚本（`trial("sleeping ...", ...)` 序列打印 `leaked total_bw N`，0.2 CPU 对应 209715），可作为复现/验证基座。修复效果「带宽不再泄漏」目前为逻辑推演，未见实测。

## 我可以参与的点
- **testing**：跑 Tejun 的复现脚本，先确认在最新 tip 上能复现泄漏，再验证 Juri 补丁使 `leaked total_bw` 归零，并把结果回帖。
- **review**：核对 `switched_from_dl()` 新分支的锁与 `dl_bw_cpus()` 语义，确认与 `sched_dl_overflow()` / inactive timer 路径无重复归还或遗漏。

## 参考链接
- lore thread（Tejun 报告）: https://lore.kernel.org/all/2b5fb3f22bca6aa383be8f4781923392@kernel.org/
- Juri 修复回帖的真实 Message-ID 未在缓存中取得，未获取到独立链接。

---
id: sched-20261030-001
date: 2026-10-30
subject: "sched/deadline: total_bw leak when a task leaves SCHED_DEADLINE while not queued"
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: "<2b5fb3f22bca6aa383be8f4781923392@kernel.org>"
lore_url: "https://lore.kernel.org/all/2b5fb3f22bca6aa383be8f4781923392@kernel.org/"
authors: [Tejun Heo]
maintainers_involved: [Juri Lelli]
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "Juri 的 inline 补丁需转正为正式 patch 并过一轮 review"
    - "缺 Fixes 标签指向引入该泄漏的原始 commit"
  next_action: "补丁正式成串、补 Fixes 标签并附 total_bw 归零的复现验证"
contribution_opportunities:
  - kind: testing
    description: "跑 Tejun 的复现脚本，验证 Juri 补丁使 leaked total_bw 归零并回帖"
  - kind: review
    description: "核对 switched_from_dl() 新分支的锁与 dl_bw_cpus() 语义，确认与 overflow/inactive timer 路径无重复归还"
generated_at: "2026-10-31T09:00:00"
source_email_count: 2
related_articles: []
tags: [deadline]
---