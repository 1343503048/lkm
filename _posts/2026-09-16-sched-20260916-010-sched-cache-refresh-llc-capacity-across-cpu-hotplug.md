---
id: sched-20260916-010
date: '2026-09-16'
subject: 'sched/cache: Refresh LLC capacity across CPU hotplug'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260916134432.11767-1-davichazbh@gmail.com>
lore_url: https://lore.kernel.org/all/20260916134432.11767-1-davichazbh@gmail.com/
authors:
- Davi Chaves Azevedo
maintainers_involved: []
current_version: v3
patch_series:
- version: v3
  msgid: <20260916134432.11767-1-davichazbh@gmail.com>
  date: '2026-09-16'
  summary: 仅补 R-b/T-b 标签，无代码改动
  review_outcome: Chen Yu / Tim Chen / K Prateek Nayak 的 Reviewed-by 与 Tested-by 齐备
upstream_commit: null
fixes_commit: 7030513a0877
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 待 sched 维护者收取
contribution_opportunities:
- kind: testing
  description: 在多 LLC/多 cpuset 分区机器上跑 hotplug 往返核对 llc_bytes 刷新
- kind: review
  description: 核对按 mask 逐 CPU 刷新与 boot 期 shared_cpu_map 增量构建的兼容性
generated_at: '2026-09-17T09:00:00'
source_email_count: 6
related_articles:
- sched-20260912-003
tags:
- topology
title: 'sched/cache: Refresh LLC capacity across CPU hotplug'
layout: article
---

## TL;DR
Davi Chaves Azevedo 的 v3（tag-only）：修复 CPU hotplug 时 LLC 容量被低估的问题——CPU 下线时调度域先于 cacheinfo 重建，用了旧的共享权重，导致存活 CPU 的 `llc_bytes` 偏低（例：16MiB LLC 掉一个 SMT sibling 后算成 15379114 而非 16777216），在 cache-aware 调度下可能错误拒绝进程聚合。v3 收齐了 Chen Yu/Tim Chen/K Prateek Nayak 的 Reviewed-by/Tested-by，无代码改动，合入概率高。

## 背景与问题
调度器按 `llc_bytes = cache_size * span_weight / shared_weight` 缩放 LLC 容量。CPU teardown 时 `sched_cpu_deactivate()` 在 `cacheinfo_cpu_pre_down()` 移除该 CPU 之前重建调度域，新域仍用旧的共享权重；随后的 `sched_update_llc_bytes()` 查找已 detach 的离场 CPU 的 `sd_llc`，找不到就直接返回，未纠正存活 CPU。在 Ryzen 5 7535U（12 逻辑核共享 16MiB LLC）上，下线一个 SMT sibling 后存活 CPU 得到 `llc_bytes = floor(16777216*11/12) = 15379114`，而正确值仍应为 16777216。在启用 cache-aware 调度的系统上，低估容量会使 `exceed_llc_capacity()` 拒绝本可容纳的聚合。

## 技术方案
把 cacheinfo 已保留的 cache-sharing mask 传给调度器更新函数，签名从 `sched_update_llc_bytes(unsigned int cpu)` 改为 `sched_update_llc_bytes(const struct cpumask *cpus)`；对 mask 内每个存活 CPU 用其**自己的** LLC 域刷新 `sd->llc_bytes`，使每个 cpuset 分区都得到正确份额，同时保留 boot 期 cache-sharing map 增长所需的纠正逻辑。更新仍位于 hotplug 路径，无稳态开销或持久分配。改动覆盖 `drivers/base/cacheinfo.c`、`include/linux/sched/topology.h`、`kernel/sched/topology.c`。

## 版本演进与当前进展
- **v3**（本日 107345，`<20260916134432.11767-1-davichazbh@gmail.com>`）：仅补 Reviewed-by/Tested-by 标签，无功能性改动。
- v2：按 Chen Yu 建议恢复 boot 期 shared_cpu_map 说明，补多 LLC 测试说明；v1 为初始修复。完整背景见 <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-016-sched-cache-refresh-llc-capacity-across-cpu-hotplug.html">sched-20260911-016</a> / <a class="article-ref" href="/lkm/2026/09/12/sched-20260912-003-sched-cache-refresh-llc-capacity-across-cpu-hotplug.html">sched-20260912-003</a>。

## Maintainer 意见与讨论焦点
- **Chen Yu**：`Reviewed-by` + `Tested-by`（在 Ryzen 8945HX 双 LLC 与 Xeon 每节点四 LLC 上复现并验证 v1 恢复正确 `sd->llc_bytes`）。
- **Tim Chen**：`Reviewed-by`。
- **K Prateek Nayak**：`Reviewed-by` + `Tested-by`。
- 无 NAK 或遗留争议。

## 合入评估
*likelihood=high*。带 `Fixes: 7030513a0877 ("sched/cache: Calculate the LLC size and store it in sched_domain")`，已集齐三位 reviewer 的 R-b/T-b、单/多 LLC 与 hotplug 场景均有验证，改动聚焦 hotplug 路径无稳态开销。*blocking_issues*：无。*next_action*：待 sched 维护者收取。

## 效果评估
本地（单 LLC 主机）：在 7.2.3-arch1-3 上复现陈旧值，补丁内核存活 CPU 均保持 16777216；十轮 SMT-thread 与十轮 whole-core hotplug 周期通过；8 个 source-level 状态场景从 5 失败修复后 8 全过。Chen Yu 在双 LLC Ryzen 8945HX 与四 LLC Xeon 上确认修复。无性能对比数据，属容量记账正确性修复。

## 我可以参与的点
- kind=testing：在带 `CONFIG_SCHED_CACHE` 的多 LLC/多 cpuset 分区机器上跑 hotplug 往返，核对各分区 `llc_bytes` 是否随共享权重变化正确刷新。
- kind=review：核对 `sched_update_llc_bytes()` 改为按 mask 逐 CPU 刷新后，与 boot 期 `shared_cpu_map` 增量构建的兼容性（首个上线 CPU 先看到自己、后随 map 补全纠正）。

## 参考链接
- v3 patch：https://lore.kernel.org/all/20260916134432.11767-1-davichazbh@gmail.com/
- v2：https://lore.kernel.org/all/20260911220229.1368887-1-davichazbh@gmail.com/
