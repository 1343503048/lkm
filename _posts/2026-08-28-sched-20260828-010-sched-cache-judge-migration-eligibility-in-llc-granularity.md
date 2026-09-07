---
id: sched-20260828-010
date: '2026-08-28'
subject: 'sched/cache: Judge migration eligibility in LLC granularity'
subsystem: sched
type: feature
status: rfc
severity: medium
thread_root_msgid: <20260828015808.784722-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/20260828015808.784722-1-wujianyong@hygon.cn/
authors:
- Jianyong Wu
maintainers_involved:
- Peter Zijlstra
- Chen Yu
current_version: v2
patch_series:
- version: v2
  msgid: <20260828015808.784722-1-wujianyong@hygon.cn>
  date: '2026-08-28'
  summary: v2 后半段 15/23-23/23：affinity gain 接入迁移准入、alb_break_llc 只管单任务 rq、active balance
    推方向取消 nr_balance_failed 等待、NUMA balancing 拆 task/page、线程组 scan 纳入全部 active preferred
    node、非对称 EWMA(1/2 vs 1/8) 估算线程组利用率并按前缀放行扩散、debug 打印 preferred LLC
  review_outcome: 8/28 当日无回帖；8/31 Peter Zijlstra 的评审集中在前半段 02/04/07/08，后半段至今无人评审
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 仍为 RFC，作者自述 NUMA balancing 拆分部分未完成
  - 23 补丁体量且全系列无 Reviewed-by，评审集中在前半段并已有多轮质疑
  - 16/20/21 的行为论断（只纠正 overshoot、扩张快收缩慢）无任何量化数据
  - 18/23 与 17/23 是同一冲突的两种解法，社区未表态走哪条
  next_action: 作者按 Peter 对前半段的意见出 v3 并补齐扩散/抖动数据；Chen Yu 侧需对 NUMA balancing 拆分表态
contribution_opportunities:
- kind: testing
  description: 在 4 node/多 LLC 机型上量化 16/21 放开后的跨 LLC 迁移次数与每 LLC 负载方差，验证是否出现来回迁移
- kind: testing
  description: 对 20/23 的 EWMA 权重 1/2 与 1/8 做敏感性对照
- kind: review
  description: 确认 alb_break_llc 只管单任务 rq 后，多任务 rq 的 LLC 偏好保护是否仍完整（结合 nr_pref_llc_running
    的 DELAY_DEQUEUE 缺陷）
- kind: discussion
  description: 提出 cgroup/cpuset 维度缺失：线程组级估算在多进程 cgroup 上如何聚合
generated_at: '2026-09-07T22:40:00'
source_email_count: 7
related_articles:
- sched-20260827-002
- sched-20260831-005
- sched-20260828-004
- sched-20260830-003
tags:
- topology
- load_balance
- numa_balancing
- cfs
title: 'sched/cache: Judge migration eligibility in LLC granularity'
layout: article
---

## TL;DR

**本文为增量更新**（完整方案背景见 sched-20260827-002）。Jianyong Wu（Hygon）23 补丁 RFC v2 在 8/27 只送到 cover + 00–14，**8/28 补齐了后半段的 7 封：15/23–18/23、20/23、21/23、23/23**（`4/23`、`11/23`、`12/23`、`19/23`、`22/23` 到 9/5 缓存末尾仍未收到）。这半段是整套"按 LLC 粒度有序扩张"的**执行端**：迁移准入判定（15）、active balance 双向不对称放行（16）、NUMA balancing 拆成 task/page 两条独立开关（17）、线程组 scan 范围纳入全部 active preferred node（18）、线程组整体利用率的非对称 EWMA 估算（20）、按估算前缀放行扩散（21，单封 325 增 25 删，是全系列最重的一封）、`/proc` 里打印任务 preferred LLC（23）。8/28 当日这 7 封**无一人回帖**；8/31 Peter Zijlstra 的六连帖全部打在更早的 02/04/07/08 上，后半段至今未被评审。

## 背景与问题

前 14 封铺好了"偏好序列"这套数据结构：每 CPU 的 NUMA/LLC 偏好计数、行内去重的 node 距离矩阵、合成的 LLC 距离矩阵、以及每个任务一条按偏好排序的 LLC 序列。8/28 这批要回答的是三个此前无法回答的问题：

1. **判据往哪儿接**：负载均衡的多条路径（`can_migrate_task()`、`can_migrate_llc_task()`、`alb_break_llc()`、`need_active_balance()`）各自用不同信号决定是否迁移，CAS 的 affinity gain 必须逐条接入才不会被现有逻辑绕过。
2. **扩得快不快**：如果坚持"序列里前一个 LLC 不饱和就不许往后一个 LLC 放"，一个突发增长的线程组会被挡在扩撒之外，实测表现为 LLC 级负载聚合（aggregation）过度、局部过热。
3. **与 NUMA balancing 打架**：NUMA balancing 靠任务迁移 + 页迁移配对工作，而 CAS 只靠任务迁移做聚合，两者同时开启时互相拆台。

## 技术方案

- **15/23 `sched/cache: Judge migration eligibility in LLC granularity`**（1 文件 49 增 77 删）：把前序补丁引入的 affinity gain helper 接到 `can_migrate_llc_task` 与 `alb_break_llc`。这里有一个容易被忽略的形态变化：`alb_break_llc()` 改为**只处理单任务 runqueue**，因为判断"要不要放弃破坏 LLC 局部性"需要把任务的 preferred LLC 当输入；多任务 runqueue 的判定挪到 `can_migrate_task()`。同时**把 NUMA affinity 检查提到 active balance 逻辑之前**——作者给的理由是具体的：不这样排，多任务 runqueue 会跳过 `alb_break_llc` 的过滤，在任务已经位于最优节点的情况下仍然置起 `need_active_balance = true` 和 `LBF_ACTIVE_LB`，产生一次本不想要的迁移。删多于增说明这一步同时收拢了原有分支。
- **16/23 `Allow un-throttled active balance to spread out of a full LLC`**（+58）：明确指出 v2 现状是**两条不对称路径**——把任务拉回 preferred LLC 走 `migrate_llc_task`，`need_active_balance()` 无条件放行；而把一个已经超过聚合上限的 LLC 上的任务推到有空间的 LLC，只能走 `migrate_task`，要先等 `nr_balance_failed` 超过 `cache_nice_tries + 2`。补丁取消推方向的这层等待，并把前提写死：源 LLC 已超 cap、目标在"再加一个满 CPU 的负载"之后仍在 cap 内，因此只能纠正 overshoot，不会反过来跟聚合机制对抗。
- **17/23 `sched/fair: Fine-granularity NUMA balancing`**（4 文件 +105，Suggested-by: Chen Yu）：把 NUMA balancing 的任务迁移与页迁移解耦成可独立开关的两条路径，避免与 CAS 的聚合方向冲突。这块在 cover 里被作者标注为未完成、开放讨论。
- **18/23 `Scan all prefer nodes in thread group`**（3 文件 +44/-5）：`get_scan_cpumasks()` 原先只看当前任务的 preferred node，而线程组内每个任务可能不同，导致每次 scan 的范围不一致、preferred LLC 找不稳。改法是把整个线程组的 active preferred node 全部纳入 scan 范围，并且**对长期未触碰的 preferred node 做失效剔除**（作者注明与 preferred LLC 的失效逻辑同款）。
- **20/23 `Estimate utilization of the whole thread group`**（2 文件 +43/-2）：用一个**非对称 EWMA**跟踪线程组整体利用率——上升按 1/2 加权、下降按 1/8 加权。设计意图是"扩张要快、收缩要慢"：负载上来了立刻允许铺开到更多 LLC，短暂无忙期不会让估算范围塌回去引起抖动。
- **21/23 `Spread workloads within an estimated LLC range`**（4 文件 +325/-25）：把"前序 LLC 未饱和即禁止迁移"改成"先估线程组总负载，只要目标 LLC 落在可接受的负载前缀范围内就放行"，范围外仍保留有序饱和检查。这是把 20 的估算真正接进迁移准入的一封，也是改动量最大的一封。
- **23/23 `sched/debug: Print task preferred LLC`**（+27/-1，Suggested-by: XIAO WU）：把每个任务的 preferred LLC 暴露到调度诊断输出，用于排查 CAS 决策。

## 版本演进与当前进展

- v1：2026-06-25（见 sched-20260827-002）。
- v2：8/27 发 cover 与 00–14（缺 4/11/12），8/28 续发 15/16/17/18/20/21/23（缺 19/22）。**作者本人未在同一天对后半段补充说明，也没有 gentle ping**。
- 8/28 当日：后半段 0 回复。
- 8/31：Peter Zijlstra 在该系列连发 6 帖，针对 02/23 的去重算法边界、04/23 命名、07/23 与 NUMA balancing preferred node 的关系、08/23 新增计数器的必要性（详见 sched-20260831-005）。**评审压力仍集中在前半段**，后半段的形态问题（下面几处）尚未被提出。

## Maintainer 意见与讨论焦点

8/28 当日**没有任何 maintainer 回帖**，因此这一节记录的是"该半段内部暴露、但社区尚未追问"的实质风险点：

- **`alb_break_llc()` 语义被缩小**（15/23）：这个函数原本是 active balance 尊重 LLC 偏好的唯一闸门。改成只管单任务 rq 之后，多任务 rq 的保护要靠 `can_migrate_task()` 里的新判定补足——而 `can_migrate_task()` 是热路径且判据已多达 8 条（站内 sched-20260828-007 刚在整理这份清单）。同一周内该计数器还暴露过 DELAY_DEQUEUE 导致的集合不一致问题（sched-20260828-004、sched-20260830-003），说明这里的判定条件是当前 CAS 最不稳定的部分。
- **不对称放行的代价没有数据**（16/23）：`cache_nice_tries` 这套等待机制本身就是历史上为抑制抖动而加的。取消推方向的等待、只靠"源超 cap + 目标可容纳"两个前提，理论上确实只能纠正 overshoot，但 active balance 的触发频率与跨 LLC 迁移次数变化没有给出任何计数。
- **非对称 EWMA 的两个常数从何而来**（20/23）：1/2 与 1/8 直接决定"扩张多快、收缩多慢"，是全系列最影响线上行为却最难论证的参数，邮件里没有敏感性分析。
- **NUMA balancing 拆分**（17/23）：作者自己在 cover 标注未完成。它与 18/23 的 scan 范围改造是同一个问题的两种解法（拆开互不干扰 vs 扩大 scan 范围包容彼此），社区尚未表态该走哪条。

## 合入评估

**likelihood: unclear**。

- 有利：方向是 Peter Zijlstra 此前提出的（v2 就是按该方向重做）；问题陈述（LLC 级聚合过热、preferred LLC 抖动、与 NUMA balancing 冲突）是主线 CAS 的真实缺陷；作者给出了具体的失效场景（不重排 NUMA 检查会误置 `LBF_ACTIVE_LB`）。
- 卡点：仍是 **RFC**，作者自述有未完成项；23 补丁体量 + 全系列无 `Reviewed-by`；评审集中在前半段且已出现多轮质疑（02/04/07/08）；后半段的性能论证（尤其 16/20/21）缺数据。
- `next_action`：按 Peter 对前半段的意见重发出 v3，并把后半段的抖动/扩散数据补齐；NUMA balancing 拆分那两封需要 Chen Yu/Intel 侧明确立场。

## 效果评估

**这 7 封里没有任何 benchmark 数据**：commit message 全部是机制描述与失效场景说明，唯一的量化信息是改动规模（21/23 单封 325 增 25 删，说明准入判定改动量集中在这一封）。v2 的 cover（8/27，见 sched-20260827-002）提到过 schbench 等测试暴露的饱和问题被本版修复，但同样未给出前后对比数字。因此本版效果无法独立评估，只能作为"作者自述已改善"记录。

## 我可以参与的点

- **最有价值的回帖是数据而不是读码**：16/23 与 21/23 都宣称"只纠正 overshoot、不跟聚合对抗"，这类论断在真实多线程负载上很容易证伪。用固定线程数的并发负载（多线程 schbench/自定义 spin 组）在 4 node/多 LLC 机型上量一下：跨 LLC 迁移次数、`nr_active`/active balance 成功率、每 LLC 运行时间方差。若能看到"推方向放开等待后出现来回迁移"，就是 v3 必须修的第一条。
- **参数敏感性分析**：20/23 的 1/2 与 1/8 是纯经验值。给出"上升更快/更慢"的对照组（哪怕只是同一负载下三个取值的时间序列），对社区的价值高于一句"看起来更好"。
- **与 `nr_pref_llc_running` 那条线交叉验证**：15/23 之后 `alb_break_llc()` 只对单任务 rq 生效，而该判据里用的 `nr_pref_llc_running == cfs.h_nr_runnable` 本周已被证明在 DELAY_DEQUEUE 下失效（sched-20260828-004、sched-20260830-003）。可以顺着这条线确认 CAS 的聚合闸门在多任务 rq 上是否还剩有效保护。
- **cpuset/cgroup 视角的缺口值得点出**：整套估算以"线程组（thread group）"为单位，没有 cgroup 层级维度。若客户侧的放置单元是 cgroup/cpuset 而非单进程线程组，跨 LLC 前缀估算在多进程 cgroup 上如何聚合，是 v3 之前应当提出的问题。
- **回合判断**：该系列与主线 CAS 强耦合（`CONFIG_SCHED_CACHE`、per-sd 计数、距离矩阵），OLK-6.6 无对应基础设施，短期内不具备回合条件；但 17/23（NUMA balancing 任务迁移与页迁移拆分）是**可独立参考的设计**，内部若有"关 NUMA balancing 页迁移、只留任务迁移"的需求，可以直接对照这封的实现面。

## 参考链接

- 15/23: https://lore.kernel.org/all/20260828015808.784722-1-wujianyong@hygon.cn/
- 16/23: https://lore.kernel.org/all/20260828020457.785383-1-wujianyong@hygon.cn/
- 17/23: https://lore.kernel.org/all/20260828020731.785556-1-wujianyong@hygon.cn/
- 18/23: https://lore.kernel.org/all/20260828020924.785596-1-wujianyong@hygon.cn/
- 20/23: https://lore.kernel.org/all/20260828021156.785662-1-wujianyong@hygon.cn/
- 21/23: https://lore.kernel.org/all/20260828021332.785700-1-wujianyong@hygon.cn/
- 23/23: https://lore.kernel.org/all/20260828021554.785781-1-wujianyong@hygon.cn/
- v2 cover（8/27）: 未获取到（邮件正文 msgid 不在本日语料中，见 sched-20260827-002）
- Peter Zijlstra 8/31 的评审: 见 sched-20260831-005
