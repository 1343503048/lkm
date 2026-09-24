---
id: sched-20260911-002
subject: 'sched: Add support for long task name'
date: '2026-09-11'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <20260910-tonyk-long_name-v6-0-d70afbf194c5@igalia.com>
lore_url: https://lore.kernel.org/all/20260910-tonyk-long_name-v6-0-d70afbf194c5@igalia.com/
authors:
- André Almeida
maintainers_involved: []
current_version: v6
patch_series:
- version: v5
  msgid: <20260827-tonyk-long_name-v5-0-5fa843782a00@igalia.com>
  date: 2026-08-28
  summary: comm 扩到 TASK_COMM_EXT_LEN=64，旧 UAPI 显式截断，新增 PR_{SET,GET}_EXT_NAME + copy_task_comm()
    + KUnit + selftests。
  review_outcome: 截至 09-05 无任何回帖，无 review 标签。
- version: v6
  msgid: <20260910-tonyk-long_name-v6-0-d70afbf194c5@igalia.com>
  date: 2026-09-11
  summary: 修 security/ 编译错误；修 i915（%.*s 限宽）与 blktrace/intel_display_driver 缓冲区尺寸；修
    KUnit 测试逻辑。
  review_outcome: 当日缓存内零回帖，无 review 标签。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - v6 依旧零 review，sched/core 与 tracing 侧维护者未表态
  - task_struct 增大 48 字节无可复现数据
  - patch 1/2 treewide 改动需多子系统 ack
  - 新增 prctl UAPI 需与 man-pages/glibc 协调
  next_action: 等第一批维护者回帖；作者补 task_struct 尺寸与 tracing 开销数据
contribution_opportunities:
- kind: testing
  description: 实测 comm 16→64 的 task_struct 尺寸与 ftrace/perf 采样开销，补数据
- kind: review
  description: 排查 treewide 收口（get_task_comm/memcpy 替换）是否仍有漏网调用点
- kind: discussion
  description: 就长名字是否体现在 /proc/PID/comm 给出使用场景与立场
generated_at: '2026-09-14T11:35:00'
source_email_count: 2
related_articles:
- sched-20260828-009
tags:
- sched_debug
title: 'sched: Add support for long task name'
layout: article
---

## TL;DR
André Almeida（Igalia）把线程名从 16 字节扩展到 TASK_COMM_EXT_LEN=64 的系列发布 v6：新增 PR_{SET,GET}_EXT_NAME prctl 接口 + 保证 NUL 结尾的 copy_task_comm() helper，旧用户态 API 显式截断到 TASK_COMM_LEN。本文为增量更新，完整背景见 sched-20260828-009（v5）：v6 修复了 security/ 编译错误、i915/blktrace 缓冲区尺寸与 KUnit 测试逻辑；系列从 v5 到 v6 依旧零 review。

## 背景与问题
调试/追踪数百线程的复杂程序时，16 字节 comm 不够用；pthread_setname_np()/prctl(PR_SET_NAME) 设置的名字受此限制，而 cmdline 不受。作者希望给用户态线程对齐 kthreads 已有的待遇（commit 6b59808bfe48 让 /proc/PID/{comm,stat,status} 显示最新 workqueue 名）。直接放大 comm 会带来缓冲区溢出风险与 tracing 开销，因此系列同时引入收口措施。

## 技术方案
- patch 1/2（treewide）：清退 get_task_comm() 直接调用、把 memcpy(..., current->comm) 换成 copy_task_comm()，为 comm 变长做准备；
- copy_task_comm()：能用 memcpy 时用 memcpy，否则回退 strscpy()，保证目标缓冲 NUL 结尾——作者引用 [0] 说明 strscpy 在 tracing 路径有可测开销，故不直接全用 strscpy；
- patch 3：为 copy_task_comm() 加 KUnit 测试；
- patch 4：current->comm 扩到 TASK_COMM_EXT_LEN=64，所有既有用户态 API（/proc、i915、blktrace 等）显式截到 TASK_COMM_LEN=16；v6 修正 i915 gem context 的 snprintf 用 `%.*s` 限宽、blktrace 与 intel_display_driver 缓冲区按 EXT_LEN 调整；
- patch 5：新增 prctl PR_{SET,GET}_EXT_NAME 读写完整 64 字节名字；
- patch 6：扩展 selftests/prctl/set-process-name.c 覆盖新接口。

## 版本演进与当前进展
*current_version: v6（cover msgid `<20260910-tonyk-long_name-v6-0-d70afbf194c5@igalia.com>`，09-11 00:49 入缓存）*。

- v1（2026-05-17）→ v2：新增 copy_task_comm()（memcpy 优先 + NUL 保证）与 KUnit 测试；
- v3：简化 copy_task_comm() 为 memcpy + 末尾置 NUL；
- v4：copy_task_comm() 只用于 task_struct，补 len 边界检查；
- v5（08-27）：helper 限定到 task_struct 并补 len 检查（详见 sched-20260828-009）；
- v6（09-10 发出）：修 security/ 编译错误；修 i915 与 blktrace 的 comm 缓冲区尺寸；修 KUnit 测试逻辑。

## Maintainer 意见与讨论焦点
- 与 v5 时相同：本日缓存内 v6 没有收到任何回帖，sched/core 与 tracing 侧维护者均未表态，未获取到任何 Reviewed-by/Acked-by。系列已迭代 6 版约 4 个月，零反馈本身是最大的争议点。

## 合入评估
*likelihood=unknown*：没有任何维护者意见可依据。*blocking_issues*：v6 依旧零 review；task_struct 增大 48 字节只有一句「no significant change」、无可复现数据；patch 1/2 是 treewide 改动需要 drm/audit/LSM/net/tracing 等多方 ack；新增 prctl UAPI 需与 man-pages/glibc 协调（均承 sched-20260828-009，当日缓存无新信息解除或加重这些卡点）。*next_action*：等待第一批维护者回帖；作者侧需补 task_struct 尺寸与 tracing 开销数据。

## 效果评估
作者在 v6 cover 中重申：沿用 v2 时报告的 benchmark（[0] 20260526190625.3f4aca0a），「no significant change was found」——即 comm 16→64 无可测开销，但这是作者主观陈述，具体数字未在邮件中给出，第三方数据未获取到。

## 我可以参与的点
- kind=testing：实测 comm 扩到 64 后 task_struct 尺寸变化与 ftrace/perf sched 采样开销，补上系列一直缺的数据（v5 分析中已提出，v6 仍缺）。
- kind=review：评审 patch 1/2 的 treewide 收口是否有漏网调用点（v6 刚修过 security/、i915、blktrace 三处，说明该面仍在暴露问题）。
- kind=discussion：就「长名字是否应同时体现在 /proc/PID/comm」给出使用场景与立场（此前提出的开放问题，无人回应）。

## 参考链接
- v6 cover letter：https://lore.kernel.org/all/20260910-tonyk-long_name-v6-0-d70afbf194c5@igalia.com/
- v6 4/6（sched: Extend task command name with TASK_COMM_EXT_LEN）：https://lore.kernel.org/all/20260910-tonyk-long_name-v6-4-d70afbf194c5@igalia.com/
- v5 cover：https://lore.kernel.org/all/20260827-tonyk-long_name-v5-0-5fa843782a00@igalia.com/
- strscpy 开销参考 [0]：https://lore.kernel.org/lkml/20260526190625.3f4aca0a@gandalf.local.home/
