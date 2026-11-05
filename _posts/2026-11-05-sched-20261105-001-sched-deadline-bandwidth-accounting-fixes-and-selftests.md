---
id: sched-20261105-001
date: 2026-11-05
subject: 'sched/deadline: bandwidth accounting fixes and selftests'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261104211207.1392343-1-mathieu.desnoyers@efficios.com>
lore_url: https://lore.kernel.org/all/20261104211207.1392343-1-mathieu.desnoyers@efficios.com/
authors:
- Mathieu Desnoyers
maintainers_involved:
- Juri Lelli
current_version: v2
patch_series:
- version: v1
  msgid: <cover.1793804635.git.mathieu.desnoyers@efficios.com>
  date: 2026-11-03
  summary: 12 补丁修复 SCHED_DEADLINE 带宽记账 bug，含自测与 sched_debug。
  review_outcome: Sashiko AI 9 条评审，引出 v2 新增 9 个补丁。
- version: v2
  msgid: <20261104211207.1392343-1-mathieu.desnoyers@efficios.com>
  date: 2026-11-05
  summary: 21 补丁：17 个修复 + 3 个自测 + 1 个 sched_debug，含 49 用例。
  review_outcome: Juri 多封 Reviewed-by/Acked-by，patch 4/2/6 有保留；Marek Tested-by。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 系列规模大（21 补丁 + 3353 行自测），与 Ingo 严格 -stable 子集的要求有张力
  - patch 2 的 KEEP_PARAMS ABI 变更需维护者拍板
  - patch 4 除零的实现方式未收敛
  next_action: 作者按 Juri 的 patch 4/8 意见修订，并拆分出可直接回退 stable 的修复子集
contribution_opportunities:
- kind: testing
  description: 在真实硬件（cpuset 分区/CPU hotplug/PREEMPT_RT）跑 deadline_bw_test 等 49 用例并回帖
- kind: review
  description: 人工仔细审阅 patch 4/6/15-18 的记账与 root domain 记录逻辑
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 21
related_articles: []
tags:
- deadline
- cgroup
title: 'sched/deadline: bandwidth accounting fixes and selftests'
layout: article
---

## TL;DR

Mathieu Desnoyers 的 v2 系列（21 补丁）在 Juri Lelli 此前 4 个 sched/urgent 修复之上，再修 17 个 SCHED_DEADLINE 带宽记账 bug（其中 3 个可直接打死内核：`__dl_sub()` 除零、无 active CPU 时 `dl_task_root_domain_cpu()` BUG()、隔离 CPU 全下线后重建记账 BUG()），并带 49 个用例的自测与 sched_debug 展示。Juri 已对多数补丁给 Reviewed-by/Acked-by，Marek Szyprowski 实测确认修复了他在 -next 上复现的 CPU hotplug 崩溃并给 Tested-by；但 Ingo 要求「严格只含 -stable 可回退修复的子集」，系列规模与一处 ABI 变更仍需收敛。

## 背景与问题

Juri Lelli 前一轮 4 个 SCHED_DEADLINE 带宽记账修复（tip/sched/urgent）在 linux-next 上触发 CPU hotplug 崩溃（见当日另一篇 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-002-sched-deadline-fix-stale-root-domain-in-cpuset-bandwidth-tra.html">sched-20261105-002</a>），被 Ingo 从 sched/urgent 移除。Mathieu 在该 4 个修复之上系统梳理了 dl_bw/total_bw 记账的边界缺陷——这些缺陷来自他正在开发的一个 cgroup 特性的自测（其中两个用例一个约每 1350 次挂一次、一个约每 10 次挂一次），逐根因追踪后扩展到整类问题。

17 个 bug 大致分三类：

1. **直接崩溃**：`__dl_sub()`/`__dl_add()` 用 root domain 的 active CPU 数做除法，在 CPU 通过 default domain 瞬间该数为 0（patch 4）；deadline 任务 affinity 无 active CPU 时 `dl_task_root_domain_cpu()` BUG()，PI 与 CPU hotplug 在默认内核即可触达（patch 5）；隔离 CPU 全下线后重建记账对无家可归的任务 BUG()（patch 18）。
2. **违反预留保证**：被 throttle 的任务切出 SCHED_DEADLINE 又切回后留在 throttle 态且无 replenish（patch 6，会永久不运行）；任务离开原预留后 replenishment timer 仍按旧预留周期 armed（patch 20）。
3. **记账泄漏/下溢**（约 11 个）：root domain 的 total_bw 或 runqueue 的 this_bw 与真实任务不符，导致要么超额准入 deadline 任务、要么一个都不准入且拒绝 offline 最后一颗 CPU，或在 this_bw 下溢时反复告警（patch 1/2/3/7/9/11/13/15/16/17/19/21）。

## 技术方案

核心手段是让「谁在记账」这件事可被追溯、可被幂等：

- **patch 1/2/3**：`SCHED_FLAG_KEEP_PARAMS` 的准入时序问题——patch 1 把准入检查挪到最后，避免「先预留带宽、后因后续失败拒绝」造成的泄漏；patch 2 拒绝「KEEP_PARAMS 请求会改变 policy」的情况（此前只拒绝换 class）；patch 3 让被保留参数不再无锁读取造成 stale 准入。
- **patch 9/15/16/17/18**：给 root domain 记账引入 generation 计数（patch 9），并让每个分发/回收带宽的站点记录「记账所在 root domain 的 CPU」（patch 15），cgroup attach 移动带宽时只在确有腾挪空间时移动（patch 16/17），重建记账时把带宽记到能容纳该任务的 CPU（patch 18）。
- **patch 11/21**：`add_rq_bw()`/`sub_rq_bw()` 幂等化（「该 runqueue 是否记账此任务」的标记内移），patch 21 补上 PI boost 后唤醒任务的 runqueue 侧记账。
- **patch 12**：sched_debug 增加每个 runqueue 的 this_bw/running_bw，让 patch 11 的下溢从用户态可见。
- **patch 8/10/14**：三个自测程序（deadline_bw_test 3353 行、deadline_rebuild_test、deadline_switch_test），共 49 个用例。

作者在 cover letter 中**明确披露**：这些补丁与测试由 LLM 编程助手在其指导下编写，并请熟悉该代码的人仔细审阅修复本身。

## 版本演进与当前进展

*current_version: v2（2026-11-05 发出，msgid 20261104211207.1392343-1）*。v1 为 12 补丁（`[PATCH 00/12]`），v2 扩到 21 补丁：新增 9 个来自 v1 评审（Sashiko AI 9 条评审 + 第二模型 1 条）与由此引出的修复，含 patch 2/3（KEEP_PARAMS 泄漏）、patch 7（PI donor 窗口内的死循环风险）、patch 9 的 generation 计数、patch 11 的幂等化重写、patch 13 的 dl_accounting_mutex、patch 15 的记录 root domain、patch 16/17（cgroup attach 两条路径）、patch 18（隔离 CPU 重建）、patch 19/20（两个基线 bug）与 patch 21。patch 编号与 v1 有重排（如 v1 的 9 变为 v2 的 11）。

## Maintainer 意见与讨论焦点

Juri Lelli（SCHED_DEADLINE 维护者）逐封回复，整体正面但有三处保留：

- patch 1/2/3 直接给 Reviewed-by；patch 5 给 Acked-by（但对 changelog 中「fall back」表述的小讽刺性 remark）。
- **patch 4（除零）**：Juri 质疑「是否应在 cpus==0 时绕过 add/sub，而不是在除法里处理」，尚未给 tag。
- **patch 2 的 ABI 变更**：作者明确说明「拒绝会改变 policy 的 KEEP_PARAMS 请求是 ABI 变化」，请维护者定夺是否保留。
- **patch 6**：Juri 指出 Sashiko 点出一个后续 re-entry 场景仍可能有问题（且他「似乎看到更多」），但认为该补丁修复的是真实 hang，倾向先合入、剩余问题单独处理。
- **patch 8（selftests）**：Juri 表示「非常有价值」，提到自己曾提过类似 kselftest 但没跟进，建议「是否要在 sched 下按 policy 分子目录」。

Sashiko AI（sashiko-bot@kernel.org）自动评审对多个补丁给出「潜在问题」提示（如 patch 7 指出 `switched_from_dl()` 清参数后留下 stale params）。Ingo 虽未直接评论本系列，但在相关线程（<a class="article-ref" href="/lkm/2026/11/05/sched-20261105-002-sched-deadline-fix-stale-root-domain-in-cpuset-bandwidth-tra.html">sched-20261105-002</a>）明确要求「严格只含 -stable 可回退的修复子集」。Marek Szyprowski 应用整系列实测通过并给 Tested-by。

## 合入评估

*likelihood=medium*。方向无异议、有维护者 Reviewed-by/Acked-by 与独立测试背书，但尚未满足合入条件：*blocking_issues*：① 系列规模偏大（21 补丁 + 3353 行自测），与 Ingo「严格 -stable 子集」的要求存在张力，可能需要拆分；② patch 2 的 ABI 变更需维护者拍板；③ patch 4 的实现方式（除零时绕过 vs 除法内处理）未收敛；④ LLM 参与写作，社区可能要求更仔细的人工审阅。*next_action*：作者按 Juri 的 patch 4/8 意见修订，并配合把「可直接回退 stable 的修复」单独挑出成子系列。

## 效果评估

作者在 8 个 8-vCPU QEMU guest 中跑 49 用例全过；4 vCPU、PREEMPT_RT、CONFIG_SCHED_PROXY_EXEC 开关、无 CONFIG_CPUSETS 五种配置下均无内核告警（16 个 guest）。逐补丁 bisect 显示各补丁在套件中的价值（base 下 8 个用例失败，+1/+2/+6/+7/+9 逐次转绿）。Marek 在 Odroid-N2（Amlogic Meson G12B）上复现了修复前 -next 的 CPU hotplug BUG，应用整系列后「everything works fine」。patch 21 的独立 reproducer 显示修复前 runqueue this_bw 停在 157285（应为 262142）。

## 我可以参与的点

- **testing**：在真实硬件（非 QEMU）上跑 `tools/testing/selftests/sched/deadline_bw_test` 等 49 用例，尤其带 cpuset 分区、CPU hotplug、PREEMPT_RT 的配置，回帖数据可加速合入。
- **review**：作者明确寻求对修复本身的仔细人工审阅（LLM 参与写作），尤其 patch 4 的除零处理、patch 6 的后续 re-entry 场景、patch 15-18 的 root domain 记录逻辑。

## 参考链接

- lore thread（v2 cover）: https://lore.kernel.org/all/20261104211207.1392343-1-mathieu.desnoyers@efficios.com/
- 作者「How this was developed / Changes since v1」说明在上述 cover 内，未获取到单独的 diffstat 链接。
