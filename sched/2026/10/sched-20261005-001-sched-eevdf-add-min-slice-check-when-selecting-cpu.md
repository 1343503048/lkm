# sched/eevdf: Add min slice check when selecting CPU

> **subject**：`sched/eevdf: Add min slice check when selecting CPU`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261002-001：Vincent Guittot 把 8 补丁 v1 扩张成 **18 补丁 v2** 重发——`select_slice_cpu()` 并入 `select_idle_capacity()` 与 `select_idle_cpu()`；系列同时吸收 lag 管理（睡眠实体正 lag 衰减、idle CPU 唤醒重置 lag）、per-cpu min_slice 缓存、wake_affine min slice 比较，并新增 fair 的 push task 机制与 feec() 重构（用 OPP cost 而非 spare capacity 选 CPU、EAS 计入 slice）。
- sched-20261005（今天）：Kayra Cizmeci 对 v2 连发三封 review（02/18、04/18、05/18），除拼写问题外各带一个实质技术点——02/18 问「Shouldn't this skip DEQUEUE_SAVE?」（lag 重置是否应跳过 DEQUEUE_SAVE 出队路径）；04/18 指出 `cfs_rq_min_slice()` 只看 rq 的 cfs_rq、跳过 dl/rt，且 cfs_rq 为空时返回 `~0ULL` 起始值直接写回，RT+fair 双 CPU 场景下行为随 prev/this 换位翻转；05/18 指出 `select_idle_cpu()` 里 nr 递减耗尽后即使找到过 slice_cpu 也未晋升为 best。另抱怨系列部分补丁缺 v2 tag 导致 b4 追踪困难。Vincent 当日未回。

## 背景与问题

（承接 sched-20261002-001）EEVDF 下短 slice 任务在 `select_task_rq_fair()` 找不到空闲 CPU 时，可能被放到已运行同长或更短 slice 任务的 CPU 上导致显著等待。v1 的 8 补丁系列「Improving latency of short slice tasks」以 `select_slice_cpu()` 在选 CPU 最后阶段加 min slice 检查；v2 扩张为 18 补丁，覆盖 lag 管理（睡眠正 lag 衰减、idle CPU 唤醒重置）、per-cpu min_slice 缓存、wake_affine min slice 比较、fair push task 机制与 feec() 重构。今天的 review 暴露的是 v2 新代码自身的边界问题：min slice 值的来源范围（cfs_rq 为空/被 RT 压制时取什么值）、以及 idle CPU 搜索预算耗尽时 slice 候选的晋升逻辑。

## 技术方案

（承接）v2 共 18 补丁（系列 cover `<20261002154415.2270586-1-vincent.guittot@linaro.org>`）：01/18 睡眠实体正 lag 衰减；02/18 idle CPU 上 enqueue 直接清零 vlag（`se->vlag_seq`/`cfs_rq->idle_seq` 序列机制）；03/18 per-cpu min_slice 缓存；04/18 wake_affine 纳入 min slice 比较；05/18 把 `select_slice_cpu()` 并入 `select_idle_capacity()` 与 `select_idle_cpu()`；06-14/18 push task 机制及其三种触发面；16/18 feec() 重构为 OPP cost；18/18 EAS 计入 slice。

今天 Kayra 的三点技术质疑（均待 Vincent 回应）：

- **02/18（Reset lag when waking up on idle cpu）**：「Shouldn't this skip DEQUEUE_SAVE?」——lag 清零发生在 enqueue 路径，但 `DEQUEUE_SAVE`（如 migration 期间的出队保存）语义上不应触发重置，疑为遗漏的过滤条件。
- **04/18（Compare min slice during wake_affine）**：`cfs_rq_min_slice()` 只遍历 rq 的 cfs_rq，跳过 dl/rt 实体；cfs_rq 为空时返回 min 的起始值 `~0ULL` 并被写回缓存。构造场景：CPU0 跑 RT 任务 TA、CPU1 跑 100ms slice 的 fair 任务 TB——若 CPU0 是 prev 则选 CPU0，否则选 CPU1，行为随换位翻转，「IDK if this is tolerated tho」。
- **05/18（Add min slice check when selecting CPU）**：域内 8 CPU、`has_idle_core=false`、`nr=4`、`sched_cluster_active=true` 时，`select_idle_cpu()` 进入 `for_each_cpu_wrap` 的 else 分支，nr 每次递减；若全程没有 idle CPU，即使中途找到过 slice_cpu 也不会 set 为 best，循环检查 3 个 CPU 后直接退出——slice 候选在预算耗尽路径上被丢弃；主循环下方同构代码同理。

## 版本演进与当前进展

- v1（09-21，8 补丁「Improving latency of short slice tasks」，sched-20260921-001）：dragonboard rb5 数据（cyclictest 99.9 分位 +14%~+25%、hackbench pipe +11%~+30%）。
- 10-02：18 补丁 v2 发出（sched-20261002-001）；当日无人 review。
- 10-05（今天）：Kayra 三连 review——`<20261004173032.18867-1-…>`（02/18，01:30）、`<20261004191817.20225-1-…>`（05/18，03:18）、`<20261005155813.25126-1-…>`（04/18，23:58）。Vincent 当日未回复。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci**（独立 reviewer，长期跟踪 EEVDF 系列）：三点实质意见（DEQUEUE_SAVE 过滤、min slice 值域范围、slice_cpu 晋升逻辑）+ 拼写订正；另反馈工具链问题——系列部分补丁无 v2 tag，b4 无法自动追踪，需手工拼 tip 分支。
- **Vincent Guittot**（作者）：当日未回。Peter Zijlstra 对 v2 本体仍无表态。
- 焦点：v2 新增代码的边界条件正确性（空 cfs_rq、无 idle CPU、DEQUEUE_SAVE）；均无分歧升级，属正常 review 轮次。

## 合入评估

*likelihood=medium*。系列方向此前已获多轮讨论推进，但 v2 体量（18 补丁）大、新增机制多，Peter 尚未介入 review；Kayra 的三点若被确认成立都需修改。*blocking_issues*：v2 无维护者 review；04/18 与 05/18 指出的行为翻转/候选丢弃问题待作者确认或反驳。*next_action*：Vincent 回应三点 review 后视情况发 v3 或逐点答复。

## 效果评估

本日无新 benchmark。既有数据（v1）：cyclictest 99.9 分位 +14%~+25%、hackbench pipe +11%~+30%（dragonboard rb5）。Kayra 的反馈为代码逻辑论证，无运行时数据。

## 我可以参与的点

- `review`：独立复核 04/18 的 RT+fair 构造场景——在本地跑一个 RT hog + 长 slice fair 任务的双 CPU 场景，验证 min slice 缓存被 `~0ULL` 污染后 wake_affine 决策是否真的换位翻转，给讨论补上可复现数据。
- `review`：核对 05/18 指出的 `select_idle_cpu()` nr 预算耗尽路径与主线既有代码（未打 v2 时）行为的差异，确认这是 v2 引入的回归还是既有行为。
- `discussion`：DEQUEUE_SAVE 问题可顺着 v2 的 02/18 补丁读 enqueue_lag 路径，给出「save 出队不应清 lag」的语义论证。

## 参考链接

- Kayra review 02/18: https://lore.kernel.org/all/20261004173032.18867-1-kayracizmeci@gmail.com/
- Kayra review 05/18: https://lore.kernel.org/all/20261004191817.20225-1-kayracizmeci@gmail.com/
- Kayra review 04/18: https://lore.kernel.org/all/20261005155813.25126-1-kayracizmeci@gmail.com/
- v2 系列 cover: https://lore.kernel.org/all/20261002154415.2270586-1-vincent.guittot@linaro.org/

---
id: sched-20261005-001
date: '2026-10-05'
subject: 'sched/eevdf: Add min slice check when selecting CPU'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20261002154415.2270586-1-vincent.guittot@linaro.org>'
lore_url: 'https://lore.kernel.org/all/20261005155813.25126-1-kayracizmeci@gmail.com/'
authors:
  - 'Vincent Guittot'
maintainers_involved:
  - 'Kayra Cizmeci'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20261002154415.2270586-1-vincent.guittot@linaro.org>'
    date: '2026-10-02'
    summary: '18 补丁 v2：min slice 选 CPU + lag 管理 + push task + feec 重构'
    review_outcome: '10-05 Kayra 三连 review：DEQUEUE_SAVE 疑漏、cfs_rq_min_slice 值域、slice_cpu 晋升逻辑'
related_articles:
  - sched-20260921-001
  - sched-20260929-018
  - sched-20261001-010
  - sched-20261002-001
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: 'v2 无维护者 review；Kayra 三点技术意见待作者回应'
  next_action: 'Vincent 回应 review 后决定 v3'
generated_at: '2026-10-06T01:00:00'
---
