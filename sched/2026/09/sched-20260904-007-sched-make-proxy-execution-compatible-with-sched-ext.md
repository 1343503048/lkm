# sched: Make proxy execution compatible with sched_ext

## TL;DR

目前 `CONFIG_SCHED_PROXY_EXEC` 与 `CONFIG_SCHED_CLASS_EXT` 在构建期互斥。Andrea Righi 的 v13（18 补丁，标注目标分支 `sched_ext/for-7.4`）把代理执行做成 sched_ext 的可选能力：BPF 调度器通过 `SCX_OPS_ENQ_BLOCKED` 自行决定是否接收被阻塞的 donor，并统一「调度上下文呈给 sched_ext、执行上下文由 core 内部替换」这条规则。sched_ext 维护者 Tejun Heo 本日表态「大体可以、可以合进去在树内迭代」，并直接把问题抛给 Peter Zijlstra，等 Peter 拍板。

## 背景与问题

代理执行让等待中的任务（donor）把调度上下文让给 mutex owner，owner 得以前进，而 donor 仍在 runqueue 上保持可运行。两者今天不能同时开启，原因是 sched_ext 用自己的接口驱动分派：一次 proxy handoff 可能让 CPU 去跑一个 BPF 侧从未通过 DSQ 分派过的任务，于是 sched_ext 回调看到的 `current` 与 BPF 认为的「谁在跑」不一致，kfunc 与 helper 状态随之失真；DSQ 状态、vtime、「谁在运行」的记账也会与 core 实际执行的东西对不上。

对发行版和「一个内核、运行时选特性」的部署方式，这个互斥是个实际障碍。

## 技术方案

核心是把「调度上下文」与「执行上下文」的边界明确暴露给 sched_ext，而不是给 BPF 造假的回调：

- **opt-in 能力**：BPF 调度器设置 ops flag `SCX_OPS_ENQ_BLOCKED` 才保留 mutex-blocked donor 可运行并从 `ops.enqueue()` 收到带 `SCX_ENQ_BLOCKED` 的任务；该 flag 要求实现 `ops.enqueue()`，把「是否/在哪/什么顺序分派每个 donor」的控制权交给 BPF。未设置该 flag 的调度器下 mutex 等待者正常阻塞、不参与 proxy-exec。
- **上下文规则**：donor 仍是呈现给 sched_ext 的调度上下文，其调度状态、runtime 与 slice 被消耗；mutex owner 只作为 core 内部选出的执行上下文，不做「对 BPF 可见的切换」，因此不会为 BPF 未分派的任务合成 sched_ext 回调。面向调度器的 current 任务类 kfunc（`scx_bpf_task_running()`、`scx_bpf_cpu_curr()`、`scx_bpf_cid_curr()`）统一返回 donor 而非 owner。
- **回调配对**：被阻塞的 donor 只在代理解析成功后才进入被跟踪的 `ops.running()`/`ops.stopping()` 会话，`ops.stopping()` 只对进入过该会话的任务调用，与物理 `rq->curr` 解耦。
- **CPU 归属**：`wake_cpu` 继续表示 donor 进入代理前的 CPU，`task_cpu()` 表示代理 CPU；donor 唤醒时正常唤醒路径用 `wake_cpu` 作为 prev_cpu 把任务交回 BPF，由 BPF 自行决定下一次放置。
- **NOHZ**：CFS 带宽检查跟随 `rq->donor` 并用排队 FAIR 任务数判断 tick 能否停，避免受带宽约束的 FAIR donor 因为其 owner 在别的调度类可运行而失去强制。
- **所有权变更**：任何调度类或 BPF 调度器归属变更（root enable、root ↔ sub-scheduler、进出 EXT）都从干净状态开始——变更前提前完全 deactivate 被保留的 donor，由新调度器在任务下次阻塞时按自己的 admission policy 处理。这条保守规则把「兼容的 RT/DL PI 转换之间保留 proxy 状态」留作后续改进。
- **远端 DSQ 转移**：拿到源 rq 锁后重查代理敏感状态；若与代理执行竞态，任务被停在源 rq 的 reject DSQ，等代理解析结束后交回其所属 BPF 调度器（即同日 008 所讨论的 reject DSQ 泛化路径）；普通 migrate-disabled 任务仍走正常校验路径以暴露非法的 BPF 指定迁移；affinity 迁移挂起时保持停靠。

## 版本演进与当前进展

- 系列基于 John Stultz 的早期工作，已迭代到 v13（v12 于 08-16 发出，`20260816173732.17162-1-arighi@nvidia.com`）。
- v13（08-31，`20260831134338.1531664-1-arighi@nvidia.com`）的 6 条变化全部来自 Tejun Heo：re-enqueue reason 的生命周期移出通用 DSQ unlink 原语、在 `ops.enqueue()` 后保留并在新放置解析前清除；代理被拒任务立即排空，仅在任务仍在运行或仍在 donating 时用 `SCX_RQ_PROXY_RETRY` 请求稍后重试；重构 reject 处理、helper 按职责改名并说明「持锁 DSQ 转移为何故意诊断普通 migrate-disabled 任务而不是当作代理竞态」；引入 `WF_ON_RQ` 区分「已可运行的唤醒」与「完整激活」，取代 `SCX_TASK_ENQ_WAKEUP` 追踪，并把 sched_ext 的 resched 路径按代理执行门控；保持类转换时的保守 reset；`scx_qmap` 的 blocked donor 分派到合格的 self cid、优先当前 cid、对时间共享目标带 `SCX_ENQ_IMMED`，并把共享 DSQ 的重入队计入 `nr_enq_blocked`。
- 本日（09-04）Tejun 给出系列级结论并把决定权交给 Peter；同时他在 12/18 上留了 nits（见 008）。缓存中未见 Peter Zijlstra 的回复。
- 更早的相关 review：09-01 K Prateek Nayak 对 02/18 的锁范围提问，09-01 Richard Cheng（NVIDIA）对 17/18 的 `scx_qmap` CID 竞态提问。

## Maintainer 意见与讨论焦点

**Tejun Heo（sched_ext 维护者，09-04 06:51，决定性表态）**：`"Other than some nits, generally looks okay to me from sched_ext POV and it looks ready to merge and iterate in tree. Peter, what do you think?"` —— 认可方向与「先进树再迭代」的处理方式，但明确表示要 Peter Zijlstra 同意后才动。

**Peter Zijlstra**：被直接点名，缓存中未获取到回复。这是本系列当前唯一的实质闸口。

**K Prateek Nayak（AMD，09-01，对 02/18 `sched/core: Dequeue waking proxy donors before reset`）**：质疑「`TASK_WAKING` 已由 `DEQUEUE_SPECIAL` 保证把任务拦下」的前提下，为什么不能只把 `proxy_reset_donor()` 移出 blocked lock、其余保持原样；并追问「transiently re-enqueuing the waking donor」在他给出的 `__task_rq_lock` 全程持锁的写法下如何可能发生；猜测拆分的原因是 `dequeue_task_scx()` 需要正确的 `rq->donor` 引用，或 ext 要求 `dequeue_task_scx()` 总在 `put_prev_task_scx()` 之前。缓存中未见作者对此的答复。

**Richard Cheng（NVIDIA，09-01，对 17/18 `scx_ext: scx_qmap: Add proxy execution support`）**：指出 `ops.enqueue()` 与重建 `qa.self_cids.mask` 的路径之间缺序列化——`apply_partition()` 可能在检查之后、`cmask_next_and_set_wrap()` 之前清空或重建 `self_cids`；交集为空时 helper 返回的 CID 会被 `needs_immed()` 用作 `SCX_DSQ_LOCAL_ON | cid` 的下标，成为非法 CPU，建议先做 `cid < scx_bpf_nr_cids()` 检查。

**讨论焦点**：系列级的争点已从「要不要兼容」收敛到「谁承担 core 侧的改动风险」；剩余的开放技术问题是（1）代理解析与 sched_ext 回调/锁序的边界（K Prateek Nayak），（2）`scx_qmap` 示例调度器在分区重建时的 CID 有效性（Richard Cheng）。

## 合入评估

likelihood: **possible**（明显偏积极，但不由 sched_ext 维护者单方决定）。

依据：sched_ext 维护者 Tejun Heo 已给出「ready to merge and iterate in tree」的定性结论；系列已到 v13 且最后一轮改动全部是对维护者意见的落实；目标分支标签写在主题里（`sched_ext/for-7.4`），说明作者与维护者已就落点达成一致；18 个补丁中前 11 个基本是 core 侧的准备改动与 sched_ext 内部重构，风险边界清晰。

卡点：
- Peter Zijlstra 尚未表态，而本系列有相当一部分改动落在 `kernel/sched/core.c`（`WF_ON_RQ`、`sched_change_begin()` 传 next class、donor 保留/解除、NOHZ 判定），需要调度器核心维护者认可。
- Tejun 的「some nits」尚未清空，其中最具体的一条在 12/18（reject reason 清理分散、且有时被清两次，要求收敛到统一出口标签）。
- K Prateek Nayak 与 Richard Cheng 的两条提问在缓存中未见答复。
- 该系列依赖 sched_ext 的 sub-scheduler/rescue 等前序工作，与本窗口的排队顺序有耦合（邮件中未讨论）。

## 效果评估

邮件中未提供性能数据。v13 封面与补丁正文都没有吞吐/延迟基准，收益是能力性的：允许同一个内核同时构建 `CONFIG_SCHED_PROXY_EXEC` 与 `CONFIG_SCHED_CLASS_EXT`，并按调度器逐个 opt-in。封面也未附自述的测试清单（如 scx 自测、`scx_qmap -X` 之类），只有 16/18 一个 blocked donor admission 的 selftest 补丁。

需要指出的定性代价：作者明确把「兼容的 RT/DL PI 转换之间保留 proxy 状态」列为 future work，也就是说当前版本在任何调度类/调度器归属变更处都会先终止被保留的代理执行，属保守实现。

## 我可以参与的点

- **机制理解优先于跑分**：这条线决定 proxy execution 能否在 sched_ext 之上使用，属于「回合时要不要预留」的判断依据。值得先读的是封面里的两条不变式——donor 是呈现给 sched_ext 的调度上下文、owner 只是执行上下文；以及 `wake_cpu` 与 `task_cpu()` 在代理期间的分工。这与 OLK 侧任何「cgroup/cpuset 迁移 + 代理执行」的推导都要对齐。
- **可代查的具体点**：
  1. 回答/验证 K Prateek Nayak 在 02/18 的疑问：在 `__task_rq_lock` 全程持锁的前提下，把 `proxy_reset_donor()` 移出 blocked lock 是否真的会引发 donor 的瞬时重入队；这条只需读 v13 的 02/18 与 `dequeue_task_scx()`/`put_prev_task_scx()` 的调用顺序即可给出结论。
  2. 验证 Richard Cheng 在 17/18 的 CID 竞态是否成立：在 `apply_partition()` 与 `cmask_next_and_set_wrap()` 之间插入人工延时，用 `scx_qmap` 高频改分区 + 带 `-X` 的 blocked donor，观察是否出现 `SCX_DSQ_LOCAL_ON | <invalid cid>`。这个复现成本很低，回报是给作者一份现成的证据。
  3. 复核 NOHZ 判定改用「排队 FAIR 任务数」后，受 `cpu.max` 约束的 donor 与 EXT 上运行的 owner 组合下 tick 依赖是否正确（这条与 cpuset/isolcpus 场景直接相关，也可设计验证用例）。
- **可补的验证**：构建 `CONFIG_SCHED_PROXY_EXEC=y` + `CONFIG_SCHED_CLASS_EXT=y` 的内核，跑 scx 自测与 `scx_qmap`，把覆盖到的 config 组合与结果回帖；本系列缺的就是这类树外验证证据。

## 参考链接

- 邮件线程：
  - v13 cover letter: <https://lore.kernel.org/all/20260831134338.1531664-1-arighi@nvidia.com/>
  - Tejun Heo 的系列级表态: <https://lore.kernel.org/all/apn6AdgyTr0btXDS@slm.duckdns.org/>
  - Tejun Heo 在 12/18 上的 nits: <https://lore.kernel.org/all/apn3GHPzhPZtGbSs@slm.duckdns.org/>
  - K Prateek Nayak 对 02/18 的提问: <https://lore.kernel.org/all/3d4116ff-0634-4ab6-be24-0bd2c68f1698@amd.com/>
  - Richard Cheng 对 17/18 的提问: <https://lore.kernel.org/all/apaDOhiWKcLH5iQt@MWDK4CY14F/>
  - v12 cover letter（上一版）: <https://lore.kernel.org/all/20260816173732.17162-1-arighi@nvidia.com/>
- 相关文章/系列：
  - [[sched-20260902-001]] Proxy Exec 批合入 tip（主线起点）。
  - [[sched-20260904-008]] 本系列 12/18（reject DSQ 泛化）的讨论详情。
- 相关代码/commit：
  - `kernel/sched/ext/ext.c` / `kernel/sched/ext/sub.c` / `kernel/sched/core.c`
  - `SCX_OPS_ENQ_BLOCKED` / `SCX_ENQ_BLOCKED` / `SCX_RQ_PROXY_RETRY` / `WF_ON_RQ`
  - `scx_bpf_task_running()` / `scx_bpf_cpu_curr()` / `scx_bpf_cid_curr()`

---
id: sched-20260904-007
date: '2026-09-04'
subject: 'sched: Make proxy execution compatible with sched_ext'
subsystem: sched
type: discussion
status: under_review
severity: high
thread_root_msgid: 20260831134338.1531664-1-arighi@nvidia.com
lore_url: https://lore.kernel.org/all/20260831134338.1531664-1-arighi@nvidia.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v13
generated_at: '2026-09-07'
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
patch_series:
- 'sched/core: Drop mutex locks before proxy rescheduling'
- 'sched/core: Dequeue waking proxy donors before reset'
- 'sched: Make NOHZ CFS bandwidth checks follow proxy donor'
- 'sched/core: Avoid false migration warning for proxy donors'
- 'sched: Pass next class to sched_change_begin()'
- 'sched: Add helper to block retained proxy donors'
- 'sched: Add sched_ext hooks for proxy execution'
- 'sched: Introduce WF_ON_RQ wake flag'
- 'sched_ext: Block proxy donors across scheduler transitions'
- 'sched_ext: Fix ops.running/stopping() pairing for proxy-exec donors'
- 'sched_ext: Move reject DSQ draining into core'
- 'sched_ext: Generalize the reject DSQ reenqueue path'
- 'sched_ext: Handle proxy-exec races in remote DSQ transfers'
- 'sched_ext: Split curr|donor references properly'
- 'sched_ext: Delegate proxy donor admission to BPF schedulers'
- 'sched_ext: Add selftest for blocked donor admission'
- 'sched_ext: scx_qmap: Add proxy execution support'
- 'sched: Allow enabling proxy exec with sched_ext'
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter Zijlstra 被 Tejun 点名后尚未表态，而系列大量改动落在 kernel/sched/core.c
  - Tejun 的 nits 未清空，最具体一条在 12/18（reject reason 清理分散且重复，要求统一出口标签）
  - K Prateek Nayak（02/18 锁范围）与 Richard Cheng（17/18 CID 竞态）的提问未见答复
  - RT/DL PI 转换保留 proxy 状态被明确留作后续改进，当前实现偏保守
  next_action: 等 Peter Zijlstra 的表态；作者侧需先回应 12/18 的 nits 与两条未答复的 review 提问。若进入排队，18/18（解除构建互斥）应是最后合入的一片。
contribution_opportunities:
- 验证 02/18：__task_rq_lock 全程持锁下 proxy_reset_donor() 移出 blocked lock 是否仍会瞬时重入队
- 复现 17/18：apply_partition() 与 cmask_next_and_set_wrap() 之间的 CID 有效性竞态（建议的 cid < scx_bpf_nr_cids() 检查）
- 构建 PROXY_EXEC + EXT 同时开启的内核跑 scx 自测，回帖给出覆盖的 config 组合
- 复核 NOHZ tick 依赖改用排队 FAIR 任务数后，cpu.max 受限 donor + EXT owner 组合的正确性
source_email_count: 2
related_articles:
- sched-20260902-001
tags:
- sched_ext
- proxy_execution
---
