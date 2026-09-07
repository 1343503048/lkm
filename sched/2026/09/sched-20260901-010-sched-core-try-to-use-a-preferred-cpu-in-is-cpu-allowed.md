# sched/core: Try to use a preferred CPU in is_cpu_allowed

## TL;DR

增量更新（完整方案见 sched-20260831-007 / sched-20260810-008）。Shrikanth Hegde 的 preferred-CPU / steal_governor v11 系列中，`05/12` 关于「要不要只在实测过的架构上启用」的争论在 09-01 收口：Vincent Guittot 与 Dietmar Eggemann 都认为无需为 arm64 单独设限，理由是这条路径本来就架构无关——`task_cpu_possible_mask(p)` 默认即 `cpu_possible_mask`，且它在 `kernel/sched/core.c` 与 `kernel/cgroup/cpuset.c` 里早已为 `allow_mismatched_32bit_el0` 服务过。

## 背景与问题

patch 05/12 让 `is_cpu_allowed()` / `select_fallback_rq()` 在受限时优先选择仍被允许的 preferred CPU。争议点不在代码，而在**启用范围**：作者此前只在 PPC+pSeries LPAR（xPVM）与 x86+KVM 上实测过，Yury Norov 认为 arm64 缺少验证，`ARM64 testing is obviously missed.`——即主张先按已测架构开、arm64 等数据。

## 技术方案

本片的做法（前序文章已展开，此处只记与本轮争论直接相关的部分）：新增 `task_can_sched_on_preferred()`，只对 `fair_sched_class` 生效，任务正在改亲和性（`task_cpu(p)` 已不在 `p->cpus_ptr` 内）时忽略偏好状态；对存在架构专属 CPU 掩码的情形（典型是 arm64 上跑 32 位任务）不直接用 `cpumask_intersects()`，而是 `for_each_cpu_and(i, p->cpus_ptr, cpu_preferred_mask)` 再逐个与 `valid_mask` 求交。

**本轮争论的实质就是这个 `valid_mask` 分支值不值得为它单独设置架构门槛。** 反方论点有两层：(1) 该分支是通用代码，`valid_mask` 的取值与掩码运算本身不依赖 arm64 特定行为；(2) `task_cpu_possible_mask()` 这条获取 valid_mask 的通路并不是新代码，`kernel/cgroup/cpuset.c` 里已经在用它做同一件约束判断，因此 arm64 上的风险面已经被现有代码覆盖过。

## 版本演进与当前进展

v11（12 片）阶段，本日 3 封回帖全部集中在架构启用问题上，**无人对 v11 的代码本身提新意见**。争论走向已明确偏向 Vincent 的立场：`It's always better to support all arch by default, unless something is missing which is not the case here.`（08-31）→ 09-01 他补一句 `But the cpumask is already available not like if you need to create a new one`，即「启用 arm64 不需要新增任何基础设施」。Dietmar 随后从经验维度补上背书。当日没有作者回应记录。

## Maintainer 意见与讨论焦点

- **Dietmar Eggemann（本日最有信息量的一条，`<3368b089-32ce-4521-ab19-e37c9f029b8b@arm.com>`）**：
  - `IMHO, when testing the steal_governor on arm64 w/o 'allow_mismatched_32bit_el0', I wouldn't expect much difference in this respect compared to the architectures already tested.`
  - `Also, AFAIK, 'allow_mismatched_32bit_el0' was mainly relevant for Android devices up to Android 13 that supported 32-bit userspace, so I wouldn't expect it to be commonly enabled on recent devices.`
  - `As Vincent pointed out, 'task_cpu_possible_mask(p)' (which defaults to 'cpu_possible_mask') is already used in 'kernel/sched/core.c' and 'kernel/cgroup/cpuset.c' to support 'allow_mismatched_32bit_el0'.`

  注意他把风险精确切到了 `allow_mismatched_32bit_el0` 这一个配置上：只要它关着，arm64 的 `task_cpu_possible_mask()` 就等于 `cpu_possible_mask`，本片的特殊分支根本不会被走到；而这个配置在新设备上基本不再启用。**这实际上把 Yury 的「arm64 没测过」转化为「没测的那个分支在主流 arm64 配置下不可达」。**
- **Vincent Guittot**：坚持默认全架构启用，反对按架构设门槛。
- **Yury Norov**：立场是「arm64 缺测试」，本日未再回应 Dietmar 的可达性论证——分歧未被正式关闭，但已处于孤立。

## 合入评估

`likelihood = possible`。整个 v11 系列的瓶颈不在 05/12 的这条小改动，而在 steal_governor 主线本身（见 sched-20260817-005 / sched-20260825-001 记录的 v10/v11 演进与基准回退讨论）。本日争论向「全架构默认启用」收敛，若作者按此发 v12，本片不需要额外工作；`Reviewed-by` 仍未出现。

## 效果评估

**本日无任何数据**。3 封回帖全部是可达性与配置普遍性的论证（`allow_mismatched_32bit_el0` 的部署面、cpumask 是否复用），没有 arm64 实测数字。前序版本里出现过的 steal_governor 基准数据不在本日邮件范围内。

## 我可以参与的点

- **arm64 数据正好是缺失项**：Dietmar 的论证是「不开启 `allow_mismatched_32bit_el0` 时行为应无差异」——这是一个可以直接证伪或证实的经验命题。在 arm64 服务器（含我们自己的平台）上跑一轮 steal_governor + preferred CPU，分别开/关该配置，比继续讨论更有决定性。
- **cpuset 交叉点值得提前评估**：既然 `kernel/cgroup/cpuset.c` 已经使用同一个 `task_cpu_possible_mask()`，preferred CPU 语义与 cpuset 约束的叠加行为就是我们这条主线上需要盯的接口。可以帮忙构造「cpuset 收紧 + preferred 掩码 + 32 位任务」的组合用例。
- **回合判断**：OLK-6.6 若引入 preferred CPU 类特性，本片的 `fair_sched_class` 限定与「亲和性变更中忽略偏好」两个保护条件是必须一并带回的，否则 `migration_cpu_stop()` 可能把任务留在允许的亲和集合之外。

## 参考链接

- Yury Norov（arm64 缺测试）: https://lore.kernel.org/all/apWxmL_brfi4fa4z@yury/
- Vincent Guittot（cpumask 已可用）: https://lore.kernel.org/all/CAKfTPtA4zmD=0Es2cXSHAodTZGLJPvv88s0_4QScp745PxFVMw@mail.gmail.com/
- Dietmar Eggemann（可达性论证）: https://lore.kernel.org/all/3368b089-32ce-4521-ab19-e37c9f029b8b@arm.com/
- 05/12 补丁本体（v11）: 未获取到（本日缓存中只有回帖）
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched/core: Try to use a preferred CPU in is_cpu_allowed"
id: sched-20260901-010
date: '2026-09-01'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: null
lore_url: "https://lore.kernel.org/all/3368b089-32ce-4521-ab19-e37c9f029b8b@arm.com/"
authors: [Yury Norov, Vincent Guittot, Dietmar Eggemann, Shrikanth Hegde]
maintainers_involved: [Dietmar Eggemann, Vincent Guittot]
current_version: v11
patch_series:
  - version: v11
    msgid: null
    date: null
    summary: 'steal_governor / preferred CPU 系列的 05/12：is_cpu_allowed()/select_fallback_rq() 在受限时优先挑选仍被允许的 preferred CPU，含 task_can_sched_on_preferred() 与架构专属 valid_mask 求交分支（背景见 sched-20260831-007）'
    review_outcome: '09-01 三封回帖只争论启用范围：Yury Norov 认为 arm64 缺测试；Vincent Guittot 反对按架构设门槛（cpumask 本就复用）；Dietmar Eggemann 指出不开 allow_mismatched_32bit_el0 时 arm64 与已测架构无差异，且 task_cpu_possible_mask() 已在 core.c 与 cpuset.c 中被使用，故该特殊分支在主流 arm64 配置下不可达'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: possible
  blocking_issues:
  - '本片争论已收敛，但整个 v11 steal_governor 主线尚未稳定（历史上有基准回退争议）'
  - '无 Reviewed-by/Acked-by'
  - 'Yury Norov 未回应 Dietmar 的可达性论证，架构启用分歧未正式关闭'
  next_action: '作者按"全架构默认启用"发 v12；如要彻底关闭分歧，需要一份 arm64 实测数据'
contribution_opportunities:
  - kind: testing
    description: '在 arm64 服务器上分别以 allow_mismatched_32bit_el0 开/关跑 steal_governor + preferred CPU，验证 Dietmar 的"行为无差异"推断'
  - kind: testing
    description: '构造 cpuset 收紧 + preferred 掩码 + 32 位任务的组合用例，检验 valid_mask 三方求交分支的实际行为'
source_email_count: 3
related_articles: [sched-20260831-007, sched-20260810-008, sched-20260825-001, sched-20260817-005]
tags:
- affinity
- cgroup
- arm64
generated_at: '2026-09-07'
---
