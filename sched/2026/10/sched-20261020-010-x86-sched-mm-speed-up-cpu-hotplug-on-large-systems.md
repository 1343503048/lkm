# x86, sched, mm: Speed up CPU hotplug on large systems

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261015-002：Pasha Tatashin 发 v1 八补丁系列（x86+sched+mm）加速大规模 x86 服务器顺序热插拔，调度侧为 5/8（sgc 缓存 + 惰性分配）与 6/8（dl_server O(N^2)→O(N) 记账）；480 核 Intel 总耗时 106.23s→5.07s（21x）。
- sched-20261016-014：Tony Luck 实测离线 4.833s→3.17s、在线 6.157s→3.796s；Prateek 对 5/8 提 `find_group_balance_cpu()` 重构；Tim Chen 指出 7/8 的 free 不受 `sched_domains_mutex` 保护。
- sched-20261018-010：作者逐条回应并确认折入各方意见。
- sched-20261019-004：Pasha 发 v2（8 补丁）折入各方意见；Borislav Petkov 提醒 merge window 已开、要求「stop the spamming please」。
- sched-20261020-010（今天）：Tony Luck 提了一个侧问——Intel 验证团队在大系统上「循环离线/上电所有 CPU」时会因「smart I/O 设备支持的中断向量太多、缩到单 CPU 放不下」而离线失败；Pasha 回复未在基准采集中遇到该问题，并说明其 Live Update 当前留 8 个 host CPU。

## 背景与问题

（承接 20261015-002 → 016-014 → 018-010 → 019-004）live update 要求快速 CPU online/offline；系列消除大规模 x86 服务器顺序热插拔在 arch/x86、调度拓扑构建器、deadline 带宽记账、vmstat 四层的瓶颈。v2 已发出、处于 merge window 等待期。今天的讨论是一条并行侧问，与本系列加速目标相关但不阻塞：CPU 全部下线时中断向量的容纳问题。

## 技术方案

（承接，今日无补丁改动）Tony Luck 的侧问：Intel 验证团队有一个「循环把全部 CPU 下线再上电」的测试，从 Sapphire Rapids 起会卡在「只剩 CPU0/CPU1 时无法让 CPU1 下线」——因为 smart I/O 设备支持的中断向量太多，塞不进单个 CPU 的可用向量。Pasha 回复：自己在采集 benchmark 数据时未遇到该问题；其 Live Update 方案当前在 host 上留 8 个 CPU 执行 kexec、其余 AP CPU 从调度器移除，未来计划只留 1 个 host CPU、其余 CPU 以 Caretaker 模式管理 VM。

## 版本演进与当前进展

*current_version: v2*（无新版本）。今日为侧问交流，无补丁改动。

## Maintainer 意见与讨论焦点

今日无维护者回帖。Tony Luck（Intel，非维护者）抛出中断向量容纳的侧问，Pasha 正面回应。此前 x86 维护者 Borislav Petkov 的「merge window 等待」要求仍然有效。

## 合入评估

*likelihood=unknown*。方向有实质三方验证与数据，但处于 merge window、sched 侧补丁 5-7/8 无正式 review。*blocking_issues*：merge window 期间暂停、sched 侧补丁无正式 review。*next_action*：作者等待 merge window 结束，推进调度维护者对 5-7/8 的 review；Tony 的 interrupt-vector 话题作为背景记录。

## 效果评估

今日无新增 benchmark。此前（20261019-004）作者给出 10 次均值：Intel 480 核 total 106.23→5.07s（-95.2%，21x）、AMD 512 核 8.41→3.38s（-59.8%，2.5x）。今日为中断向量可行性讨论，无量化数据。

## 我可以参与的点

- `testing`：在其它大核数平台（arm64、多 socket/CCD 拓扑）复测离线/在线耗时，验证 5-7/8 的拓扑/带宽优化无跨架构回退。
- `discussion`：Tony 提出的「smart I/O 多向量设备在 CPU 缩到单核时中断向量溢出」是独立于本系列的边界问题，可结合中断子系统现状评估是否需要在极小数 CPU 场景下处理。

## 参考链接

- Tony Luck 侧问：https://lore.kernel.org/all/SJ1PR11MB608365E406C4DA7CB91858A4FC982@SJ1PR11MB6083.namprd11.prod.outlook.com/
- Pasha 回复：https://lore.kernel.org/all/CA+CK2bAQr=Ak1u-Aiwbw=DZ22Nk8oRDqnC2AnRaez7nOyJj0-w@mail.gmail.com/
- v2 封面信：https://lore.kernel.org/all/20261019011446.834487-1-pasha.tatashin@soleen.com/

---
id: sched-20261020-010
date: 2026-10-20
subject: "x86, sched, mm: Speed up CPU hotplug on large systems"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261019011446.834487-1-pasha.tatashin@soleen.com>"
lore_url: "https://lore.kernel.org/all/20261019011446.834487-1-pasha.tatashin@soleen.com/"
authors: ["Pasha Tatashin"]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261015153331.1872641-1-pasha.tatashin@soleen.com>"
    date: 2026-10-15
    summary: "八补丁 v1：x86 WBINVD/CMCI/MTRR + sched 拓扑 O(N^3)/dl_server O(N^2) + vmstat"
    review_outcome: "Tony Luck 实测认可；Prateek/Tim Chen 给 5/8、7/8 改动意见"
  - version: v2
    msgid: "<20261019011446.834487-1-pasha.tatashin@soleen.com>"
    date: 2026-10-19
    summary: "折入各方意见，8 补丁重发并附逐项 benchmark"
    review_outcome: "Borislav 指 merge window 期间应等待；今日 Tony Luck 侧问中断向量问题"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["merge window 期间维护者要求等待", "sched 侧补丁 5-7/8 无正式 review"]
  next_action: "作者等待 merge window 结束，推进调度维护者对 5-7/8 的 review"
contribution_opportunities:
  - kind: testing
    description: "在 arm64/多 socket 拓扑复测离线/在线耗时，验证 5-7/8 无跨架构回退"
  - kind: discussion
    description: "评估极少数 CPU 场景下 smart I/O 多向量设备的中断向量容纳问题"
generated_at: "2026-10-21T01:30:00"
source_email_count: 2
related_articles: ["sched-20261015-002", "sched-20261016-014", "sched-20261018-010", "sched-20261019-004"]
tags: [topology, deadline, load_balance]
---