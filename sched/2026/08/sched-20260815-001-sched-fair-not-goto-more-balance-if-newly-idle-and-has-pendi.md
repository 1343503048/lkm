# sched/fair: Not goto more_balance if newly idle and has pending task when LBF_NEED_BREAK

## TL;DR
Xin Zhao 提交 10 个 patch 引入 `LB_PROMOTE` 调度特性，目标是在 `CONFIG_HZ_250` 等低 HZ 嵌入式平台上消除 CFS 任务的"不合理 CPU 空闲"事件（>4ms 调度延迟），提升实时性。目前 v1 刚发出，尚无 maintainer 意见，合入价值取决于通用性论证。

## 背景与问题
嵌入式平台常用 `CONFIG_HZ_250`，测试发现大量"不合理 CPU 空闲"：CPU 进入空闲状态 t 时间，而存在可运行、且不受 cgroup 约束、能在空闲 CPU 上运行的任务，却超过 t（>2.5ms）未被调度。
- 测试显示超过 95% 的此类事件 <4ms，但仍有 4-5ms 甚至 5-10ms 的长尾。
- 对实时系统而言，>4ms 的调度延迟会导致性能尖刺。

## 技术方案
新增 `LB_PROMOTE` feature（`kernel/sched/features.h`，+24 行），仅在 CFS 负载均衡路径生效。系列结构：
- patch 1（独立 bugfix）：`set_rd_overloaded()` 在 `rd->online != env->cpus` 时不该置位。
- patch 2/3（prerequisite）：解除 `active_load_balance_cpu_stop()` 中 `busiest_cpu == smp_processor_id()` 的绑定，并结束时清理 `active_balance`，为后面复用做准备。
- patch 4：定义 `LB_PROMOTE`，核心开关。
- patch 5：`select_task_rq_fair_thin()`，面向嵌入式平台的精简版选核逻辑。
- patch 6/7：改造 `active_load_balance_cpu_stop()` 以复用，并在 CFS 任务被抢占时触发"抢占式 active balance"。
- patch 8：移除 `avg_idle` 检查以避免 newly idle 提前退出。
- patch 9（独立小优化）：`LBF_NEED_BREAK` 时若有 pending task 不再 goto more_balance。
- patch 10：`LB_PROMOTE` 下 newly idle 尽力寻找可迁移任务。

注意：`+220/-25` 集中在 `fair.c`，涉及负载均衡与选核核心路径，改动面较广。

## 版本演进与当前进展
当前为 v1（2026-08-15 发出）。按封面信描述，所有 patch 源于对每次不合理空闲事件的 ftrace + 流程日志分析。v1 刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点
v1 刚发出，暂无 maintainer 意见。

## 合入评估
合入可能性未知。关键争议点（预判）：
- 新增一个调度 feature 仅对低 HZ 嵌入式场景收益明显，maintainer 很可能要求论证在通用/服务器场景不引入回退或过度 sys% 开销。
- patch 2/3 声称可独立合入，是否会被先单独收下、LB_PROMOTE 主体需要更多数据，值得关注。
- 作者承认开启该特性会增加 sys%，并带来"搜索合适任务"的 CPU 开销，需量化。

## 效果评估
作者给出实测（fillback 场景）：
- 不合理空闲事件：开启后（index 0/2/4 为 on）2.5-3ms、3-4ms、4ms+ 三档均为 0；关闭（index 1/3/5）仍有 4/13/1、6/3/0、1/1/0 的分布。开启可"完全消除 >4ms 事件"。
- 端到端延迟：开启 max 172 vs 关闭 180；median of avg 166 vs 167.68（提升有限）。
- sys%：开启 max 9.68 vs 关闭 9.35；median 8.81 vs 8.55（开启略增，符合预期）。
数据来自嵌入式平台 fillback 场景，非通用负载，结论外推需谨慎。

## 我可以参与的点
- 在 `CONFIG_HZ_250` 之外场景测试 LB_PROMOTE 对 sys% 与尾延迟影响，验证通用性。
- 评审 patch 2/3 是否真的独立于 LB_PROMOTE、以及 `select_task_rq_fair_thin()` 与现有 `wake_affine` 逻辑是否冲突。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched/fair: Not goto more_balance if newly idle and has pending task when LBF_NEED_BREAK"
id: sched-20260815-001
date: 2026-08-15
subsystem: sched
type: feature
status: under_review
severity: medium
thread_root_msgid: "<uid-41479@qq-imap>"
lore_url: "未获取到"
authors: [Xin Zhao]
maintainers_involved: [Peter Zijlstra, Vincent Guittot, Dietmar Eggemann]
current_version: v1
patch_series:
  - version: v1
    msgid: "<uid-41479@qq-imap>"
    date: 2026-08-15
    summary: "10 个 patch 实现 LB_PROMOTE 特性：在低 HZ（如 CONFIG_HZ_250）嵌入式平台上降低 CFS 任务"不合理 CPU 空闲"事件，提升实时性。"
    review_outcome: "v1 刚发出，暂无 review 意见。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: [需要 maintainer 评估新增 sched feature 的通用性价值, 仅在低 HZ 嵌入式场景收益明显，需更通用场景数据]
  next_action: "等待 maintainer 对 LB_PROMOTE 作为 sched feature 是否值得合入的反馈；补充非嵌入式/高 HZ 场景对比数据。"
contribution_opportunities:
  - kind: testing
    description: "在 CONFIG_HZ_250 之外的场景（如服务器高 HZ、NOHZ_FULL）测试 LB_PROMOTE 对 sys% 与尾延迟的影响，验证通用性。"
  - kind: review
    description: "评审 patch 2/3 的 prerequisite 改动是否真的独立于 LB_PROMOTE，以及 select_task_rq_fair_thin() 是否引入与现有 wake_affine 逻辑的冲突。"
generated_at: "2026-08-16T00:10:00"
source_email_count: 10
related_articles: []
tags: [sched/fair, load_balance, preempt, perf]
---
