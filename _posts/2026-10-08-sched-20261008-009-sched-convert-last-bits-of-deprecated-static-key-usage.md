---
id: sched-20261008-009
subject: 'sched: Convert last bits of deprecated static key usage'
date: '2026-10-08'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <cd340d0b-31b0-490a-9961-78c5de117e70@transsion.com>
lore_url: https://lore.kernel.org/all/cd340d0b-31b0-490a-9961-78c5de117e70@transsion.com/
authors:
- Hongyan Xia
maintainers_involved:
- Valentin Schneider
current_version: v2
patch_series:
- version: v1
  msgid: null
  date: null
  summary: 首版迁移（不在当日窗口，见 related 文章）
  review_outcome: null
- version: v2
  msgid: <20260903115728.11864-1-hongyan.xia@transsion.com>
  date: '2026-09-03'
  summary: rebase 并修掉 core.c 大冲突
  review_outcome: Valentin 就代码生成差异提问，作者回复零 delta
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无正式 Acked-by/Reviewed-by
  - core.c 部分与 Simplify PREEMPT_DYNAMIC 系列落地顺序待定
  next_action: 等 Valentin 给出 Ack 并确认 rebase 顺序
contribution_opportunities:
- kind: testing
  description: riscv/s390 等架构复核迁移前后机器码 delta 是否为零
- kind: review
  description: 核对零 delta 验证方法是否覆盖 PREEMPT_DYNAMIC 各分支
generated_at: '2026-10-09T01:00:00'
source_email_count: 1
related_articles:
- sched-20260903-007
- sched-20261006-009
tags:
- cfs
- preempt
title: 'sched: Convert last bits of deprecated static key usage'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-007-sched-convert-last-bits-of-deprecated-static-key-usage.html">sched-20260903-007</a>：Hongyan Xia 收掉调度器里最后一批已废弃 static key 用法——`fair.c` 的 CFS bandwidth `__cfs_bandwidth_used` 迁到 `DEFINE_STATIC_KEY_FALSE()` + `static_branch_unlikely/inc_cpuslocked()`，`core.c` 的 PREEMPT_DYNAMIC 更新宏改用 `static_branch_enable/disable()`；v2 为 rebase 并修掉 core.c 大冲突的版本，09-03 无回帖。
- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-009-sched-convert-last-bits-of-deprecated-static-key-usage.html">sched-20261008-009</a>（今天）：Valentin Schneider 关注迁移对生成机器码的影响，作者回帖确认在 aarch64 与 x86 上机器码 delta 为零。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-007-sched-convert-last-bits-of-deprecated-static-key-usage.html">sched-20260903-007</a>）raw static key 不带类型信息、`static_key_{true,false}()` 命名有歧义，故被废弃；调度器多数站点已在前序补丁转换，本补丁处理剩下两处（fair.c 的 CFS bandwidth、core.c 的 PREEMPT_DYNAMIC）。今天的进展是维护者 Valentin Schneider 就「把 preempt_dynamic 的 static key 迁移到 static branch 是否会改变生成机器码」提出关切——这是该类迁移补丁常见的 review 关注点（static_branch 的 no-op 站点理论上应与 static_key 等价，但需实测确认 delta）。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-007-sched-convert-last-bits-of-deprecated-static-key-usage.html">sched-20260903-007</a>）fair.c 侧 `static_key_false/slow_inc/dec_cpuslocked` → `static_branch_unlikely/inc/dec_cpuslocked`；core.c 侧 `preempt_dynamic_key_{enable,disable}` 宏改名并改用 `static_branch_enable/disable`，总计 8 增 8 删、无功能变化。今天的补充是验证结论：作者声明至少在 aarch64 与 x86 上，转换前后机器码 delta 为零（即静态站点在编译期仍被优化为直接跳转，无运行时开销差异）。

## 版本演进与当前进展

v2（`<20260903115728.11864-1-hongyan.xia@transsion.com>`，见 related 文章）之后无新版；本日为维护者 question → author 回复，无新补丁版本。

## Maintainer 意见与讨论焦点

- **Valentin Schneider**（sched 维护者）：就迁移对生成代码的影响提问（关切点：static_branch 迁移不应引入机器码膨胀/行为差异）。
- **Hongyan Xia**（作者）：回复「在 aarch64 和 x86 上机器码 delta 为零」，即迁移是无损的。
- 仍有未决项：core.c 部分与 Mark Rutland 的 Simplify PREEMPT_DYNAMIC 系列争用同一代码区域，落地顺序待定（见 related 文章）；本日该点无新进展。

## 合入评估

*likelihood=medium*。维护者已介入并得到「零 delta」的正面答复，方向无争议；但尚无正式 Acked-by/Reviewed-by，且 core.c 半部分仍受 PREEMPT_DYNAMIC 系列落地顺序约束。*blocking_issues*：无正式 Ack；与 Simplify PREEMPT_DYNAMIC 系列的顺序协调。*next_action*：等 Valentin 基于「零 delta」答复给出 Ack，并确认与 Mark Rutland 系列的 rebase 顺序。

## 效果评估

本日新增的效果数据是代码生成层面：作者实测 aarch64 与 x86 上迁移前后机器码 delta 为零（无 benchmark 数字，属「无功能/无代码差异」的正确性验证）。

## 我可以参与的点

- `testing`：在其它架构（如 riscv/s390）上复核迁移前后机器码 delta 是否也为零，扩大验证覆盖。
- `review`：核对作者「零 delta」的验证方法（CONFIG 组合、对比对象）是否覆盖了 PREEMPT_DYNAMIC 的 full/lazy 各分支。

## 参考链接

- 今日作者回复: https://lore.kernel.org/all/cd340d0b-31b0-490a-9961-78c5de117e70@transsion.com/
- v2 补丁: https://lore.kernel.org/all/20260903115728.11864-1-hongyan.xia@transsion.com/
