# sched_ext: Make ops.cpu_acquire/release() reliable

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261018-004：Kuba Piecuch 发往 `sched_ext/for-7.4` 的 RFC 五补丁——修复并「反弃用」`ops.cpu_acquire/release()`，把 CPU 可用性判定归约到 `rq->donor` 的类；RFC 首日无回帖。
- sched-20261019-015（今天）：作者本人主动回帖**重新考虑方案**——指出 v1 改了 `ops.cpu_acquire()` 语义（`ops.dispatch()` 运行时不再保证 CPU 已 acquired）、且漏掉「RT→RT 切换永不释放 CPU」的情形；提出改用一个 `__schedule()` 内的 `scx_settle_pick()` 单钩子，既能修 SCX_ENQ_IMMED 缺口、又能保留原语义，并直接征询 Tejun / Peter 是否可接受。

## 背景与问题

（承接 20261018-004）`ops.cpu_acquire/release()` 本应告知 BPF 调度器 CPU 何时可用/被收回，现状不可靠（RT 唤醒不触发 release、无上下文切换的提升不触发、投机 acquire 被高优先级类任务抢走、`cpu_released` 跨调度器残留等）。作者今日自我复盘出 v1 的两个缺陷：

1. **语义变化**：v1 把 acquire 从「`ops.dispatch()` 之前」移到「CPU 真正切到 SCX/idle」时，调度器作者惯于假设「`ops.dispatch()` 运行时 CPU 必已 acquired」，v1 打破该假设。
2. **漏掉 release 情形**：RT 任务阻塞 → `ops.dispatch()` 把 T 插入本地 DSQ → rq 锁释放 → 另一 RT 任务唤醒 → SCX pick 返回 RETRY_TASK、RT 任务胜出，这是 RT→RT 切换，CPU 从不变得可用、不触发 `ops.cpu_release()`，T 卡在本地 DSQ 直到 SCX 再被选中。标准答案 `SCX_ENQ_IMMED` 也不牢靠（`sched_setscheduler`/PI 提升、DL replenishment、CFS/RT unthrottle、ext dl_server 选 SCX、core-sched forced idle 等多条路径都不走 `wakeup_preempt()`）。

## 技术方案

今日无新补丁，作者提出 v2 方向：在 `__schedule()` 的 pick 之后加一个 SCX 单钩子

```
next = pick_next_task(rq, &rf);
rq->next_class = next->sched_class;
scx_settle_pick(rq, next);
```

以 `scx_enabled()` 与「next 类高于 ext」为门控。此时 pick 已最终确定、钩子跑在即将运行的 CPU 上（core-sched sibling 各自 settle）、被抢占的 prev 与 `ops.dispatch()` 已插入的任务都在本地 DSQ。若 `rq->scx.nr_immed` 非零则重排 IMMED 任务（修 `SCX_ENQ_IMMED`，`Fixes: 98d709cba319`）；同时 `ops.cpu_acquire()` 可回到 `dispatch_one()` 的原位（`ops.dispatch()` 之前），钩子在 pick 落在 ext 之上时释放仍 acquired 的 CPU、`args->task` 带真实选中任务——正确处理所有被放弃的 pick（RETRY_TASK、ext dl_server 返 NULL、core-sched 重启），并把 v1 加到 `put_prev_task_scx()/put_prev_task_idle()` 的 release 调用去掉。作者建议先把 IMMED 修复单独发，v2 系列基于其上 rebase。

## 版本演进与当前进展

*current_version: v1*（RFC，作者正在重塑 v2）。v1（20261018-004）→ 今日作者自我复盘两个缺陷、提出 `scx_settle_pick()` 钩子方案并征询维护者。

## Maintainer 意见与讨论焦点

暂无维护者回帖。作者直接向 Tejun Heo、Peter Zijlstra 征询「这样一个钩子是否可接受」——强调 core.c 足迹仅一行、SCX 未启用时是 static branch、out-of-line 调用仅发生在 pick 落到 ext 之上的类。这是决定 v2 走向的关键一问。

## 合入评估

*likelihood=unknown*。方案仍在作者手中重塑（v1 被作者自己部分推翻），且核心依赖维护者对 `__schedule()` 单钩子的态度，短期难定。*blocking_issues*：`scx_settle_pick()` 钩子是否被 Tejun/Peter 接受未决、v1 语义缺陷需在 v2 重构。*next_action*：等 Tejun/Peter 对钩子表态；作者拟先单发 SCX_ENQ_IMMED 修复再 rebase v2。

## 效果评估

无 benchmark，属正确性/契约语义设计。作者以具体 RT 场景（RT→RT 切换漏 release、IMMED 多路径失效）论证 v1 缺陷，未见量化数据。

## 我可以参与的点

- `discussion`：评估 `__schedule()` 内 `scx_settle_pick()` 单钩子的可行性与副作用（与 core-sched、proxy exec、dl_server 的交互），帮作者和 Tejun/Peter 收敛。
- `review`：核对作者列举的「`wakeup_preempt()` 之外改变 next_class 的路径」（setscheduler/PI、DL replenishment、unthrottle、ext dl_server、forced idle）是否穷尽。

## 参考链接

- 作者回帖（重新考虑 + 钩子提议）：https://lore.kernel.org/all/20261019144807.1207781-1-jpiecuch@google.com/
- RFC 封面信（v1）：https://lore.kernel.org/all/cover.1792248922.git.jpiecuch@google.com/

---
id: sched-20261019-015
subject: "sched_ext: Make ops.cpu_acquire/release() reliable"
date: 2026-10-19
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<cover.1792248922.git.jpiecuch@google.com>"
lore_url: "https://lore.kernel.org/all/cover.1792248922.git.jpiecuch@google.com/"
authors: ["Kuba Piecuch"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<cover.1792248922.git.jpiecuch@google.com>"
    date: 2026-10-18
    summary: "RFC 五补丁：把 cpu_acquire/release 可用性归约到 donor 类，反弃用并加 selftests"
    review_outcome: "作者今日自我复盘：语义变化 + 漏 RT→RT 释放情形，拟改 scx_settle_pick 钩子（见今）"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["scx_settle_pick 钩子是否被 Tejun/Peter 接受未决", "v1 语义缺陷需在 v2 重构"]
  next_action: "等 Tejun/Peter 对钩子表态；作者拟先单发 SCX_ENQ_IMMED 修复再 rebase v2"
contribution_opportunities:
  - kind: discussion
    description: "评估 __schedule() 内 scx_settle_pick 钩子的可行性与副作用，帮维护者收敛"
  - kind: review
    description: "核对改变 next_class 而不走 wakeup_preempt 的路径是否穷尽"
generated_at: "2026-10-20T01:30:00"
source_email_count: 1
related_articles: ["sched-20261018-004"]
tags: [sched_ext]
---