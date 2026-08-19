# sched ext fix stale cgroup id in sched ext ops kernel doc

## TL;DR

Liang Luo (Kylinos) 修复 sched_ext_ops 结构体的 kernel-doc 注释：`@cgroup_id` 应更新为 `@sub_cgroup_id` 以匹配实际成员名。此不一致导致两个 kernel-doc 警告。单行修复，合入可能性高。

## 背景与问题

sched_ext_ops 结构体中的 `sub_cgroup_id` 成员在之前的重命名中从 `cgroup_id` 改为 `sub_cgroup_id`，但 kernel-doc 注释未同步更新，导致：

```
Warning: struct member sub_cgroup_id not described in sched_ext_ops
Warning: Excess struct member cgroup_id description in sched_ext_ops
```

## 技术方案

将 `kernel/sched/ext/internal.h` 中 `@cgroup_id:` 改为 `@sub_cgroup_id:`，单行修改。

## 版本演进与当前进展

- **v1**（2026-07-31）：刚发出，暂无 review 意见

## Maintainer 意见与讨论焦点

暂无。

## 合入评估

- **likelihood: high** — 纯文档修复，消除编译警告，无争议

## 效果评估

暂无效果数据。消除 kernel-doc 构建警告。

## 我可以参与的点

当前阶段暂无明显参与空间。

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260731023004.1062947-1-luoliang@kylinos.cn

---
subject: "sched ext fix stale cgroup id in sched ext ops kernel doc"
id: sched-20260731-004
date: 2026-07-31
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20260731023004.1062947-1-luoliang@kylinos.cn>"
lore_url: "https://lore.kernel.org/lkml/20260731023004.1062947-1-luoliang@kylinos.cn"
authors: [Liang Luo]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260731023004.1062947-1-luoliang@kylinos.cn>"
    date: 2026-07-31
    summary: "将 sched_ext_ops 的 kernel-doc 中过时的 @cgroup_id 更新为 @sub_cgroup_id"
    review_outcome: "v1 刚发出，暂无 review 意见"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 review"
contribution_opportunities: []
generated_at: "2026-07-31T16:30:00"
source_email_count: 1
related_articles: []
tags: [sched_ext, sched_debug]
---
