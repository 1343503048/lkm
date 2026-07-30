---
id: sched-20260728-003
date: 2026-07-28
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260727-b4-sched-sync-wakeup-v3-1-90cf481dbd85@gentwo.org>"
lore_url: "https://lore.kernel.org/r/20260727-b4-sched-sync-wakeup-v3-1-90cf481dbd85@gentwo.org"
authors: [Shubhang Kaushik]
maintainers_involved: []
current_version: v3
patch_series:
  - version: v2
    msgid: "<20260722-b4-sched-sync-wakeup-v2-1-f1164560b24b@gentwo.org>"
    date: 2026-07-22
    summary: "Move reciprocal handoff preference under wake_affine domain check"
    review_outcome: "未获取到"
  - version: v3
    msgid: "<20260727-b4-sched-sync-wakeup-v3-1-90cf481dbd85@gentwo.org>"
    date: 2026-07-27
    summary: "Limit to !sched_smt_active(); drop redundant affinity check; use plain p->last_wakee read; rebase on v7.2-rc5"
    review_outcome: "v3 刚发出，暂无 review"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["需要 CFS maintainer (PeterZ / Vincent Guittot) review", "SMT 场景的排除逻辑需要确认是否充分"]
  next_action: "等待 maintainer review"
contribution_opportunities:
  - kind: testing
    description: "在非 SMT ARM 平台（如 Ampere Altra）或 x86 关闭 SMT 后测试 pipe/hackbench/schbench，验证 30% 提升可复现且无回退"
generated_at: "2026-07-30T10:00:00"
source_email_count: 1
related_articles: []
tags: [cfs, affinity, perf]
---

## TL;DR

Ampere 的 Shubhang Kaushik 发出 v3，针对非 SMT 系统上的 pipe 式 ping-pong 负载，在 wake-affine 域内优先将 wakee 放到 waker CPU 上（而非走 select_idle_sibling 找 idle CPU）。在 80 核 Ampere Altra 上 `perf bench sched pipe` 提升约 30%。v3 刚发出，暂无 review。

## 背景与问题

Pipe-style ping-pong 负载（A wakes B, B wakes A, ...）的瓶颈在 handoff 成本。现有路径中 `select_idle_sibling()` 倾向于把 wakee 放到 idle CPU 上，但对于这种紧密交替的场景，让 pair 留在同一 runqueue 反而更快（减少跨 CPU 迁移开销）。

## 技术方案

利用已有的 `last_wakee` 和 `wake_wide()` 状态识别"窄幅互惠 WF_SYNC wakeup"模式：

- 检测 A→B→A→B 的交替唤醒链
- 当 wake-affine domain 允许 `SD_WAKE_AFFINE` 且系统非 SMT（`!sched_smt_active()`）时，优先选 waker CPU
- 额外约束：waker CPU 上无其他 runnable fair task，且在 asymmetric-capacity 系统上 wakee 能 fit

SMT 系统和不匹配此模式的 wakeup 继续走原有 `wake_affine()` + `select_idle_sibling()` 路径。

v3 相对 v2 的改动：
- 限制为 `!sched_smt_active()`（SMT 系统完全不走新路径）
- 去掉冗余的 affinity 检查（`want_affine` 已验证）
- 用 plain `p->last_wakee` 读取替代 `READ_ONCE()`
- Rebase 到 v7.2-rc5

## 版本演进与当前进展

- v1：初始版本
- v2（2026-07-22）：将互惠 handoff 偏好移到 wake_affine domain 检查下
- v3（2026-07-27）：限制非 SMT、去掉冗余检查、rebase v7.2-rc5

## Maintainer 意见与讨论焦点

v3 暂无 review 意见。此前 v2 的 review 意见未在本次邮件中体现。需要关注：
- PeterZ / Vincent Guittot 对"在 select_idle_sibling 前插入特殊路径"的态度
- SMT 排除是否足够——有人可能认为 SMT 下也应受益

## 合入评估

可能性中等。30% 的 pipe benchmark 提升数据扎实（40 次平均），但 CFS wakeup 路径是高度敏感区域，maintainer 对新增特判路径通常很谨慎。关键看 PeterZ/Vincent 是否认为这个模式识别足够通用。

## 效果评估

> Tested on 80-core non-SMT Ampere Altra: perf bench sched pipe -l 1000000 improved by about 30%, averaged over 40 runs. Hackbench, schbench and SPECjBB showed no material regression.

- `perf bench sched pipe`：~30% 提升（40 次平均）
- hackbench / schbench / SPECjBB：无明显回退
- 基线：v7.2-rc5

## 我可以参与的点

- **测试**：在 x86 关闭 SMT 后（或 ARM 非 SMT 平台）复现 pipe benchmark 提升，并补充 fio / netperf 等 IO 密集场景数据，回帖到邮件列表增加合入信心
- 如果有多 LLC 的 NUMA 机器，可以测试跨 LLC 场景是否有回退

## 参考链接

- lore thread: https://lore.kernel.org/r/20260727-b4-sched-sync-wakeup-v3-1-90cf481dbd85@gentwo.org
- v2 link: https://lore.kernel.org/r/20260722-b4-sched-sync-wakeup-v2-1-f1164560b24b@gentwo.org
- tip-bot commit: 未获取到
