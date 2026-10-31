---
id: sched-20261031-005
date: 2026-10-31
subject: 'sched: Add support for long task name'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <20261030-tonyk-long_name-v8-0-c9b030332254@igalia.com>
lore_url: https://lore.kernel.org/all/20261030-tonyk-long_name-v8-0-c9b030332254@igalia.com/
authors:
- André Almeida
maintainers_involved: []
current_version: v8
patch_series:
- version: v7
  msgid: <20260911-tonyk-long_name-v7-0-34e1ee1564ae@igalia.com>
  date: 2026-09-11
  summary: 修 bpf selftest 与 security/smack 编译错误
  review_outcome: 零回帖
- version: v8
  msgid: <20261030-tonyk-long_name-v8-0-c9b030332254@igalia.com>
  date: 2026-10-31
  summary: 6 片：treewide 收口 + copy_task_comm() KUnit + TASK_COMM_EXT_LEN 扩展 + prctl
    UAPI + selftest
  review_outcome: 当日零回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - v8 依旧零 review
  - task_struct 增大 48 字节无可复现数据
  - prctl UAPI 需与 man-pages/glibc 协调
  next_action: 等第一批维护者回帖；作者用全量构建矩阵自证收口完整
contribution_opportunities:
- kind: review
  description: 按缓冲区尺寸逐目录排查 treewide 收口漏网点
- kind: testing
  description: 实测 comm 16→64 的 task_struct 尺寸与 tracing 开销
generated_at: '2026-11-01T09:00:00'
source_email_count: 2
related_articles:
- sched-20260828-009
- sched-20260911-002
- sched-20260912-010
tags:
- sched_debug
title: 'sched: Add support for long task name'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/08/28/sched-20260828-009-sched-add-support-for-long-task-name.html">sched-20260828-009</a>：André Almeida 的 comm 16→64 字节系列（TASK_COMM_EXT_LEN=64、`PR_{SET,GET}_EXT_NAME`、`copy_task_comm()`）首发。
- <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-002-sched-add-support-for-long-task-name.html">sched-20260911-002</a> / <a class="article-ref" href="/lkm/2026/09/12/sched-20260912-010-sched-add-support-for-long-task-name.html">sched-20260912-010</a>：v6→v7 持续修 treewide 编译错误（security/、i915、blktrace、bpf test、smack），仍零维护者 review。
- <a class="article-ref" href="/lkm/2026/10/31/sched-20261031-005-sched-add-support-for-long-task-name.html">sched-20261031-005</a>（今天）：v8 发出（cover + 4/6 入缓存）——把 kthreads 已有的长名支持（`6b59808bfe48`）推广到用户线程，新增 64 字节的 `PR_{SET,GET}_EXT_NAME`，并引入保证 NUL 结尾的 `copy_task_comm()`。仍然无任何人类 review，卡点不变。

## 背景与问题
（承接）调试/追踪数百线程的程序时 16 字节 comm 不够；`pthread_setname_np()`/`prctl(PR_SET_NAME)` 只影响 16 字节。v8 封面明确用例：把 kthreads 在 `6b59808bfe48` 获得的「长工作名」待遇推广到用户线程。系列由 6 片组成：patch 1/2 收口 treewide 缓冲区、patch 3 为 `copy_task_comm()` 加 KUnit、patch 4 把 `current->comm` 扩到 `TASK_COMM_EXT_LEN`、patch 5 加 `prctl` 读写完整长名、patch 6 适配 selftest。

## 技术方案
（承接，接口不变）v8 核心仍是 `TASK_COMM_EXT_LEN=64` + `copy_task_comm()`（保证 NUL 结尾；作者说明不用 `strscpy()` 因为它在 tracing 路径有可测开销）。4/6 补丁标注「Changes from v5: Fix blktrace buffer size, Fix i915 buffer size」——该变更行与 v8 版本号不匹配（疑似遗留），v8 相对 v7 的完整 changelog 未在缓存中取得（cover 正文被截断）。

## 版本演进与当前进展
*current_version: v8*（2026-10-31，cover `<20261030-tonyk-long_name-v8-0-c9b030332254@igalia.com>`，当日缓存含 0/6 与 4/6，其余补丁未入缓存）。系列自 v5 起以修编译错误方式迭代；v8 当日零回帖，维护者 review 依旧为零。

## Maintainer 意见与讨论焦点
与 v5–v7 相同：当日缓存内 v8 零回帖，sched/core 与 tracing 侧维护者均未表态，未获取到任何 review 标签。系列已约 8 版、跨约 5 个月，零反馈仍是最大风险。

## 合入评估
*likelihood=unknown*（不变）：无维护者意见可依据。*blocking_issues*：零 review；`task_struct` 增大 48 字节无可复现数据；treewide 收口漏网调用点仍在暴露；`prctl` UAPI 需与 man-pages/glibc 协调。*next_action*：等第一批维护者回帖；作者用全量构建矩阵（allyesconfig/allmodconfig + 各 arch）先行自证收口完整。

## 效果评估
承前：作者沿用 v2 时 benchmark 结论「no significant change was found」，为作者主观陈述、无具体数字，第三方数据未获取到。v8 无新增数据。

## 我可以参与的点
- **review**：重点核对 patch 1/2 的 treewide 收口——此前连续暴露五处问题，按 `TASK_COMM_EXT_LEN` 引入后的缓冲区尺寸逐目录排查漏网点。
- **testing**：实测 comm 16→64 的 `task_struct` 尺寸与 ftrace/perf 采样开销，补系列一直缺失的数据。

## 参考链接
- v8 cover: https://lore.kernel.org/all/20261030-tonyk-long_name-v8-0-c9b030332254@igalia.com/
- v8 4/6: https://lore.kernel.org/all/20261030-tonyk-long_name-v8-4-c9b030332254@igalia.com/
