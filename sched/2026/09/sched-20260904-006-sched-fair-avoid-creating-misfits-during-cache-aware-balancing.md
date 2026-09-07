# sched/fair: avoid creating misfits during cache-aware balancing

## TL;DR

Tim Chen 的单补丁修复已进入 tip `sched/urgent` 并成为该分支 HEAD：`f0d243a96f2684ad771d678767d17972cf840bd7`，0day 在 58 个 config 上构建成功。修的是混合架构（`SD_ASYM_CPUCAPACITY`）上 cache-aware 均衡为了追 preferred LLC 把任务拉到装不下它的目标 CPU、从而人为制造 misfit 的问题，同时把 misfit 迁移的优先级提到 LLC 聚合之上。Peter Zijlstra 在合入前只提了两条格式性意见（补 SoB、`sched/fair:` 后首字母大写），均已照办。

## 背景与问题

cache-aware 负载均衡会偏向任务的 preferred LLC。在 CPU 容量不对称的系统（hybrid / big.LITTLE）上，目标 LLC 里可能装着容量太小、跑不动该任务的 CPU：把任务拉过去就让它变成 misfit，用一次缓存局部性的收益换了一次更伤性能的容量损失。

另外在 active balance 侧，`alb_break_llc()` 会因为 LLC 聚合的考虑否决迁移；若源 CPU 上已有 misfit 任务，这个否决方向是反的——更好的匹配 CPU 带来的收益大于更好的缓存局部性。

## 技术方案

- 新增 `task_misfits_asym_cpu(env, p)`：`(env->sd->flags & SD_ASYM_CPUCAPACITY) && p && !task_fits_cpu(p, env->dst_cpu) && task_fits_cpu(p, env->src_cpu)`。即只有「源 CPU 装得下、目标 CPU 装不下」才判定为会制造 misfit；已经不适配源 CPU 的任务仍交给既有 LLC 策略决定（这样不会挡住 misfit 向大核的上迁，也保证对称系统不受影响）。
- `can_migrate_llc_task()` 签名改为接收 `struct lb_env *env`（原来只收 `src_cpu` / `dst_cpu`），在函数入口用上述判定 `return mig_forbid`。
- `alb_break_llc()`：`env->migration_type == migrate_misfit` 时直接 `return false`，把 misfit 迁移排在 LLC 聚合之前；同时在其原有的 LLC 否决条件前加上同一个 `task_misfits_asym_cpu(env, cur)` 判定。
- 改动全部落在 `kernel/sched/fair.c`，45 行新增 / 5 行删除。

## 版本演进与当前进展

- 08-19 起草（补丁内 Date 为 `Wed, 19 Aug 2026 13:03:56 -0700`），08-25 以 `[PATCH] sched/fair: avoid creating misfits during cache-aware balancing` 发出（`20260825174112.2580942-1-tim.c.chen@linux.intel.com`）。
- 08-26 作者自己补一封「Forgot my signed off」加上 SoB。
- 08-31 Peter Zijlstra：`"Tim sends patch, Tim adds SoB, yes?"` + `"Also, we start $subject with capital after subsystem: part."`——两条都是格式问题，无技术异议。
- 09-01 Tim Chen 以 `From d28acbf5a7f30125a7f15d85bf77b8e4b6e8bfc5` 重发修正版，主题改为大写首字母的 `sched/fair: avoid creating misfits during cache-aware balancing`。
- 本日（09-04 14:24）0day/LKP 报告 `[tip:sched:urgent] BUILD SUCCESS f0d243a96f2684ad771d678767d17972cf840bd7`：tree/branch 为 `tip.git sched/urgent`，branch HEAD 即该 commit，58 个 config 构建成功、3 个跳过，elapsed 2817m，并注明「More configs may be tested in the coming days」。合入已完成，本日匹配 1 封邮件。

## Maintainer 意见与讨论焦点

**Peter Zijlstra（调度器维护者）**：08-31 的评论只涉及提交规范，未质疑机制，且合入后的 commit 标题正是他要求的大写形式——可视为默示接受。

**已给出的技术背书（补丁标签，重发版）**：`Reviewed-by: Ricardo Neri <ricardo.neri-calderon@linux.intel.com>`、`Tested-by: Ricardo Neri`、`Reviewed-by: Chen Yu <yu.c.chen@intel.com>`。

**收件人分布**：To 为 Peter Zijlstra 与 Ingo Molnar，Cc 含 K Prateek Nayak（AMD）、Vincent Guittot（Linaro）、Chen Yu、Ricardo Neri、Len Brown、Aubrey Li——即 hybrid / 非对称容量方向的相关人。

**技术判断上的分歧点**（从补丁自身的措辞可读出，缓存中未见针对它的反对意见）：
- 判定条件刻意做成「源能装下、目标装不下」才否决，而不是无脑禁止跨 LLC；作者明确说明这是为了不破坏 misfit 向大核的上迁路径。
- 所有检查都用 `SD_ASYM_CPUCAPACITY` 门控，对称系统零影响——这是本补丁能被当作 urgent 修复的前提。

## 合入评估

likelihood: **likely**（实际已合入 tip 树，等待进入主线）。

依据（全部来自邮件正文，非推断）：`tip.git` 的 `sched/urgent` 分支 HEAD 已是 `f0d243a96f2684ad771d678767d17972cf840bd7`，标题与本补丁一致；0day 已在 58 个 config 上构建成功且无回归报告；两位 reviewer 已给 Reviewed-by / Tested-by；维护者只提了格式要求并已满足。

卡点：仅剩常规流程风险——`sched/urgent` 需由 Ingo 向主线发 pull，以及 0day 明示「后续可能测更多 config」，若出现新平台的构建/回归报告可能被回退。补丁本身不带 `Fixes:` 标签，说明它按「新引入的 cache-aware 行为的配套修正」而非历史 bug 处理，因此大概率不进 stable（这一点邮件中未讨论）。

## 效果评估

邮件中未提供性能数据：既无 microbenchmark 数字，也无 hybrid 平台上的实测收益，验证方式是构建与代码走查（Ricardo Neri 给了 Tested-by 但未附数据）。

本日报匹配到的唯一证据是构建层面：58 个 config 全部 BUILD SUCCESS（3 个跳过），覆盖 alpha/arc/arm/arm64/csky/hexagon/i386/loongarch/m68k/microblaze/mips/nios2/openrisc/parisc/powerpc/riscv/s390/sh/sparc/um/x86_64/xtensa，编译器为 gcc 11.5~16.1 与 clang 17~24，elapsed 2817m。功能层面的效果（misfit 数量下降、hybrid 平台吞吐）在邮件中未量化。

## 我可以参与的点

- **可直接复核的代码点**：
  1. `can_migrate_llc_task()` 现在从 `env` 取 `src_cpu` / `dst_cpu`，需确认所有调用点在 `env` 尚未完全初始化（尤其 `env->sd`）时不会被走到。
  2. `task_misfits_asym_cpu()` 里 `env->sd->flags & SD_ASYM_CPUCAPACITY` 只覆盖 `has_asym_cpucapacity` 场景；若系统的非对称性只体现在 SMT 层的 `SD_ASYM_PACKING` 而不是容量层，本检查不会生效——这与同日 `sched: Enable preferred SMT siblings on NVIDIA Olympus` 走的门控正好互补，值得对照看两者是否会在同一 CPU 上互相抵消收益。
  3. `alb_break_llc()` 中 `migration_type == migrate_misfit` 提前 `return false` 与后续 `task_misfits_asym_cpu(env, cur)` 的先后关系：前者对 misfit 迁移完全放行 LLC 否决，需确认在目标 LLC 全部 CPU 都不适配时不会反向拉回。
- **可补的实测**：本修复缺的正是数据。在 intel hybrid（或任何 `SD_ASYM_CPUCAPACITY` 平台）上用「大核放不下的多线程突发 + preferred LLC 分布不均」的负载，统计 misfit 迁移次数与 LLC 局部性收益的净变化（可从 `sched_debug` / `sched_stat` 输出中取），回帖给维护者，比再加一层 review 更有价值。
- **回合参考**：若内部树已回合 cache-aware 负载均衡（`can_migrate_llc_task()` / `alb_break_llc()` / `llc_mig` 框架），且目标硬件是混合架构，这个补丁属于必回合，改动小（单文件 45 行）、依赖仅 `task_fits_cpu()`；若内部树没有 `sched/cache` 框架则无需跟进。

## 参考链接

- 邮件线程：
  - 本日 tip/sched/urgent 构建通报（含 commit 标题与分支）: <https://lore.kernel.org/all/202609041453.XqFGjEhJ-lkp@intel.com/>
  - 修正后重发的补丁本体: <https://lore.kernel.org/all/d28acbf5a7f30125a7f15d85bf77b8e4b6e8bfc5.1788198279.git.tim.c.chen@linux.intel.com/>
  - 初版补丁: <https://lore.kernel.org/all/20260825174112.2580942-1-tim.c.chen@linux.intel.com/>
  - Peter Zijlstra 的格式意见: <https://lore.kernel.org/all/20260831084149.GG4120091@noisy.programming.kicks-ass.net/>
- 相关文章/系列：
  - [[sched-20260903-011]] migrate_llc_task 语义 v4 主动均衡。
  - [[sched-20260903-012]] sched/cache 迁移决策 helper RFC v2。
- 相关代码/commit：
  - `f0d243a96f2684ad771d678767d17972cf840bd7` "sched/fair: avoid creating misfits during cache-aware balancing"（tip `sched/urgent`）
  - `kernel/sched/fair.c` `can_migrate_llc_task()` / `alb_break_llc()` / `task_misfits_asym_cpu()` / `task_fits_cpu()`

---
id: sched-20260904-006
date: '2026-09-04'
subject: 'sched/fair: avoid creating misfits during cache-aware balancing'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: 20260825174112.2580942-1-tim.c.chen@linux.intel.com
lore_url: https://lore.kernel.org/all/20260825174112.2580942-1-tim.c.chen@linux.intel.com/
upstream_commit: f0d243a96f2684ad771d678767d17972cf840bd7
fixes_commit: null
merged_branch: tip sched/urgent
current_version: null
generated_at: '2026-09-07'
authors:
- Tim Chen
maintainers_involved:
- Peter Zijlstra
- Ricardo Neri
- Chen Yu
patch_series:
- 'sched/fair: avoid creating misfits during cache-aware balancing'
merge_assessment:
  likelihood: likely
  blocking_issues:
  - 仅剩常规流程：sched/urgent 需由 Ingo Molnar 向主线发 pull
  - 0day 明示后续可能测更多 config，新平台若报回归可能回退
  - 补丁无 Fixes 标签，是否进 stable 未在邮件中讨论
  next_action: 等待进入主线的 pull 通报；有需要的话可补一组 hybrid 平台的 misfit 计数与吞吐数据回帖。
contribution_opportunities:
- 核对 can_migrate_llc_task() 改用 env 后所有调用点的 env 初始化完备性
- 在 SD_ASYM_CPUCAPACITY 平台量化 misfit 计数与 LLC 局部性收益的净变化
- 对照 SD_ASYM_PACKING 路径（Olympus 系列）确认两套门控不会互相抵消
- 评估内部树回合必要性：依赖 task_fits_cpu() 与 llc_mig 框架
source_email_count: 1
related_articles:
- sched-20260903-011
- sched-20260903-012
tags:
- sched/fair
- sched/cache
- load_balance
---
