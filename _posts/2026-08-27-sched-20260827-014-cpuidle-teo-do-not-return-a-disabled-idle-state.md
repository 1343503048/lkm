---
id: sched-20260827-014
date: '2026-08-27'
subject: 'cpuidle: teo: Do not return a disabled idle state'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <20260827090505.3703860-1-luoxueqin@kylinos.cn>
lore_url: https://lore.kernel.org/all/20260827090505.3703860-1-luoxueqin@kylinos.cn/
authors:
- Xueqin Luo
maintainers_involved:
- Rafael J. Wysocki
current_version: v1
patch_series:
- version: v1
  msgid: <20260827090505.3703860-1-luoxueqin@kylinos.cn>
  date: 2026-08-27
  summary: teo_select() 选定状态被禁用时回退到最浅的启用状态
  review_outcome: Rafael 提出把 idx0 并入 constraint_idx 钳制的更简写法
upstream_commit: null
fixes_commit: c410a9a142f1
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 需按 Rafael 的 constraint_idx 钳制方案重做并发 v2
  next_action: 作者出 v2 并确认极端约束组合下新钳制逻辑的行为
contribution_opportunities:
- kind: testing
  description: 在禁用 state0 + 紧 QoS 约束的定制机型上验证问题与修复效果
generated_at: '2026-09-07T22:05:00'
source_email_count: 2
related_articles:
- sched-20260827-015
tags:
- idle
title: 'cpuidle: teo: Do not return a disabled idle state'
layout: article
---

## TL;DR
Xueqin Luo 修复 teo governor 的一个边界 bug：idle state 0 被禁用且没有其它启用状态满足 PM QoS 延迟约束时，`teo_select()` 把 `constraint_idx` 停在初值 0 并把**已禁用的 state 0** 返回给核心层执行。补丁当日获 Rafael J. Wysocki 回复并给出一条更简洁的替代写法（把 idx0 纳入 constraint_idx 钳制），方案讨论仍在进行。

## 背景与问题
`teo_select()` 的主扫描循环从 state 1 开始更新 `constraint_idx`（初值 0）。当 state 0 被禁用（`dev->states_usage[0].disable`）且所有启用状态都不满足 `latency_req` 时，`idx > constraint_idx` 钳位把候选压回 0，而 cpuidle 核心对 governor 返回的状态**不再校验 disable 标志**，CPU 就这样进了一个本应禁用的状态。触发条件是"禁用 state 0 + QoS 约束过紧"的组合，多见于用 `/sys/.../state0/disable` 或 `cpu_idle_poll` 类手段做过电源面裁剪的系统。

## 技术方案
作者方案：主循环已顺带找到"最浅的启用状态"，当选定状态被禁用时回退到它；并在 changelog 论证这是最小侵入选择、与 menu governor 行为一致。**Rafael 的替代方案**（回帖原文）：在循环处加

```
if (idx0 < constraint_idx)
        constraint_idx = idx0;
```

即把 state 0 也纳入约束钳制，让约束检查本身产出合法候选，不必事后打补丁式回退。两者语义差异（Rafael 写法在 state 0 禁用时约束下界落在哪）邮件里没展开。

## 版本演进与当前进展
v1（`<20260827090505.3703860-1-luoxueqin@kylinos.cn>`），`Fixes: c410a9a142f1`（"cpuidle: teo: Change the main idle state selection logic"）。当日 Rafael 已回复替代写法，作者未再回应，等 v2。

## Maintainer 意见与讨论焦点
唯一分歧即上述实现路径之争：事后回退 vs 钳制阶段修 `constraint_idx`。Rafael 是 cpuidle 领域维护者，他的写法大概率就是 v2 的形态。无 NAK、无正确性质疑。

## 合入评估
**likely**。维护者认可问题、只改写法，Fixes 标签齐全；`next_action`：作者按 Rafael 建议出 v2（并验证 `idx0` 语义下禁用 state 0 + 约束为 0 的极端组合行为）。同作者同日还有 menu governor 的姊妹修复（sched-20260827-015），两封很可能被打包处理。

## 效果评估
无数据（行为正确性修复）。触发路径为代码推导，未见 syzbot/现场报告。

## 我可以参与的点
- 嵌入式/裁剪 `states_usage` 的产品环境（关闭深睡状态的定制机型）可以验证这个组合是否会静默生效——Rafael 的替代写法落地前，多一个实测case对 v2 有直接价值。

## 参考链接
- lore: https://lore.kernel.org/all/20260827090505.3703860-1-luoxueqin@kylinos.cn/
- Rafael 的替代写法: https://lore.kernel.org/all/CAJZ5v0gcsx6nsCBWfDjP7OEez2jM3-hNj8kSSm=xH5nS_fNSug@mail.gmail.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
