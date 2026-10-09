# lib, sched: Introduce sparsebitmap (sbm)

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261002-007：K Prateek Nayak（AMD）的 13 补丁 RFC v3（10 K Prateek + 3 Peter Zijlstra）——大机器全局 cpumask 的 C2C ping-pong 问题引入 sparsebitmap（sbm）：按 LLC/节点实例分片的位图，写保持本地 cacheline；v3 补 7 架构 enablement 并把 `nohz.idle_cpus_mask` 转为首个用户；实测平均 ~1-2% 持平略好、最坏场景更新代价降到 1/100；作者将在 LPC'26 Scheduling MC 讲此工作。当日零回帖。
- sched-20261003-005（今天）：系列收到**首个实质 review**——Chen Yu（Intel，调度侧核心开发者）确认「interesting topic」并给出四点深度意见：(1) 询问延迟数据用的 schbench/sched-messaging；(2) 若 sbm 用于 wakeup 路径（per-LLC mask），与 Mel Gorman 提议的 per-sd_share `idle_cpus_span[]` 差异不大、LLC 内频繁更新仍有 C2C 延迟，猜测 u8 版本（同掩码同时只 8 CPU 触碰）更合适；(3) 指出读者侧 `for_each_cpu_wrap(balance_cpu, nohz.idle_cpus_mask, this_cpu+1)` 起点可能不是 LLC sibling、建议从本 CPU 的 LLC sibling 起（避免 reader/writer 跨 LLC 的 HITM）；(4) 列出可同样 sbm 化的其它全局掩码：`rd->rto_mask`（附 Pan Deng ffmpeg 案例链接）、`rd->dlo_mask`、`tick_broadcast_**mask`。

## 背景与问题

（承接 sched-20261002-007）大容量多插槽/多节点机器上，调度器与定时器状态用的全局 cpumask 是所有核争写的共享 cacheline 集合——每次置位/清位跨 socket 抢 cacheline（C2C ping-pong），`nohz.idle_cpus_mask` 是典型高频更新者。Steve Sistare 早近十年前提过 sparsemask、2026 年 3 月 Peter 给过最小实现但未通用化，本系列把它做成跨架构通用设施。v3 实测：全局掩码、per-NUMA、per-LLC、per-LLC u8 各形态下 nohz 掩码的空间占用与性能收益（引用数据见效果评估节）。

## 技术方案

（承接）13 补丁（`<20261001192849.74788-1-kprateek.nayak@amd.com>`，20 文件 +883/−51，base tip sched/core @ 1fb28c664a19）：lib/sbm.c + sbm.h 核心（`num_instances` + `max_threads_per_instance` 架构声明、CPU 激活时动态分配索引、`[数组下标|元素内位偏移]` 拼装编码）、7 架构 enablement、`nohz.idle_cpus_mask` 首个用户。

今天 Chen Yu 的增量意见：
- **wakeup 路径适配性**：sbm 叶子掩码与 Mel Gorman 的 per-sd_share `unsigned long idle_cpus_span[]` 在 per-LLC 粒度上趋同；频繁更新的 C2C 延迟在 1 个 LLC 内仍在，u8 版（同掩码同时最多 8 CPU 触碰）可能更适合 wakeup 路径——呼应 cover 自述的「16 CPU/LLC 上叶子更新对 benchmark 仍有 ~8-10% 影响」。
- **读者侧扫描优化**：`_nohz_idle_balance()` 的 `for_each_cpu_wrap(..., this_cpu+1)` 改为从本 CPU 的 LLC sibling 起扫，规避 reader 在 LLC1、writer 在 LLC0 的跨 LLC HITM。
- **扩展候选**：`rd->rto_mask`（rt overloaded，Pan Deng ffmpeg 案例[1]）、`rd->dlo_mask`（DL overloaded）、`tick_broadcast_**mask`。

[1] https://lore.kernel.org/lkml/a3207ebf537bbe5605ff5454f63b5604d83a04a0.1753076363.git.pan.deng@intel.com/

## 版本演进与当前进展

- v3（10-02，`<20261001192849.74788-1-kprateek.nayak@amd.com>`）发出；10-03 Chen Yu 首个实质 review，作者暂未回复。
- LPC'26 Scheduling MC（下周）作者将现场讲此工作。

## Maintainer 意见与讨论焦点

- **Chen Yu**：非 maintainer 但是调度侧核心 reviewer，四点意见均为技术深化（benchmark 归属、wakeup 适配性、读者侧扫描、扩展面），无方向性反对。
- Peter Zijlstra（3 片核心补丁共同作者）本轮未回帖；各架构 maintainer 的 ACK 收集仍未开始。

## 合入评估

*likelihood=low*。RFC 阶段 + 跨 7 架构 + 883 行新增，架构侧 ACK 收集本身是长周期；但首个高质量 review 已到、方向无人反对、LPC 曝光在即。*blocking_issues*：各架构 maintainer 逐一 ACK；wakeup 路径扩展可行性未证明（作者自认 ~8-10% 开销还差很远）。*next_action*：LPC'26 Scheduling MC 现场收集意见；回复 Chen Yu 的四点（benchmark 归属与 u8/wakeup 判断）。

## 效果评估

（承接 v3 cover 数据）全局掩码占用 100%、per-NUMA 32.9%、per-LLC 1.3%、per-LLC u8 0.49%（相对原全局 cpumask）；nohz 均衡路径平均 ~1-2% 持平略好，最坏场景（每次上下文切换一个事件）更新代价降到全局掩码的 1/100。Chen Yu 追问的 schbench/sched-messaging 归属待作者澄清。

## 我可以参与的点

- `extend`：按 Chen Yu 建议试做读者侧 `for_each_cpu_wrap` 从 LLC sibling 起扫的变体并跑 nohz 均衡 micro-benchmark，回帖给数据（该改动小、可独立成 patch 评估）。
- `testing`：在 arm64 多 LLC 系统上补 wakeup 路径（16 CPU/LLC）的 sbm 叶子更新开销数据，验证 u8 形态判断。
- `review`：评审 `rd->rto_mask`/`rd->dlo_mask`/`tick_broadcast_**mask` 转 sbm 的可行性（Chen Yu 列出的扩展候选，可先做评估报告回帖）。

## 参考链接

- lore（v3 cover）: https://lore.kernel.org/all/20261001192849.74788-1-kprateek.nayak@amd.com/
- lore（Chen Yu review）: https://lore.kernel.org/all/asDGbBEHkDouWOwC@three-body/

---
id: sched-20261003-005
date: '2026-10-03'
subject: 'lib, sched: Introduce sparsebitmap (sbm)'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<20261001192849.74788-1-kprateek.nayak@amd.com>'
lore_url: 'https://lore.kernel.org/all/20261001192849.74788-1-kprateek.nayak@amd.com/'
authors:
  - 'K Prateek Nayak'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v3
patch_series:
  - version: v3
    msgid: '<20261001192849.74788-1-kprateek.nayak@amd.com>'
    date: '2026-10-02'
    summary: '13 补丁：sbm 核心 + 7 架构 enablement + nohz.idle_cpus_mask 首用户'
    review_outcome: '10-03 Chen Yu 首个实质 review（四点深化意见），作者未复'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - '各架构 maintainer ACK 收集未开始'
    - 'wakeup 路径扩展可行性未证明（~8-10% 开销）'
  next_action: 'LPC''26 Scheduling MC 收集意见；回复 Chen Yu 四点'
contribution_opportunities:
  - kind: extend
    description: '试做读者侧 for_each_cpu_wrap 从 LLC sibling 起扫的变体并给数据'
  - kind: testing
    description: 'arm64 多 LLC 上补 wakeup 路径 sbm 叶子更新开销数据验证 u8 判断'
  - kind: review
    description: '评估 rto_mask/dlo_mask/tick_broadcast 掩码 sbm 化可行性并回帖'
generated_at: '2026-10-04T01:00:00'
source_email_count: 2
related_articles:
  - sched-20261002-007
tags:
  - cfs
  - topology
  - nohz
---
