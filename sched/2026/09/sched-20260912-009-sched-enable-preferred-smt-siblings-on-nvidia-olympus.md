# sched: Enable preferred SMT siblings on NVIDIA Olympus

## TL;DR
Andrea Righi 当日对 Dietmar 的 ThunderX2 无收益实测给出长篇机理回应：PE0 更可能处理中断等 per-CPU 杂务，Olympus 有「PE0 需持续 WFI 10K 周期才回到全资源单线程模式」的迟滞设计，因此 ThunderX2（无该延迟模式切换）的驻留型负载确实无法复现收益；并提出在 THX2 上只验证放置行为而非性能的具体方案。系列仍处于被 drop 状态，但收益机理首次得到完整阐述。本文为增量更新，测试争议见 sched-20260911-017。

## 背景与问题
（承 sched-20260911-017）系列让调度器在 SMT 不对称平台偏向首选 sibling；Dietmar 在 ThunderX2 SMT-4 上 SGEMM 七种布局实测 v5 与基线无差异，并质疑「任务数 ≤ 核数时 SIB 已一核一任务铺开，收益难以发生」。

## 技术方案
Andrea 的回应揭示了两点此前未在邮件列表写清的硬件/平台差异：

1. 中断归属：PE0（首选 sibling）更可能处理中断与 per-CPU 杂务。ThunderX2 上把基准线程强放 PE0 反而可能增加直接抢占；而 Olympus 上负载驻留 PE0 时，PE0 上的中断只会短暂抢占负载、不会激活 PE1——负载在 PE1 时同样中断会激活两个 PE、把核心切进双线程模式（资源静态切分）；
2. 迟滞阈值：回到全资源单线程模式要求 PE0 连续 WFI 10K 周期——该阈值防止反复排空/重构核心内部结构，零星中断即可重启资格计时，让核心停留在双线程模式远超中断本身；
3. 承认边界：稳态（每核一个持续 runnable 任务、无迁移无唤醒）下调度器改动确实没什么可改进的，且 ThunderX2 没有 Olympus 的延迟模式切换，不期待复现吞吐提升；
4. 提出替代验证：在 THX2（32 个 SMT4 核、4 级 sibling 优先级）上验证**放置行为**而非性能——32 任务应先占满全部 PE0，64 任务占 PE0+PE1，再随 runnable 数向 PE2/PE3 扩展。

## 版本演进与当前进展
current_version: v5（v5 cover msgid `<20260908082345.103087-1-arighi@nvidia.com>`；当日缓存为 Andrea 在 v4 0/2 主题下的回帖一封）。

- v5（09-09）→ Will 拒 MIDR、PeterZ drop（09-10）→ Dietmar THX2 实测无收益（09-11）→ 09-12 Andrea 的机理回应与替代验证方案。无新代码。

## Maintainer 意见与讨论焦点
- **Andrea Righi**：承认 Dietmar 场景的结论（稳态无收益空间），但给出 Olympus 独有的中断/迟滞机理解释——收益定位从「普适吞吐提升」收窄到「Olympus 类有延迟模式切换的平台」；
- **Dietmar Eggemann**（承 09-11）：实测数据仍站在「收益不显著」一侧，尚未对机理回应表态；
- 分歧焦点转移：从「有没有收益」转为「收益该在什么平台上、用什么方式验证」——放置行为验证方案是当前唯一的建设性出口，无人接手。

## 合入评估
likelihood=low（不变）：PeterZ 已 drop、arm64 检测机制仍无替代提案；机理回应提升了论证质量但未改变系列状态。blocking_issues：与 09-11 相同（检测机制无方案、v6 未发、static key 待换）；新增——放置行为验证需要有人执行并回帖。next_action：Dietmar（或第三方）在 THX2 上跑放置行为验证；作者侧与 arm64 维护者解决检测机制后重发。

## 效果评估
无新性能数据。Andrea 的回应本身给出可验证的预测（THX2 上 32/64/128 任务的 PE 分层放置模式）——这比吞吐数字更容易第三方复现，是该线程当前最有价值的可检验陈述。

## 我可以参与的点
- kind=testing：在 THX2（或任何多级 sibling 优先级的 SMT 平台）按 Andrea 给出的模式跑 32/64/128 任务放置验证并回帖——直接检验机理回应的核心预测，且比 SGEMM 更贴近系列的意图。
- kind=discussion：跟进 arm64 检测机制的替代提案（承 sched-20260910-007，仍无人认领）。

## 参考链接
- Andrea 的机理回应：https://lore.kernel.org/all/aqSEB2N_NQbBVab6@gpd4/
- Dietmar 的 THX2 实测（09-11）：https://lore.kernel.org/all/66610fa3-982a-45f0-b39a-34f81598ad18@arm.com/
- v5 cover：https://lore.kernel.org/all/20260908082345.103087-1-arighi@nvidia.com/

---
id: sched-20260912-009
subject: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
date: '2026-09-12'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: '<20260908082345.103087-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/aqSEB2N_NQbBVab6@gpd4/'
authors:
  - 'Andrea Righi'
maintainers_involved:
  - 'Peter Zijlstra'
  - 'Dietmar Eggemann'
current_version: v5
patch_series:
  - version: v5
    msgid: '<20260908082345.103087-1-arighi@nvidia.com>'
    date: 2026-09-09
    summary: 'Olympus 首选 SMT sibling 支持（收口 select_idle_sibling() 之后 + arm64 MIDR 检测）。'
    review_outcome: '09-12 Andrea 详述 PE0 中断归属与 10K 周期 WFI 迟滞机理，承认 THX2 稳态负载无收益空间，提出 THX2 放置行为验证方案（32/64/128 任务的 PE 分层预测）。'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - 'PeterZ 已 drop，arm64 检测机制无替代提案'
    - '放置行为验证无人执行'
  next_action: 'THX2 放置行为验证回帖后与 arm64 维护者定检测机制，再谈重发'
contribution_opportunities:
  - kind: testing
    description: 'THX2 等平台按 32/64/128 任务模式验证 PE 分层放置'
  - kind: discussion
    description: '跟进 arm64 平台检测机制替代提案'
generated_at: '2026-09-14T12:40:00'
source_email_count: 1
related_articles:
  - 'sched-20260911-017'
  - 'sched-20260910-007'
tags:
  - arm64
  - topology
  - idle
  - hyperthreading
---
