---
id: sched-20260805-006
date: '2026-08-05'
title: 'sched/fair: Let sync wakeups target the waker''s core'
series: Let sync wakeups target the waker's core
type: feature
status: under_review
severity: none
merge_likelihood: medium
tags:
- cfs
- load_balance
- topology
- wake_affine
authors:
- K Prateek Nayak <kprateeknayak@amd.com>
reviewers:
- Peter Zijlstra <peterz@infradead.org>
- Tim Chen <tim.c.chen@linux.intel.com>
related_articles:
- sched-20260804-006
emails:
- uid-21417@qq-imap
layout: article
---

# sched/fair: sync wakeup 让目标落到唤醒者所在 core

## 摘要

K Prateek Nayak（AMD）提出：当发生 **sync wakeup**（`WF_SYNC`，典型场景：生产者唤醒消费者、希望消费者尽快在附近跑起来）时，应让被唤醒任务的目标 CPU 优先落在**唤醒者所在的物理 core**（的空闲兄弟），而不是仅按现有 `select_idle_sibling()` 的宽泛 idle 探测去选。

动机：sync wakeup 通常意味着「唤醒者马上要让出 CPU 给被唤醒者」（如 `wake_up_sync` 后紧接 `schedule()`），二者有强协作关系。把它们放到同一物理 core 的不同 SMT 兄弟上，可以最大化共享 cache / 前端，并减少跨核迁移的唤醒延迟。

本日要点（21417）：
- Prateek 给出 patch：在 `select_idle_sibling()` 的 sync 分支里，先尝试 `waker_cpu` 所在 core 的空闲兄弟，仅在 core 内无空闲兄弟时才回退到现有 LLC 级探测。
- Peter 的质疑：**「core 内兄弟」与「LLC 内兄弟」在 SMT 拓扑下可能不一致**，需要明确 `core` 的定义（是 SMT sibling 集合，还是更大的 `mc` 域），否则在「core 边界 != LLC 边界」的 big.LITTLE / 多 LLC 平台上可能选错。
- Tim（Intel）补充：需要区分「waker 自己即将 sleep」和「waker 只是提示 sync 但继续跑」两种情况，后者把 wakee 塞到 waker 的 core 反而可能制造 SMT 争用。

## 技术细节

现有 `select_idle_sibling()` 对 `WF_SYNC` 已有一定偏好（选更近的 idle cpu），但 Prateek 的改动把它收紧到「优先 waker 的 core」：
```
if (wake_flags & WF_SYNC) {
    target = __select_idle_cpu_in_core(waker_cpu);
    if (target != -1) return target;
}
// 回退到既有 LLC 探测
```

争议点：
- `core` 粒度定义：在 `sched_domain` 拓扑里，`SMT` 域的 `span` 才是真正的 SMT 兄弟；`MC` 域通常对应 LLC。Prateek 用的是 `per_cpu(sibling_mask, waker_cpu)` 还是 `core_mask`？需明确，否则在 AMD Zen（CCX/LLC 复杂）与 ARM DynamIQ 上行为会偏。
- 与「waker 继续运行」场景的冲突：sync 只是 hint，并非保证 waker 立刻让出。需要数据证明在大多数真实 workload 下把 wakee 放进 waker core 是净收益。

## 影响与风险

- 影响面：sync wakeup 的目标 CPU 选择，影响协作型负载（pipe、IPC、某些网络栈）的唤醒延迟与 cache 局部性。
- 风险：中。改动拓扑敏感，错误定义 `core` 可能在非 uniform 拓扑上引入回退；需要多平台数据。
- 数据状态：**本日未附实测数字**，Peter 明确等一个「core 定义 + 多平台」的说明。

## 评价

是 08-04-006「sync wakeup 多子方向」讨论的延续与具体化。方向有吸引力，但「core 粒度定义」和「waker 是否真让出」两个未决点需要先解答 + 给数据，才有望推进。属于 under_review 的明确参与点（缺数据）。
