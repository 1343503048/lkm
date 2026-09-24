---
id: sched-20260911-017
subject: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
date: '2026-09-11'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <20260908082345.103087-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/66610fa3-982a-45f0-b39a-34f81598ad18@arm.com/
authors:
- Andrea Righi
maintainers_involved:
- Peter Zijlstra
- Dietmar Eggemann
- Vincent Guittot
current_version: v5
patch_series:
- version: v5
  msgid: <20260908082345.103087-1-arighi@nvidia.com>
  date: 2026-09-09
  summary: 删冗余 olympus_prefer_pe0 状态；调度器侧收口 select_idle_sibling() 之后；arm64 MIDR 检测。
  review_outcome: PeterZ 曾 tentative 收取，09-10 因 Will 拒绝 MIDR 检测而 drop；09-11 Dietmar
    在 THX2 实测无收益并质疑机理。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 收益的普适性被 Dietmar 的 THX2 数据质疑（驻留型负载无差异）
  - arm64 平台检测机制无替代提案
  - v6（sched_smt_active() 替换 static key）未发出
  next_action: 作者补拥挤/唤醒型负载的收益数据或收缩系列；与 arm64 维护者定检测机制后重发
contribution_opportunities:
- kind: testing
  description: 任务数>核数 + 高唤醒负载上复测，回应机理质疑
- kind: discussion
  description: 调研 ACPI/固件侧 CPU 优先级描述机制作为 MIDR 替代提案
generated_at: '2026-09-14T11:35:00'
source_email_count: 1
related_articles:
- sched-20260910-007
- sched-20260909-007
- sched-20260904-002
tags:
- arm64
- topology
- idle
- hyperthreading
title: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
layout: article
---

## TL;DR
Andrea Righi 让调度器在 NVIDIA Olympus（SMT 不对称）平台上偏向首选 SMT 兄弟的系列再获一条重量级反馈：Dietmar Eggemann 在 ThunderX2（arm64 SMT-4）上用 OpenBLAS SGEMM 实测 v5 与基线「看不出变化」，并从机理上质疑——任务数 ≤ 核数时 SMT 感知的 select_idle_sibling() 本就该一核一任务铺开，作者宣称的收益难以发生。系列承 sched-20260910-007：PeterZ 已撤下、Will Deacon 拒绝 MIDR 检测，本条反馈进一步压低合入预期。

## 背景与问题
Olympus 平台的 SMT 兄弟不等价，需要调度器在选核时偏向首选 sibling。系列已迭代到 v5（删冗余状态、收口到 select_idle_sibling() 之后的调度器侧 + arm64 侧 MIDR 检测），09-10 被 PeterZ 从收取队列撤下、等待 arm64 侧检测机制重做（详见 sched-20260910-007）。

## 技术方案
（承 sched-20260910-007 的 v5：调度器侧收口在 select_idle_sibling() 之后，arm64 侧 MIDR 检测；static key 按 Vincent 意见待改 sched_smt_active()。）当日无新代码，Dietmar 提供的是测试与机理质疑：
- 用 /proc/schedstat 确认 THX2 的 SMT 域 span，numactl 绑定 7 种 CPU 布局（8 核 32 线程、16 核、32 核、全 NUMA 节点、三组不同 32 核窗口）跑 OpenBLAS SGEMM（16384^3，OMP_NUM_THREADS=32）；
- 结论：v5 相对基线在无约束场景（d）868,285 vs 861,663 MFLOPS（差 ~0.8%，无一致性收益），布局 (a)-(g) 亦无系统性差异；
- 机理质疑：trace 显示 32 个基准任务 10 秒持续运行、无休眠唤醒——任务数 ≤ 核数时 select_idle_sibling() 已把任务一核一个铺开并驻留，「看不到你的收益如何发生」（作者的 88 核场景任务数同样不大于核数）。

## 版本演进与当前进展
*current_version: v5（v5 cover msgid `<20260908082345.103087-1-arighi@nvidia.com>`；当日缓存为 Dietmar 对该线程的回帖， subject 因回复旧邮件而显示 v4 0/2）*。

- v1-v4：承 sched-20260904-002/09-09-007（Olympus 平台引入偏好 + 多轮收口）；
- v5（09-09）：Prateek R-b/T-b、PeterZ tentative picked up；随后 Will Deacon 拒绝 MIDR 检测、Vincent 质疑 static key；
- 09-10：PeterZ 明确 drop 系列，等 arm64 侧方案重做（sched-20260910-007）；
- 09-11（本文窗口）：Dietmar 的 ThunderX2 实测与机理质疑。

## Maintainer 意见与讨论焦点
- **Dietmar Eggemann**：实测无收益 + 机理质疑（任务 ≤ 核数时既有 SIB 已铺开），同时肯定「有公开可用的基准可复现是好事」；
- **Peter Zijlstra**（承 09-10）：已 drop，等 arm64 方案；
- **Will Deacon**（承 09-10）：拒绝 MIDR 检测，替代机制无人提案；
- 分歧焦点扩大：不只检测机制未定，收益本身的普适性也开始被质疑——Olympus 之外的 SMT 不对称平台（THX2）上收益不可见。

## 合入评估
*likelihood=low*（维持并强化 sched-20260910-007 的 low）：PeterZ 已撤下、arm64 检测机制无提案，新增的独立平台数据表明收益不显著。*blocking_issues*：收益需要在「任务数 > 核数、唤醒频繁」的真实场景重新论证（Dietmar 的质疑点）；MIDR 替代机制仍无方案；v6（sched_smt_active() 替换 static key）未发出。*next_action*：作者要么给出门控更精确的收益场景与数据（拥挤/唤醒型负载），要么收缩系列范围；与 arm64 维护者商定检测机制后重发。

## 效果评估
Dietmar 的数据（唯一新增）：ThunderX2 SGEMM 七种布局下 v5/v1/基线 MFLOPS 差异均在噪声量级（如全节点场景 868,285 vs 861,663 vs 861,663 上下）。作者此前宣称的 Olympus 收益（88 核场景）在本次缓存窗口内没有出现新的第三方复现。

## 我可以参与的点
- kind=testing：在「任务数 > 核数 + 高唤醒」的负载（如 sysbench/nginx 类）而非 SGEMM 这种驻留型负载上复测，正面回应 Dietmar 的机理质疑——这是当前对系列存亡最关键的数据缺口。
- kind=discussion：跟进 arm64 侧平台检测机制的提案（ACPI/固件描述 CPU 优先级的既有接口调研，承 sched-20260910-007 的参与点，仍无人认领）。

## 参考链接
- Dietmar 的实测回帖：https://lore.kernel.org/all/66610fa3-982a-45f0-b39a-34f81598ad18@arm.com/
- v5 cover：https://lore.kernel.org/all/20260908082345.103087-1-arighi@nvidia.com/
- v2 2/2（asymmetric SMT 系列相关线程）：https://lore.kernel.org/all/20260909062649.469633-3-arighi@nvidia.com/
