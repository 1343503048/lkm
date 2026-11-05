# sched/psi: let procfs copy in trigger writes

## TL;DR

- sched-20261102-009：Brauner 大型 procfs "work" 系列 v1（27 补丁）的第 17 封，把 `/proc/pressure/*` trigger 写路径从 `copy_from_user()` 改为 procfs 的 `->proc_write_buf()`，PSI 侧无功能变化。
- sched-20261105（今天）：该系列 RESEND v2（`work-procfs-fs`，30 补丁）落地，PSI 相关增至 4 封——17/30 让 procfs 拥有 pressure 文件的 seq_file、18/30 让 procfs 拷贝 trigger 写、19/30 把 pressure 文件标为 permanent、20/30 让 procfs 拥有 pressure 文件的 wait queue。仍属统一 procfs 写/开语义的大重构，无独立评审。

## 背景与问题

- sched-20261102-009：Brauner 目标是把 procfs 各文件写路径统一成「先拷贝、再 pin entry」的 `->proc_write_buf()` 约定，PSI trigger 写是调理对象之一（旧 `psi_write()` 自己 `copy_from_user`，且把前 32 字节拷进栈上 buf）。

今天 RESEND v2 进一步把 PSI 文件的「open/seq_file/wait queue」生命周期也交给 procfs：`psi_io/memory/cpu_open` 消失，`->proc_release()` 只销毁 trigger；pressure 文件被标为 permanent。PSI 侧仍是纯代码搬移，无运行时语义变化。

## 技术方案

- sched-20261102-009：实现 `->proc_write_buf()`，`psi_write()` 改接已拷贝内核缓冲，签名去掉 `__user`，只取前 31 字节、超 `PAGE_SIZE-1` 的写返回 -EINVAL。
- 今天（RESEND v2）：声明 `psi_*_show` 让 procfs open/free 各自的 seq_file（17/30）；trigger 写走 `->proc_write_buf()`（18/30）；用 `proc_create` 的 permanent 语义替代手动 keep（19/30）；wait queue 交给 procfs（20/30）。`kernel/sched/psi.c` 有 38→? 行删除（多为删 open 函数）。

## 版本演进与当前进展

*current_version: v2（RESEND，30 补丁）*。v1（27 补丁）为 11-02 的 RFC；今日为 RESEND v2，根因 11-02 后补发的修正（v2 13/51 的 psi trigger bugfix 也在同窗口，见 sched-20261105-014）。仍无针对 PSI 封的独立 review。

## Maintainer 意见与讨论焦点

无针对 PSI 封的独立表态；整体系列的讨论（procfs 写/pin 语义统一）在 fs 侧进行，PSI 部分属配套搬移。

## 合入评估

*likelihood=unknown*。作为大重构系列的组成补丁，合入取决于整个 procfs work 系列走向，短期无独立合入可能。*blocking_issues*：需等 procfs work 系列整体被目标树收取。*next_action*：跟踪 procfs work 系列主线进度。

## 效果评估

无功能变化（纯代码搬移）。

## 我可以参与的点

- review：核对 PSI 写/开路径在 `->proc_write_buf()` 与 permanent 语义下，`PAGE_SIZE-1` 上限、「只取前 31 字节」、错误码与旧实现一致。
- testing：回归 `/proc/pressure/*` 的 trigger 写入（超长/边界/空写）与 cat 读取。

## 参考链接

- lore thread（RESEND v2 18/30）: https://lore.kernel.org/all/20261104-work-procfs-fs-v2-18-319e0f9a8aae@kernel.org/
- 同系列 17/30（procfs 拥有 seq_file）: https://lore.kernel.org/all/20261104-work-procfs-fs-v2-17-319e0f9a8aae@kernel.org/

---
id: sched-20261105-015
date: 2026-11-05
subject: "sched/psi: let procfs copy in trigger writes"
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<20261104-work-procfs-fs-v2-18-319e0f9a8aae@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261104-work-procfs-fs-v2-18-319e0f9a8aae@kernel.org/"
authors: [Christian Brauner]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261102-work-procfs-fs-v1-17-d09a996317b3@kernel.org>"
    date: 2026-11-02
    summary: "procfs work RFC 27 补丁第 17 封：PSI trigger 写改走 proc_write_buf。"
    review_outcome: "无独立 review。"
  - version: v2
    msgid: "<20261104-work-procfs-fs-v2-18-319e0f9a8aae@kernel.org>"
    date: 2026-11-04
    summary: "RESEND v2 30 补丁：PSI 相关 17-20/30（seq_file/写拷贝/permanent/wait queue 交 procfs）。"
    review_outcome: "无独立 review。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "取决于 procfs work 系列整体是否被收取"
  next_action: "跟踪 procfs work 系列主线进度"
contribution_opportunities:
  - kind: review
    description: "核对 proc_write_buf 与 permanent 语义下 PSI 写/开路径与旧实现一致"
  - kind: testing
    description: "回归 /proc/pressure/* trigger 写入与读取"
generated_at: "2026-11-06T09:00:00+08:00"
source_email_count: 5
related_articles: [sched-20261102-009]
tags: [psi]
---