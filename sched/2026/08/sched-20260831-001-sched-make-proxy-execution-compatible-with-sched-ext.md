# sched: Make proxy execution compatible with sched_ext

## TL;DR

本文为增量更新（完整背景见 related_articles）。Andrea Righi 在 8/31 21:42 发出 v13（18 patch，标记 `sched_ext/for-7.4`），把 Tejun Heo 对 v12 的四类意见全部落地：新增 `WF_ON_RQ` 唤醒标志替代 `SCX_TASK_ENQ_WAKEUP`、reject DSQ 排空逻辑收进 core 并改用 `SCX_RQ_PROXY_RETRY` 跟踪待重试、把 re-enqueue reason 的生命周期从通用 DSQ unlink 原语里剥离、调度类/BPF 调度器换主时保守地先终结被保留的 donor。v13 当天刚发出、尚无新 review；18/18 已带 `Acked-by: John Stultz`。这是目前最值得盯的 cpuset/亲和性之外的调度器结构性变更之一。

## 背景与问题

proxy-exec 让处于 mutex 阻塞中的任务（donor）把调度上下文捐给 mutex owner，使 owner 能在 donor 仍留在 runqueue 上的情况下获得 CPU。当前内核里两者在**构建期互斥**：`CONFIG_SCHED_PROXY_EXEC` 带有 `depends on !SCHED_CLASS_EXT`，发行版无法用同一份内核在运行时二选一（cover letter 明确把这列为动机）。

互斥的根因是"谁在跑"这件事在两套体系下不一致：BPF 调度器通过 DSQ 与自己的 dispatch 规则驱动派发，而 proxy handoff 会执行一个 BPF 侧从未 dispatch 过的任务，于是 kfuncs/helper 看到的 `curr` 与 BPF 认为的运行任务对不上；DSQ 状态、vtime、"who is running" 记账都会与 core 实际执行结果背离。

## 技术方案

核心取舍是**把上下文一分为二**：donor 继续作为调度器可见的调度上下文（`rq->donor`），mutex owner 只是 core 内部选出的执行上下文（`rq->curr`）。cover 里把这个模型描述为"从调度器视角看像一次函数调用"——donor 的 slice/runtime 照常消耗，core 临时调用 owner 的代码推进临界区，这对 sched_ext 不是一次可见的切换，因此不会为 BPF 从未派发过的任务伪造回调。

- 能力开关：BPF 调度器通过 ops flag `SCX_OPS_ENQ_BLOCKED` 选择接受 mutex 阻塞 donor，这些 donor 会带 `SCX_ENQ_BLOCKED` 进入 `ops.enqueue()`；该 flag 要求实现 `ops.enqueue()`，把"是否/在哪/按什么顺序派发 donor"的控制权交给 BPF。不带该 flag 则等待者按普通方式阻塞，不参与 proxy-exec。
- 调度器侧取当前任务的 kfunc（`scx_bpf_task_running()`、`scx_bpf_cpu_curr()`、`scx_bpf_cid_curr()`）统一返回 donor 而非 owner。
- 回调配对：blocked donor 只有在 proxy 解析成功后才进入被跟踪的 `ops.running()/ops.stopping()` 会话，`ops.stopping()` 只对进入过该会话的任务调用。
- CPU 归属语义：donor 移交后 `wake_cpu` 仍标识 proxy 前的 CPU，`task_cpu()` 标识 proxy CPU，donor 唤醒时走正常 wakeup 路径把 prev_cpu 交回 BPF 决策。
- 换主处理（v13 收敛点）：root 调度器 enable、root↔sub-scheduler 迁移、进出 EXT 的类切换之前，一律先把被保留的 donor 完整 deactivate，让新调度器下次阻塞时按自己的接纳策略重新处理。cover 明确把"在兼容的 RT/DL PI 切换中保留 proxy 状态"列为 future work。
- 远端 DSQ 迁移：拿锁后复检 proxy 敏感状态，撞车时把任务停到源 rq 的 reject DSQ，等 proxy 解析稳定后再交回其所属 BPF 调度器；合法的 BPF 定向迁移仍会走正常校验路径报错；若有 affinity migration pending 则继续 parked。
- 辅助机制：`scx_qmap` 加 `-X` 选项（blocked donor 拿新 slice、插入按 allowed cid 与 self cid 选出的合适 local DSQ 头部，优先当前 cid，带 `SCX_ENQ_IMMED`）；新增 kselftest `enq_blocked`（同 CPU / 跨 CPU 两种拓扑，owner nice +19、donor nice -20、每 CPU 一个 nice 0 竞争者，配合 TEST_GEN_MODS_DIR 的内核模块提供 mutex）。

## 版本演进与当前进展

- v13（2026-08-31，18 patch，`<20260831134338.1531664-1-arighi@nvidia.com>`）：全部 changelog 条目标注为回应 Tejun Heo —— ① re-enqueue reason 不再侵入通用 DSQ unlink 原语，改由 `ops.enqueue()` 透传并在解析新位置前清除；② proxy-rejected 任务立即排空，仅在其仍在 running/donating 时用 `SCX_RQ_PROXY_RETRY` 请求后续重试；③ 重构 reject 处理、helper 按职责重命名，并注释说明"锁定 DSQ 迁移时刻意诊断普通 migration-disabled 任务"而非当作 proxy 竞争；④ 引入 `WF_ON_RQ` 区分"已 runnable 的唤醒"与完整激活，取代 `SCX_TASK_ENQ_WAKEUP` 跟踪，并把 sched_ext reschedule 路径门控在 proxy execution 上；⑤ 保留类切换的保守 reset。
- v12（`<20260816173732.17162-1-arighi@nvidia.com>`，链接见 v13 cover）：处理 sashiko 机器人意见——同步拒绝时保留 fresh re-enqueue reason、rq-lock 交接中途变成 migration-disabled 的任务立即处理、受保护 slice 接纳/rescue 抢占/slice 保存恢复与 bypass 全部改用 donor 调度上下文。
- v11：终结每次类/调度器换主时的 retained proxy execution，向 `sched_change_begin()` 传入 incoming class 并删除 `prepare_switch()` 类回调；拆分 reject-DSQ 代码搬移与泛化；blocked-donor 命令行选项从 `-B` 改为 `-X`（`-B` 已被 rescue bandwidth 占用）；撤掉 `SCHED_FLAG_KEEP_PARAMS` 预备修复（另发）。
- v10：在 `sched_can_stop_tick()` 中把受约束的 FAIR proxy donor 检查放到 RT 快速路径之前，避免被 throttle 的 RT owner 绕过带宽执行。
- 当前状态：v13 已发出，`init/Kconfig` 的 `depends on !SCHED_CLASS_EXT` 在 18/18 中被删除；18/18 带 `Acked-by: John Stultz`，其余补丁当天未见新 review。

## Maintainer 意见与讨论焦点

- 方向上没有人反对：Tejun Heo（sched_ext 维护者）从 v10 一路 review 到 v13，v13 的 changelog 五条全部是照他的意见改的；John Stultz（proxy-exec 早期作者）对最终解除 Kconfig 互斥的 18/18 明确 `Acked-by`。
- 未解决的分歧：Tejun 在 v12 指出 reject 路径上的 deferred work 标志其实是 **core-sched 的通用问题**（core-sched 可以 zap 掉 deferred work callback），建议引入 generic deferred work pending flag，但同时认为"那是另一个 patch series 的事"——v13 仍用 proxy 专属的 `SCX_RQ_PROXY_RETRY` 过渡，这笔技术债没有还。
- 刻意保留的限制：调度类换主时一律丢弃 proxy 状态，作者自己在 cover 里写"这条保守规则把 RT/DL PI 兼容切换下保留 proxy 状态留作未来改进"；PREEMPT_RT 仍 `depends on !PREEMPT_RT`，Kconfig 注释写的是"等修好之前先避免构建失败"。
- v13 发送时间为当天 21:42，邮件缓存内无人回帖，因此本日没有针对 v13 的实质意见。

## 合入评估

**likely**。判断依据：① 系列已迭代到 v13，且标题带 `sched_ext/for-7.4` 前缀，说明作者按 sched_ext 维护分支的目标版本在推；② 有维护者 `git://git.kernel.org/pub/scm/linux/kernel/git/arighi/linux.git scx-proxy-exec` 公开树；③ 关键 review 意见（Tejun）已被逐条落地，收尾补丁拿到 John Stultz 的 Acked-by；④ 自带可验证的 kselftest。卡点：v13 刚发出、还没有 Tejun 对新版的首轮表态；`SCX_RQ_PROXY_RETRY` 这类 proxy 专属机制是否会被要求改成通用 deferred work 尚未定；PREEMPT_RT 与多 rq proxying 仍是显式限制（Kconfig 注释"multi-rq proxying 之前该特性用处不大"）。

## 效果评估

cover 内嵌一组 `enq_blocked` kselftest 实测数据（每配置 10 次采样、16 个 contender）：

| 拓扑 | mutex_hold 变化 | mutex_wait 变化 | blocked enqueue 次数 |
|---|---|---|---|
| same-cpu | -11798366 ns（-4.48%） | -53789335 ns（**-20.41%**） | 50（全部在 donor CPU） |
| cross-cpu | -31307645 ns（-12.69%） | -31800407 ns（**-12.86%**） | 80（donor CPU 20 / owner CPU 60） |

需要提醒的是：这是**功能自测的性质数据**（打开 `SCX_OPS_ENQ_BLOCKED` 前后对比），样本只有 10 次，且 disabled 组自身 run-to-run variance 未给出；cover 中 `ok 1 enq_blocked`、`PASSED: 1 / FAILED: 0`。邮件中没有 server-side 宏观 benchmark，也没有对 NOHZ/带宽路径开销的量化数据。

## 我可以参与的点

- **回合价值评估**：该系列动的是 `kernel/sched/core.c`、`kernel/sched/ext.c`、`init/Kconfig` 三处耦合点，且 03/18 把 NOHZ CFS bandwidth 检查改为跟随 `rq->donor`——对以 cgroup cpu 带宽 + cpuset 为主的 OLK-6.6 回合，这条是最需要评估的语义变化（涉及 throttling 与 tick 停止判断），可以在 6.6 基线上先验证 `sched_can_stop_tick()` 路径的行为差异并回帖。
- **跨架构复测 `enq_blocked`**：kselftest 已进系列，缺 arm64 混合容量与大批量 CPU 机型的公开数据，跑一遍并把结果贴回线程是低成本贡献。
- **generic deferred work flag**：讨论里明确指出 reject DSQ 的延迟重试机制与 core-sched 的 zap 问题同源但被推迟为"另一个系列"，如果要做后续 patch，这是一个社区已认可、目前没人接的方向。

## 参考链接

- lore thread（v13 cover）: https://lore.kernel.org/all/20260831134338.1531664-1-arighi@nvidia.com/
- v13 收尾补丁 18/18（带 Acked-by: John Stultz）: https://lore.kernel.org/all/20260831134338.1531664-19-arighi@nvidia.com/
- v12: https://lore.kernel.org/all/20260816173732.17162-1-arighi@nvidia.com/
- 作者公开树: `git://git.kernel.org/pub/scm/linux/kernel/git/arighi/linux.git` 分支 `scx-proxy-exec`
- 上游 John Stultz 早期工作（cover 内引用）: https://lore.kernel.org/all/20251206001451.1418225-1-jstultz@google.com
- tip-bot commit: 未获取到（尚未见 tip 树收录）
- stable backport: 未获取到

---
id: sched-20260831-001
date: '2026-08-31'
subject: "sched: Make proxy execution compatible with sched_ext"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260831134338.1531664-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20260831134338.1531664-1-arighi@nvidia.com/"
authors: [Andrea Righi, John Stultz]
maintainers_involved: [Tejun Heo, John Stultz]
current_version: v13
patch_series:
  - version: v10
    msgid: "<20260728154425.1549660-1-arighi@nvidia.com>"
    date: null
    summary: "把受约束 FAIR proxy donor 的检查前置于 sched_can_stop_tick() 的 RT 快速路径；补 DEQUEUE_CLASS 预备修复"
    review_outcome: "sashiko 机器人报同步拒绝丢失 re-enqueue reason、migration-disabled 交接等问题"
  - version: v11
    msgid: "<20260810151523.86994-1-arighi@nvidia.com>"
    date: null
    summary: "类切换前终结 retained proxy execution，sched_change_begin() 传入 incoming class，删除 prepare_switch() 回调"
    review_outcome: "按 Tejun Heo 意见拆分 reject-DSQ 代码搬移与其泛化；撤回 SCHED_FLAG_KEEP_PARAMS 预备修复（另发）"
  - version: v12
    msgid: "<20260816173732.17162-1-arighi@nvidia.com>"
    date: null
    summary: "受保护 slice 接纳/rescue 抢占/slice 保存恢复与 bypass 全部改用 donor 上下文；__schedule() 中 rq->donor 变化后刷新 NOHZ tick 依赖"
    review_outcome: "Tejun 要求去掉 SCX_TASK_ENQ_WAKEUP、改传 WF_ON_RQ；reject DSQ 延迟重试与 core-sched 通用 deferred work 问题同源但推迟处理"
  - version: v13
    msgid: "<20260831134338.1531664-1-arighi@nvidia.com>"
    date: 2026-08-31
    summary: "18 patch；引入 WF_ON_RQ、reject DSQ 排空进 core 并用 SCX_RQ_PROXY_RETRY、reason 生命周期移出 DSQ unlink 原语、换主前保守 deactivate"
    review_outcome: "当天刚发出无回帖；18/18 已带 Acked-by: John Stultz"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "v13 刚发出，Tejun Heo 尚未对新版表态"
    - "reject DSQ 的 proxy 专属 SCX_RQ_PROXY_RETRY 与 core-sched 通用 deferred work 问题未合并解决，可能被要求重构"
    - "PREEMPT_RT 与 multi-rq proxying 仍是 Kconfig 显式限制"
  next_action: "等 Tejun Heo 对 v13 的首轮 review，尤其 reject 路径是否需改为通用 deferred work 机制"
contribution_opportunities:
  - kind: testing
    description: "在 arm64/混合容量与大核数机型上跑新加入的 enq_blocked kselftest 并回帖数据"
  - kind: review
    description: "评估 03/18 将 NOHZ CFS bandwidth 检查改为跟随 rq->donor 对 cgroup cpu 带宽限流语义的影响（OLK-6.6 回合前置检查）"
  - kind: extend
    description: "社区已认可但被推迟的 generic deferred work pending flag（替代 proxy 专属重试标志）可作为后续 patch 方向"
generated_at: "2026-09-07T21:16:22"
source_email_count: 19
related_articles: [sched-20260810-001, sched-20260817-001, sched-20260818-002]
tags: [sched_ext, preempt, nohz, cgroup]
---
