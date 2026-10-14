---
id: sched-20261014-002
subject: 'sched/numa: fix several NUMA balancing issues'
date: 2026-10-14
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261014094347.99157-1-lizhe.67@bytedance.com>
lore_url: https://lore.kernel.org/all/20261014094347.99157-1-lizhe.67@bytedance.com/
authors:
- Li Zhe
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261014094347.99157-1-lizhe.67@bytedance.com>
  date: 2026-10-14
  summary: 0/6：修复 scan-period 分母/共享 fault 语义、tiering promotion 反馈污染、陈旧 preferred-node
    状态
  review_outcome: Gregory Price 逐封要求性能数据，4/6 全局 sysctl 方向被否
upstream_commit: null
fixes_commit: 04bb2f947505
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 缺用户可见性能/行为影响数据
  - 4/6 全局 sysctl 方向被 reviewer 否定
  - 无维护者表态
  next_action: 补齐 benchmark 论证并重做 4/6 接口后发 v2
contribution_opportunities:
- kind: testing
  description: 在 NUMA/tiering/hotplug 环境实测 scan-period 补丁对扫描频率与性能的影响
- kind: review
  description: 评估 4/6 全局 sysctl 是否可被 mempolicy(MPOL_F_NUMA_BALANCING) 覆盖
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 13
related_articles: []
tags:
- numa_balancing
- cfs
title: 'sched/numa: fix several NUMA balancing issues'
layout: article
---

> **subject**：sched/numa: fix several NUMA balancing issues

## TL;DR
Li Zhe（字节跳动）今日发出 0/6 系列，修复 NUMA balancing 在 scan-period 调整、memory-tiering promotion 反馈、陈旧 task-placement 状态三个方向的多个问题（含一个 memory hotplug 下可复现的除零）。当日 Gregory Price 对 6 个补丁逐一回帖，普遍要求补「用户可见的性能影响」数据，并对 4/6 的全局 sysctl 开关方向明确表示「不是正确方向」。v1 刚发、无维护者表态，合入前需先补齐性能论证。

## 背景与问题
系列覆盖三类既存缺陷：

- **scan-period 分母与共享 fault 语义**（1–3/6）：`update_task_scan_period()` 的 ratio 分母校验与实际除数是两套 sum，memory hotplug 后 `for_each_online_node()` 跳过已下线节点会留下「local>0 但 private/shared 均为 0」的窗口，触发除零（作者在 v7.3-rc1 QEMU guest 上 hot-remove NUMA 节点复现）；且「共享 fault 该减速扫描」的意图与实现不一致（用 private ratio 当减速信号，共享主导的窗口反而落进加速路径）。
- **memory-tiering promotion 反馈污染**（4–6/6）：free-space bypass 会无视 hotness/rate-limit 把冷页与突发热页回填到 fast tier，破坏刻意铺到 CXL+DRAM 的带宽分布；tiering-only 的 promotion fault 会漏过 `task_numa_fault()` 的排除逻辑、污染正常 task-placement 统计与 preferred-node 状态。

`Fixes:` 分别指向 `04bb2f947505`（execve 清理）与 `37ec97deb3a8`（scan rate 慢化，1/6 与 2–3/6）。

## 技术方案
六补丁（`kernel/sched/fair.c` +181/−63，另改 `include/linux/{sched,mm,mmzone}.h`、`mm/memory.c`、`sysctl/kernel.rst`）：

1. `task_numa_free()` 非 final 路径 `memset` 清掉整个 retained `numa_faults` 数组与 `numa_faults_locality`，execve 后新镜像不再继承旧 fault 反馈。
2. 用实际分母 `locality_faults`/`type_faults` 做前置校验（`!locality_faults || !type_faults`），替代旧的 `local + shared == 0` 判据。
3. 新增 `NUMA_FAULT_REMOTE_PRIVATE` 计数器：只有「既 remote 又 private」的 fault 足够多才加速扫描，local/shared 主导一律减速，避免共享远程 fault 造成额外 hint 开销。
4. 新增 `kernel.numa_balancing_promote_free_space_bypass`（默认 1 保持旧行为），置 0 时 fast tier 空闲不再绕过 hotness/rate-limit 检查。
5. 引入 `LAST_CPUPID_UNSET` / `LAST_CPUPID_ACCESS_TIME` 哨兵，把 slow-tier 页用 last_cpupid 存的 access-time 元数据与普通 cpupid 区分开，tiering-only 模式的 promotion fault 只记迁移、不喂 placement 统计。
6. 新增 `numa_balancing_normal_enabled()` helper，NORMAL 位关闭时 `task_numa_preferred_nid()` 返回 `NUMA_NO_NODE`，让各调度路径忽略陈旧 preferred-node 状态（保留 `nr_numa_running`/`nr_preferred_running` 记账避免不对称）。

## 版本演进与当前进展
v1（今日首发，`<20261014094347.99157-1-lizhe.67@bytedance.com>`）。当日 Gregory Price 对 1–6/6 逐封回复，尚无新版本。

## Maintainer 意见与讨论焦点
无维护者（Peter/Juri/Dietmar 等）表态。**Gregory Price**（NUMA balancing 资深 reviewer）逐封意见：

- 1/6：exec 后进程能否跑得足够久收集到真实 fault 数据？「不是错的，但影响不明」，要明确复现。
- 2/6：改动超出修除零、整体改变了函数行为，「不清楚是否正确」。
- 3/6：改变 2017 年以来的既有行为，担心意外回归，**要性能数字**证明优于现状。
- 4/6：**「全局开关是差方案」**——刻意铺开的内存通常由 mempolicy 完成，未设 `MPOL_F_NUMA_BALANCING` 时该分布已被保护、不会迁移；明确「不认为这是正确方向」。
- 5/6、6/6：前提认同，但属重大改动，同样要用户可见的性能收益数据；6/6 另转述「Sashiko 也有一些 correctness 反馈」。

争议集中在「缺性能/用户可见影响数据」与「4/6 的接口形态」，无 NAK。

## 合入评估
*likelihood=medium*。修复对象真实（含可复现除零、`Fixes:` 齐全），但 reviewer 一致要求补性能数据，且 4/6 的全局 sysctl 方向被明确否定、需回到 mempolicy 等既有机制重新考虑。*blocking_issues*：缺用户可见性能/行为影响数据；4/6 接口形态被否；无维护者表态。*next_action*：作者补齐 benchmark 论证，重做 4/6（或说明为何 mempolicy 方案不适用），再提交 v2。

## 效果评估
暂无性能数据。除 2/6 除零有 QEMU hotplug 复现外，其余补丁作者未提供量化收益，Gregory 也明确指出「除『期待某种性能收益』外，难以判断用户可见影响」。3/6 属行为回归风险型改动，尤其需要数据支撑。

## 我可以参与的点
- testing：在 NUMA 机器（尤其含 memory tiering/CXL 或 memory hotplug 环境）上跑 scan-period 相关基准，验证 1–3/6 对扫描频率、迁移量与性能的实际影响并回帖。
- review：结合 4/6 的 mempolicy `MPOL_F_NUMA_BALANCING` 语义，评估「全局 sysctl」是否真能覆盖作者要解决的工作负载（CXL+DRAM 聚合带宽）场景，或是否应由 mempolicy/per-cgroup 表达。

## 参考链接
- 系列 cover lore：https://lore.kernel.org/all/20261014094347.99157-1-lizhe.67@bytedance.com/
