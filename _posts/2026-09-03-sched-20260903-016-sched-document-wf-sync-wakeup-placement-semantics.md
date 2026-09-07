---
id: sched-20260903-016
date: '2026-09-03'
subject: 'sched: Document WF_SYNC wakeup placement semantics'
subsystem: sched
type: discussion
status: rfc
severity: low
thread_root_msgid: <20260825-sched-wf-sync-doc-v1-0-f899edb44ff5@gentwo.org>
lore_url: https://lore.kernel.org/all/20260825-sched-wf-sync-doc-v1-1-f899edb44ff5@gentwo.org/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Shubhang Kaushik
maintainers_involved:
- Madadi Vineeth Reddy
patch_series:
- 'sched: Document WF_SYNC wakeup placement semantics (RFC 1/2)'
merge_assessment:
  likelihood: possible
  blocking_issues:
  - Vineeth 指出文档逐字复述实现会静默过期，需按契约/实现分层重写
  - 仍是 RFC，无 sched 维护者表态、无任何 tag
  - 0/2 与 2/2 正文缺失，无法确认系列其余部分是否同样复述实现
  - 同区域 sched-sync-wakeup 系列若先落地，本文档描述的路径当场过期
  next_action: 等作者回应分层意见，并先把五条不保证做成可执行断言
contribution_opportunities:
- 给出契约/实现分层的写法建议并替代逐字复述的 call flow
- 把五条不保证写成 sched kselftest 断言，作为文档失效检测
- 整理 WF_SYNC 被当成放置请求的真实调用点作为文档动机
- 在绑核/cpuset 场景验证 wake_wide() 与 migration_cost/4 阈值行为是否与文档一致
source_email_count: 1
related_articles:
- sched-20260826-004
tags:
- sched_ext
- sched/fair
title: 'sched: Document WF_SYNC wakeup placement semantics'
layout: article
---

## TL;DR

Shubhang Kaushik 的 RFC 1/2 新增 `Documentation/scheduler/sched-wake-affinity.rst`（133 行）并在 `Documentation/scheduler/index.rst` 挂上目录，把 **fair 类**（不是 sched_ext）的 `WF_SYNC` 唤醒放置与抢占行为第一次成文：`sync = (wake_flags & WF_SYNC) && !(current->flags & PF_EXITING)`、`WF_SYNC` 不绕过 `wake_wide()` 分类、`wake_affine()` 的结果只是候选（还要经 `select_idle_sibling()` 改写）、也不保证被唤醒者立即抢占（阈值是 `sysctl_sched_migration_cost`，`WF_RQ_SELECTED` 时除以 4）。作者刻意声明「只记录现状、不建立新策略」。本日唯一一封回帖来自 IBM 的 Madadi Vineeth Reddy，他反对的不是结论而是写法：文档逐字复述实现（`want_affine`、`nr_running`、helper 名），「This could quickly go stale with code changes and nothing will tell us then. I think the contract doesn't need the call flow.」

## 背景与问题

`WF_SYNC` 由「预计很快让出 CPU 的唤醒者」提供，是提示而非放置请求；fair 类把它当启发式使用，但从 `try_to_wake_up()` 经 `select_task_rq_fair()`、`select_idle_sibling()`、`preempt_sync()` 的整条路径上，它对最终 CPU 选择与抢占的实际影响力从未成文。缺文档的直接后果是调用方容易把它当成「让被唤醒者跑在我这个 CPU 上」的请求，而实现给出的是一串条件与例外。

作者对新文档的定位极为保守——「This documents existing behavior only. It does not establish a new WF_SYNC placement policy.」这句话并非套话：`WF_SYNC` 的放置语义此刻正被多路改动争抢。同一作者 7 月就在推 `[PATCH v3] sched/fair: Prefer waker CPU for non-SMT reciprocal ...`（msg slug 为 `sched-sync-wakeup`），K Prateek Nayak 在其上回帖给出把判断下推到 `select_idle_sibling()` 的原型（给 `select_idle_sibling()` 增加 `sync` 参数、`select_idle_smt()` 改用 `rd->span` 并加 `task_fits_cpu()` 检查）；Madadi Vineeth Reddy 自己 08-01 也发过 `[PATCH] sched/fair: Let sync wakeups target the waker's core ...`。也就是说，「记录现状」的文档与「改变现状」的补丁属于同一个尚未收敛的讨论域，这正是本日回帖担心的地方。

## 技术方案

1/2 是纯文档：`Documentation/scheduler/index.rst` +1 行，新增 `Documentation/scheduler/sched-wake-affinity.rst` 133 行（SPDX GPL-2.0，标题 "WF_SYNC Wakeup Placement Hints"）。内容分五节：

- **Wakeup paths**：成功的唤醒不一定选 CPU——wakee 已入队时 `try_to_wake_up()` 可经 `ttwu_runnable()` 完成，保留原 runqueue 但仍可能调用 `wakeup_preempt()`；未入队时走 `select_task_rq()`，而只有一个允许 CPU 或迁移被禁用时会绕过调度类的选择方法。明确「同步等待原语会传 `WF_SYNC`，`WF_SYNC` 本身不会让唤醒者阻塞或让出」。
- **Fair-class CPU selection**：给出 `sync` 的计算式并指出 current 处于 `PF_EXITING` 时 `WF_SYNC` 不起作用；`select_task_rq_fair()` 先 `record_wakee()`，在 `WF_CURRENT_CPU` 且唤醒 CPU 允许、或 `find_energy_efficient_cpu()` 已选中且根域未 overutilized 时，会**在 wake-affine 选择之前返回**；否则 `want_affine = !wake_wide(p) && cpumask_test_cpu(cpu, p->cpus_ptr)`，并强调 `WF_SYNC` 不覆盖 `wake_wide()` 的分类；`wake_affine()` 只比较唤醒 CPU 与 wakee 的 previous CPU 两个候选，`wake_affine_idle()` 在 `rq->nr_running - cfs_h_nr_delayed(rq) == 1` 时可偏好唤醒 CPU，`wake_affine_weight()` 会扣除 current 负载并偏置 previous CPU 的有效负载。
- **Idle CPU selection**：`wake_affine()` 的结果只是候选，`select_idle_sibling()` 可改选 previous CPU、最近使用 CPU、空闲 SMT 兄弟或搜索域内其它空闲 CPU；非对称容量系统优先用 `sd_asym_cpucapacity`，否则用候选 CPU 的 `sd_llc`。结论式表述：`WF_SYNC` 不保证 wakee 跑在唤醒者 CPU、不保证留在 previous CPU、不保证避免迁移、不保证与唤醒者共享同一核。
- **Fair-class wakeup preemption**：常规 fair 抢占检查先跑（非空闲 wakee 可抢占空闲实体、`PREEMPT_SHORT` 可能先选中 wakee）；只有 wakee 成为 next buddy 后 `preempt_sync()` 才用 `WF_SYNC` 决定是否请求重调度，条件包括 wakee 早于 current 且 current 已运行超过阈值（`sysctl_sched_migration_cost`，`WF_RQ_SELECTED` 时为四分之一）；不满足则返回 `PREEMPT_WAKEUP_NONE`。因此 `WF_SYNC` 既不保证也不阻止立即抢占，UP 上它反而能避免一次不必要的抢占。
- **Semantics and policy**：把上述归纳为「非绑定提示」的五条不保证清单，并写明调度器不会校验唤醒者随后是否真的阻塞，因此唤醒者继续运行、或连续发起多次唤醒后才让出，都是合法用法。最后一段是面向未来的：当前策略把局部性/并行度/拓扑/负载/容量的取舍留在调度器内，**任何强化 `WF_SYNC` 放置语义的未来策略都必须考虑各调用点、负载形态与硬件拓扑**。

## 版本演进与当前进展

- 08-25（邮件于 08-26 入库）Shubhang Kaushik（Ampere，投递地址 `sh@gentwo.org`）发 `[RFC PATCH 0/2]` + 1/2；**本缓存中没有 0/2 与 2/2 的正文**，故 2/2 的内容无法确认。
- 08-26 之后到本日无任何回帖，线程静默 8 天。
- 本日（09-03）Madadi Vineeth Reddy（IBM）给出唯一一条意见，指向文档写法而非语义；作者尚未回应，也没有 v2。
- 与本文档同源的策略改动仍在并行推进：作者自己的 `sched-sync-wakeup` v3（07-27）与 Vineeth 本人的 `Let sync wakeups target the waker's core`（08-01）都还没收敛，K Prateek Nayak（07-30 给出把 `sync` 下推进 `select_idle_sibling()` 的试用补丁）、Shrikanth Hegde、Zhan Xusheng、Kayra Cizmeci 均有参与（这些邮件多数正文未被缓存保留，无法引述具体意见）。

## Maintainer 意见与讨论焦点

- **Madadi Vineeth Reddy（IBM）**本日全帖只有三句话，但位置很准：「This document reproduces the implementation literally like `want_affine`, `nr_running`, helper names. This could quickly go stale with code changes and nothing will tell us then. I think the contract doesn't need the call flow.」他的关切是**文档与代码之间没有任何联动失效检测**：内核文档不存在能因 `select_idle_sibling()` 签名变化而失败的机制，所以逐字复述实现的部分会在下一次重构后静默变成错误信息，而这比没有文档更糟。
- 值得注意的是他的利益立场：他自己在推「让 sync 唤醒目标为唤醒者所在核」的代码改动，作者本人的 `sched-sync-wakeup` v3 也在同一区域，Prateek 的原型甚至就是给 `select_idle_sibling()` 加 `sync` 参数。换言之，被文档化的调用流程在短期内就是会被改的对象，这使他的反对不是抽象原则而是直接经验。
- 讨论焦点因此是文档的**分层**：五条「不保证」清单与「调度器不校验唤醒者是否真的阻塞」这类契约性表述是稳定的、值得进文档的；`want_affine`/`rq->nr_running - cfs_h_nr_delayed(rq) == 1`/`sysctl_sched_migration_cost / 4` 这类实现细节属于代码注释与 changelog 的范畴。文档末尾那句「未来强化 `WF_SYNC` 语义必须考虑调用点/负载/拓扑」恰好说明作者自己也知道契约与实现的分界在哪里。
- 无人对文档陈述的行为本身提出纠正——这在「行为从未成文」的主题上是重要的正面信号：语义层面作者读得对。
- 未见 Peter Zijlstra、Ingo Molnar 表态；无 `Acked-by`/`Reviewed-by`。

## 合入评估

likelihood: **possible**。

依据：文档类补丁的成本收益很容易成立，而且本主题确实有真实缺口（`WF_SYNC` 被大量调用方使用，而它对调用方可见的提示语义此前只存在于代码里）；回帖者认可语义、只要求改写法，是「可修」而非「可否」的反对；作者本人是这块区域的活跃改动者，重写文档的门槛低；133 行的结构（四条路径 + 一节契约）本身已经具备可拆分性。

卡点：一是必须正面处理 Vineeth 的意见——要么把 call-flow 段落抽象到不依赖具体符号/表达式，要么给出「如何避免静默过期」的机制说明，否则同一片区域的任何重构都会让文档失真；二是仍是 RFC，需要去掉 RFC 标记并拿到 sched 维护者的接受；三是 0/2 与 2/2 的正文缺失，若 2/2 也复述实现则同一问题要处理两次；四是**真正的风险是时序**：如果 `sched-sync-wakeup` 那条线先落地（`select_idle_sibling()` 接收 `sync`、`select_idle_smt()` 改用 `rd->span`），本文档描述的路径当场过期，理想顺序应是策略先收敛、文档随后。

## 效果评估

纯文档补丁，不涉及效果数据；本日回帖也没有任何量化内容。可量化的只有覆盖面：`Documentation/scheduler/sched-wake-affinity.rst` 新增 133 行、`index.rst` 1 行，覆盖唤醒路径、fair 类 CPU 选择、空闲 CPU 选择、fair 类唤醒抢占与策略契约五节，明确写出 5 条「不保证」和 1 条「调度器不校验唤醒者随后是否阻塞」。

需要标注的证据缺口：本缓存未保留 0/2 与 2/2 正文，无法判断系列是否声称了额外收益或包含测试/其它文档改动；作者也未说明这份文档是回应过哪些具体的误用案例——而这恰是文档类补丁最有说服力的动机材料。

## 我可以参与的点

1. 顺着 Vineeth 的意见给出可执行的分层方案，比单纯附和更有价值：文档只保留契约（不保证清单 + 合法用法 + 阈值来源的名称而非算式），把 `want_affine` 表达式、`nr_running` 判据、`/4` 阈值这类细节留在 `kernel/sched/fair.c` 注释里，并在文档中用「本节描述 v7.x 的 fair 路径实现，具体判据以代码为准」这类版本锚替代逐字复述。
2. 补上他担心的「过期无人知」的机制：把五条不保证写成可执行的断言用例（例如 `WF_SYNC` 唤醒后 wakee 的落点、是否立即抢占，在绑核与多任务并发下均不成立），放进 sched 的 kselftest 或一个小型回归脚本。测试失败就是文档失效的信号，这比在文档里加警告有效得多，也正好是本区域几个并行系列都需要的基础设施。
3. 从调用方角度提供材料：`WF_SYNC` 的误用案例（谁把它当成了放置请求、后果是什么）目前在邮件里一个都没有。整理若干真实调用点（同步等待原语、管道/socket 类唤醒）作为 cover letter 的动机，会显著提高这类文档补丁的接受速度。
4. 自家内核的对照检查：文档里的判据可以直接当作运维核对表——`sysctl_sched_migration_cost` 与 `WF_RQ_SELECTED` 的四分之一阈值、`wake_wide()` 不受 `WF_SYNC` 影响这两条，在绑核 + cpuset 划分的延迟敏感服务上验证「sync 唤醒是否被 `wake_wide()` 打散」，既能给上游提供数据，也能判断自研树上是否需要自己的放置补丁。

## 参考链接

- 本文档系列：
  - RFC 封面（0/2，正文未保留于本缓存）：https://lore.kernel.org/all/20260825-sched-wf-sync-doc-v1-0-f899edb44ff5@gentwo.org/
  - RFC 1/2（新增 sched-wake-affinity.rst）：https://lore.kernel.org/all/20260825-sched-wf-sync-doc-v1-1-f899edb44ff5@gentwo.org/
  - 本日 Madadi Vineeth Reddy 的回帖：https://lore.kernel.org/all/d52d3775-ded0-4b7a-8315-6e940ba90f4a@linux.ibm.com/
- 同区域的策略改动线索：
  - 作者自己的 sync wakeup v3 补丁：https://lore.kernel.org/all/20260727-b4-sched-sync-wakeup-v3-1-90cf481dbd85@gentwo.org/
  - K Prateek Nayak 把 sync 下推进 select_idle_sibling() 的原型：https://lore.kernel.org/all/f3d5530f-3811-42af-8c34-c40cf314deed@amd.com/
- 相关文章：[[sched-20260826-004]]（本 RFC 首发日的记录）。
