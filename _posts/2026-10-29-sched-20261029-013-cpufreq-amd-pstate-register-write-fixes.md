---
id: sched-20261029-013
date: 2026-10-29
subject: cpufreq/amd-pstate register write fixes
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261029121945.854675-1-christian.loehle@arm.com>
lore_url: https://lore.kernel.org/all/20261029121945.854675-1-christian.loehle@arm.com/
authors:
- Christian Loehle
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261029121945.854675-1-christian.loehle@arm.com>
  date: 2026-10-29
  summary: 2 补丁：min 请求钳到 max_limit_perf；resume 的 Desired 钳到缓存 min/max
  review_outcome: 首帖，当日无回帖
upstream_commit: null
fixes_commit: 3f7b835fa4d0
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等 Rafael Wysocki / Viresh Kumar 之一 review 后合入
contribution_opportunities:
- kind: testing
  description: 在 amd-pstate + 固定频率 policy + suspend/resume 的 AMD 机器上验证 2/2
- kind: review
  description: 核对 amd_pstate_adjust_perf() 里是否还有同类「抬高而非钳制」路径
generated_at: '2026-10-30T09:30:00'
source_email_count: 3
related_articles: []
tags:
- cpufreq
title: cpufreq/amd-pstate register write fixes
layout: article
---

## TL;DR
Christian Loehle（Arm）在把 AMD 机器纳入其 acpi-cppc 测试时发现两个 amd-pstate 寄存器写值缺陷，发 2 补丁修复（合计 1 文件 2 增 2 删）：① minimum 性能 hint 可超过 policy 上限（如 schedutil 遇到要满容量的 RT 任务时），旧逻辑反过来把 `max_perf` 抬到 `min_perf`、突破 policy cap，改为把 `min_perf` 钳到 `max_limit_perf`；② resume 路径把 `policy->cur` 换算回 Desired 时因频率/性能换算向上取整，可能超出 `max_limit_perf`（实测 Ryzen 5 7430U 固定 1.2GHz policy：Desired=46 → cur=1216621 kHz → 换算回 Desired=47，resume 写出 MIN=46/Desired=47/MAX=46 的自相矛盾组合），改为恢复前把 Desired 钳到缓存的最小/最大值。系列刚发、无当日 review。

## 背景与问题
作者在把一台 AMD 机器纳入 `acpi-cppc` 测试时（为验证 Sumit Gupta 的另一个补丁）暴露两个问题：

1. **min 请求越过 policy 上限**（1/2）：`schedutil` 遇到请求满容量的 RT 任务时，minimum 性能 hint 可超过 policy maximum；`amd_pstate_adjust_perf()` 把 `max_perf` 抬到 `min_perf`，等于用调度器的 min 请求替换掉 policy cap，随后的 Desired clamp 用的是一个被扩大的区间。
2. **resume 的 Desired 写值越界**（2/2）：`amd_pstate_resume()` 把 `policy->cur` 换算成性能等级后与缓存 policy 限制一起直接写回；频率/性能两个换算都向上取整，于是换算值可能超过 `max_limit_perf`，即便 suspend 前的请求在 policy 限制内。

## 技术方案
两处都是「钳制而非抬高」的最小改动（`drivers/cpufreq/amd-pstate.c`）：

- **1/2** 把 `min_perf` 钳到 `max_limit_perf`，而不是把 `max_perf` 抬到 `min_perf`，重新收紧 policy 上限（1 增 2 删）。
- **2/2** 在恢复请求前，把换算得到的 Desired 钳到缓存的最小/最大值之间（1 增）。

## 版本演进与当前进展
*current_version: v1*（2026-10-29，cover `<20261029121945.854675-1-christian.loehle@arm.com>`）。首帖当日无 review 回帖。base-commit `c339f4010dea8b0d754f84ace70cd1b089878ef8`。

## Maintainer 意见与讨论焦点
今日无任何回帖，维护者（cpufreq 的 Rafael Wysocki / Viresh Kumar）尚未表态。作者在封面自评：1/2 属 Fixes commit 重构时漏掉的 case；2/2 的平台「似乎处理得还好」但仍属奇怪行为——即修复有正确性依据，但触发影响有限。

## 合入评估
*likelihood=medium*。两个补丁都是 trivial 的钳制修复、有明确 `Fixes:` 标签与复现描述，方向正确；但 cpufreq 需 Rafael/Viresh 之一 review，且尚无当日回帖。*blocking_issues*：暂无实质技术分歧，等维护者 review。*next_action*：Rafael 或 Viresh 回帖 Ack 后合入。

## 效果评估
2/2 给出具体复现：Ryzen 5 7430U、固定 1.2 GHz policy，请求 Desired=46 经 `policy->cur=1216621 kHz` 换算回 Desired=47，resume 时写出 `MIN=46, Desired=47, MAX=46` 的不一致组合。这是正确性演示而非性能收益；作者自述该场景在其平台上实际影响有限。

## 我可以参与的点
- **testing**：在带 amd-pstate（尤其 fixed-frequency policy + suspend/resume 循环）的 AMD 机器上验证 2/2 后 resume 写出的 MIN/Desired/MAX 不再自相矛盾。
- **review**：核对 1/2 的 clamp 是否遗漏了 `min_perf` 与 `max_perf` 比较顺序的其它分支（`amd_pstate_adjust_perf()` 里还有没有同类「抬高而非钳制」的路径）。

## 参考链接
- lore thread（0/2 cover）: https://lore.kernel.org/all/20261029121945.854675-1-christian.loehle@arm.com/
- 相关 acpi-cppc 补丁（作者测试动机所引）: https://lore.kernel.org/lkml/20261020121846.691218-2-sumitg@nvidia.com/
