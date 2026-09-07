# Cache-aware scheduling does not work well with amd big/little cores

## TL;DR

用户报告（Klaus Kusche，AMD Ryzen HX 370）：开启 cache-aware scheduling 后，一个跑在小核上的长时 LTO 链接进程**即使大核全空闲也不会迁走**——因为所有大核构成一个 L3 域、所有小核构成另一个域，CAS 的判定压过了大/LITTLE 容量调度。Chen Yu 确认"当前代码里 CAS 覆盖了非对称调度策略"，并指向 Tim Chen 8/25 的修复 `[PATCH] sched/fair: avoid creating misfits during cache-aware balancing`（该文已在 sched-20260826-010 分析过）；报告者 8/31 晚回报"两个补丁配合起来看起来达到期望效果"，但**没有数字**。同日 Peter Zijlstra 对 Tim 的补丁只提了 SoB 链与 subject 大小写两处形式意见。

## 背景与问题

- **平台/负载**：AMD Ryzen HX 370（Zen 混合架构），Gentoo + Clang full-LTO 编译；LTO 链接是单个进程连续跑数分钟、其余机器基本空闲的典型形态。
- **症状**：CAS 引入前，AMD pstate 驱动把大/小核容量差异告知调度器，LTO 进程会被挪到大核；CAS 引入后，"大核集合"与"小核集合"各自构成一个 L3 域，进程一旦起在小核域上就不再迁往大核，哪怕全部大核空闲数分钟。
- **为什么在 LTO 上伤两次**：小核频率 3.3 GHz vs 大核 5.1 GHz；且小核 L3 只有 8 MB、大核 16 MB——LTO 恰恰是 cache 密集型，域内局部性红利也拿不到。
- **报告者的诉求（原话概括）**：若大核空闲而小核上有长时任务，大/小核（容量）调度应当**压过** cache-aware 调度，即便这意味着跨缓存域迁移。
- **影响范围**：所有 SD_ASYM_CPUCAPACITY 平台上的 CAS 用户（AMD Zen 客户端、Intel 混合架构、ARM big.LITTLE 同构问题）。

## 技术方案

Chen Yu 给出的判断是"这不是配置问题而是代码问题"：CAS 可以调（debugfs 里 `aggr_tolerance`，Mario Limonciello 在帖里点名了这个旋钮并给出引入它的 commit `c1e7fe5e75ed11fa85368e5a186472afd3858f3a`）甚至整体关掉，但根因是 CAS 的迁移判定覆盖了非对称调度的策略；Ricardo Neri 早前已发现同一问题，Tim Chen 的补丁按"在 CAS 判定中尊重 CPU 容量、避免把任务变成 misfit"来修，只针对 **misfit** 这一类：

- `can_migrate_llc_task()`：当任务能装得下源 CPU、却装不下目的 CPU 时，禁止这次 LLC 迁移。
- `alb_break_llc()`：同一条件下否决 active balance，避免把 runnable 任务推到容不下的 CPU。
- 两处检查都用 hybrid 处理器条件门控，对称系统不受影响。
- 已经不匹配源 CPU 的任务仍交给既有 LLC 策略（因为这次移动不会让 fitness 更差，同时保留 misfit 向大核的**上迁移**）。
- 额外一条：负载均衡分类阶段若发现 misfit 任务，**misfit 迁移优先于 LLC 聚合**——"更合适的 CPU 带来的收益大于更好的缓存局部性"。

与 8/31 另一条相关的信号：AUTOSEL 把 Andrea Righi 的 `sched/fair: Reject misfit pulls onto busy SMT siblings on asym-capacity...`（upstream `bf6aa722198d3c06e4236e8c5a480f30a64e1513`，`Reported-by: Felix Abecassis`，`Reviewed-by: Vincent Guittot`，由 Peter Zijlstra 收进 tip）回合到 6.1 系列——说明"非对称容量 × 迁移目标判定"这一类问题已被认定为 stable 级别。

## 版本演进与当前进展

- 8/25：Tim Chen 发出 `sched/fair: avoid creating misfits during cache-aware balancing`（`<20260825174112.2580942-1-tim.c.chen@linux.intel.com>`），已带 `Reviewed-by: Ricardo Neri`、`Tested-by: Ricardo Neri`、`Reviewed-by: Chen Yu`；8/26 的分析见 sched-20260826-010。
- 8/29：Klaus Kusche 发报告线程；Mario Limonciello 抄送 CAS 相关的人并提示 `aggr_tolerance`。
- 8/31：Chen Yu 确认根因并把 Tim 的补丁摆到报告者面前；Peter Zijlstra 在 Tim 的补丁线程上回两处形式意见；报告者实测回报有效。
- 补丁本体仍是 **v1**，当天没有因这些意见发出 v2。

## Maintainer 意见与讨论焦点

- **Chen Yu（Intel，CAS 侧核心作者）**：直接承认设计冲突——"The issue in current code is that the cache aware scheduling overwrites the strategy of asymmetric scheduling"，并指出该问题 Ricardo 早已发现；给出的答案是复用 misfit 路线（容量优先），而不是给 CAS 加"空闲大核唤醒"这类新机制。
- **Peter Zijlstra**：没有质疑方案，只提两点形式要求——"Tim sends patch, Tim adds SoB, yes?"（发送者与 SoB 链对不上）与"we start $subject with capital after subsystem: part"（subject 冒号后首字母要大写）。
- **Mario Limonciello（AMD）**：先把 CAS 的历史作者们拉进线程，再给出 `aggr_tolerance` 调参路径，态度是"先确认能否绕过"。
- 未解决的分歧：报告者真正问的是**优先级**（长时任务 + 空闲大核时应否由容量压过缓存），而 Tim 的补丁只覆盖了"别把任务变成 misfit"这一子集；对"已经不在 misfit 判定范围内的长时任务"（例如容量上勉强能跑、但大核明显更快的情况）本日没有任何人给出结论。报告者说"两个补丁配合起来"有效，但当日线程里无法确认第二份补丁具体是哪一个（未获取到）。

## 合入评估

**likely**（就 Tim Chen 的 misfit 防护补丁而言）。它已有两位 Intel 侧 reviewer（其中一位还 Tested-by），维护者只要了 SoB 与 subject 大小写的修正，属于"改了就能收"的状态；同一问题域的另一半（`bf6aa722198d`）已进 tip 并被 AUTOSEL 回合到 6.1/6.18，是这条路径正在被稳定收口的旁证。**开放问题**是报告者提出的更一般的"容量优先于缓存"策略是否要单独做——本日无人接手，属于讨论级别，不影响当前补丁合入。

## 效果评估

**只有主观观察，没有数据**。报告者明确写："I just look at a bar graph showing the current load of each core... I have the impression that LTO compilations finish significantly faster now. I don't have exact numbers or benchmarks."（每核负载柱状图显示长时 CPU 密集任务会迁到快核；感觉 LTO 编译明显变快；无精确数字）。作者与 reviewer 当天也没有贴 benchmark。因此"修复有效"目前只到个案复现级别。

## 我可以参与的点

- **补一个可信的量化结果**：这是全线程最缺的东西。在 AMD Zen 混合客户端（或 Intel 混合架构）上跑 full-LTO 内核/LLVM 构建，记录总耗时与小核占用时间片，分别测 CAS 默认 / `aggr_tolerance` 调参 / 打 Tim 补丁三种配置——报告者只能看柱状图，任何带数字的回帖都会直接被引用。
- **把"优先级"问题写实**：本日的核心分歧是 misfit 防护够不够覆盖"长时任务 + 空闲大核"。可以先量化 Tim 的补丁在报告者场景下究竟拦住了哪条路径（`can_migrate_llc_task()` 还是 `alb_break_llc()`），再回答是否需要更强的容量优先规则。
- **顺手确认第二份补丁**：报告者说"两个补丁一起"，线程里没人问是哪两个；回帖问清并把它一并纳入验证矩阵，可以避免一个错误的"已修复"结论扩散。
- **回合判断**：OLK-6.6 若已带 CAS（或计划带），misfit 防护这条属于低风险可回合；`bf6aa722198d` 有 AUTOSEL 记录、可直接对照检查。

## 参考链接

- lore thread（报告者原始邮件）: https://lore.kernel.org/all/2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info/
- Mario Limonciello（拉人 + debugfs 旋钮）: https://lore.kernel.org/all/8064e1d8-b51c-48e5-a312-8c31581991f5@amd.com/
- Chen Yu（根因确认 + 指向修复）: https://lore.kernel.org/all/b475039b-defe-46e7-ab85-46e3196da667@intel.com/
- Klaus Kusche（实测回报）: https://lore.kernel.org/all/369d0bbb-db7a-4f86-bee2-332d5295c452@computerix.info/
- 对应修复补丁: https://lore.kernel.org/all/20260825174112.2580942-1-tim.c.chen@linux.intel.com/
- Peter Zijlstra 当日对该修复的意见: https://lore.kernel.org/all/20260831084149.GG4120091@noisy.programming.kicks-ass.net/
- 同域已合入并被回合的补丁（AUTOSEL 6.18-6.1 通知）: https://lore.kernel.org/all/20260831133314.4125787-171-sashal@kernel.org/
- tip-bot commit: `bf6aa722198d3c06e4236e8c5a480f30a64e1513`（同问题域的另一半，非本补丁）
- stable backport: `bf6aa722198d3c06e4236e8c5a480f30a64e1513` 已进 6.1/6.18 AUTOSEL 流程；Tim Chen 的修复尚无 stable 记录

---
id: sched-20260831-006
date: '2026-08-31'
subject: "Cache-aware scheduling does not work well with amd big/little cores"
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info>"
lore_url: "https://lore.kernel.org/all/369d0bbb-db7a-4f86-bee2-332d5295c452@computerix.info/"
authors: [Klaus Kusche, Chen Yu, Mario Limonciello, Tim Chen, Peter Zijlstra]
maintainers_involved: [Chen Yu, Peter Zijlstra, Mario Limonciello]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260825174112.2580942-1-tim.c.chen@linux.intel.com>"
    date: 2026-08-25
    summary: "在 can_migrate_llc_task()/alb_break_llc() 两处 CAS 入口按容量否决会造成 misfit 的迁移，并在 LB 分类阶段让 misfit 迁移优先于 LLC 聚合"
    review_outcome: "已有 Reviewed-by/Tested-by Ricardo Neri 与 Reviewed-by Chen Yu；Peter Zijlstra 只要求补 SoB 链与 subject 大写；报告者实测有效但无数据"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: likely
  blocking_issues:
    - "SoB 链需作者补正、subject 冒号后需大写，未发 v2"
    - "修复只覆盖 misfit 子集，报告者提出的长时任务空闲大核优先级问题无人接手"
    - "仅有个案柱状图观察，无 benchmark 数据"
  next_action: "补 SoB/标题后重发或等维护者直接 apply，并由用户在混合架构机型上提供量化结果"
contribution_opportunities:
  - kind: testing
    description: "在 AMD/Intel 混合架构上测 full-LTO 构建总耗时与小核占用，对比 CAS 默认/aggr_tolerance 调参/该补丁三种配置"
  - kind: discussion
    description: "确认该补丁是否覆盖'长时任务 + 空闲大核'的全部路径，回答容量与缓存局部性的优先级取舍"
  - kind: review
    description: "对照 bf6aa722198d 的 AUTOSEL 记录评估 OLK-6.6 需要一并回合哪些 misfit 修复"
generated_at: "2026-09-07T21:16:22"
source_email_count: 5
related_articles: [sched-20260826-010]
tags: [load_balance, regression, x86]
---
