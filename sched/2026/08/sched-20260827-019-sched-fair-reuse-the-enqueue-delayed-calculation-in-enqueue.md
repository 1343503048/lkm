# sched/fair: reuse the ENQUEUE_DELAYED calculation in enqueue_task_fair()

## TL;DR
本文为增量更新（完整背景见 related_articles）。Kayra Cizmeci 的 enqueue 路径清理系列在 08-26 被 K Prateek Nayak（AMD）提了个 nit——引入局部 `bool delayed` 后可读性变差（"not delayed or delayed?"），建议要么改名 `wakeup_delayed` 要么直接沿用宏；08-27 作者反问：为什么不干脆改名后两处共用，若不认可则维持 `ENQUEUE_DELAYED`（两处判断逻辑本一致）。讨论停留在命名口味层面，无功能分歧。

## 背景与问题
该系列（v2 共 2 补丁）把 `enqueue_task_fair()` 内散落的 `flags & ENQUEUE_DELAYED` 检查收敛为函数开头一次计算的 `bool delayed`，并去掉 `place_entity()`/`requeue_delayed_entity()` 对 curr 状态的重复判断，声明 "No functional change intended"。背景细节见 sched-20260824-011 / sched-20260826-002。

## 技术方案
争点只有一个：局部布尔量的**命名**。Prateek 的观点是编译器最终会优化掉这层间接，代码读者对着一个大写的 `ENQUEUE_DELAYED` 更不容易误解（他特别嫌 `if (!p->se.sched_delayed || delayed)` 这种"取反 || 布尔"的读感），并顺带建议 `wakeup_delayed` 但自认没必要。作者的立场：若不做重命名，宁可保留宏原位使用，因为两处判断的语义相同。备选方向（改名并两处共用）已由作者在本日回帖中主动提出，等 Prateek 表态。

## 版本演进与当前进展
- 08-24：v1 首次出现（sched-20260824-011）。
- 08-26：v2（1/2 msgid `<0b1ef9d0122ae3037dac38d2549f13c9b063369a.1787737648.git.kayracizmeci@gmail.com>`）；Prateek 提 nit（`<3ae49b35-2188-4b29-af4a-6fff500098d3@amd.com>`）。
- 08-27：作者回帖反问（`<20260826184432.911321-1-kayracizmeci@gmail.com>`），当日无人再回复，等待裁决。

## Maintainer 意见与讨论焦点
Prateek 非调度核心维护者但以 AMD 侧 reviewer 身份活跃；意见属 reviewable nit、无 NAK。未决问题：局部变量名（`delayed` vs `wakeup_delayed` vs 保留宏）。维护者层面无人拍板。

## 合入评估
**possible**。纯可读性清理、无功能变化，此前已获部分 review 关注；卡点极小——按 Prateek 任一条建议落地即可 v3。此类 patch 常因"没人在意"而停滞而非因反对。

## 效果评估
无数据，也无需求证（声明无功能变化）。

## 我可以参与的点
当前阶段无实质参与空间；若在做 EEVDF delayed dequeue 相关回合，可顺带对 `enqueue_task_fair()` 的可读性改法表态——两行回帖就能推动 v3。

## 参考链接
- 作者本日回帖: https://lore.kernel.org/all/20260826184432.911321-1-kayracizmeci@gmail.com/
- Prateek 的 nit: https://lore.kernel.org/all/3ae49b35-2188-4b29-af4a-6fff500098d3@amd.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260827-019
date: '2026-08-27'
subject: "sched/fair: reuse the ENQUEUE_DELAYED calculation in enqueue_task_fair()"
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: "<0b1ef9d0122ae3037dac38d2549f13c9b063369a.1787737648.git.kayracizmeci@gmail.com>"
lore_url: "https://lore.kernel.org/all/20260826184432.911321-1-kayracizmeci@gmail.com/"
authors: [Kayra Cizmeci, K Prateek Nayak]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: "<0b1ef9d0122ae3037dac38d2549f13c9b063369a.1787737648.git.kayracizmeci@gmail.com>"
    date: 2026-08-26
    summary: "将 ENQUEUE_DELAYED 检查收敛为局部 bool 并去除重复计算"
    review_outcome: "Prateek nit 可读性/命名；作者 08-27 反问改名方案，讨论未闭环"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "命名 nit 未达成共识，无功能异议"
  next_action: "作者按任一审阅建议出 v3"
contribution_opportunities:
  - kind: discussion
    description: "对 delayed 局部变量命名表态，推动收敛"
generated_at: "2026-09-07T22:05:00"
source_email_count: 1
related_articles: [sched-20260824-011, sched-20260826-002]
tags: [cfs, eevdf]
---
