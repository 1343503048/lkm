# sched_ext: Prefer ___v2 kfunc names in compat.bpf.h

## TL;DR

Ihor Solodrai 的 bpf-next v2 系列之 2/6：配合 libbpf「按原型选 kfunc 变体」的新行为，让 `compat.bpf.h` 优先解析 `___v2` kfunc 名，避免 wrapper 悄悄回退到 `___v1`（如 `scx_bpf_dsq_move_to_local()` 丢掉 `enq_flags`）。bpf-ci 机器人当日复审指出一个遗漏：`__COMPAT_scx_bpf_reenqueue_local_from_anywhere()` 仍只查 `___v2___compat` 名，新版 libbpf 下可能在 v6.19+ 内核上错误返回 false，静默禁用 scx_qmap 的 sched_switch 重入队。

## 背景与问题

`compat.bpf.h` 声明 `scx_bpf_dsq_insert___v2___compat` 等名字；libbpf 会丢掉声明最后的 `___` 后缀并精确查找其余部分，从而解析出内核的 `___v2` kfunc。系列下一个 patch 让 libbpf 也丢掉内核函数名最后的后缀、按原型选择变体；于是 `___v2___compat` 名字解析不到任何东西，wrapper 静默回退到 `___v1` kfunc。

## 技术方案

改为先尝试 `___v2` 名字：带新 patch 的 libbpf 按原型解析它们；旧 libbpf 因无后缀 kfunc 原型不同而解析不到、仍解析随后跟的 `___v2___compat` 名字。改动集中在 `tools/sched_ext/include/scx/compat.bpf.h`（26 增 / 13 删行）。

## 版本演进与当前进展

*current_version: v2（2026-11-21，`<20261121003403.2928928-3-ihor.solodrai@linux.dev>`，bpf-next v2 之 2/6）*。当日收到 bpf-ci 机器人复审，指出一个遗漏点。

## Maintainer 意见与讨论焦点

- **bpf-ci（CI 机器人，非维护者）**：`__COMPAT_scx_bpf_reenqueue_local_from_anywhere()` 仍只测 `scx_bpf_reenqueue_local___v2___compat`，新版 libbpf 下该谓词在 v6.19+ 内核上会返回 false，静默关闭 scx_qmap 的 `qmap_sched_switch()` 重入队并回退到 `ops.cpu_release()`；建议谓词也检查 `scx_bpf_reenqueue_local___v2`，且两个 ksym 检查应分开分支而非 `||`（clang 可能折叠）。
- 无 NAK；属需补齐遗漏点的常规复审。

## 合入评估

*likelihood=medium*。改动小、目标明确，但需先按 bpf-ci 意见补齐 `reenqueue_local_from_anywhere` 谓词。*blocking_issues*：`__COMPAT_scx_bpf_reenqueue_local_from_anywhere()` 未检查 `___v2` 名的遗漏。*next_action*：作者补齐谓词对 `___v2` 的检查（分开分支）后由 bpf 维护者收取。

## 效果评估

无性能数据；价值在兼容层正确性——避免新 libbpf 下 wrapper 无声回退到旧 kfunc 语义（丢参数）。

## 我可以参与的点

- **review**：核对 `compat.bpf.h` 其余 `___v2___compat` 谓词是否还有同类只查 compat 名、未查 `___v2` 名的遗漏；确认分分支 vs `||` 的必要性。

## 参考链接

- lore thread（2/6）: https://lore.kernel.org/all/20261121003403.2928928-3-ihor.solodrai@linux.dev/
- bpf-ci 复审: https://lore.kernel.org/all/d76bfe6573fc2c9e4aca4d36766a3c616070ae7e@kernel.org/

---
id: sched-20261121-011
date: '2026-11-21'
subject: "sched_ext: Prefer ___v2 kfunc names in compat.bpf.h"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261121003403.2928928-3-ihor.solodrai@linux.dev>"
lore_url: "https://lore.kernel.org/all/20261121003403.2928928-3-ihor.solodrai@linux.dev/"
authors: [Ihor Solodrai]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261121003403.2928928-3-ihor.solodrai@linux.dev>"
    date: '2026-11-21'
    summary: "compat.bpf.h 优先解析 ___v2 kfunc 名，避免新 libbpf 下回退到 ___v1"
    review_outcome: "bpf-ci 指出 reenqueue_local_from_anywhere 谓词遗漏 ___v2 检查"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["__COMPAT_scx_bpf_reenqueue_local_from_anywhere() 未检查 ___v2 名"]
  next_action: "补齐谓词对 ___v2 的检查（分开分支）后由 bpf 维护者收取"
contribution_opportunities:
  - kind: review
    description: "核对 compat.bpf.h 其余 ___v2___compat 谓词是否还有同类遗漏"
generated_at: "2026-11-22T01:00:00+08:00"
source_email_count: 91
related_articles: []
tags: [sched_ext]
---