# sched_ext: Fix missing @slice and @vtime descriptions in finish_dispatch() kernel-doc

## TL;DR

luoliang@kylinos.cn 发出单 patch 修复 `finish_dispatch()` 的 kernel-doc 警告：commit 13f1eae3b662 添加了 `@slice` 和 `@vtime` 参数但未更新 kernel-doc，导致编译时产生两个 "function parameter not described" 警告。修复方式是用 `dispatch_to_local_dsq()` 中相同参数的措辞来描述。

## 背景与问题

commit 13f1eae3b662 ("sched_ext: Synchronize slice and dsq_vtime writes") 给 `finish_dispatch()` 增加了 `slice` 和 `vtime` 参数，但漏更新了 kernel-doc 注释。`W=1` 构建时产生警告：
```
Warning: function parameter 'slice' not described in 'finish_dispatch'
Warning: function parameter 'vtime' not described in 'finish_dispatch'
```

## 技术方案

在 `kernel/sched/ext/ext.c` 的 `finish_dispatch()` kernel-doc 中添加两行参数描述，措辞复用自 `dispatch_to_local_dsq()`：
- `@slice: slice carried by the insert verdict, 0 keeps the current value`
- `@vtime: vtime carried by the insert verdict, committed on PRIQ inserts`

仅修改 1 个文件，增加 2 行。

## 版本演进与当前进展

v1，刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点

暂无。

## 合入评估

- **likelihood: high** — 纯文档修复，无争议
- **blocking_issues**: 无
- **next_action**: 等待 sched_ext maintainer 捡起

## 效果评估

暂无效果数据（纯文档修复）。

## 我可以参与的点

当前阶段暂无明显参与空间，纯文档修复等待合入即可。

## 参考链接

- lore thread: 未获取到
- Fixes: 13f1eae3b662 ("sched_ext: Synchronize slice and dsq_vtime writes")
- tip-bot commit: 未获取到

---
id: sched-20260825-006
date: 2026-08-25
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "unknown"
lore_url: "unknown"
authors: [luoliang]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "unknown"
    date: 2026-08-25
    summary: "为 finish_dispatch() 补充 @slice 和 @vtime 的 kernel-doc 参数描述"
    review_outcome: "暂无 review 意见"
upstream_commit: null
fixes_commit: "13f1eae3b662"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 sched_ext maintainer 捡起"
contribution_opportunities: []
generated_at: "2026-08-27T10:00:00"
source_email_count: 1
related_articles: []
tags: [sched_ext]
---
