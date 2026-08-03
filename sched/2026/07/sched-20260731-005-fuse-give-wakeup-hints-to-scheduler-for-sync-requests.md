---
id: sched-20260731-005
date: 2026-07-31
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<20260731070102.5850-1-xuewen.yan@unisoc.com>"
lore_url: "https://lore.kernel.org/lkml/20260731070102.5850-1-xuewen.yan@unisoc.com"
authors: [Xuewen Yan]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260731070102.5850-1-xuewen.yan@unisoc.com>"
    date: 2026-07-31
    summary: "RFC: 为 fuse 同步请求添加调度器唤醒提示，通过 FR_SYNC_WAKEUP 标志位避免修改导出接口"
    review_outcome: "RFC 刚发出，暂无 review 意见"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["RFC 阶段，需要社区反馈", "Miklos 之前对接口变更有疑虑"]
  next_action: "等待 fuse 和 sched 维护者的反馈"
contribution_opportunities:
  - kind: testing
    description: "在 big.LITTLE 或不对称拓扑设备上测试 fuse 同步请求的唤醒迁移效果"
  - kind: discussion
    description: "评估 FR_SYNC_WAKEUP 标志位方案的合理性，与 WF_SYNC 的关系"
generated_at: "2026-07-31T16:30:00"
source_email_count: 1
related_articles: []
tags: [cfs, load_balance]
---

## TL;DR

Xuewen Yan (Unisoc) 发出 RFC 补丁，为 fuse 文件系统的同步请求添加调度器唤醒提示。通过在 `fuse_req->flags` 中新增 `FR_SYNC_WAKEUP` 标志位，让 fuse_dev_do_read() 在处理同步请求时使用 `wake_up_interruptible_sync()`，使调度器将唤醒目标迁移到调用者所在 CPU。在 4K 文件复制/压缩/解压工作负载上观察到约 28% 提升（13.8s → 9.9s）。

## 背景与问题

fuse 文件系统在处理同步请求时，使用普通的 `wake_up_interruptible()` 唤醒 daemon 线程。在非对称拓扑（如 big.LITTLE）上，daemon 通常运行在小核上，而请求来自大核，导致 daemon 被唤醒后仍在小核上运行，增加了跨核通信延迟。

之前的版本尝试通过给 `struct fuse_iqueue_ops` 的三个钩子添加 `bool sync` 参数来解决，但 Miklos 对接口变更有疑虑，补丁因此搁置。

## 技术方案

重新设计方案，不修改导出接口：

- 在 `fuse_req->flags`（`unsigned long` 位域）中新增 `FR_SYNC_WAKEUP` 标志位
- `__fuse_request_send()` 在调用 `fuse_send_one()` 前设置该标志
- `fuse_dev_do_read()` 检查该标志，对同步请求使用 `wake_up_interruptible_sync()`
- 导出接口保持不变，避免之前的接口争议

作者报告的效果：
- 4K 文件复制/压缩/解压工作负载：约 28% 提升（13.8s → 9.9s）
- 收益主要出现在不对称拓扑（big.LITTLE，daemon 在小核上）和小型同步请求为主的工作负载
- Miklos 之前报告在他的测试盒子上未观察到实际迁移，对称 SMP 上无回退

## 版本演进与当前进展

- **RFC**（2026-07-31）：当前版本。通过标志位而非接口参数传递同步信息

## Maintainer 意见与讨论焦点

暂无新的 review 意见。历史上 Miklos Szeredi 对修改 `fuse_iqueue_ops` 导出接口有疑虑，这是之前版本搁置的原因。当前 RFC 通过标志位方案绕过了接口变更问题。

## 合入评估

- **likelihood: unknown** — RFC 阶段，需要 fuse 和 sched 维护者反馈
- **blocking_issues**: 需要 Miklos 确认标志位方案可接受；需要 sched 维护者确认 WF_SYNC 使用合理
- **next_action**: 等待社区反馈

## 效果评估

- 4K 文件工作负载：13.8s → 9.9s（约 28% 提升），作者测试数据
- Miklos 报告在其测试盒子上未观察到 `wake_up_interruptible_sync()` 触发的实际迁移（主观判断，效果依赖拓扑）
- 对称 SMP 上无回退报告

## 我可以参与的点

- **在 big.LITTLE 设备上测试**：如果有 ARM big.LITTLE 设备，可以测试 fuse 同步请求的唤醒迁移效果
- **评估与 WF_SYNC 的关系**：当前方案使用 `wake_up_interruptible_sync()` 而非 `WF_SYNC` 标志，可以讨论两者的适用场景差异
- **更多工作负载测试**：除 4K 文件操作外，测试其他 fuse 工作负载（如 sshfs、网络文件系统场景）

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260731070102.5850-1-xuewen.yan@unisoc.com
