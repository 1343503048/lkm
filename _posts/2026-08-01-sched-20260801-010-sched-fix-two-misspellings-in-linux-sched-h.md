---
subject: sched fix two misspellings in linux sched h
id: sched-20260801-010
date: 2026-08-01
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <uid-14484@qq-imap>
lore_url: unknown
authors:
- Jiangong.Han
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <uid-14484@qq-imap>
  date: 2026-08-01
  summary: 修正 include/linux/sched.h 中的两处笔误：task_mm_cid() 注释中的 althrough 改为 although；以及
    PF_MEMALLOC_NOFS 注释中引用的函数名 memalloc_nfs_save()
  review_outcome: 当日刚发出，暂无 review 意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - patch 中 PF_MEMALLOC_NOFS 一处的改动方向存疑：diff 显示把 memalloc_nfs_save() 改成了 memalloc_nfos_save()，而实际存在的函数名应为
    memalloc_nofs_save()，疑似引入了新的拼写错误
  next_action: 作者需确认 PF_MEMALLOC_NOFS 注释的目标拼写应为 memalloc_nofs_save()，若 diff 确为 memalloc_nfos_save()
    则需发 v2 更正
contribution_opportunities:
- kind: review
  description: 核对 diff 中 memalloc_nfos_save() 的拼写并在 thread 中指出——如果这确实是笔误，一条简短回复就能避免一个错别字修复
    patch 反而引入新错别字
generated_at: '2026-08-02T00:55:00'
source_email_count: 1
related_articles: []
tags:
- sched_debug
title: sched fix two misspellings in linux sched h
layout: article
---

## TL;DR

一个仅改 2 行注释的 typo 修复 patch，但其中一处的目标拼写看起来是错的——把 `memalloc_nfs_save()` 改成了 `memalloc_nfos_save()`，而内核中实际的函数名是 `memalloc_nofs_save()`。值得回帖指出。

## 背景与问题

`include/linux/sched.h` 中有两处文字问题：

1. `task_mm_cid()` 的注释里 "althrough" 应为 "although"——单纯的英文拼写错误。
2. `PF_MEMALLOC_NOFS` 的注释里引用了一个函数名，作者认为拼写有误。

这类改动没有功能影响，属于代码可读性维护。

## 技术方案

单文件 `include/linux/sched.h`，2 处修改共 2 增 2 删。

**第一处（正确）**：

```
-	 * in user-space, althrough it won't provide the memory usage benefits.
+	 * in user-space, although it won't provide the memory usage benefits.
```

这处修改无疑问，`althrough` → `although` 正确。

**第二处（存疑）**：

```
-#define PF_MEMALLOC_NOFS	0x00040000	/* All allocations inherit GFP_NOFS. See memalloc_nfs_save() */
+#define PF_MEMALLOC_NOFS	0x00040000	/* All allocations inherit GFP_NOFS. See memalloc_nfos_save() */
```

按 diff 字面看，改动方向是 `memalloc_nfs_save()` → `memalloc_nfos_save()`。**但内核中实际存在的函数名是 `memalloc_nofs_save()`**（定义在 `include/linux/sched/mm.h`，与 `memalloc_noio_save()` 配对，命名规律为 `no` + `fs` / `no` + `io`）。相邻一行的 `PF_MEMALLOC_NOIO` 注释引用的正是 `memalloc_noio_save()`，可以对照印证这个命名规律。

也就是说：原文 `memalloc_nfs_save()` 漏了一个 `o`，确实是错的；但改成 `memalloc_nfos_save()` 是把 `o` 加错了位置，仍然不是正确的函数名。正确写法应为 `memalloc_nofs_save()`。

需要说明的是，这个判断基于对内核 mm 接口命名的了解与相邻行的对照，而非从当日邮件中直接读到——thread 中没有任何人对此发表意见。若作者本地代码树与此不同，需以实际代码为准。

## 版本演进与当前进展

v1 于 2026-08-01 20:58 发出，当日无任何 review 回复。

## Maintainer 意见与讨论焦点

**暂无相关内容**。当日无人回复。

typo 类 patch 通常由 maintainer 直接 pick 或直接忽略，很少产生讨论。但正因为 review 关注度低，一个"修错别字反而引入错别字"的 patch 有被静默合入的风险——这类改动恰恰值得有人扫一眼。

## 合入评估

合入可能性 **medium**。

第一处修改（`althrough` → `although`）本身没有任何问题，如果单独提交几乎必然被接受。

拖累整体的是第二处：如果 diff 确如所示改成了 `memalloc_nfos_save()`，那么这个 patch 修正了一个错别字的同时引入了另一个，maintainer 一旦发现就会要求重发。如果没被发现而合入，则留下一个新的错误注释。

因此下一步很明确：确认第二处的目标拼写。正确应为 `memalloc_nofs_save()`。

## 效果评估

暂无效果数据，也不需要——纯注释改动，无功能与性能影响。

## 我可以参与的点

- **Review（成本极低、价值明确）**：在 thread 中回帖指出第二处改动的拼写问题，建议改为 `memalloc_nofs_save()`，并引用相邻 `PF_MEMALLOC_NOIO` 行的 `memalloc_noio_save()` 作为命名对照。这是一条几分钟就能发出、且能实际避免错误合入的回复，对新接触邮件列表流程的人来说也是一个门槛很低的参与切入点。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
