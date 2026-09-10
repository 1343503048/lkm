# sched: Enable preferred SMT siblings on NVIDIA Olympus

## TL;DR
本文为增量更新，完整背景见 related_articles 中的 sched-20260909-007 / sched-20260904-002。v5 在 09-09 收获 Prateek 的 Reviewed-by+Tested-by、Peter 的 tentatively picked up，但 Will Deacon 拒绝 arm64 MIDR 拓扑检测方案；09-10 Peter 直接表态把该系列从收取队列里撤下（"I'll drop this, no worries"），并点出 Andrea 重发过快。系列合入路径回到「先解决 arm64 侧反对」的原点。

## 背景与问题
NVIDIA Olympus（Grace 类 arm64 平台）的 SMT 兄弟核存在非对称优先级（PE0/PE1），希望调度器在 idle 选核时优先选择高优先级 sibling，避免任务落在性能较差的兄弟核上。方案演进多版后（v5：仅删除冗余的 olympus_prefer_pe0 状态），sched 侧改动已获认可，争议集中在 arm64 侧如何检测「该平台需要此行为」。

## 技术方案
本日无新代码。当前 v5 形态见 sched-20260909-007：调度器侧把 SMT 优先级调整收口在 select_idle_sibling() 选出 idle 候选之后（select_idle_smt_cpu()），arm64 侧以 MIDR 检测启用，diffstat 6 files changed, 163 insertions(+), 17 deletions(-)。未决的设计问题有两个：其一，Will Deacon 认为基于 MIDR 的拓扑检测不可接受（arm64 维护者反对，09-09 提出）；其二，Vincent Guittot 质疑新增 static key——Andrea 已在旧线程承诺去掉 static key、改用 sched_smt_active()（见同日文章 sched-20260910-008）。

## 版本演进与当前进展
current_version: v5（2026-09-09 发出，msgid `<20260909062649.469633-1-arighi@nvidia.com>`）。09-09：Prateek Reviewed-by+Tested-by（4th gen EPYC 与 128C Ampere ARM 服务器无性能影响）；Peter tentatively picked up 但要求 arm64 ack；Will Deacon 拒绝 MIDR 检测；Vincent 质疑 static key。09-10：Peter 在 Will 的邮件下回复 "Yeah, Andrea is a wee bit fast with re-posting. I'll drop this, no worries."——正式撤下收取，等待 arm64 侧方案重做后的新版本。

## Maintainer 意见与讨论焦点
- Peter Zijlstra（09-10）：撤下收取。语气无否定技术方向之意（"no worries"），更多是流程信号：在 arm64 维护者明确反对的情况下不该急于重发。
- Will Deacon（09-09，本日线程的父邮件作者，原文未进入缓存）：MIDR 检测拓扑不可接受——这是当前最硬的 blocking 意见，替代检测机制（如固件/ACPI 描述、cpufeature cap）尚无人给出。
- Vincent Guittot（09-09 质疑 static key）：Andrea 已在平行线程让步（改用 sched_smt_active()）。
- 焦点：arm64 侧「如何识别需要 SMT 优先级偏好的平台」没有双方都能接受的机制。

## 合入评估
likelihood: low（从 09-09 的 tentatively picked up 倒退：Peter 已撤下，arm64 维护者反对未解决）。blocking_issues：MIDR 检测被 Will Deacon 拒绝且无替代方案；static key 需按 Andrea 承诺改为 sched_smt_active()；需要 arm64 维护者可接受的拓扑/平台描述机制后才可能有 v6。next_action：Andrea 与 Will/arm64 侧商定平台检测机制，去掉 static key 后发 v6，再请 Peter 重新收取。

## 效果评估
本日无新数据。既有数据为 Prateek 在 v5 的 Tested-by：4th gen EPYC 与 128C Ampere ARM 服务器上无性能影响（具体数字未展开，未获取到）；Olympus 平台上的收益数据在更早版本邮件中（见 related_articles）。

## 我可以参与的点
- 关注并参与 arm64 平台检测机制的讨论：如果有基于 ACPI/firmware 描述 CPU 优先级的先例（如 CPPC highest/lowest perf 或 CLCC 类接口），可以整理成提案回到线程，这是当前唯一卡点（discussion）。
- 在非 Olympus 的 SMT 不对称平台（如 Intel ITMT 机器）测试 v6 候选方案的通用性，帮助论证检测机制不应绑死 MIDR（testing）。

## 参考链接
- lore thread（v5 封面）: https://lore.kernel.org/all/20260909062649.469633-1-arighi@nvidia.com/
- Peter 撤下收取的回复: https://lore.kernel.org/all/20260909215117.GO776954@noisy.programming.kicks-ass.net/
- 父邮件（Will Deacon，未进入缓存）: https://lore.kernel.org/all/aqF84So9WUQCDgsz@willie-the-truck/
- static key 让步（平行线程）: https://lore.kernel.org/all/aqGHtIo2Bk2irSdu@gpd4/

---
id: sched-20260910-007
date: 2026-09-10
subject: "sched: Enable preferred SMT siblings on NVIDIA Olympus"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260909062649.469633-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20260909062649.469633-1-arighi@nvidia.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v5
generated_at: "2026-09-11T10:25:00"
authors:
  - "Andrea Righi"
maintainers_involved:
  - "Peter Zijlstra"
patch_series:
  - version: v5
    msgid: "<20260909062649.469633-1-arighi@nvidia.com>"
    date: "2026-09-09"
    summary: "仅删除冗余的 olympus_prefer_pe0 状态；调度器侧收口在 select_idle_sibling() 之后，arm64 侧 MIDR 检测。"
    review_outcome: "09-09 Prateek Reviewed-by+Tested-by、Peter tentatively picked up、Will Deacon 拒绝 MIDR 检测、Vincent 质疑 static key；09-10 Peter 回复 Will 时明确 drop 该系列，等 arm64 侧方案重做。"
merge_assessment:
  likelihood: low
  blocking_issues:
    - "Will Deacon 拒绝基于 MIDR 的拓扑检测，替代机制尚无提案"
    - "Peter Zijlstra 已把系列从收取队列撤下"
    - "Vincent 质疑的 static key 需按作者承诺改为 sched_smt_active() 并落入新版本"
  next_action: "与 arm64 维护者商定平台检测机制、去掉 static key 后发 v6，再请 Peter 重新收取"
contribution_opportunities:
  - kind: discussion
    description: "整理 ACPI/固件侧描述 CPU 优先级的既有机制（如 CPPC 类接口）作为 MIDR 替代提案回到线程——当前唯一卡点且无人给出方案"
  - kind: testing
    description: "在非 Olympus 的 SMT 不对称平台（如 Intel ITMT 机器）验证候选检测机制的通用性"
source_email_count: 1
related_articles:
  - "sched-20260909-007"
  - "sched-20260904-002"
tags:
  - arm64
  - topology
  - idle
  - hyperthreading
---
