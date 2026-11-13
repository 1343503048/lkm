---
id: sched-20261113-016
subject: 'sched_ext: make DSQ iterator stay drained after NULL'
date: 2026-11-13
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261110125113.2935742-1-k.chen@smail.nju.edu.cn>
lore_url: https://lore.kernel.org/all/20261110125113.2935742-1-k.chen@smail.nju.edu.cn/
authors:
- Kang Chen
maintainers_involved:
- Tejun Heo
current_version: v2
patch_series:
- version: v1
  msgid: <20261110125113.2935742-1-k.chen@smail.nju.edu.cn>
  date: 2026-11-10
  summary: 游标 flag 记 DRAINED 状态，next() 返回 NULL 后持续返回 NULL
  review_outcome: Tejun Heo Applied to sched_ext/for-7.4-fixes
- version: v2
  msgid: <20261113024505.922854-1-k.chen@smail.nju.edu.cn>
  date: 2026-11-13
  summary: 新增 dequeue_iter selftest 断言排空后恒 NULL + 注释精简
  review_outcome: 刚发出，暂无新回复
upstream_commit: null
fixes_commit: 650ba21b131e
merged_branch: sched_ext/for-7.4-fixes
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: v2 自测增补等待 Tejun 收取
contribution_opportunities:
- kind: testing
  description: 跑扩展后的 dequeue_iter 自测确认排空后 next() 恒 NULL
- kind: review
  description: 核对 DRAINED 位与用户可见 flag 位布局不冲突
generated_at: '2026-11-14T01:30:00'
source_email_count: 2
related_articles:
- sched-20261110-005
- sched-20261111-016
tags:
- sched_ext
title: 'sched_ext: make DSQ iterator stay drained after NULL'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-005-sched-ext-make-dsq-iterator-stay-drained-after-null.html">sched-20261110-005</a>：Kang Chen 修 sched_ext DSQ 迭代器的 verifier 契约违约——`bpf_iter_scx_dsq_next()` 走到队尾游标被摘除，下次调用从 DSQ 头重遍历返回同一轮第一个任务，而 verifier 依赖「next() 返回 NULL 后持续返回 NULL」契约，重启迭代会把任务指针交回 BPF 程序、verifier 却认为 R0==0。修复在游标 flag 记 drained 状态。`Fixes: 650ba21b131e`。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-016-sched-ext-make-dsq-iterator-stay-drained-after-null.html">sched-20261111-016</a>：Tejun Heo 已应用 v1 到 sched_ext/for-7.4-fixes。
- <a class="article-ref" href="/lkm/2026/11/13/sched-20261113-016-sched-ext-make-dsq-iterator-stay-drained-after-null.html">sched-20261113-016</a>（今天）：**v2 发出**——新增 dequeue_iter selftest（排空后多调一次 `bpf_iter_scx_dsq_next()` 并断言返回 NULL），并精简代码注释，其余不变。

## 背景与问题
（承接 20261110-005）`nldsq_cursor_next_task()` 遍历完会 unlink 游标并返回 NULL；之后调用 `bpf_iter_scx_dsq_next()` 见到空游标、`nldsq_next_task(dsq, NULL, rev)` 从 DSQ 头重来，老任务仍在队列里被再次返回。verifier 依赖迭代契约、一旦 next() 返回 NULL 就把迭代器置 DRAINED 并把后续返回值当常量 0——重启的迭代向 BPF 程序递交内核指针而 verifier 以为 R0==0。

## 技术方案
（承接 v1）游标 flag 加 `__SCX_DSQ_ITER_DRAINED`（`1U << 28`），`bpf_iter_scx_dsq_next()` 开头检查 `kit->dsq` 为 NULL 或 drained 位即返回 NULL，遍历返回 NULL 时置位。v2 新增：selftest `dequeue_iter` 扩展——排空后多调一次 next() 并存原始返回值，用户态断言至少迭代过一个任务且额外 next() 返回 NULL；在无该修复的内核上会失败（游标已 unlink、额外 next() 从头重来）。v2 亦缩短代码注释。

## 版本演进与当前进展
v1（20261110，已 Applied to for-7.4-fixes）→ **v2（今日）**：新增 selftest + 注释精简，逻辑不变。无维护者针对 v2 的新回帖。

## Maintainer 意见与讨论焦点
v1 已获 Tejun Heo Applied（for-7.4-fixes）。v2 仅新增自测与注释，无争议点。

## 合入评估
v1 已进 for-7.4-fixes（merged）；v2 的自测增补大概率随之跟进，合入概率高。

## 效果评估
无 benchmark；属 verifier 契约正确性修复，v2 的 selftest 提供了回归验证（无修复内核失败、有修复通过）。

## 我可以参与的点
- **testing**：在启用 sched_ext 自测的环境跑扩展后的 `dequeue_iter`，确认排空后 next() 恒 NULL。
- **review**：核对游标 `__SCX_DSQ_ITER_DRAINED` 位与现有用户可见 flag（`SCX_DSQ_ITER_REV`）的位布局不冲突。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261113024505.922854-1-k.chen@smail.nju.edu.cn/
- v1（已 Applied）: https://lore.kernel.org/all/20261110125113.2935742-1-k.chen@smail.nju.edu.cn/
