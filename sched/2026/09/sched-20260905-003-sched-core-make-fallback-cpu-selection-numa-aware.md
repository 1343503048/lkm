# sched/core: Make fallback CPU selection NUMA-aware

## TL;DR

Yury Norov（NVIDIA）的单补丁改动 `select_fallback_rq()`：原实现先查本地节点、再按任务亲和性掩码的**数值顺序**扫描，在超过两个 NUMA 节点的系统上可能挑到比必要更远的 CPU；改成遍历调度器的 NUMA hop 掩码、每个新到达的 CPU 只考察一次，从而在整段 fallback 搜索和亲和性放宽之后都保持局部性。09-05 首发，正文里**没有 benchmark、没有 Fixes/Reported-by、当天也没有任何回帖**，属未起步的新线程。

## 背景与问题

`select_fallback_rq()` 是「任务无法放在期望 CPU」时的兜底选择（wakeup 失败、cpuset/亲和性收紧、CPU 下线等）。旧代码结构是：先在 `cpumask_of_node(cpu_to_node(cpu))` 里找允许的在线 CPU，找不到就退回 `for_each_cpu(dest_cpu, p->cpus_ptr)` 按掩码数值顺序取第一个允许的。数值顺序与拓扑距离无关，因此三节点以上系统里，本地节点没有可用 CPU 时可能直接跳到编号靠后但物理更远（hop 更多）的节点。另外旧代码还专门为「节点已下线导致 `cpu_to_node()` 返回 -1」写了分支。

## 技术方案

- 用 `for_each_numa_hop_mask(cpus, nid)` 按拓扑距离逐层遍历，配合 `for_each_cpu_andnot(dest_cpu, cpus, prev)` 保证每层只考察新到达的 CPU，天然去重；整段 hop 遍历被搬进原来的 `for(;;)` 内，所以 `cpuset → possible` 亲和性放宽后仍沿用同一局部性顺序。
- hop 掩码在拓扑重建期间可能不可用或不完整，因此在放宽亲和性**之前**额外扫描 `p->cpus_ptr & ~prev`（未被掩码覆盖的 CPU），保证这个窗口里 fallback 仍然能找到落点。
- 掩码遍历用 `rcu_read_lock()/rcu_read_unlock()` 包住（hop 掩码受 RCU 保护），`goto out` 前先解锁。
- `nid` 初始化改为 `IS_ENABLED(CONFIG_NUMA) ? cpu_to_node(cpu) : NUMA_NO_NODE`，即 !CONFIG_NUMA 时以 `NUMA_NO_NODE` 进入 hop 遍历。
- 改动局限在 `kernel/sched/core.c`，+25/-22。

## 版本演进与当前进展

- 09-05 首次投递（subject 无版本号），同日在 steal_governor 线程里仍是主力 reviewer（见 005 的 08/13 回帖）。
- 截至本日报覆盖范围（含 09-06/09-07 缓存）未见该补丁的任何回帖，也没有 tip 收树迹象。
- 与作者正在推动的 preferred-CPU/steal_governor 方向同源：v12 cover 把「NUMA Splicing：目前按 CPU 编号剔除最后一个 active 核，尚不做 NUMA 感知的拼接」列为已知限制，本补丁处理的正是同一区域里的 NUMA 局部性问题。

## Maintainer 意见与讨论焦点

**邮件正文中未获取到任何维护者回帖**，因此无法给出态度判断——这是客观上的「还没被 review」，不是「review 后沉默」。可以在正文里站得住的观察是：

- 该函数是 preferred-CPU 系列的关键依赖：v12 06/13 让 `is_cpu_allowed()` 优先挑 preferred CPU、08/13 的 push stopper 直接调用 `select_fallback_rq(rq->cpu, p)` 来找落点，且 cover letter 声称「在 `select_fallback_rq` 里会选到 preferred CPU，所以任务不会再回到这个 CPU」。也就是说 hop-mask 化的 fallback 顺序会直接改变 preferred-CPU 系列的推送落点，两件事必须先解决先后顺序。
- 值得注意的是：作者同一天在 08/13 回帖里追问的正是「`select_fallback_rq()` 拿锁后释放，到后续 `rq_lock()` 之间有竞争窗口」这一路径。本补丁给该路径新增了 RCU 临界区，两者对锁/RCU 顺序的关注是同一处代码。

## 合入评估

**likelihood: unclear。**

依据（正面）：改动小且限定单函数、语义清晰（按拓扑距离排序而非掩码数值），复用了已有的 `for_each_numa_hop_mask()` 基础设施，并且顺手处理了拓扑重建窗口这个容易被忽略的退化情形。

卡点：
1. 无 `Fixes:`、无 `Reported-by:`、无任何实测数据，维护者会按「placement 优化」而非「修复」对待，需要作者自己给出收益证据；
2. `select_fallback_rq()` 处在 wakeup/迁移兜底路径上，逐层遍历 hop 掩码 + 额外一次 `andnot` 扫描的开销未量化；
3. !CONFIG_NUMA 与 `cpu_to_node()` 返回 `NUMA_NO_NODE`（节点下线）两种情况下 `for_each_numa_hop_mask()` 的退化行为在正文里没有说明，而旧代码对后者有显式分支，这是维护者大概率会问的点；
4. 与 preferred-CPU 系列对同一函数的依赖关系需要理清（谁先进树）。

下一步预期：等维护者或 Shrikanth Hegde / Tim Chen 一线回帖；若进入 v2，大概率会补上多节点实测。

## 效果评估

邮件中未提供效果数据。补丁正文只有问题描述与实现说明，diffstat 为 `kernel/sched/core.c | 47 ++++++------`（25 insertions / 22 deletions），无 fallback 落点分布、无迁移距离、无任何 workload 数字。

## 我可以参与的点

- 直接可做的验证：在多于 2 个 NUMA 节点的机器上（4 节点最直观）比较打补丁前后 fallback 实际选中的 CPU 与其 `node_distance()`，最省事的观测是给 `select_task_rq_fair()` 的 fallback 分支加 tracepoint，或直接读 `sched:sched_stat_*` / `sched:migrate_task_rq` 判断跨了几跳——这正是补丁缺的那块证据。
- 可复核的具体代码点：`nid == NUMA_NO_NODE` 时 hop 遍历是否退化为「掩码为空」，从而完全依赖补丁新增的「掩码未覆盖 CPU」兜底；节点被 offline 后 `cpumask_of_node()`/hop 掩码的更新时序；以及 `for_each_cpu_andnot(dest_cpu, cpus, prev)` 在 `prev = cpu_none_mask` 首轮的行为。
- 与用户主线的交叉点（cpuset/cgroup）：fallback 顺序变化会影响「cpuset 收紧后任务落到哪个节点」，如果 OLK 侧做过 cpuset + 多实例 NUMA 绑定的性能基线，可以直接量化该补丁对亲和性放宽场景的影响。
- 若关心 steal_governor 回合：本补丁与 v12 06/13、08/13 改的是同一函数，回合时要一起记账，否则 preferred-CPU 推送落点语义会与上游不一致。

## 参考链接

- 补丁本体：https://lore.kernel.org/all/20260905033656.311477-1-ynorov@nvidia.com/
- 同作者对依赖该函数的 preferred-CPU 补丁的 review：https://lore.kernel.org/all/aptiJP_8SWwZWju6@yury/
- 相关代码：
  - `kernel/sched/core.c` `select_fallback_rq()` / `is_cpu_allowed()`
  - `for_each_numa_hop_mask()`
---
id: sched-20260905-003
date: '2026-09-05'
subject: 'sched/core: Make fallback CPU selection NUMA-aware'
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: '<20260905033656.311477-1-ynorov@nvidia.com>'
lore_url: https://lore.kernel.org/all/20260905033656.311477-1-ynorov@nvidia.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Yury Norov
maintainers_involved: []
patch_series:
- 'sched/core: Make fallback CPU selection NUMA-aware'
merge_assessment:
  likelihood: unclear
  blocking_issues:
  - '无 Fixes/Reported-by，也无任何实测数据，维护者会按 placement 优化对待'
  - 'select_fallback_rq() 在 wakeup 兜底路径上，hop 掩码逐层遍历开销未量化'
  - 'nid 为 NUMA_NO_NODE（!CONFIG_NUMA、节点下线）时的退化行为正文未说明'
  - '与 preferred-CPU/steal_governor 系列依赖同一函数，先后顺序未理清'
  next_action: '补多节点 fallback 落点数据或回帖确认退化行为'
contribution_opportunities:
  - '在 >2 NUMA 节点机器上量化 fallback 选中 CPU 的 node_distance/hop 数'
  - '复核 cpu_none_mask 首轮与拓扑重建窗口兜底扫描的正确性'
  - '评估 cpuset 收紧场景下 fallback 顺序变化对 NUMA 落点的影响'
source_email_count: 1
related_articles: []
tags:
- sched/core
- numa_balancing
- topology
---
