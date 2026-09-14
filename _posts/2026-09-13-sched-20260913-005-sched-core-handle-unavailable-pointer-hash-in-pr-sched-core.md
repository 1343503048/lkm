---
id: sched-20260913-005
date: 2026-09-13
subject: 'sched/core: Handle unavailable pointer hash in PR_SCHED_CORE_GET'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260913141040.2338964-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20260913141040.2338964-1-sh_def@163.com/
upstream_commit: null
fixes_commit: 7ac592aa35a6
merged_branch: null
current_version: v2
generated_at: '2026-09-14T10:24:00'
authors:
- Hui Su
maintainers_involved: []
patch_series:
- version: v1
  msgid: <20260913063439.1513107-1-sh_def@163.com>
  date: 2026-09-13
  summary: 传播 ptr_to_hashval() 的 -EBUSY（core_sched.c 3 行），selftest 对 EBUSY 重试至多 1s；QEMU
    熵饥饿早期启动复现 cookie 0 误报，修复后返回 EBUSY。
  review_outcome: 无回帖。
- version: v2
  msgid: <20260913141040.2338964-1-sh_def@163.com>
  date: 2026-09-13
  summary: 补丁 1 不变；selftest 把 GET 状态与 cookie 分离、致命错误经 get_cs_cookie_or_die() 中止（故障注入
    EBUSY 时 v1 会以错误哨兵继续比对出 5 failures，v2 直接中止）、最终重试后不睡眠、rebase 2f0c1cf72f46。
  review_outcome: 无回帖（发出当天零反馈）。
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无维护者评审（v2 发出当天零反馈）
  - selftest 中止语义（get_cs_cookie_or_die + __builtin_unreachable）是否符合 selftests 惯例未经确认
  next_action: 等 sched 树维护者收取或提出意见
contribution_opportunities:
- kind: review
  description: 从容器/安全工具消费者角度评审 -EBUSY 作为 PR_SCHED_CORE_GET 用户态契约的合理性
- kind: testing
  description: 在 core scheduling 生产配置上验证错误传播对启动阶段 cookie 查询工具的影响（上游仅 QEMU 熵饥饿单场景）
- kind: new_patch
  description: 产品分支若带 core scheduling，评估该 Fixes 7ac592aa35a6 修复的回合必要性
source_email_count: 6
related_articles: []
tags:
- core_sched
title: 'sched/core: Handle unavailable pointer hash in PR_SCHED_CORE_GET'
layout: article
---

## TL;DR
Hui Su 修复 PR_SCHED_CORE_GET 忽略 `ptr_to_hashval()` 的 -EBUSY 错误、在指针哈希 key 未初始化的早期启动窗口把已有 cookie 的任务误报为默认 cookie 0 的问题（Fixes 7ac592aa35a6「sched: prctl() core-scheduling interface」，Cc stable），配套 selftest 对 EBUSY 重试。同日连发 v1→v2：v2 把 selftest 的失败处理从「拿错误哨兵继续比对断言」改为「致命错误直接中止」。尚无维护者评审。经查当前主线 `kernel/sched/core_sched.c:181` 仍是忽略返回值的旧写法，该 bug 在主线真实存在。

## 背景与问题
PR_SCHED_CORE_GET 把内部 core scheduling cookie 用 `ptr_to_hashval()` 哈希成不透明用户态值。指针哈希 key 未初始化时该函数返回 -EBUSY 且不写结果，而调用点忽略返回值、`id` 初值为 0——失败被当成功返回 cookie 0。cookie 0 表示默认 core scheduling cookie，因此早期启动期间一个已带 cookie 的任务会暂时表现为默认 cookie。

作者在 x86_64 QEMU 熵饥饿早期启动复现（补丁正文原样数据）：

```
Before:
  CREATE ret=0 errno=0 (Success)
  GET ret=0 errno=0 (Success) cookie=0x0000000000000000

With patch 1:
  GET ret=-1 errno=16 (Device or resource busy)
```

未修复内核上完整 cs_prctl_test 在 PR_SCHED_CORE_CREATE 成功后、后续 GET 持续返回 cookie 0 的情况下失败 7 个 cookie 断言。影响面：早期启动 + 熵初始化未完成的时间窗，属边缘场景，但错的是 prctl ABI 语义。

## 技术方案
两个补丁：

- **sched/core: Propagate pointer hash errors from PR_SCHED_CORE_GET**（kernel/sched/core_sched.c +3/-2）：`err = ptr_to_hashval((void *)cookie, &id); if (err) goto out;`，把哈希错误传播给用户态。设计取舍明示：**不等待 RNG 初始化**——ptr_to_hashval() 已把「指针哈希 key 不可用」表达为 -EBUSY，直接经 prctl 接口暴露，让用户态自行重试。
- **selftests/sched: Retry PR_SCHED_CORE_GET on EBUSY**（cs_prctl_test.c）：EBUSY 时最多重试 1 秒（CORE_COOKIE_RETRIES=100 × CORE_COOKIE_RETRY_US=10000），其他错误立即报告（不再把一切 GET 失败都说成「Not a core sched system」）。

v2 的 selftest 结构改动是本日主要演进：GET 的系统调用状态与返回的 cookie 值分离（`get_cs_cookie(pid, &cookie)` 返回错误码），致命错误走 `get_cs_cookie_or_die()` 直接 `handle_error()` 中止——错误值永远不会再被当 cookie 比对；最后一次重试后不再 usleep。

## 版本演进与当前进展
current_version: v2（v1 与 v2 同日发出：09-13 14:34 与 22:10，北京时间）。

- v1→v2：补丁 1（内核修复）不变；selftest 在 PR_SCHED_CORE_GET 故障注入为 EBUSY 时，v1 会以错误哨兵继续执行 5 个失败的 cookie 断言，v2 直接中止不再评估断言；返回值路径改为直接返回 cookie 保持比对代码紧凑；避免最终重试后睡眠；rebase 到 2f0c1cf72f46。
- 截至当日无任何回帖，v2 刚发出。

## Maintainer 意见与讨论焦点
无维护者或社区成员回帖——两个版本发出当天即结束，本节无内容可摘。风险点（作者自述的故障注入对比）显示作者对 selftest 失败语义做过自审，但这不是外部评审信号。

## 合入评估
likelihood: unknown——干净的小修复（内核侧 3 行 + selftest），带 Fixes: 与 Cc: stable，但发出当天零反馈，无人表态即无从判断。blocking_issues：无维护者评审；selftest 的中止语义（get_cs_cookie_or_die + __builtin_unreachable）是否符合 tools/testing/selftests 的惯例未经确认。next_action：等 core scheduling 侧维护者（Peter Zijlstra / Ingo Molnar 的 sched 树）收取或提出意见。

## 效果评估
补丁正文数据（作者自述，x86_64 QEMU）：

- 熵饥饿早期启动：修复前 GET 成功但 cookie=0（错），修复后 GET 返回 -EBUSY（对，可重试）；
- 未修复内核 cs_prctl_test 失败 7 个 cookie 断言；
- v1 selftest：正常随机初始化下 `SUCCESS !!! TEST_RESULT=PASS`；故障注入 EBUSY 下 5 failures（v1 缺陷）；
- v2 selftest：正常随机初始化下 `SUCCESS !!!`；故障注入下中止而非误判。
无性能数据（正确性修复，无需）。

## 我可以参与的点
- 语义评审（review）：-EBUSY 的用户态契约是否是 core scheduling prctl 接口的合理选择（另一种方案是等待 RNG 初始化后返回真值，作者明确否掉），值得从容器/安全工具消费者角度给意见。
- 真实环境验证（testing）：在 core scheduling 生产配置（SMT 隔离 + 大量并发 CREATE/GET）的机器上验证补丁 1 的错误传播对启动阶段监控工具的影响——上游只有 QEMU 熵饥饿一个场景的数据。
- OLK/内部回合评估（new_patch）：Fixes 7ac592aa35a6 的老接口 bug + Cc stable，若产品分支带 core scheduling，可评估此修复对启动阶段 cookie 查询工具的影响并考虑回合。

## 参考链接
- lore thread（v2 cover）: https://lore.kernel.org/all/20260913141040.2338964-1-sh_def@163.com/
- v1 cover: https://lore.kernel.org/all/20260913063439.1513107-1-sh_def@163.com/
- 主线现状核实: kernel/sched/core_sched.c:181（当前主线仍忽略 ptr_to_hashval() 返回值，bug 未修）
