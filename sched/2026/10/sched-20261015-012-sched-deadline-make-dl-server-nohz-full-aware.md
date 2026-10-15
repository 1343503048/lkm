# sched/deadline: Make dl-server nohz full aware

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20260925-013：Juri Lelli 的「让 dl-server 感知 nohz_full」修复（v2，自 5 月未被收取）重新活跃——Ionut Nechita 发现 v2 恢复了 CFS 带宽保证但把隔离核变成满 CONFIG_HZ tick。
- sched-20261001-002：Frederic Weisbecker 提出根本性概念问题；Peter Zijlstra 给具体 review（dl-server 定时器加 PINNED、`dl_server_stop_all()` 只放 true 分支），称方向「best we can hope for」。
- sched-20261002-003：Peter 自我否决 PINNED 建议（远程 enqueue 下钉错 CPU，需尚不存在的 `hrtime_start_on()` 原语）。
- sched-20261005-003：Ionut 给出 stop-from-tick-stop 路径的可靠复现器与 `running_bw` 下溢双 WARN splats，证明 stop 必须收敛到真正停 tick 的路径。
- sched-20261013-009：Ionut 发 v3——重做机制：`sched_can_stop_tick()` 里 dl-server 只在 RT 占满时启动、`inc_dl_tasks()/dec_dl_tasks()` 补 `sched_update_tick_dependency()`，把「武装 server」与「强制 tick」解耦。
- sched-20261015-012（今天）：Juri Lelli review v3——要求 changelog 去掉历史讨论引用、认为 nohz_full 上即便「快速」hrtimer 过期也不理想、同意去掉 v2 的 bool、对 deadline 代码里直接调 `sched_update_tick_dependency()` 略感不适但可接受。

## 背景与问题
（承接 20260925-013 → 20261013-009）nohz_full 隔离核上 RT（SCHED_FIFO）与 CFS 任务共存时，dl-server 应在 RT 占满 CPU 时保证 CFS 预留带宽（fair_server 默认 50ms/1s）；但 CFS 带宽记账依赖 tick 调 `update_curr_dl_se()`，安静隔离核上 tick 完全停止导致记账缺位。v2 用「保持 tick 不停」换带宽达标，代价是满速 tick；且 enqueue/dequeue 频率上循环 start/stop server 让 `rq->dl.running_bw` 下溢触发 WARN。v3 把「武装 server」与「强制 tick」解耦：deferred server 大部分时间处于零松弛等待（throttled、off dl_rq、等 hrtimer），本不需要 tick。

## 技术方案
（承接 v3）v3 核心（`kernel/sched/core.c` +32/−1、`kernel/sched/deadline.c` +4，base tip/sched/core）：
- `sched_can_stop_tick()`：当 `rq->rt.rt_nr_running` 时，若有 CFS 队列则 `dl_server_start(&rq->fair_server)`、若有 SCX 队列则 `dl_server_start(&rq->ext_server)`；非 deferred 启动会立刻 enqueue server，随即经 `rq->dl.dl_nr_running` 复查而保持 tick。
- `inc_dl_tasks()/dec_dl_tasks()`：对 `dl_server()` 分支补 `sched_update_tick_dependency()`——server 入 dl_rq 时启动 tick、离开 dl_rq 时再停。
- 不再从 `sched_can_stop_tick()` stop server（避免 `running_bw` 下溢），teardown 交给既有的 `__pick_task_dl()` 惰性路径；代价是 tickless 核继续收 server 的 defer/inactive 定时器。

## 版本演进与当前进展
- v1/v2：见 related 文章；v2 用「保持 tick」换带宽达标，被证明副作用大。
- v3（2026-10-13，<20261013133010.390823-1-ionut.nechita@windriver.com>）：解耦机制如上。
- 今天（2026-10-15）：Juri Lelli 给出 v3 review。

## Maintainer 意见与讨论焦点
Juri Lelli（SCHED_DEADLINE 维护者）review v3 的四点：
1. **changelog**：不希望把历史讨论引用塞进 changelog，只记录当前方案做什么。
2. **hrtimer 干扰**：觉得方案「not completely ideal」——nohz_full 配置通常不想受任何干扰，即便「快速」hrtimer 过期也嫌多（且看起来无用）。
3. 同意去掉 v2 用的 bool。
4. **API 口味**：不太喜欢在 deadline 代码里调 `sched_update_tick_dependency()`，但 `add/sub_nr_running` 最终做的是一样的事，所以「maybe it's fine」。

分歧点集中在第 2 点：deferred/inactive server 定时器在 tickless 核上仍每周期几次中断，与 nohz_full 零干扰的期望存在张力。

## 合入评估
*likelihood=medium*。维护者整体接受方向（感谢发布、认可解耦与去 bool），但保留对 hrtimer 干扰的疑虑，未明确 ACK。*blocking_issues*：nohz_full 上 server 定时器干扰的疑虑未解决；changelog 需改写。*next_action*：作者按 Juri 意见改 changelog、回应 hrtimer 干扰点（论证或给出零定时器方案），再交 Juri 定夺。

## 效果评估
暂无新的量化数据。此前 v2 实测满速 tick（~200 irq_vectors/s vs fair server 关闭时 ~19/s）是核心动机；v3 的 tickless 残余中断量未见数字。

## 我可以参与的点
- *review*：评估 v3 下 tickless 核上 deferred/inactive server 定时器的实际中断频率，判断 Juri「hrtimer 干扰」顾虑的量级。
- *testing*：在 nohz_full + RT + CFS 混合负载上验证 v3 的带宽保证与中断计数。

## 参考链接
- Juri 的 review：https://lore.kernel.org/all/atDLKLaAerqK1Hhz@jlelli-thinkpadt14gen4.remote.csb/
- v3 patch：https://lore.kernel.org/all/20261013133010.390823-1-ionut.nechita@windriver.com/

---
id: sched-20261015-012
date: 2026-10-15
subject: "sched/deadline: Make dl-server nohz full aware"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261013133010.390823-1-ionut.nechita@windriver.com>"
lore_url: "https://lore.kernel.org/all/20261013133010.390823-1-ionut.nechita@windriver.com/"
authors: ["Ionut Nechita"]
maintainers_involved: ["Juri Lelli"]
current_version: v3
patch_series:
  - version: v1
    msgid: null
    date: null
    summary: "首次提出让 dl-server 感知 nohz_full"
    review_outcome: "未见收取（见 related 文章）"
  - version: v2
    msgid: null
    date: null
    summary: "用「保持 tick 不停」换取 CFS 带宽达标，副作用是满速 tick"
    review_outcome: "Peter/Frederic 提出概念问题，PINNED 建议被自我否决"
  - version: v3
    msgid: "<20261013133010.390823-1-ionut.nechita@windriver.com>"
    date: 2026-10-13
    summary: "解耦「武装 server」与「强制 tick」：sched_can_stop_tick + inc/dec_dl_tasks 补 tick dependency"
    review_outcome: "Juri Lelli 认可方向，保留 hrtimer 干扰疑虑与 changelog 意见"
upstream_commit: null
fixes_commit: "557a6bfc662c"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["nohz_full 上 server 定时器干扰的疑虑未解决；changelog 需改写"]
  next_action: "按 Juri 意见改 changelog、回应 hrtimer 干扰点后再交 Juri 定夺"
contribution_opportunities:
  - kind: review
    description: "评估 v3 下 tickless 核 server 定时器的实际中断频率，量化 hrtimer 干扰"
  - kind: testing
    description: "在 nohz_full + RT + CFS 混合负载上验证带宽保证与中断计数"
generated_at: "2026-10-16T01:05:00"
source_email_count: 1
related_articles: ["sched-20260925-013", "sched-20261001-002", "sched-20261002-003", "sched-20261005-003", "sched-20261013-009"]
tags: [deadline, dl_server, nohz]
---