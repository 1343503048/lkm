# sched/fair: avoid creating misfits during cache-aware balancing

## TL;DR

Tim Chen 在 09-01 按 Peter Zijlstra 的意见重发了「cache-aware 负载均衡不要制造 misfit 任务」的补丁（内容不变，只是补 SoB 与标题大小写），同一线程里还挂着一件更要紧的事：**AMD 大小核平台上的实测者 Klaus Kusche 说没有 debugfs 就完全看不到大核/小核调度**，Tim 直接问他换用默认 `aggr_tolerance` 能测出什么数字，Mario Limonciello 则否认 debugfs 补丁与现象有关。补丁本身已有 2 个 `Reviewed-by` + 1 个 `Tested-by`，卡点已经从代码转到了「非 Intel 异构平台上这套聚合逻辑是否正确」。

## 背景与问题

cache-aware 负载均衡（`CONFIG_SCHED_CACHE`）会把任务往其偏好 LLC 上聚。在**非对称 CPU 容量**系统（big.LITTLE / Intel hybrid）上，目的 LLC 里可能只有容量不足以承载该任务的 CPU：任务被拉过去就变成 misfit，用一次缓存收益换一次容量损失，通常净亏。本片要在两个入口都拦住它：

- `can_migrate_llc_task()`：任务在源 CPU 上放得下、但在目的 CPU 上放不下时，禁止这次 LLC 迁移。
- `alb_break_llc()`：同一条件下否决 active balance，别把 runnable 任务推到装不下它的 CPU。

两处都用 hybrid 判定做了门控，对称系统行为不变；已经在源 CPU 上放不下的任务仍交给既有 LLC 策略（挪过去不会更差，也保留了 misfit 向大核上迁的能力）。此外在负载均衡分类阶段一旦发现 misfit 任务，**misfit 迁移优先于 LLC 聚合**。

## 技术方案

机制上最关键的一条取舍是优先级次序：作者写的是 `A better fitting CPU will boost performance more than better cache locality.`——容量适配压过缓存局部性。这与同日海光 RFC v2 里 Peter 主张的「NUMA 优先于 LLC」是同一种思路的不同实例：**先满足粗粒度的资源可获得性，再谈缓存局部性。**

第二处值得注意：misfit 优先级只作用在「分类阶段发现存在 misfit 任务」时，即不改全局聚合策略，只在异构系统上让 misfit 逃逸先插队。

单文件 `kernel/sched/fair.c`，45 增 5 删，四处插入点各有分工：

- 新增 `task_misfits_asym_cpu(env, p)`，判据 `SD_ASYM_CPUCAPACITY && !task_fits_cpu(p, env->dst_cpu) && task_fits_cpu(p, env->src_cpu)`。
- `can_migrate_llc_task()` 的入参从 `(src_cpu, dst_cpu, p)` 改为 `(env, p)`——因为它现在需要 `env->dst_cpu/src_cpu` 与 `env->sd`，`migrate_degrades_llc()` 调用点随之收敛。
- `alb_break_llc()` 里 **两个** 方向都处理：`env->migration_type == migrate_misfit` 时直接 `return false`（不要为了 LLC 偏好打断一次 misfit 迁移），同时在既有否决条件前加上 `task_misfits_asym_cpu(env, cur) ||`。
- `llc_balance()` 增加 `(env->sd->flags & SD_ASYM_CPUCAPACITY) && sgs->group_misfit_task_load` 时返回 false，即该 sched_group 干脆不参与 cache-aware 打标。

## 版本演进与当前进展

- 2026-08-25：原补丁（`20260825174112.2580942-1-tim.c.chen@linux.intel.com`），带 `Reviewed-by: Ricardo Neri`、`Tested-by: Ricardo Neri`、`Reviewed-by: Chen Yu`。
- 2026-08-31：Peter Zijlstra 两条意见——`Tim sends patch, Tim adds SoB, yes?`（补丁里没有作者本人的 SoB）与 `Also, we start $subject with capital after subsystem: part.`（标题在 `sched/fair:` 之后应大写）。
- **2026-09-01 01:17**：Tim 承认 `Yeah, I forgot to add my SoB. Added that in a followed up email. Sorry about that. Let me know if you prefer me send an updated patch with those corrected.`
- **2026-09-01 01:40**：Tim 以「回帖里内嵌完整 patch」的形式重发更新版（`Here is the patch updated with the fixes.`），正文的 format-patch 头已改成 `Subject: [PATCH] sched/fair: Avoid creating misfits during cache-aware balancing`（大写 A），但邮件实际 Subject 行仍是小写——因为这不是通过 `git send-email` 重新发的独立邮件。本日之后未见 Peter 的进一步回应。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：只提了两条流程问题（缺 SoB、标题大小写），**未对本片的机制提出任何异议**——这在本系列当天是罕见的顺利状态。
- **实测者侧的未决问题（本日真正的技术信息）**：Klaus Kusche 在 AMD 大小核线程里报告 `because all my kernels are built without debugfs (using an earlier version of Mario's patch), and without Mario's patch and without debugfs, I don't get any big/little scheduling at all.` 即在他的构建里「大核/小核区分」似乎依赖 debugfs 是否挂载。
- **Mario Limonciello（AMD）**否定这个关联：`The debugfs patch doesn't really add anything tangible. I'd say tests with that and debugfs turned off are just as valid as tests with no patch and debugfs turned on.`
- **Tim Chen 的处理方式值得学**：他没有陷入 debugfs 争论，而是把问题收回自己的可测参数上——`If you just apply https://lore.kernel.org/lkml/20260825174112.2580942-1-tim.c.chen@linux.intel.com/, with default aggr_tolerance, what numbers do you see? That will be helpful for further tuning.` 也就是说，异构平台上的 `aggr_tolerance` 取值是当前最需要外部数据的量。
- 结论性分歧：**没有**。本片的风险全部集中在「Intel hybrid 之外的异构平台」（AMD 大小核、arm64 big.LITTLE）上是否成立。

## 合入评估

`likelihood = high`。已有 `Reviewed-by: Ricardo Neri`、`Reviewed-by: Chen Yu`、`Tested-by: Ricardo Neri`，主评审人只要求流程修正且当日已修好，门控保证对称系统零影响。剩余不确定性是 Peter 尚未对重发版表态，以及 AMD 平台的反馈仍在收集（不成合入障碍，但可能引出后续 tuning 补丁）。

## 效果评估

**本日无新数据。** 已有的是 Intel 侧的评审/测试背书库（`Tested-by`），但没有量化数字。跨平台部分只有一个明确的负面观测：AMD 大小核平台上，测试者表示未打 Mario 的补丁且不开 debugfs 时观察不到大小核调度行为——该观测与本片机制的关系未验证，**属个人构建环境下的主观描述，未见数据**。Tim 索要的 `aggr_tolerance` 默认值下的数字，当日尚未给出。

## 我可以参与的点

- **最实际的一条：给 AMD / arm64 异构平台补 `aggr_tolerance` 数据**。Tim 已经公开向测试者要这组数字（`with default aggr_tolerance, what numbers do you see?`）。在自有大小核机型上跑一轮并回帖，是本日门槛最低、对上游最有用的贡献。
- **misfit 判定与既有 misfit 通路的对齐**：本片新增的 `task_misfits_asym_cpu()` 直接复用 `task_fits_cpu()`，判据是 `(env->sd->flags & SD_ASYM_CPUCAPACITY) && !task_fits_cpu(p, env->dst_cpu) && task_fits_cpu(p, env->src_cpu)`；而上游另有 `migrate_misfit` 这一 migration_type 与 `sgs->group_misfit_task_load` 统计（本片同时用了这两者）。可以核对本片在 `alb_break_llc()`/`llc_balance()` 中插队的优先级，是否与既有 misfit 迁移的分类顺序存在重复判定或互相抵消。
- **cpuset/容量交互**：OLK-6.6 若有异构 + cpuset 组合场景，本片的「源放得下、目的放不下则禁止」判据是可直接借鉴的独立小改动，回合成本极低（`kernel/sched/fair.c` 两处 + 分类阶段优先级）。
- **流程细节**：Peter 的 `Tim sends patch, Tim adds SoB, yes?` 提醒——从别人 fork/改出来的补丁也要作者本人 SoB；同时修正后应以正式 resend 而非内嵌回帖发出，否则 lore 上的 Subject 与 changelog 不一致（本片就是这样）。

## 参考链接

- 原始补丁（2026-08-25）: https://lore.kernel.org/all/20260825174112.2580942-1-tim.c.chen@linux.intel.com/
- Tim Chen（承认漏 SoB）: https://lore.kernel.org/all/71c2ce7a2d443246755035379556382866a83156.camel@linux.intel.com/
- Tim Chen（重发修正版）: https://lore.kernel.org/all/edbb2503d554c63dc9b72e201fb4a17e1cb119e7.camel@linux.intel.com/
- AMD 大小核线程中 Tim 索要 aggr_tolerance 数据: https://lore.kernel.org/all/406a5c407bbe60cafc24f715e089f5552a0791f9.camel@linux.intel.com/
- Klaus Kusche（无 debugfs 即无大小核调度）: https://lore.kernel.org/all/3a8985e1-77b4-4127-af0a-ec1c397eb1ad@computerix.info/
- Mario Limonciello（debugfs 补丁无关）: https://lore.kernel.org/all/b8510d6e-4303-4698-a056-9f12cb859bc9@amd.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched/fair: avoid creating misfits during cache-aware balancing"
id: sched-20260901-011
date: '2026-09-01'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: "https://lore.kernel.org/all/edbb2503d554c63dc9b72e201fb4a17e1cb119e7.camel@linux.intel.com/"
authors: [Tim Chen, Peter Zijlstra, Klaus Kusche, Mario Limonciello]
maintainers_involved: [Peter Zijlstra]
current_version: null
patch_series:
  - version: null
    msgid: '<20260825174112.2580942-1-tim.c.chen@linux.intel.com>'
    date: '2026-08-25'
    summary: 'can_migrate_llc_task()/alb_break_llc() 在"源放得下、目的放不下"时禁止/否决 cache-aware 迁移，hybrid 门控；分类阶段发现 misfit 时让 misfit 迁移优先于 LLC 聚合'
    review_outcome: 'Ricardo Neri Reviewed-by + Tested-by、Chen Yu Reviewed-by；Peter Zijlstra 仅要求补作者本人 SoB 与标题大小写'
  - version: '修正重发'
    msgid: '<edbb2503d554c63dc9b72e201fb4a17e1cb119e7.camel@linux.intel.com>'
    date: '2026-09-01'
    summary: '补 SoB、format-patch 头标题改为 Avoid；以回帖内嵌方式重发，邮件实际 Subject 行仍为小写'
    review_outcome: '本日未见 Peter Zijlstra 进一步表态'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 'Peter Zijlstra 尚未对修正重发版表态'
  - 'AMD/非 Intel 异构平台上的行为仍在向外部测试者收集数据（aggr_tolerance 默认值下的表现）'
  - '重发采用回帖内嵌 patch 形式，lore 上的 Subject 与内容不一致，可能需要正式 resend'
  next_action: '等 Peter 对重发版确认；补充异构平台 aggr_tolerance 实测数据'
contribution_opportunities:
  - kind: testing
    description: '在 AMD 大小核或 arm64 异构机型上给出默认 aggr_tolerance 下的实测数字并回帖——Tim Chen 当日明确在向测试者要这组数据'
  - kind: review
    description: '核对本片新增的 task_misfits_asym_cpu() 与既有 migrate_misfit / group_misfit_task_load 通路是否存在重复判定或优先级互相抵消'
  - kind: new_patch
    description: '把"源可容纳而目的不可容纳则拒绝迁移"这一判据独立化，供非 cache-aware 的异构负载均衡路径复用'
source_email_count: 5
related_articles: [sched-20260826-010, sched-20260831-006, sched-20260904-006, sched-20260905-007]
tags:
- load_balance
- cfs
- topology
generated_at: '2026-09-07'
---
