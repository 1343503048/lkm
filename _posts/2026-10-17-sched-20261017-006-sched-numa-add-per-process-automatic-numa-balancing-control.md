---
id: sched-20261017-006
subject: 'sched/numa: Add per-process automatic NUMA balancing control'
date: 2026-10-17
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260908122446.56708-1-lizhe.67@bytedance.com>
lore_url: https://lore.kernel.org/all/20260908122446.56708-1-lizhe.67@bytedance.com/
authors:
- Li Zhe
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260908122446.56708-1-lizhe.67@bytedance.com>
  date: 2026-09-08
  summary: prctl 级 per-process NUMA balancing 开关（PR_SET/GET_NUMA_BALANCING）
  review_outcome: 接口形态经多轮讨论，今日向复用 prctl 系列 per-cgroup 方案收敛，Yafang 认可
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无顶层维护者表态；原系列与 cache-aware 系列、BPF RFC 的合并方式未定
  next_action: 发布复用 prctl 系列的 per-cgroup 版本；作者回应是否并轨到 cache-aware 系列
contribution_opportunities:
- kind: discussion
  description: 对 Step 1 per-cgroup 设置与 per-group tolerance 是否同期设计给出意见
- kind: review
  description: 审视 per-cgroup 版本 fork/exec/migration 四处 hook 与显式分组优先语义的自洽性
generated_at: '2026-10-18T01:20:00'
source_email_count: 2
related_articles:
- sched-20260908-007
- sched-20261013-004
- sched-20261014-012
- sched-20261016-015
tags:
- numa_balancing
- cfs
title: 'sched/numa: Add per-process automatic NUMA balancing control'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/08/sched-20260908-007-sched-numa-add-per-process-automatic-numa-balancing-control.html">sched-20260908-007</a>：Li Zhe（ByteDance）发 4 补丁（v1），给自动 NUMA 平衡加 prctl 级 per-process 开关（`PR_SET/GET_NUMA_BALANCING`），让个别进程整体退出 NUMA 扫描与 locality 统计，`kernel.numa_balancing` 保留为管理员硬总闸；当日零 review。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-004-sched-numa-add-per-process-automatic-numa-balancing-control.html">sched-20261013-004</a>：Chen Yu 建议把全局开关做成三元（always/advise/never），Yafang Shao 主张从开始就做成 BPF-cgroup 式可扩展语义；方向（prctl vs cgroup/BPF vs 三元键）未收敛。
- <a class="article-ref" href="/lkm/2026/10/14/sched-20261014-012-sched-numa-add-per-process-automatic-numa-balancing-control.html">sched-20261014-012</a>：作者 Li Zhe 回应「三元键可行」、per-cgroup 也可接受，愿在维护者偏向 per-cgroup 时帮 review Yafang 系列；立场向 per-cgroup 松动。
- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-015-sched-numa-add-per-process-automatic-numa-balancing-control.html">sched-20261016-015</a>：接口形态之争展开——Tim Chen 质疑 per-cgroup 继承与跨 cgroup 聚合；Yafang 主张 cgroup::numab_mode + BPF、反对 prctl；Chen Yu 用 threaded cgroup 场景论证互补并追问实现细节。
- <a class="article-ref" href="/lkm/2026/10/17/sched-20261017-006-sched-numa-add-per-process-automatic-numa-balancing-control.html">sched-20261017-006</a>（今天）：讨论收敛——Tim Chen 用腾讯 threaded cgroup 实测用例说明「数据共享分组 ≠ 资源分组」的需求，并给出「复用 prctl 系列基础设施、按三步演化」的 cgroup 接口方案；Yafang Shao 明确「It works for me」，放弃自己更简单的 cgroup-field-only 想法，请 Tim 发帖时 Cc 他。

## 背景与问题
（承接 20260908-007 → 20261016-015）核心用例仍是一个 launcher 让多数进程用默认策略、少数进程自己管 NUMA 放置或吃不起采样开销。今日讨论把它从「per-process NUMA balancing」的接口争辩，推进到与**cache-aware/LLC-aware 调度**共享同一套基础设施的更宽问题：Tim Chen 指出腾讯存在「A1/B1 做数据压缩、A2/B2 做数据库」的 threaded cgroup 部署，数据主要按功能在 A1↔B1、A2↔B2 间共享——资源分组（cgroup 层级）与数据共享分组（cache group）并不一致，需要另一种分组维度。

## 技术方案
（承接 20261016-015）今日无新补丁，Tim Chen 提出一套「BPF 式 cgroup 接口三步演化」方案，核心原则是「调度器只认 per-task 的 `p->sched_cache_grp`，每个接口只是设置它的又一种方式，调度器侧永不改动」：
1. **Step 1（per-cgroup 设置）**：`struct cgroup` 增加 `sched_cache_grp` 指针与模式（inherit/off/整棵子树一个 group）；一个 kfunc 按 cgroup id 设模式（暂无 cgroupfs 文件）；内核在模式设置、fork（`sched_post_fork`）、exec（`exec_mmap`）、迁移（`cgroup_migrate_execute`）四处把任务放进该 group；显式分组过的任务不被 cgroup 覆盖。Step 1 复用 prctl 系列的大部分代码（refcounted `sched_cache_group`、`__sched_cache_set()`、footprint 迁移、fork/exec 处理、per-group enabled 标志、always/advise/never 模式），仅 prctl UAPI 不需要。
2. **Step 2（BPF 选 group）**：加创建/读/设/重置 group 的 kfunc，允许两个 cgroup（如 A1、B1）共享一个 group。
3. **Step 3（BPF 按任务决策）**：仅在需要时，在 fork/exec/cgroup-attach 钩子上直接给任务设 group。
Tim 并澄清 prctl 不必改应用：orchestrator daemon 可对别的任务发 `prctl(PR_SCHED_CACHE, ...)`（权限检查 `ptrace_may_access()`，同 core scheduling）。Yafang Shao 回应这套方案「It works for me」，并说明自己原来的「cgroup-field-only、lookup 时从 cgroup 派生」更简单想法站不住（prctl 显式分组要优先、footprint 估计要在成员变更时跨 group 转移），既然大部分基础设施复用 prctl 系列，他同意按 Tim 的方式实现。

## 版本演进与当前进展
v1（2026-09-08）→ 接口形态辩论 → 今天（2026-10-17）向「复用 prctl 系列基础设施 + Step 1 per-cgroup 设置」收敛，Yafang 明确认可。尚无 v2 补丁，也无顶层维护者（Peter/Ingo）表态。

## Maintainer 意见与讨论焦点
- Tim Chen（Intel，cache-aware 调度提案作者）：给出腾讯实测用例与三步方案，主张「per-cgroup 设置与 prctl 并存」。
- Yafang Shao（ByteDance，原 cgroup/BPF 主张）：从「反对 prctl」转向「It works for me」，放弃更简方案，达成实质共识。
- Chen Yu（Intel，sched/numa 维护者，前一日）：曾追问 threaded cgroup 跨 mm 共享的语义。
- 尚未表态：Peter Zijlstra / Ingo Molnar 等顶层维护者。核心开放问题从「选哪个接口」转为「Step 1 方案是否被接受、per-group tolerance 是否需要在 Step 1 一并设计」。

## 合入评估
*likelihood=medium*。辩论已收敛到具体技术路线（复用 prctl 系列 + per-cgroup Step 1），但尚未出现顶层维护者表态、也无 v2 补丁，且这套方案实际脱离了原「per-process NUMA balancing」补丁、转向 cache-aware 调度的更大棋局。*blocking_issues*：无顶层维护者表态；原系列与 cache-aware 系列、Yafang 的 BPF RFC 三个线头的合并方式未定。*next_action*：由拥有者（Tim/作者）发布复用 prctl 系列的 per-cgroup 版本；作者回应是否并轨到 cache-aware 系列。

## 效果评估
无量化数据；讨论为接口设计与用例辩论，无 benchmark 数字。

## 我可以参与的点
- *discussion*：对 Tim 的 Step 1「per-cgroup 设置」与「per-group tolerance（区别于全局 llc_aggr_tolerance）」是否应同时设计给出意见；这是今日仍未拍板的开放点。
- *review*：在 Tim 发布复用 prctl 系列的 per-cgroup 版本后，审视 fork/exec/migration 四处 hook 与「显式分组不被 cgroup 覆盖」的语义是否自洽。

## 参考链接
- 系列 cover lore：https://lore.kernel.org/all/20260908122446.56708-1-lizhe.67@bytedance.com/
- Tim Chen 今日回帖（三步方案）：https://lore.kernel.org/all/8d1997019d00fad3f250c4df3f18c53dff25e054.camel@linux.intel.com/
- Yafang Shao 今日回应（It works for me）：https://lore.kernel.org/all/CALOAHbDGx-2MfHiUs2S5cWT9yWiKp_22kg-OFL4gtuGG4aCUAw@mail.gmail.com/
- Tim 的 cache-aware prctl 系列：https://lore.kernel.org/lkml/cover.1787955777.git.tim.c.chen@linux.intel.com/
