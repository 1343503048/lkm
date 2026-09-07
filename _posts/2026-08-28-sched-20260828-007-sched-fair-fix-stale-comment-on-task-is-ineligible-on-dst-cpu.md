---
id: sched-20260828-007
date: '2026-08-28'
subject: 'sched/fair: Fix stale comment on task_is_ineligible_on_dst_cpu()'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260828083628.1406519-1-zhanxusheng@xiaomi.com>
lore_url: https://lore.kernel.org/all/20260828083628.1406519-1-zhanxusheng@xiaomi.com/
authors:
- Zhan Xusheng
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260828083628.1406519-1-zhanxusheng@xiaomi.com>
  date: '2026-08-28'
  summary: 1/2 修正 task_is_ineligible_on_dst_cpu() 的失准注释并记录 eligibility 在源 rq 求值的理由；2/2
    把 can_migrate_task() 否决清单补成 8 条并按测试顺序排列
  review_outcome: 截至 9/5 无任何回帖，无 review 标签
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 纯注释补丁无人看见，维护者尚未表态
  - can_migrate_task() 注释块是 proxy-exec/CAS 等多个系列的公共改动区，存在重叠/dup 与 rebase 风险
  next_action: 等 Peter Zijlstra/Vincent Guittot 表态；如与其它系列重叠需 rebase
contribution_opportunities:
- kind: review
  description: 核对 8 条判据并给 Reviewed-by，低成本推动纯注释修复落地
- kind: new_patch
  description: 按本文模板排查内部树 can_migrate_task() 注释与本地闸口（smt_qos/soft domain/bpf_sched）的漂移
generated_at: '2026-09-07T22:40:00'
source_email_count: 2
related_articles:
- sched-20260827-018
- sched-20260828-004
tags:
- cfs
- load_balance
- eevdf
title: 'sched/fair: Fix stale comment on task_is_ineligible_on_dst_cpu()'
layout: article
---

## TL;DR

Zhan Xusheng（Xiaomi）的 2 补丁**纯注释修复**，对象是负载均衡里两处"读代码时真正会去看的注释"：`task_is_ineligible_on_dst_cpu()` 的函数头注释和 `can_migrate_task()` 的否决清单。两处注释都与代码脱节已久——前者写的判据是 `dst_cfs_rq->nr_queued > 1`，而代码从 `873199d27bb2` 落地那天起测的就是"目标队列非空"，且 `85570f10a4c6`（single runqueue）之后 `dst_cfs_rq` 已经是目标 CPU 的 **root** cfs_rq、读的字段是 `h_nr_queued`、eligibility 是在 `&task_rq(p)->cfs`（源队列）上算的；后者列了 6 条否决条件，实际有 8 条，`kthread_is_per_cpu()`（`9bcb959d05ee`）和 eligibility 判定（`873199d27bb2`）都没进清单。1/2 还顺手把"为什么在源 runqueue 上算 eligibility"这件原本只写在 commit changelog 里的理由固化进注释。**当日无人回帖**，但它是一份现成的 `can_migrate_task()` 判据地图，对 review 他人 LB 补丁有直接用处。

## 背景与问题

`can_migrate_task()` 决定"busiest 队列上的这个任务能不能被拽走"，被常规均衡的 `detach_tasks()` 与 active balance 的 `detach_one_task()` 两条路径调用（本地 `/home/zq/code/linux` 树 `kernel/sched/fair.c:10870`、`10936`）。它的头部注释是一份清单，作用是让下面一长串 `return 0` 能被对照阅读：

```
/*
 * We do not migrate tasks that are:
 * 1) delayed dequeued unless we migrate load, or
 * 2) target cfs_rq is in throttled hierarchy, or
 * 3) cannot be migrated to this CPU due to cpus_ptr, or
 * 4) running (obviously), or
 * 5) are cache-hot on their current CPU, or
 * 6) are blocked on mutexes (if SCHED_PROXY_EXEC is enabled)
 */
```

问题在于清单与代码已经双向脱节：

1. **少项**：`9bcb959d05ee` ("sched/fair: Ignore percpu threads for imbalance pulls") 加了 `kthread_is_per_cpu()`，`873199d27bb2` ("sched/core: Prioritize migrating eligible tasks in sched_balance_rq()") 加了 eligibility 判定，两者都只留了行内注释，没更新清单——实际 8 条。
2. **顺序**：清单顺序与测试顺序不一致，读者无法按注释定位代码。
3. **另一处更危险**：`task_is_ineligible_on_dst_cpu()` 的头注释描述了一条**代码里从来没有过的**判据（`nr_queued > 1`），并且点名的字段名在 `85570f10a4c6` ("sched/eevdf: Move to a single runqueue") 之后已经不是被读的那个。这类注释不只是无用，它会把后续改动往错误的语义上带。

## 技术方案

- **1/2** 重写 `task_is_ineligible_on_dst_cpu()` 注释：说明"这是判断 @p 迁到 @dest_cpu 后是否会 ineligible"，并补上两条真实约束——判据是"目标队列上有东西排队"（空队列上加入的任务两种情况下都 eligible，所以这个限制只在目标非空时有意义），以及**eligibility 在源 runqueue 上求值**的理由是 `place_entity()` 在迁移时保留 lag，源上 ineligible 的任务到目标上仍然 ineligible。1 文件 6 增 5 删。
- **2/2** 把 `can_migrate_task()` 的清单补成 8 条并按实际测试顺序排列：

```
1) delayed dequeued unless we migrate load, or
2) target cfs_rq is in throttled hierarchy, or
3) ineligible, while this domain has not failed to balance yet, or
4) per-CPU kthreads, or
5) blocked on mutexes (if SCHED_PROXY_EXEC is enabled), or
6) cannot be migrated to this CPU due to cpus_ptr, or
7) running (obviously), or
8) are cache-hot on their current CPU
```

其中第 3 条的措辞带上了 eligibility 判定的前提条件（本 domain 尚未 balance 失败），与代码里的实际写法一致：`if (!env->sd->nr_balance_failed && task_is_ineligible_on_dst_cpu(p, env->dst_cpu)) return 0;`，其上方行内注释即为 "we soft-limit them and only allow them to migrate when nr_balance_failed is non-zero"（本地 `/home/zq/code/linux` master 树 `kernel/sched/fair.c:10738` 处读到）。也就是说 ineligible 任务并非绝对不迁，只是优先迁 eligible 的。1 文件 6 增 4 删。

两个补丁都无 `Fixes:` 标签、无功能改动、base-commit `1b78070aaef63512688aebfbc82365ef9d6660f1`。

## 版本演进与当前进展

- v1（8/28 16:36）：2 补丁一次发出，无 cover letter。
- 截至本次邮件数据源末尾（9/5），**这条线程没有任何回帖**，也未被任何 maintainer 打上标签。
- 同一作者本周期内另外两次出现值得注意：8/27 他提出 `nr_pref_llc_running` 与 `h_nr_runnable` 集合不一致的疑问（站内 sched-20260827-018），8/28 Tim Chen 直接在该线程内联给出修复补丁并由他回 `Reviewed-by`（站内 sched-20260828-004）。这是一个"读码发现真 bug → 顺手修注释"的作者，注释修复的可信度因此比一般 clean-up 高。

## Maintainer 意见与讨论焦点

未获取到——当日及后续缓存（至 9/5）内无任何回复。

线程本身也没有可争议的技术点：唯一可能被挑刺的是"注释清单要不要写这么多"（Peter Zijlstra 在别的线程里表达过对冗长注释/封装的保留态度），以及第 5 条里 `SCHED_PROXY_EXEC` 这类条件项是否该出现在通用清单里。这两点都没人提出。

## 合入评估

**likelihood: possible**。

- 有利：零功能风险；改动落点是 EEVDF/singleton-runqueue 重构后的真实漂移，作者用 commit hash 逐条给出了"从哪个 commit 开始不一致"的证据，这类补丁维护者接受成本低；同一作者同期在 CAS 线程里已有一次被 Tim Chen 采纳的记录。
- 卡点：**没人看见**。纯注释补丁在 tip/sched 队列里天然靠后，且 `can_migrate_task()` 这段注释是proxy-exec、CAS、软域等多个系列的公共改动区（清单里已经有 `SCHED_PROXY_EXEC` 一条是外部系列加进去的），后续任何动这块的系列都可能与它产生冲突或把它带偏。若有人在同一天提交重叠的注释修补，就会被当成 dup 拒掉。
- `next_action`：等 Peter Zijlstra / Vincent Guittot 表态；若后续系列改动同一注释块，作者需要 rebase。

## 效果评估

无功能改动，因此不涉及性能数据，作者也未提供任何测量。实际收益是阅读性的：`can_migrate_task()` 的判据从"读代码自己数"变成"照清单数"，`task_is_ineligible_on_dst_cpu()` 的注释不再描述不存在的判据。

## 我可以参与的点

- **直接给 Reviewed-by / 帮忙推**：这是零成本贡献点，且这类补丁对上层的价值是真实的——`can_migrate_task()` 是每次 LB review 都要读的函数。回帖前可以先核对作者列的 8 条与自己的树是否一致（内部树常有额外否决条件，见下条）。
- **对照检查内部树的同一份注释已经漂到什么地方**：OLK-6.6 的 `can_migrate_task()` 头部注释只有 4 条（`throttled_lb_pair` / `cpus_ptr` / `running` / cache-hot），而函数体里实际已有 `smt_qos_can_migrate_task()`、`CONFIG_SCHED_SOFT_DOMAIN` 下的软域跨 NUMA 否决、`CONFIG_BPF_SCHED` 的 `bpf_sched_cfs_can_migrate_task()` 等多个本地闸口未进清单；`task_is_ineligible_on_dst_cpu()` 在 6.6 基线上根本不存在（PLACE_LAG 相关改动未回合）。也就是说：**这份 upstream 注释修复无法直接 cherry-pick 到 6.6，但它给出了 6.6 注释欠账的对照模板**。若内部后续要回合 eligibility-aware migration，注释清单要一并按 upstream 顺序整理，否则冲突会集中在这个块上。
- **把"注释与代码漂移"做成例行检查**：作者列的三个漂移源（`873199d27bb2`、`85570f10a4c6`、`9bcb959d05ee`）分别对应"加判据不改清单"、"重构改了字段语义"、"加 early-exit 不改清单"。这三类正是大版本重构后注释最容易失效的路径，值得作为内部 review 的检查项。

## 参考链接

- 1/2: https://lore.kernel.org/all/20260828083628.1406519-1-zhanxusheng@xiaomi.com/
- 2/2: https://lore.kernel.org/all/20260828083628.1406519-2-zhanxusheng@xiaomi.com/
- 引用的三个 commit（`873199d27bb2` / `85570f10a4c6` / `9bcb959d05ee`）：lore 链接未获取到（邮件正文只给出 hash 与标题）
- tip-bot commit: 未获取到
- stable backport: 未获取到
