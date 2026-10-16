# x86, sched, mm: Speed up CPU hotplug on large systems

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261015-002：Pasha Tatashin 发 v1 八补丁系列（x86+sched+mm）加速大规模 x86 服务器顺序热插拔，调度侧为 5/8（sgc 缓存+惰性分配）与 6/8（dl_server O(N^2)→O(N) 记账）；480 核 Intel 热插拔总耗时 106.23s→5.07s（21x）。
- sched-20261016-014（今天）：首批 review 到来——Tony Luck 实测离线 4.833s→3.17s、在线 6.157s→3.796s（36 核 Icelake），并提示反向离线可再省；Prateek 对 5/8 提出 `find_group_balance_cpu()` 的重构建议；Tim Chen 指出 7/8 的 free 不受 `sched_domains_mutex` 保护、要求补 `lockdep_assert_cpus_held()` 与惰性分配不变量注释。

## 背景与问题
（承接 20261015-002）live update 要求快速 CPU online/offline；系列消除大规模 x86 服务器顺序热插拔在 arch/x86、调度拓扑构建器、deadline 带宽记账、vmstat 四层的瓶颈。今天开始有独立验证与代码 review。

## 技术方案
（承接 20261015-002）无新补丁。今天为 review 反馈：
- Tony Luck 实测确认方向（含一个「从高到低 CPU 号 offline 可避免产生孤儿 CMCI bank」的优化提示）。
- Prateek 建议把 5/8 里「insanely specific」的 `group_balance_cpu()` 查找抽象成独立 `find_group_balance_cpu()` 辅助函数。
- Tim Chen 针对 7/8 指出 `sched_domains_mutex` 不保护 free（`sched_update_numa()` 在 hotplug 写锁下运行，free 安全靠 cpus_read_lock 兜底），要求修 changelog、在 `__sdt_free_percpu()` 加 `lockdep_assert_cpus_held()`，并把「build 开始时每个 cpu_map 槽位必须为 NULL」的惰性分配不变量写下来加检查。

## 版本演进与当前进展
v1（2026-10-15）→ 今天首批三方 review（Tony Luck 实测 + Prateek/Tim Chen 代码意见），方向被认可，但 5/8、7/8 有具体改动要求。

## Maintainer 意见与讨论焦点
Tony Luck（Intel，x86 资深）实测速度提升明显、方向认可；Prateek（AMD）与 Tim Chen（Intel）分别给出拓扑重构与锁/不变量文档的具体意见。暂无 Peter/Juri/Vincent 等正式 sched 维护者表态。

## 合入评估
*likelihood=medium*。有独立验证与建设性 review、方向正面，但仍无正式维护者 ACK，且 5/8/7/8 需按意见调整。*blocking_issues*：5/8 需重构抽象；7/8 需补锁断言与不变量文档；跨 x86/sched/mm 需多方确认。*next_action*：作者按 Tony/Prateek/Tim 意见出 v2。

## 效果评估
Tony Luck 的独立实测（2-socket 36 核 Icelake，offline/online 72 逻辑 CPU）：
- offline：4.833s → 3.17s；
- online：6.157s → 3.796s；
- 反向（高→低 CPU 号）offline：2.984s。

## 我可以参与的点
- *review*：审视 Tim Chen 指出的 7/8 free 锁保护与惰性分配不变量，确认 `__sdt_free_percpu()` 加 `lockdep_assert_cpus_held()` 后所有调用点都满足。
- *testing*：在 arm64/riscv 或 CONFIG_CPUSETS=n 配置下验证 6/8 dl 记账与 5/8 惰性分配无回归。

## 参考链接
- 系列 cover：https://lore.kernel.org/all/20261015153331.1872641-1-pasha.tatashin@soleen.com/
- Tony Luck 实测：https://lore.kernel.org/all/atFGxagFo50iG6IS@agluck-desk3/
- Tim Chen 对 7/8：https://lore.kernel.org/all/1ec1aab8eabdad173ddef7483a940bfa3f6c3238.camel@linux.intel.com/
- Prateek 对 5/8：https://lore.kernel.org/all/b618f528-ba35-4fb3-881b-e0ca12bc9558@amd.com/

---
id: sched-20261016-014
date: 2026-10-16
subject: "x86, sched, mm: Speed up CPU hotplug on large systems"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261015153331.1872641-1-pasha.tatashin@soleen.com>"
lore_url: "https://lore.kernel.org/all/20261015153331.1872641-1-pasha.tatashin@soleen.com/"
authors: ["Pasha Tatashin"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261015153331.1872641-1-pasha.tatashin@soleen.com>"
    date: 2026-10-15
    summary: "8 补丁加速 x86 热插拔；调度侧 5/8（sgc 缓存+惰性分配）与 6/8（dl_server O(N^2)→O(N)）"
    review_outcome: "Tony Luck 实测认可；Prateek/Tim Chen 对 5/8、7/8 提具体修改意见"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["5/8 需重构抽象；7/8 需锁断言与不变量文档；跨子系统需多方确认"]
  next_action: "作者按 Tony/Prateek/Tim 意见出 v2"
contribution_opportunities:
  - kind: review
    description: "确认 7/8 __sdt_free_percpu() 加 lockdep_assert_cpus_held() 后调用点满足"
  - kind: testing
    description: "arm64/riscv 或 CONFIG_CPUSETS=n 下验证 6/8 dl 记账与 5/8 惰性分配无回归"
generated_at: "2026-10-17T01:30:00"
source_email_count: 3
related_articles: ["sched-20261015-002"]
tags: [topology, dl_server, deadline]
---