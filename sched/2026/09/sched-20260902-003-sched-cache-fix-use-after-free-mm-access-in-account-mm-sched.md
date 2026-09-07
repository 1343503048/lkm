# sched/cache: Fix use after free mm access in account_mm_sched()

## TL;DR

sched/cache 的按地址空间统计 `sched_cache_stat` 原本内嵌在 `mm_struct` 里，而
`account_mm_sched()` 只持 rq lock 就解引用 `rq->curr->mm`，负载均衡谓词还会读**远端任务**的
`p->mm`——exec/exit 换 mm 时就能踩到已释放对象（Hyunwoo Kim 的 KASAN 报告）。Tim Chen 09-02 把这个
UAF 从 23 补丁的 cache-aware prctl RFC 里拆出来单发 0/2：patch 1 把它变成引用计数 + `call_rcu()`
的 `sched_cache_group`，patch 2 给每个任务一份引用 `task_struct->sched_cache_grp`。封面明确写了
**"The two patches are one fix... need to be applied, and backported, as a pair."**
到 9/7 为止该系列**零回帖**，连 maintainer 的只言片语都没有。

## 背景与问题

cache-aware 负载均衡把每个地址空间的 LLC 统计放在 mm 里
（`struct mm_struct { struct sched_cache_stat sc_stat; ... }`）：`mm_alloc_sched()` 在 `mm_init()`
里分配 `sc_stat.pcpu_sched`，`mm_destroy_sched()` 在 `__mmdrop()` 里释放，对象生命周期与 mm 绑定。
但调度器从不持 mm 引用去访问它：

- `account_mm_sched()` 从 `update_curr()` 进来，只持 rq lock，解引用 `rq->curr->mm`；
- 负载均衡谓词 `can_migrate_llc_task() -> invalid_llc_nr() / exceed_llc_capacity()` 以及
  `task_cache_work()` 的 LLC 占用扫描读的是**远端任务**的 `p->mm`。

一条任务在别的 CPU 上 `exit`、或 `exec_mmap()` 装上新的 mm，`pcpu_sched` 就在并发读者脚下被释放。
作者给出的取舍很关键：把两边串行化要在 mm 释放路径里取 rq lock，"which is a lot of coupling to pay
for a statistics object"——所以选择给对象独立生命周期，而不是加锁。

## 技术方案

**Patch 1 `sched/cache: Decouple sched_cache_group from mm`**
`sched_cache_stat` 从 `mm_struct` 提出、改名 `sched_cache_group`、变成引用计数对象、`call_rcu()` 释放；
`mm_struct` 只留指针 `sched_cache_grp`。新增文件 `kernel/sched/cache_sched.c` 承载 cache-aware helper
并定义 `sched_cache_group_put()`。顺带 "skip kthreads in `account_mm_sched()`, consistent with
`task_tick_cache()`"。改动面：`include/linux/mm_types.h`、`include/linux/sched.h`、`kernel/exit.c`、
`kernel/sched/build_utility.c`、`kernel/sched/cache_sched.c`、`kernel/sched/fair.c`，
113 插入 / 58 删除。

**Patch 2 `sched/cache: Introduce task_struct->sched_cache_grp`**
每个任务自己持一份引用：`copy_mm()` 与 `exec_mmap()` 取引用、`exit_mm()` 放引用；调度器改读
`p->sched_cache_grp` 而不是 `p->mm->sc_stat`，读者因此无需担心对象被释放。
两补丁合计 9 文件 239 插入 / 86 删除（另含 `fs/exec.c`、`kernel/fork.c`、`kernel/sched/sched.h`）。

标签（两补丁都有）：`Reported-by: Hyunwoo Kim`、`Closes: apPb-Dr4nPYuHQOK@v4bel/`、
`Tested-by: Hyunwoo Kim`、`Fixes: df0d98475954 ("sched/cache: Introduce infrastructure for cache-aware
load balancing")`；patch 1 另有 `Co-developed-by: Chen Yu`。

## 版本演进与当前进展

- 这不是 v1/v2 迭代，而是**从大系列里拆出的独立修复**。封面："These are the first two patches of the
  cache-aware prctl RFC series（`cover.1787955777.git.tim.c.chen@linux.intel.com`）reposted on their own
  with the changelogs rewritten and minor updates around the use-after-free, so that they can be
  considered ahead of the rest of that series."
- 拆解的公开承诺在 9/2 04:49（`72363`）："Thanks for confirming that patches 1 and 2 in prctl series fix
  this use after free issue. I will post those two patches separately... **We will try to expedite getting
  those two patches merged.**"
- 报告方侧的铺垫：Hyunwoo Kim 更早的 `[PATCH]/[PATCH v2] sched/cache: Fix use-after-free of the mm
  replaced by exec` 线程（68881/69059/69143/69762/70772/66088）与这 0/2 是同一问题的两种方案，
  `72363` 的致谢即是确认 Intel 这两补丁取代社区那版。
- 至今（9/7）整条 0/2 线程**无任何回帖**（按 references/in_reply_to 全库检索确认）。
- 同期另有一条独立的设计问题线程：Tim Chen `72353` "which tasks should `nr_pref_llc_running` be
  compared against?"，Chen Yu 9/3（`77670`）、Tim Chen 9/5（`80977`）在跟。

## Maintainer 意见与讨论焦点

- **没有任何 maintainer 表态**——既无 Acked-by/Reviewed-by，也无 NAK；唯一的第三方背书是报告者
  Hyunwoo Kim 的 `Tested-by`（封面："Hyunwoo confirmed the splat is gone; his Tested-by is on both
  patches."）。
- 值得记录的立场是作者给出的设计约束：**不打算**用 rq lock 去串行化 mm 释放。后续 review 若要求
  「在 `__mmdrop()` 里加锁」，会被以耦合成本否掉。
- 拆包决策透露优先级：Tim 明确说这两补丁要 "considered ahead of the rest of that series"，
  把 UAF 修复与仍在 RFC 的 prctl 接口解耦，避免被大系列的评审进度拖住。
- Chen Yu 是 patch 1 的 `Co-developed-by`；他在 `nr_pref_llc_running` 语义线程里的回答，是 review
  该系列时最有参考价值的 Intel 内部意见。

## 合入评估

**likelihood: possible。**

依据：修复带 KASAN 证据、`Fixes:` 指向 `df0d98475954`、有 `Reported-by`/`Closes:`/`Tested-by`，
作者承诺 "expedite"，且范围已压到 2 个补丁——这些正是能进 `sched/urgent`/`sched/fair` 的标准配置。

卡点：
1. 零回帖。改动侵入 `mm_struct`、`fs/exec.c`、`kernel/fork.c`、`kernel/exit.c`，跨 scheduler 与 mm
   两侧，按惯例至少需要 mm 侧 maintainer 的 ack，目前完全没有。
2. 239 插入 / 86 删除并新增 `kernel/sched/cache_sched.c`，对「修 UAF」而言体量偏大，且两补丁必须成对，
   无法拆着收。
3. 同一问题存在竞争性方案（Hyunwoo 的 exec-replaced-mm 修复），需先明确取谁。
4. 无 `Cc: stable`；`Fixes: df0d98475954` 若落在已发布分支，是否补 stable 会左右 queue 位置。

## 效果评估

功能效果有第三方确认：`Tested-by: Hyunwoo Kim`，封面写 "Hyunwoo confirmed the splat is gone"。
**没有任何性能数据**——作者把它定位成正确性修复。长期价值在解耦本身：封面点明 "the group is no longer
welded to an address space, so a later series can key it on a cgroup, a core-scheduling cookie or a
numa_group instead of on a single mm"——这句是本仓库读者最该关心的：cache-aware 均衡的分组维度一旦
可换，cgroup/亲和策略就有了挂载点。附带的小修正（`account_mm_sched()` 跳过 kthread）减少了一类
无意义统计。

## 我可以参与的点

- **给这两补丁发 `Tested-by` 是目前最缺的东西**：零回帖的 UAF 修复，一份来自第三方机型的
  KASAN + 长稳验证能直接推动 queue。构造 `execve`/`exit` 与 LLC 均衡并发的场景即可（反复 exec +
  开启 cache-aware 均衡）。
- 就跨 mm 边界的改法表态：是否接受 `copy_mm()`/`exec_mmap()`/`exit_mm()` 三点加引用，
  还是应由 mm 侧 maintainer 先 ack——这决定 queue 路径。
- 参与 `72353` 的 `nr_pref_llc_running` 语义讨论（Chen Yu 9/3 已回）：这是分组维度改到 cgroup
  之前必须定清的统计口径。
- 回背视角：作者已明说 "need to be applied, and backported, as a pair"。若在跑含
  `df0d98475954` 之后代码的产品内核（或自有 cache-aware backport），需成对回合，并重点回归
  KASAN 下的 exec/exit 并发。

## 参考链接

- https://lore.kernel.org/all/cover.1788305725.git.tim.c.chen@linux.intel.com/ （0/2 封面）
- https://lore.kernel.org/all/f7b3f8577da365010479da95b07d7dce5365e7fa.1788305725.git.tim.c.chen@linux.intel.com/ （1/2）
- https://lore.kernel.org/all/cde1eb5311b51159288b6a04f28455cf825cfc49.1788305725.git.tim.c.chen@linux.intel.com/ （2/2）
- 拆解承诺：https://lore.kernel.org/all/17afb1540240d267023aba1706bd7659d1a50197.camel@linux.intel.com/
- KASAN 报告：https://lore.kernel.org/all/apPb-Dr4nPYuHQOK@v4bel/
- 母系列（cache-aware prctl RFC）：https://lore.kernel.org/all/cover.1787955777.git.tim.c.chen@linux.intel.com/
- 统计口径讨论：https://lore.kernel.org/all/06ed8af87506f858176a81a4c29acf92d24b6dc7.camel@linux.intel.com/
- 相关：[[sched-20260902-009]]、[[sched-20260903-011]]、[[sched-20260903-012]]

---
id: sched-20260902-003
date: '2026-09-02'
subject: 'sched/cache: Fix use after free mm access in account_mm_sched()'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <cover.1788305725.git.tim.c.chen@linux.intel.com>
lore_url: https://lore.kernel.org/all/cover.1788305725.git.tim.c.chen@linux.intel.com/
upstream_commit: null
fixes_commit: df0d98475954
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Tim Chen
- Chen Yu
maintainers_involved: []
patch_series:
- 'sched/cache: Decouple sched_cache_group from mm'
- 'sched/cache: Introduce task_struct->sched_cache_grp'
merge_assessment:
  likelihood: possible
  blocking_issues:
  - 整条 0/2 线程到 9/7 零回帖，无任何 maintainer Acked-by/Reviewed-by
  - 改动跨 scheduler 与 mm（mm_struct/fs/exec.c/kernel/fork.c/kernel/exit.c），缺 mm 侧 ack
  - 两补丁必须成对合入与回合（1 patch 不独立成立），239 插入/86 删除并新增 kernel/sched/cache_sched.c
  - '与社区方案 [PATCH v2] sched/cache: Fix use-after-free of the mm replaced by exec 需二选一'
  - 未加 Cc stable，是否作为 fixes 进 stable 未定
  next_action: 等/推动 mm 侧 maintainer 表态，并补第三方 Tested-by 与 stable 需求确认
contribution_opportunities:
- 补第三方 Tested-by：KASAN 下 execve/exit 与 cache-aware 均衡并发的长稳验证
- 就「不给 __mmdrop 加 rq lock、改为 refcount + call_rcu」的取舍表态，并明确 mm 侧是否需要单独 ack
- 参与 nr_pref_llc_running 统计口径讨论（72353/77670/80977），为分组维度换到 cgroup 铺路
- OLK 回背：按成对回合要求覆盖 copy_mm()/exec_mmap()/exit_mm() 三处引用点并做 KASAN 回归
source_email_count: 4
related_articles: []
tags:
- sched/cache
- crash
---
