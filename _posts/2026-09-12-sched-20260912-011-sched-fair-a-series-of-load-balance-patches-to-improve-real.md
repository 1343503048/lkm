---
id: sched-20260912-011
subject: 'sched/fair: A series of load balance patches to improve real-time performance
  of CFS tasks'
date: '2026-09-12'
subsystem: sched
type: feature
status: rfc
severity: low
thread_root_msgid: <20260910042950.1619727-1-jackzxcui1989@163.com>
lore_url: https://lore.kernel.org/all/20260912040804.3391229-1-jackzxcui1989@163.com/
authors:
- Xin Zhao
maintainers_involved:
- Vincent Guittot
current_version: v1
patch_series:
- version: v1 (RESEND)
  msgid: <20260910042950.1619727-1-jackzxcui1989@163.com>
  date: 2026-09-10
  summary: 10 补丁 RFC：LB_PROMOTE + select_task_rq_fair_thin() 等，针对 250Hz 下 fair 类调度延迟。
  review_outcome: 09-12 作者实质回应：生产 RT 占比数据（21%~53%）、0.3% 开销交换主张、SD_BALANCE_WAKE 切换新方向、对
    Prateek 反方案的 T0/T1/T2 反例；维护者无跟进。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - Vincent 对前提的否定未化解，维护者对新论据无跟进
  - patch 1 独立收益数据仍缺
  - SD_BALANCE_WAKE 方案可行性无人评估
  next_action: 等维护者回应新论据；若 SD_BALANCE_WAKE 方向被接受则等正式 v2
contribution_opportunities:
- kind: review
  description: 评估 SD_BALANCE_WAKE 动态切换的可行性（作者首次提出的替代接口形态）
- kind: review
  description: 读 sched_balance_find_src_group()/update_sd_lb_stats() 裁决 overload 语义之争
generated_at: '2026-09-14T12:40:00'
source_email_count: 4
related_articles:
- sched-20260911-009
- sched-20260910-001
tags:
- cfs
- load_balance
- topology
title: 'sched/fair: A series of load balance patches to improve real-time performance
  of CFS tasks'
layout: article
---

## TL;DR
Xin Zhao 当日对 LB_PROMOTE RFC 的质疑做出最实质的一轮回应：给出生产系统 RT 任务占比数据（18 个 CPU 上 RT 占比 21%~53%，如 CPU0 197/369），论证「RT 任务已无法继续扩容、kworker/ksoftirqd 的公平时延才是瓶颈」，并提出新设计方向（LB_PROMOTE 使能时给各 CPU 调度域加 SD_BALANCE_WAKE、禁用时还原）；对 Prateek 的 LBF_ALL_PINNED 质疑给出双簇 T0/T1/T2 反例走查。维护者仍未跟进。本文为增量更新，09-10/09-11 讨论见 sched-20260910-001、sched-20260911-009。

## 背景与问题
（承 sched-20260911-009）Vincent 质疑「有实时需求为何不用 RT 调度器」并否定 LB_PROMOTE 前提；Prateek 索要 patch 1 数据并给出 rq->all_pinned 反方案。作者当日逐条回应。

## 技术方案
当日无新版本，作者以四封回帖推进论证：

- **回应「为什么不用 RT 调度器」（05/10 线程）**：贴出生产系统 18 CPU 的任务构成表——RT 任务占比从 21%（CPU9: 21/77）到 53%（CPU0: 197/369），「RT 任务占比已经很高，继续扩容不可行」；kworker、ksoftirqd、kswapd 不适合 RT 调度但存在时延不足拖累整条流水线的场景。LB_PROMOTE（核心是 patch 10，对 sched_balance_find_dst_cpu 的改造）正是针对 250Hz 下 fair 类调度延迟；并提出：LB_PROMOTE 使能时给每个 CPU 的调度域加 SD_BALANCE_WAKE、禁用时还原为 0，询问可行性；
- **回应「ILB 下一 tick 会修」（04/10 线程）**：作者称已深入 review 过 ILB 逻辑，250Hz 下的调度延迟可以从代码解释；愿意接受 0.3% 平均系统开销换取消除 ≥4ms 的调度延迟案例并显著减少 2.5ms~4ms 案例，认为对嵌入式实时 Linux 用户整体有益；曾考虑用 hrtimer 替换部分 ILB 逻辑以更早触发检查（与现有改进不互斥）；提示 patch 7/8/10 的负载均衡改动（尤其 patch 10）；
- **回应 Prateek 的 all_pinned 反方案（01/10 线程，两封内容相同、作者要求以后一封为准）**：用两簇×2 CPU、5 任务的 T0/T1/T2 场景走查 can_migrate_task() 的 LBF_ALL_PINNED 语义——该标志不代表「任务全部 pin 死」，只表示 src 任务无法迁往 dst CPU；构造出 newidle balance 先错误清掉 rd->overload、随后 newidle 提前返回的场景，反驳「清 overload 只是避免无谓周期」的论证。

## 版本演进与当前进展
*current_version: v1（RESEND 版，root `<20260910042950.1619727-1-jackzxcui1989@163.com>`；当日无新版本，作者以回帖响应）*。

## Maintainer 意见与讨论焦点
- **Xin Zhao（作者）**：首次给出可核查的生产数据与新的接口方向（SD_BALANCE_WAKE 切换）；对 Prateek 的反驳带完整代码走查；
- **Vincent / Prateek**：当日缓存内均无跟进——Vincent 的「改用 interactive 定位」建议与 Prateek 的反方案仍未闭环；
- 争议焦点：①SD_BALANCE_WAKE 动态加/撤域 flag 的可行性（无人评估）；②patch 1 的 overload 语义之争（双方各有一套场景论证，未收敛）。

## 合入评估
*likelihood=low*（不变）：作者的辩护质量显著提升，但 Vincent 对前提的否定仍未被正面化解，维护者无跟进。*blocking_issues*：SD_BALANCE_WAKE 方案无人评估；patch 1 数据仍缺（Prateek 索要的独立收益数字）；效果数据仍限作者单一嵌入式平台。*next_action*：等 Vincent/Prateek 对新论据的回应；若 SD_BALANCE_WAKE 方向被接受，等作者出正式 v2。

## 效果评估
新增一手数据为静态构成表（各 CPU RT/总任务数，如 CPU0 369/197、CPU1 293/132），用于论证「RT 无法扩容」，非 LB_PROMOTE 的收益数据。0.3% 平均开销与 ≥4ms 延迟消除的交换仍是作者主张（其早前测试平台承 sched-20260910-001），patch 1 的独立收益数字仍未提供。

## 我可以参与的点
- kind=review：评估「LB_PROMOTE 使能时切换 SD_BALANCE_WAKE、禁用时还原」的可行性——这是作者首次给出不需要新选核函数的替代接口形态，直接回应 Vincent 的核心反对理由，值得在 v2 前给出结论。
- kind=review：复核作者的 T0/T1/T2 反例与 Prateek 的 all_pinned 方案哪个对 rd->overload 语义的刻画正确（可直接读 sched_balance_find_src_group()/update_sd_lb_stats() 验证）。

## 参考链接
- 作者对 05/10 的回应（含 RT 占比表）：https://lore.kernel.org/all/20260912040804.3391229-1-jackzxcui1989@163.com/
- 作者对 04/10 的回应（0.3% 开销论证）：https://lore.kernel.org/all/20260912042804.3403506-1-jackzxcui1989@163.com/
- 作者对 01/10 的回应（T0/T1/T2 反例，以此封为准）：https://lore.kernel.org/all/20260912015324.3310241-1-jackzxcui1989@163.com/
- RESEND cover（09-10）：https://lore.kernel.org/all/20260910042950.1619727-1-jackzxcui1989@163.com/
