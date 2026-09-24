---
id: sched-20260912-010
subject: 'sched: Add support for long task name'
date: '2026-09-12'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <20260911-tonyk-long_name-v7-0-34e1ee1564ae@igalia.com>
lore_url: https://lore.kernel.org/all/20260911-tonyk-long_name-v7-0-34e1ee1564ae@igalia.com/
authors:
- André Almeida
maintainers_involved: []
current_version: v7
patch_series:
- version: v6
  msgid: <20260910-tonyk-long_name-v6-0-d70afbf194c5@igalia.com>
  date: 2026-09-11
  summary: 修 security/、i915、blktrace 缓冲区与 KUnit 逻辑。
  review_outcome: 零回帖。
- version: v7
  msgid: <20260911-tonyk-long_name-v7-0-34e1ee1564ae@igalia.com>
  date: 2026-09-12
  summary: 修 bpf selftest 与 security/smack 编译错误（"for good"）。
  review_outcome: 当日缓存内零回帖，无 review 标签。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - v7 依旧零 review
  - treewide 收口漏网调用点仍在暴露（v6/v7 连修五处）
  - task_struct 增大与 prctl UAPI 的既有卡点未解
  next_action: 等第一批维护者回帖；作者用全量构建矩阵自证收口完整
contribution_opportunities:
- kind: review
  description: 按缓冲区尺寸逐目录排查 treewide 收口漏网点
- kind: testing
  description: 实测 comm 16→64 的 task_struct 尺寸与 tracing 开销
generated_at: '2026-09-14T12:40:00'
source_email_count: 2
related_articles:
- sched-20260911-002
- sched-20260828-009
tags:
- sched_debug
title: 'sched: Add support for long task name'
layout: article
---

## TL;DR
André Almeida 的 comm 16→64 字节系列发到 v7：修 bpf selftest 与 security/smack 的编译错误（cover 自嘲 "for good"）。系列自 v5 起持续以修编译错误的方式快速迭代，但仍无任何人类 review。本文为增量更新，v6 见 <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-002-sched-add-support-for-long-task-name.html">sched-20260911-002</a>，完整背景见 <a class="article-ref" href="/lkm/2026/08/28/sched-20260828-009-sched-add-support-for-long-task-name.html">sched-20260828-009</a>。

## 背景与问题
（承 <a class="article-ref" href="/lkm/2026/08/28/sched-20260828-009-sched-add-support-for-long-task-name.html">sched-20260828-009</a>/09-11-002）调试追踪数百线程的程序时 16 字节 comm 不够；系列引入 TASK_COMM_EXT_LEN=64、PR_{SET,GET}_EXT_NAME prctl、保证 NUL 结尾的 copy_task_comm()，旧用户态 API 显式截断到 16。

## 技术方案
（承前文，接口设计不变。）v7 相对 v6 的变化：「Fixed build errors (for good): bpf test and security/smack」——继续收口 treewide 改动暴露的编译问题；v6 修过 security/、i915、blktrace，v7 补 bpf selftest 与 smack。当日缓存含 v7 cover 与 4/6 补丁，其余补丁未入缓存。

## 版本演进与当前进展
*current_version: v7（cover msgid `<20260911-tonyk-long_name-v7-0-34e1ee1564ae@igalia.com>`，09-12 09:23 入缓存）*。

- v1（05-17）→ v7（09-11 发出）的完整链路见 cover 变更史；v5/v6 的分析见相关文章；
- v7（09-12 入缓存）：修 bpf test 与 security/smack 编译错误；
- 迭代模式值得注意：v6→v7 间隔约一天，均为编译错误修复，说明 treewide 收口面（patch 1/2）仍在持续暴露问题，也说明系列缺的是构建矩阵覆盖而非设计争论——但维护者 review 依旧为零。

## Maintainer 意见与讨论焦点
与 v5/v6 相同：本日缓存内 v7 零回帖，sched/core 与 tracing 侧维护者均未表态，未获取到任何 review 标签。系列已 7 版约 4 个月，零反馈仍是最大风险。

## 合入评估
*likelihood=unknown*（不变）：无维护者意见可依据。blocking_issues 承前：task_struct 增大 48 字节无可复现数据；treewide 收口的漏网调用点仍在暴露（v6/v7 连修三处+两处）；prctl UAPI 需与 man-pages/glibc 协调。*next_action*：等第一批维护者回帖；treewide 补丁建议用全量构建矩阵（allyesconfig/allmodconfig + 各 arch）先行自证。

## 效果评估
承 v6：作者沿用 v2 时 benchmark，「no significant change was found」为作者主观陈述，无具体数字，第三方数据未获取到。

## 我可以参与的点
- kind=review：重点核对 patch 1/2 的 treewide 收口——v6/v7 连续暴露 security/、i915、blktrace、bpf test、smack 五处问题，说明还有漏网概率；可按 TASK_COMM_EXT_LEN 引入后的缓冲区尺寸逐目录排查。
- kind=testing：实测 comm 16→64 的 task_struct 尺寸与 ftrace/perf 采样开销，补系列一直缺的数据（承 08-28 的验证点）。

## 参考链接
- v7 cover：https://lore.kernel.org/all/20260911-tonyk-long_name-v7-0-34e1ee1564ae@igalia.com/
- v7 4/6：https://lore.kernel.org/all/20260911-tonyk-long_name-v7-4-34e1ee1564ae@igalia.com/
- v6 cover：https://lore.kernel.org/all/20260910-tonyk-long_name-v6-0-d70afbf194c5@igalia.com/
- strscpy 开销参考 [0]：https://lore.kernel.org/lkml/20260526190625.3f4aca0a@gandalf.local.home/
