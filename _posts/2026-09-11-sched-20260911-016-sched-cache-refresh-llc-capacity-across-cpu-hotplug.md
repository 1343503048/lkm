---
id: sched-20260911-016
subject: 'sched/cache: Refresh LLC capacity across CPU hotplug'
date: '2026-09-11'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260911134825.420748-1-davichazbh@gmail.com>
lore_url: https://lore.kernel.org/all/20260911134825.420748-1-davichazbh@gmail.com/
authors:
- Davi Chaves Azevedo
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260911134825.420748-1-davichazbh@gmail.com>
  date: 2026-09-11
  summary: cacheinfo 传共享掩码给 sched_update_llc_bytes()，逐幸存 CPU 刷新 llc_bytes；修热插拔时序导致的容量低估；Fixes
    7030513a0877。
  review_outcome: v1 刚发出，当日无回帖。
upstream_commit: null
fixes_commit: 7030513a0877
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 零 review；cacheinfo（驱动侧）接口改动需两侧维护者认可
  - 无多 LLC 硬件验证（作者自述边界）
  next_action: 等 cacheinfo/sched 两侧维护者首轮意见
contribution_opportunities:
- kind: testing
  description: 多 LLC 机器上热插拔循环验证各分区 llc_bytes 正确性
- kind: review
  description: 核对掩码空/单 CPU 边界与并发热插拔下的时序假设
generated_at: '2026-09-14T11:35:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- topology
title: 'sched/cache: Refresh LLC capacity across CPU hotplug'
layout: article
---

## TL;DR
Davi Chaves Azevedo 修复 CPU 热插拔后 llc_bytes 停留旧值的问题（CONFIG_SCHED_CACHE 下调度器按缓存共享比例缩放 LLC 容量）：teardown 时调度域先于 cacheinfo 重建，后续更新又查到已 detach 的域，导致幸存 CPU 的 llc_bytes 偏小（实测 16MiB LLC 只剩 15,379,114 字节）。修复把共享掩码直接传给调度器更新并逐 CPU 刷新。v1 首发，当日无回帖。

## 背景与问题
llc_bytes = cache_size * span_weight / shared_weight。CPU 下线时 sched_cpu_deactivate() 先重建调度域、cacheinfo_cpu_pre_down() 才把 CPU 移出 shared_cpu_map——新域用的是旧共享权重；随后的 sched_update_llc_bytes(cpu) 查询的是离线 CPU 已 detach 的 sd_llc，直接返回、无人纠正幸存 CPU。后果：开 cache-aware scheduling 的系统上，exceed_llc_capacity() 会错误拒绝本可聚合的进程；cpuset 分区改动时也可能残留旧值。

## 技术方案
- cacheinfo 把已保留的 cache 共享掩码（cpu_map）直接传给 sched_update_llc_bytes()，不再由调度器按 CPU 反查 sd_llc；
- online/pre_down 两条路径都改为在掩码有效时对掩码内每个幸存 CPU 用各自的 LLC 域刷新，保证各分区拿到正确份额；
- 保持既有热插拔与调度域同步顺序，更新仍留在热插拔路径上，不新增稳态调度操作或持久分配；
- Fixes: 7030513a0877 ("sched/cache: Calculate the LLC size and store it in sched_domain")。

## 版本演进与当前进展
*current_version: v1（msgid `<20260911134825.420748-1-davichazbh@gmail.com>`，09-11 21:48 入缓存）*，v1 刚发出、暂无 review 意见。改动面：drivers/base/cacheinfo.c、include/linux/sched/topology.h、kernel/sched/topology.c（3 文件，20+/22-）。

## Maintainer 意见与讨论焦点
暂无维护者或社区回帖（当日缓存零回复），未获取到任何表态。

## 合入评估
*likelihood=unknown*：无 review 可依据。有利面：修复有清晰的时序论证、真实平台复现与多场景验证（见下），且 Fixes 指向明确的 CAS 基础设施 commit（Tim Chen 的 sched/cache 系列，承 sched-20260911-003 的语境）；不利面：驱动侧（cacheinfo）与调度侧（topology）的接口改动需要两侧认可，作者非该子系统常客。*blocking_issues*：零 review；驱动侧 include 变化是否被 cacheinfo 维护者接受未定。*next_action*：等待 cacheinfo/sched 两边维护者首轮意见。

## 效果评估
作者给出了完整的验证矩阵（均为一手的、可核对的数字）：
- Ryzen 5 7535U（12 逻辑 CPU 共享 16MiB LLC）下线一个 SMT 兄弟后，修复前幸存 CPU llc_bytes = floor(16777216 * 11 / 12) = 15,379,114 字节，修复后全部恢复 16777216；
- 10 轮 SMT 线程 + 10 轮整核热插拔全部通过（每轮含容量校验），既有 CPU 热插拔 selftest 通过；
- 源码级状态夹具：修复前 8 场景 5 失败，修复后 8/8 通过（覆盖分区变化、不等 span、稀疏 CPU 编号、启动期掩码增长；不含并发）；
- 全量 x86-64 基线/修复版构建通过，ARM64、无 CONFIG_SCHED_CACHE 的 x86、x86 UP 构建通过。
作者明确边界：单 LLC 主机的活体检查只证明记账修正，不证明聚合加速；无同版本受控性能对比、无多 LLC 硬件结果。

## 我可以参与的点
- kind=testing：在多 LLC（多 socket/多 CCD）机器上做热插拔循环，验证各分区 llc_bytes 的正确性——作者明说缺多 LLC 数据，这是最直接的补位。
- kind=review：核对 online 路径掩码为空/单 CPU 时的边界行为，以及与 sched_cpu_deactivate() 域重建顺序的竞态假设是否在并发热插拔下成立（作者自述夹具未覆盖并发）。

## 参考链接
- 补丁：https://lore.kernel.org/all/20260911134825.420748-1-davichazbh@gmail.com/
- Fixes 指向：7030513a0877（"sched/cache: Calculate the LLC size and store it in sched_domain"，hash 取自补丁正文）
