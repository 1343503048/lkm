# sched/uclamp: Reject clamp values above SCHED_CAPACITY_SCALE

## TL;DR

Andrea Parri 修复 uclamp 的 `sched_util_min/max` 取值校验漏洞：由于 `util_min/util_max` 被声明为 `int` 而 `SCHED_CAPACITY_SCALE` 为 `long`，负值与 `INT_MAX` 都能绕过 `uclamp_validate()` 的 `+1 wrap` 检查，随后被截断到 11 位但仍按完整值计算 bucket，导致非特权用户可触发 `uclamp_rq_dec_id()` 的 `WARN_ON_ONCE()`。修复为把两者改为 `unsigned int`，使 `-1` 成为唯一 wrap 的取值。

## 背景与问题

`uclamp_validate()` 的范围检查依赖 `util_min + 1 > SCHED_CAPACITY_SCALE + 1` 中 `-1`（reset 值）的 `+1` 回绕为 0。但该回绕只在无符号类型下成立——`util_min/util_max` 是 `int`、`SCHED_CAPACITY_SCALE` 是 `long`，因此**所有负值**与 `INT_MAX` 都能通过检查。`uclamp_se_set()` 把漏网值截断到 `uclamp_se::value` 的 11 位，却仍用完整值计算 bucket：一个 `0xfffff800` 的最小值被存为最高 bucket 里的 0，`uclamp_rq_max_value()` 在更高值离开 rq 后把它当成最高 active clamp，导致 rq clamp 低于剩余任务实际请求、清空其 bucket 时触发 `WARN_ON_ONCE()`（`kernel/sched/core.c` dequeue_task），**无需任何特权**。作者给出一段普通用户（cgroup 外）程序即可触发。

## 技术方案

把 `util_min/util_max` 改为 `unsigned int`，使 `-1` 成为唯一回绕取值；其后的 pair 校验显式跳过 `-1`、其余取值此时已 ≤ SCHED_CAPACITY_SCALE。此前仅因该漏洞被接受的请求现在以 `-EINVAL` 拒绝。

## 版本演进与当前进展

v1 刚发出（2026-11-02），暂无 review 意见。

## Maintainer 意见与讨论焦点

尚无表态。值得注意的是该漏洞的 PR 侧背景是 Qais Yousef 正在推进的 uclamp 竞态系列（见本窗口 `sched/uclamp: Fix race condition leading to imbalanced uclamp_rq`），两者都触及 `uclamp_rq_dec_id()` 的 `WARN_ON_ONCE`，但本补丁是独立的取值校验缺陷。

## 合入评估

likelihood=medium。修复直接、有复现与 `Fixes` 语义，但尚未指定 `Fixes:` 也没有 maintainer 回帖；需 sched 维护者确认 `unsigned int` 改动是否引入其它签名/比较隐患。

## 效果评估

作者程序：`0xfffff800` 的 `sched_util_min` 请求此前触发 `WARN_ON_ONCE`，应用补丁后以 `-EINVAL` 拒绝、告警消失。

## 我可以参与的点

- testing：在非 x86 架构（signed/unsigned 行为差异）与 cgroup 内外复跑 reproducer。
- review：核对 `sched_setattr` 其它字段（nice/prio 等）是否存在同类 int/long 混用绕过校验的问题。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261102134831.243255-1-parri.andrea@gmail.com/

---
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261102134831.243255-1-parri.andrea@gmail.com>
authors:
- Andrea Parri
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261102134831.243255-1-parri.andrea@gmail.com>
  date: '2026-11-02'
  summary: util_min/util_max 改为 unsigned int，封堵 +1 wrap 校验绕过
  review_outcome: 暂无 review
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 暂无 maintainer 回帖，Fixes 标签未标注
  next_action: 等 sched 维护者确认 unsigned int 改动无其它签名/比较副作用
contribution_opportunities:
- kind: testing
  description: 跨架构与 cgroup 内外复跑 reproducer
- kind: review
  description: 审计 sched_setattr 其它数值字段的同类型校验绕过
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles: []
tags:
- uclamp
- cfs
id: sched-20261102-002
subject: 'sched/uclamp: Reject clamp values above SCHED_CAPACITY_SCALE'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
