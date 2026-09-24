# sched: Restart fair hrtick after same-task repicks

## TL;DR
增量更新：作者 Shubhang Kaushik 回应 Zhan Xusheng（09-16 评审）关于"跳过 put_prev_task_*() 无法区分 fair 与 DL"的疑问，解释了 fair 与 DL picker 侧 runtime 更新的差异（fair 在 pick 前刷新 entity、DL 无对应更新），承诺改 changelog、补注释并文档化 SNT_NORMAL/SNT_PICK 语义，且 CONFIG_SCHED_CLASS_EXT=y 编译通过。无新版本。

## 背景与问题
背景见 sched-20260916-017：当 pick_next_task() 重复选择同一个 fair 任务（repick）时跳过 put_prev_task_*()，导致 hrtick 未重启、切片到期后抢占失效。本日是对既有评审的回应，无新方案。

## 技术方案
无方案变化。关键澄清一条机制差异：
- fair：`pick_task_fair()` 在再次选中当前任务前会调用 `update_curr_eevdf()`，先刷新 hrtick_start_fair() 所用的任务 entity（含组调度），当其观察到过期切片时会先推进 entity 的虚拟 deadline 再算下一次到期。
- DL：`pick_task_dl()` 没有对应的 picker 侧 runtime 更新，SNT_REPICK 时 `p->dl.runtime` 可能陈旧。

## 版本演进与当前进展
- v3（09-15，`<20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org>`）：当前版本。
- 09-17：作者回应评审，承诺 changelog 澄清 + fair repick 路径补注释 + 文档化 SNT_NORMAL/SNT_PICK；CONFIG_SCHED_CLASS_EXT=y 重编译通过。

## Maintainer 意见与讨论焦点
- **Zhan Xusheng（评审，09-16）**：指出跳过 put_prev_task_*() 不区分 fair 与 DL 类。
- **Shubhang Kaushik（作者）**：解释两类差异后同意澄清文档，未见进一步分歧。
- 无 NAK；方向稳定，属收尾性修改。

## 合入评估
*likelihood=medium*。修复目标明确、评审已进入文案收尾；但尚未见 sched 维护者（Peter/Vincent 等）表态，且需确认 DL 类 SNT_REPICK 语义是否也要一并处理。*blocking_issues*：缺 sched 维护者评审；DL 侧陈旧 runtime 是否需要单独修复待确认。*next_action*：作者提交下一版（changelog/注释/文档），并等待维护者评审。

## 效果评估
无性能数据；属正确性修复（hrtick 抢占失效场景）。

## 我可以参与的点
- kind=review：核查 DL 类 SNT_REPICK 时 p->dl.runtime 陈旧是否会导致 EDF 抢占计算错误，确认是否需要在 DL picker 侧补 runtime 刷新。

## 参考链接
- lore（v3）: https://lore.kernel.org/all/20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org/

---
id: sched-20260917-005
date: '2026-09-17'
subject: 'sched: Restart fair hrtick after same-task repicks'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org>'
lore_url: 'https://lore.kernel.org/all/20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org/'
authors:
  - 'Shubhang Kaushik'
maintainers_involved: []
current_version: v3
patch_series:
  - version: v3
    msgid: '<20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org>'
    date: '2026-09-15'
    summary: '公平调度 repick 时重启 hrtick；本日澄清 fair/DL picker 侧 runtime 更新差异并做文案收尾'
    review_outcome: '回应 Zhan Xusheng 评审，无剩余分歧'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '缺 sched 维护者评审'
    - 'DL 侧 SNT_REPICK runtime 陈旧是否需单独修复待确认'
  next_action: '作者提交下一版并等待维护者评审'
contribution_opportunities:
  - kind: review
    description: '核查 DL 类 SNT_REPICK 时 p->dl.runtime 陈旧对 EDF 计算的影响'
generated_at: '2026-09-18T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260916-017
tags:
  - cfs
  - preempt
---