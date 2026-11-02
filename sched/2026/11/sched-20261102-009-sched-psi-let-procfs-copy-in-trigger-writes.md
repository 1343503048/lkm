# sched/psi: let procfs copy in trigger writes

## TL;DR

Christian Brauner 的大型 procfs "work" RFC 系列（27 patches，v1）中的第 17 封，把 `/proc/pressure/*`（PSI trigger）的写路径从 `copy_from_user()` 改为 procfs 的 `->proc_write_buf()`：由 procfs 在 pin entry 之前拷贝写入内容，PSI 写函数只处理已有内核缓冲区。属于「把 procfs 写语义统一搬进 VFS」的重构的一部分，PSI 侧无功能变化（历史上只用到前 31 字节；超过 PAGE_SIZE-1 的写现在返回 -EINVAL）。

## 背景与问题

Brauner 的 RFC 目标是把 procfs 各文件的写路径统一成「先拷贝、再 pin entry」的新 `->proc_write_buf()` 约定，从而让 procfs 的 pin 语义更安全一致。PSI 的 `/proc/pressure/{cpu,memory,io}` trigger 写是其中的调理对象之一：旧的 `psi_write()` 自己 `copy_from_user`（还把前 32 字节拷进栈上 buf）。

## 技术方案

实现 `->proc_write_buf()`，`psi_write()` 改成接收已拷贝的内核缓冲区 `kbuf`、`memcpy` 进栈上 buf；`psi_io/memory/cpu_write` 的签名相应去掉 `__user`。仅看前 31 字节（历史如此），大于 `PAGE_SIZE-1` 的写返回 -EINVAL。`kernel/sched/psi.c` +19/−21。

## 版本演进与当前进展

v1（RFC，2026-11-02），是整个 27-patch 系列的一部分（本窗口只收到本封 sched/psi 相关）。暂无针对本封的独立 review。

## Maintainer 意见与讨论焦点

无针对 PSI 封的独立表态；整体系列仍在 RFC 讨论期。

## 合入评估

likelihood=unknown。作为大重构 series 的组成 patch，合入取决于整个 procfs work 系列的走向，短期无独立合入可能。

## 效果评估

无功能变化；作者说明历史上只用到前 31 字节。

## 我可以参与的点

- review：核对 PSI trigger 写路径新语义下 `PAGE_SIZE-1` 上限与「只读前 31 字节」的行为是否与旧实现完全一致（含错误码）。
- testing：回归 `/proc/pressure/*` trigger 的写入（超长、恰好边界、空写）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261102-work-procfs-fs-v1-17-d09a996317b3@kernel.org/

---
type: feature
status: rfc
severity: none
thread_root_msgid: <20261102-work-procfs-fs-v1-17-d09a996317b3@kernel.org>
authors:
- Christian Brauner
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261102-work-procfs-fs-v1-17-d09a996317b3@kernel.org>
  date: '2026-11-02'
  summary: PSI trigger 写路径切换到 procfs 的 ->proc_write_buf()
  review_outcome: 暂无独立 review（大系列 RFC 期）
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 依赖整个 procfs work RFC 系列的走向
  next_action: 跟随 procfs work 系列整体评审推进
contribution_opportunities:
- kind: review
  description: 核对 trigger 写路径新旧行为与错误码一致性
- kind: testing
  description: 回归 /proc/pressure trigger 写（超长/边界/空写）
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles: []
tags:
- psi
id: sched-20261102-009
subject: 'sched/psi: let procfs copy in trigger writes'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
