# sched/topology: Retry scheduler domains after failed construction

## TL;DR
Avi Weiss 的单补丁修 `partition_sched_domains_locked()` 的一个缺陷：`build_sched_domains()` 失败后，请求的分区仍被记录，于是下一次**相同的**重建会直接复用这个失败分区，导致其 CPU 在瞬时的 `alloc_rootdomain()` 失败后一直挂在默认根域上。修法：复用/摘除分区前先确认根域已安装（`+13/-3`），让下次重建能重试失败的分区。已在 4-vCPU QEMU 用 `alloc_rootdomain()` 故障注入复现验证。`Fixes: 029190c515f1`。

## 背景与问题
cpuset 的 `sched_load_balance` 标志触发的调度域划分（`partition_sched_domains_locked()`）里，旧实现把「请求的分区」记录下来后，即使 `build_sched_domains()` 失败也会在下次重建时命中 `match1` 复用该分区、跳过重建。当 `alloc_rootdomain()` 瞬时失败（如内存压力）时，这些 CPU 就一直滞留在 `def_root_domain`（默认根域），即便后续重建请求相同分区也不再尝试修复。

## 技术方案
新增 `sched_domain_installed(cpu_map)` helper——若 `cpu_map` 非空且其首 CPU 的 `rq->rd != &def_root_domain` 则视为「根域已安装」。在 `partition_sched_domains_locked()` 的复用判定里，把 `sched_domain_installed(doms_cur[i])` 加入 `match1` 条件；摘除路径 `detach_destroy_domains(doms_cur[i])` 前也先做该检查。这样失败的分区不会被错误复用，也不会在「从未成功安装」时被摘除，下次重建即可重试。

## 版本演进与当前进展
*current_version: v1*（2026-10-31，`<20261031124949.3904462-2-thnkslprpt@gmail.com>`）。首版，带 `Fixes:` 与 QEMU 故障注入验证，尚无 reviewer 回复。

## Maintainer 意见与讨论焦点
当日无维护者回帖。判断依据全部来自作者：mechanism 清晰、有 `Fixes:` 指向 `029190c515f1`、并在 4-vCPU QEMU 中做了 `alloc_rootdomain()` 故障注入的复现/验证对比。

## 合入评估
*likelihood=unknown*。新补丁、无 review 反馈；改动聚焦 cpuset/sched domain 划分的失败重试路径，风险面小但需 topology/cpuset 维护者确认。*blocking_issues*：无 reviewer 表态；需确认 `sched_domain_installed()` 的判断在并发/多分区场景下无遗漏。*next_action*：等 topology（Peter Zijlstra）或 cpuset 侧 review。

## 效果评估
作者给出功能级验证：4-vCPU QEMU 中注入 `alloc_rootdomain()` 失败时，未打补丁的内核跳过相同重建、补丁内核恢复了调度域。无性能数据。

## 我可以参与的点
- **testing**：在 cpuset + 内存压力场景复现 `alloc_rootdomain()` 失败，验证补丁后调度域可自愈。
- **review**：核对 `sched_domain_installed()` 在多分区、并发 rebuild 下是否与 `ndoms_cur` 遍历逻辑一致。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261031124949.3904462-2-thnkslprpt@gmail.com/

---
id: sched-20261031-007
date: 2026-10-31
subject: "sched/topology: Retry scheduler domains after failed construction"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261031124949.3904462-2-thnkslprpt@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261031124949.3904462-2-thnkslprpt@gmail.com/"
authors: [Avi Weiss]
maintainers_involved: []
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: 029190c515f1
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "无 reviewer 表态"
    - "sched_domain_installed() 在并发/多分区场景下是否无遗漏待确认"
  next_action: "等 topology（Peter Zijlstra）或 cpuset 侧 review"
contribution_opportunities:
  - kind: testing
    description: "cpuset + 内存压力下复现 alloc_rootdomain() 失败，验证补丁后调度域可自愈"
  - kind: review
    description: "核对 sched_domain_installed() 在多分区、并发 rebuild 下与 ndoms_cur 遍历的一致性"
generated_at: "2026-11-01T09:00:00"
source_email_count: 1
related_articles: []
tags: [topology, cgroup]
---
