---
subject: '[RFC PATCH] fuse: give wakeup hints to the scheduler for synchronous requests'
id: sched-20260806-012
date: '2026-08-06'
title: 'fuse: give wakeup hints to the scheduler for synchronous requests'
series: 'FUSE: Pass wakeup hints to the scheduler'
type: feature
status: draft
severity: none
merge_likelihood: low
tags:
- cfs
- wake_affine
authors:
- Xuewen Yan <xuewen.yan@unisoc.com>
- Miklos Szeredi <miklos@szeredi.hu>
reviewers:
- Miklos Szeredi <miklos@szeredi.hu>
related_articles:
- sched-20260805-006
emails:
- uid-23977@qq-imap
layout: article
---

# fuse: 唤醒 hint 透传给调度器（RFC，ping Miklos）

## 摘要

Xuewen Yan（Spreadtrum/紫光展锐）提交 RFC：把 **FUSE 的唤醒 hint 透传给调度器**，意图让 FUSE 的 daemon/worker 在从等待（如等待 fuse 请求完成）被唤醒时，调度器能据 hint 做出更优的唤醒 CPU 选择（类似 `WF_SYNC`/`wake_affine` 的语义扩展）。

要点：
- 本日邮件（23977 等）主要是 Xuewen **ping Miklos Szeredi**（FUSE 维护者），说明 RFC 在等待 FUSE 侧的 ack/方向确认——因为改动跨越 VFS/FUSE 与 scheduler 两个子系统，需要 FUSE 维护者先认可「在 FUSE 路径上设置唤醒 hint」的接口设计。
- 方向：在 FUSE 的 wakeup 路径（如 `fuse_wake`/请求完成回调）调用调度器的 wakeup 提示接口（如设置 `WF_SYNC` 或一个新的 hint 标志），使被唤醒的消费者/生产者更可能落在协作 CPU 上，改善 cache 局部性与延迟。

## 技术细节

RFC 思路（示意）：
```
// FUSE 请求完成，唤醒等待者时带上协作 hint
wake_up_state(waiter, TASK_NORMAL, WF_FUSE_HINT /* 或复用 WF_SYNC */);
// 调度器 select_idle_sibling 据 hint 优先 waker 近邻
```

注意：跨子系统 RFC，当前未定义最终接口（是否新增 flag、FUSE 侧如何获取「谁是协作 waker」都待定）。

## 影响与风险

- 影响面：FUSE I/O 路径的唤醒 CPU 选择；潜在改善 fuse 类负载（如 virtio-fs、用户态文件系统）的唤醒延迟与 cache 局部性。
- 风险：中—高（RFC 阶段）。跨 VFS/FUSE + scheduler 改动，需要两子系统共同认可；错误使用 hint 可能在非协作负载上引入 SMT/LLC 争用。
- 数据状态：RFC，本日仅为 ping 维护者，**无性能数据、无确认方向**。

## 评价

与 08-05-006（sync wakeup）同一「唤醒 hint / 协作 CPU 选择」主题，是用户态文件系统侧的新探索。当前仅 ping 阶段，依赖 FUSE 维护者先 ack。合入可能性低（RFC+draft），属于方向性探索，需等 FUSE 侧回应 + 补数据。
