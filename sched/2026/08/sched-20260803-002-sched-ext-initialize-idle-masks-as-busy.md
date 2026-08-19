# sched_ext: Initialize idle masks as busy

# sched_ext: 内置 idle 掩码初始化为 busy


## TL;DR
sched_ext 内置 idle 掩码初始化时把全部 online CPU 误标为 idle，导致 busy CPU 被错误广播。改为保守地初始为空，待 bypass 解除后由真实 idle 转换填充。修复方向已获 Tejun 认可，合入概率高。

## 背景与问题
`reset_idle_masks()` 原先把全部 online CPU 拷进 idle 掩码，假设「会很快收敛到真实状态」。但在这段收敛窗口内，busy CPU 会被调度器当作 idle 来选择，造成任务被派发到实际正忙的 CPU，影响延迟与正确性。

## 技术方案
将 idle 掩码初始化为**空**（即全部标记 busy）。bypass 解除（lift）时每个 CPU 都被重调度，idle-to-idle re-pick 会用真正 idle 的 CPU 填充掩码，后续 idle 转换持续维护。代价是初始阶段可能漏报部分 idle CPU，但**永远不会**把 busy CPU 错报为 idle —— 这是一个保守但正确的取舍（16113 的另外 1/2 还修了 per-node 变体）。

## 版本演进与当前进展
v1 单 patch（2026-08-03），由 Andrea Righi 提交，Tejun Heo `Suggested-by`，已在 16113 中给出建议方向。当前待合入。

## Maintainer 意见与讨论焦点
Tejun Heo 提出「初始化为空」的修正思路并作为 Suggested-by 署名，未出现反对意见。讨论焦点在于正确性取舍（漏报 idle vs 错报 busy），选择后者优先。

## 合入评估
合入可能性高。属一行级语义修正，Tejun 维护相关分支，几乎无阻塞。

## 效果评估
邮件未给量化数据，是正确性修复（消除 busy→idle 误报这一潜在调度错误）。无性能基准，属「正确性优先」类改动。

## 我可以参与的点
- 可补一个 selftest，在 sched_ext 启用后、CPU 首次 idle 转换前断言 idle 掩码不含 busy CPU。

## 参考链接
- lore thread: 未获取到

---
subject: "sched_ext: Initialize idle masks as busy"
id: sched-20260803-002
date: 2026-08-03
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Andrea Righi]
maintainers_involved: [Tejun Heo, Andrea Righi]
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-03
    summary: "内置 idle 掩码在 sched_ext 启用前把所有 online CPU 标记为 idle，导致 busy CPU 在下次 idle 转换前被错误地广播为 idle。改为初始化为空（全部标记 busy），保守但安全；bypass 解除时每 cpu 被重调度并通过 idle-to-idle re-pick 填充真实 idle 掩码。"
    review_outcome: "Tejun Heo 在 16113 中给出 Suggested-by，方向已认可。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 Tejun 合入 for-next；属于小修复，几乎无阻塞。"
contribution_opportunities:
  - kind: testing
    description: "在 sched_ext 启用后、各 cpu 首次 idle 转换前的窗口内验证内置 idle 掩码不再把 busy cpu 暴露给调度器，可补一个 selftest 断言。"
generated_at: "2026-08-04T00:20:00"
source_email_count: 1
related_articles: []
tags: [sched_ext, idle]
---
