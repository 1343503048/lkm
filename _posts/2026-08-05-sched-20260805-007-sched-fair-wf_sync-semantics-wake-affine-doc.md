---
id: sched-20260805-007
date: '2026-08-05'
title: 'sched/fair: Let sync wakeups target the waker''s core'
series: Preserve wake-affine CPU for non-SMT reciprocal sync wakeups
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
- Shrikanth Hegde <shrikanth.hegde@oracle.com>
reviewers:
- Shrikanth Hegde <shrikanth.hegde@oracle.com>
- Peter Zijlstra <peterz@infradead.org>
related_articles:
- sched-20260804-006
emails:
- uid-21384@qq-imap
layout: article
---

# sched/fair: WF_SYNC 语义澄清 + 非 SMT 互为 sync wakeup 的 wake-affine 保留

## 摘要

本篇是 Prateek（AMD）与 Shrikanth（Oracle）围绕 **`WF_SYNC` 的精确语义**以及「互为 sync wakeup 的两个任务如何保持 wake-affine」展开的讨论（08-05，21384）。它与 006（sync wakeup 落到 waker core）是同一主题的两个不同切入点。

核心问题：当 A sync-wakeup B、B 又 sync-wakeup A（互为 sync，典型如 ping-pong）且二者**不在同一 SMT core** 时，现有的 wake-affine 逻辑可能因为「每次都去追 waker 的 core」而在两个不同 core 之间反复横跳，既破坏亲和性又引入迁移开销。

Shrikanth 的观点：
- 需要先在文档/注释里**明确 `WF_SYNC` 到底承诺什么**——它只表示「waker 倾向让出 CPU」，并不保证 waker 立刻 schedule；当前内核多处对 `WF_SYNC` 的解读不一致。
- 对于「非 SMT 的互为 sync wakeup」，应保留「二者被放在同一个 wake-affine CPU（或近邻）」的倾向，而不是每次都盲目追 waker core。

Prateek 回应：同意先澄清语义，并展示了一种做法——只对「waker 与 wakee 同 SMT core」的情形做「塞进 waker core」，跨 SMT 的互为 sync 则退回到既有 `wake_affine` 权重，避免横跳。

## 技术细节

`WF_SYNC` 当前用途分散：`try_to_wake_up()` 里用它决定 `select_idle_sibling` 的偏好，也影响 `wake_affine()` 的姻亲权重。但「sync 之后 waker 是否真让出」没有统一契约。

Shrikanth 提议的澄清：
```
WF_SYNC: 唤醒者意图在本轮尽快让出 CPU 给被唤醒者。
         调度器可据此把 wakee 放在 waker 附近的 idle CPU，
         但不保证 waker 立即 schedule()。
```

Prateek 的「非 SMT 互为 sync」处理（示意）：
```
if (wake_flags & WF_SYNC) {
    if (cpus_share_smt(waker_cpu, prev_cpu_of(wakee)))
        target = idle sibling of waker;   // 同 SMT，塞 waker core
    else
        target = wake_affine_weighted(wakee, waker);  // 跨 SMT，保留亲和
}
```

## 影响与风险

- 影响面：sync wakeup 的 CPU 选择，尤其 ping-pong 类负载（某些锁竞争、IPC）的稳态布局。
- 风险：中。需要先冻结 `WF_SYNC` 语义契约，否则后续 patch（含 006）都建立在漂移的定义上；改动需要保证不破坏现有 `wake_affine` 行为。
- 数据状态：本日主要是语义讨论 + 方向性代码，尚无量化对比。

## 评价

与 006 共同构成 08-04-006「sync wakeup 多子方向」的细化。建议先把 `WF_SYNC` 语义写进文档（呼应 08-04-017 的文档化主题），再分别推进 006 与本文的实现，避免实现先于契约。属于 under_review、待数据/待文档的明确参与点。
