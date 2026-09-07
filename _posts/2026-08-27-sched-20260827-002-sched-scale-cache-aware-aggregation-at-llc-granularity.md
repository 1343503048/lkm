---
id: sched-20260827-002
date: '2026-08-27'
subject: 'sched: Scale cache-aware aggregation at LLC granularity'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260827122816.756234-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/20260827122816.756234-1-wujianyong@hygon.cn/
authors:
- Jianyong Wu
maintainers_involved:
- Peter Zijlstra
- Chen Yu
current_version: v2
patch_series:
- version: v1
  msgid: <20260625030759.25928-1-wujianyong@hygon.cn>
  date: 2026-06-25
  summary: 初版按 sched domain 边界扩展 CAS 资源范围
  review_outcome: Peter Zijlstra 建议改为按 LLC 粒度扩展资源；schbench 等测试暴露饱和问题
- version: v2
  msgid: <20260827122816.756234-1-wujianyong@hygon.cn>
  date: 2026-08-27
  summary: 23 补丁：node 去重距离矩阵 + 合成 LLC 距离矩阵构造亲和序列，按线程组利用率估算前缀范围放行迁移
  review_outcome: v2 当日暂无外部 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 作者自述 far from perfect，与 NUMA balancing 拆分（Chen Yu 建议）未完成，本轮只求方向确认
  - 合成 LLC 距离矩阵无物理含义，机制复杂度接受度未知
  - 23 补丁规模大概率需要拆分系列
  next_action: 等待 Peter 等维护者对 cover 的方向性表态
contribution_opportunities:
- kind: testing
  description: 在多 LLC 多 node 机型复测 schbench/NPB，回帖利用率前缀估算的失效边界
- kind: discussion
  description: 就合成 LLC 距离矩阵提出有物理依据的替代排序输入（cacheinfo 共享深度/互连 hop）
- kind: extend
  description: 跟进 NUMA balancing task/page 路径独立开关的未完成部分
generated_at: '2026-09-07T22:05:00'
source_email_count: 13
related_articles: []
tags:
- topology
- load_balance
- numa_balancing
- cgroup
title: 'sched: Scale cache-aware aggregation at LLC granularity'
layout: article
---

## TL;DR
Jianyong Wu（Hygon）发出 23 补丁 RFC v2，把 cache-aware scheduling（CAS）的聚合单位从"单个 LLC 域"扩展为"按 LLC 粒度跨域有序扩张"，落地 Peter Zijlstra 此前提出的方向。作者自述仍有未解决项、先发求方向确认；v2 当天尚无人回复。这是用户主线（cgroup 聚合调度 + 大核数拓扑）直接相关的大部头，值得精读 cover。

## 背景与问题
现有 CAS 实现以 LLC 为中心做线程组聚合：任务尽量聚在同一个 preferred LLC 内。这对放得进单个 LLC 的负载有效，但聚合范围固定死，负载超出一个 LLC 时无法有序外扩，跨 LLC 场景扩展性差。第二个痛点：workload 铺满全系统且单 LLC CPU 数少时，preferred LLC 本身随运行时间统计频繁漂移，导致迁移抖动。NUMA balancing 开启还会进一步破坏 preferred LLC 的稳定性（scan 范围局限于任务当前 preferred node）。

## 技术方案
核心是给每个 preferred LLC 构造一条**亲和序列**（affinity sequence），再按线程组的总利用率估算决定"用到序列前缀到哪里"：
- **node 排序**：基于 BIOS 原始 NUMA 距离矩阵，构造每行去重（unique distance）的细化矩阵来排 node 优先级（Patch 2）；
- **node 内 LLC 排序**：系统没有 LLC 间物理距离，作者构造一个仅为排序提供 hint 的合成 LLC 距离矩阵（Patch 4/5 区间），preferred LLC 所在 node 按该行排，其他 node 内按 LLC ID 升序；
- **扩张语义**：序列是"有序扩张偏好"而非逐级饱和闸门——估算线程组总利用率，选出能容纳它的最小前缀；落在该范围内的目标 LLC 只要有容量即可迁入，即使前缀中更早的 LLC 未饱和；范围外仍走有序饱和检查以保持聚合（Patch 20–22）。
- **preferred 选择改为两级**：先按线程组运行时间选 preferred NUMA node，再在 node 内选 preferred LLC（Patch 7），并新增 per-CPU `sd->numa_counts` 偏好计数（Patch 8/9）与 `llc_to_node()`/`sd_node` 拓扑设施（Patch 1/6）。
- **与 NUMA balancing 的冲突处理**：把线程组内所有 active 任务的 preferred node 纳入 scan 范围（Patch 18 区间）；按 Chen Yu 建议把 NUMA balancing 拆成 task/page 两条可独立开关的路径——作者明确标注这部分**未完成、开放讨论**。

被放弃的备选：作者曾尝试为每个线程组维护一张 LLC mask 记录资源范围，因 mask 在 `task_cache_work()` 更新、负载均衡时读取而必然滞后，且 load balance 找源端 sched_group 时没有任务上下文可查该 mask，被判定不可行，改为任务无关（per-sd 计数 + 距离矩阵）方案。

## 版本演进与当前进展
- v1：2026-06-25 发出（cover msgid `20260625030759.25928-1-wujianyong@hygon.cn`，链接见作者 cover letter）。
- v2（本日）：11 项大改，关键的有——不再按 sched domain 边界扩张资源；新增行内去重 node 距离矩阵与 node 内 LLC 距离矩阵；affinity gain 计算方式与迁移许可判定方式全部重做；修复 schbench 等测试暴露的饱和问题；线程组整体利用率估算 + 前缀范围放行；从 preferred LLC 起点遍历 preferred node。
- 当日仅发出 cover + 部分补丁（缓存含 00–03、05–10、13、14），11/12、15–23 未收到，v2 暂无外部 review。

## Maintainer 意见与讨论焦点
当日无人回复，无分歧记录。作者自己在 cover 中摆出的争议点：(1) 合成 LLC 距离矩阵"无物理意义、仅作 hint"，命名与可解释性可能被挑战；(2) 与 NUMA balancing 拆分（Chen Yu 建议）明确未完成；(3) 作者自述"far from perfect，仍含未解决问题"，本轮目的就是方向确认。此前方向性背书：Peter Zijlstra 建议按 LLC 粒度扩展资源（cover 原文），这也是 v1→v2 的路线拐点。

## 合入评估
**unclear**。23 补丁 RFC、作者主动挂起求方向评审，且自认与 NUMA balancing 的冲突处理未完成；卡点是社区对"合成 LLC 距离矩阵 + 利用率前缀估算"这套机制复杂度的接受度（CAS 本身在主线也还在演进，同日 Zhan Xusheng 还在问 CAS 计数器的语义问题，见 sched-20260827-018）。`next_action`：等 Peter/其他维护者对 cover 的方向性表态。若方向确认，大概率还要经历按功能拆系列（拓扑设施 1–6 与迁移决策 11–16 可分拆）。

## 效果评估
v2 邮件未给出 benchmark 数字；cover 仅提到 v1 方案在 schbench 上有饱和问题且本版修复（"Fix saturation issues in some tests like schbench"），具体数据未获取到。

## 我可以参与的点
- **直接对口**：该系列与 cpuset/cgroup 大线程组跨 LLC 放置场景强相关，Hygon 机型数据是稀缺资源——若有同类 4 node/多 LLC 机型，复测 schbench/NPB 并回帖利用率前缀估算的失效边界，是 v3 最需要的输入。
- 讨论中"合成 LLC 距离矩阵无物理意义"一点可以给出替代方案（如用 cacheinfo 共享深度/互连 hop 数）参与设计讨论。
- 与 NUMA balancing 拆分（task vs page 迁移独立开关）未完成，正好是 cpu.cpuset 场景常碰的坑，可跟进并在帖内给出使用侧约束。

## 参考链接
- v2 cover (00/23): https://lore.kernel.org/all/20260827122816.756234-1-wujianyong@hygon.cn/
- Patch 02/23（node 距离矩阵）: https://lore.kernel.org/all/20260827122816.756234-3-wujianyong@hygon.cn/
- v1 系列：msg `20260625030759.25928-1-wujianyong@hygon.cn`（作者 cover 内给出的链接，本目录缓存无该 msgid，未拼 lore）
- tip-bot commit: 未获取到
- stable backport: 未获取到
