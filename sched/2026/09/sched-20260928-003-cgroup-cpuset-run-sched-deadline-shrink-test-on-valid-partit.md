# cgroup/cpuset: Run SCHED_DEADLINE shrink test on valid partition root only

## TL;DR

Waiman Long 修复 cpuset 里 SCHED_DEADLINE 带宽收缩检查的误触发——当 CS_CPU_EXCLUSIVE 标志被错误地设在并非有效 partition root 的 cpuset 上时，`validate_change()` 的 shrink 测试会在存在 deadline 任务的系统里被误触发，导致改 cpuset 控制文件时意外返回 `-EBUSY`。v1 发出后当天即出 v2，已获 Reviewed-by（Guopeng Zhang），方向明确、待维护者收取。

## 背景与问题

（bug/fix 类）commit f82f80426f7a（"sched/deadline: Ensure that updates to exclusive cpusets don't break AC"）在 `validate_change()` 里加了检查：收缩带 CS_CPU_EXCLUSIVE 的 v1 exclusive cpuset 时，要确保有足够带宽容纳 SCHED_DEADLINE 任务。引入 cgroup v2 的 cpuset partition 后，代码继续给 partition root 设 CS_CPU_EXCLUSIVE 以让该检查在 v2 下继续工作，但实现不完善：存在 cpuset 并不是有效 partition root、exclusive 标志却仍被错误置位的情况。后果是系统里有 deadline 任务时，SCHED_DEADLINE 检查被误触发，改动 cpuset 控制文件会得到意外的 `-EBUSY` 失败。

## 技术方案

修复思路：让 shrink 测试只在有效 partition root 上触发，并移除 v2 代码里已经不需要的 exclusive 标志处理。v2 按评审意见**不改动 v1 代码**，改用「v1 用 `is_cpu_exclusive()`、v2 用 `is_partition_valid()`」的判据切换：核心条件从 `is_cpu_exclusive(cur) && is_sched_load_balance(cur)` 改为 `(is_partition_valid(cur) || (!cpuset_v2() && is_cpu_exclusive(cur))) && is_sched_load_balance(cur)`。

## 版本演进与当前进展

*current_version: v2*。v1（28 日 00:34）把 v1 相关检查拆回 `cpuset1_validate_change()` 并引入 `is_in_v2_mode()`/`cpuset_v2()` 守卫；v2（28 日 05:53）在评审建议下收敛为「v1 代码原样保留，仅切换 v1/v2 的判据函数」，改动更小、更聚焦。

## Maintainer 意见与讨论焦点

- **Guopeng Zhang**：给出 `Reviewed-by: Guopeng Zhang <zhangguopeng@kylinos.cn>`。
- **Ridong Chen**：回复「Thanks.」，未给出明确的 Reviewed/Acked。
- 无 NAK，无争议点。作者是 cpuset 维护者（Waiman Long 本人），当前缺的是另一位 cgroup 维护者（如 Tejun Heo）的收取或 Ack。

## 合入评估

*likelihood=high*。这是一处有 `Fixes:` 标签的明确 bug 修复，v2 已收敛、有一名 peer 的 Reviewed-by、无异议。*blocking_issues*：尚缺维护者级别的 Ack/收取确认（Tejun Heo 尚未表态）。*next_action*：等待 cgroup 维护者收取；若想加速，可在 deadline/cpuset 场景下补充复现与验证回帖。

## 效果评估

无性能数据；属功能正确性修复——修复前在「存在 SCHED_DEADLINE 任务 + 收缩非有效 partition root cpuset」场景会意外 `-EBUSY`，修复后该误触发被消除。

## 我可以参与的点

- `testing`：在 v2 + SCHED_DEADLINE 任务的环境下复现「收缩非有效 partition root cpuset」的误 `-EBUSY`，验证修复后不再误触发并回帖。
- `review`：确认 v1/v2 判据切换（`is_cpu_exclusive()` vs `is_partition_valid()`）对 v1 开启 v2 mode 的边界场景是否覆盖完整。

## 参考链接

- v2 封面: https://lore.kernel.org/all/20260927215319.382422-1-longman@redhat.com/
- Guopeng Zhang Reviewed-by: https://lore.kernel.org/all/8b38cb59-6e3e-4fe2-bbd7-2fc4cdd9312e@linux.dev/

---
id: sched-20260928-003
date: '2026-09-28'
subject: 'cgroup/cpuset: Run SCHED_DEADLINE shrink test on valid partition root only'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260927215319.382422-1-longman@redhat.com>'
lore_url: 'https://lore.kernel.org/all/20260927215319.382422-1-longman@redhat.com/'
authors:
  - 'Waiman Long'
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260927163454.345463-1-longman@redhat.com>'
    date: '2026-09-28'
    summary: '把 v1 检查拆回 cpuset1_validate_change()，引入 is_in_v2_mode()/cpuset_v2()'
    review_outcome: '评审建议 v1 代码原样保留'
  - version: v2
    msgid: '<20260927215319.382422-1-longman@redhat.com>'
    date: '2026-09-28'
    summary: 'v1 用 is_cpu_exclusive()、v2 用 is_partition_valid() 切换判据'
    review_outcome: 'Guopeng Zhang Reviewed-by'
upstream_commit: null
fixes_commit: a86ce68078b2
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - '尚缺维护者（如 Tejun Heo）的 Ack/收取'
  next_action: '等待 cgroup 维护者收取'
contribution_opportunities:
  - kind: testing
    description: '在 v2 + SCHED_DEADLINE 环境复现收缩非有效 partition root 的误 -EBUSY 并验证修复'
  - kind: review
    description: '确认 v1/v2 判据切换对 v1 开启 v2 mode 边界场景的覆盖完整性'
generated_at: '2026-09-29T01:00:00'
source_email_count: 6
related_articles: []
tags:
  - cgroup
  - deadline
---