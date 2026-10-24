# sched: use static_branch_likely() for the NUMA balancing tick check

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261021-018：Yafang Shao 的 bpf-next RFC v3 系列中的 2/5 补丁——把 NUMA balancing tick 检查改用 `static_branch_likely()` 微优化；当日 Gregory Price 给 Acked-by 并要求「请单独提交」。
- sched-20261024-010（今天）：作者已拆出并单独重发（作为 `[PATCH 2/2]`），Gregory Price 复审后撤回其 Ack 判断——「On second look, I made a poor assumption... probably just drop this patch」，理由是在单节点系统上该 static key 默认关闭、改动收益不大。补丁趋向被放弃。

## 背景与问题
（承接 20261021-018）NUMA balancing 的 tick 检查此前用 `static_branch_unlikely()` 或普通分支，拟改用 `static_branch_likely()` 以符合多数情况走向。该改动此前混在 bpf-next RFC 系列里、评审要求拆分，作者已拆分单独重发。今日背景新增：Gregory 修正此前假设。

## 技术方案
（承接 20261021-018）单补丁：NUMA balancing tick 检查改用 `static_branch_likely()`。今日无代码变更，为复审意见转向。

## 版本演进与当前进展
*current_version: v3*（所在系列原为 bpf-next RFC v3；今日拆出的单独提交为 `[PATCH 2/2]`，具体 msgid 未进入当日缓存，可经 Gregory 回帖确认线程）。当日无新版本，为复审转向。

## Maintainer 意见与讨论焦点
Gregory Price（Meta）今日复审：此前误以为该 static key 默认开启，实际上单节点系统上即便构建了 NUMA balancing、该 key 也默认关闭，故「I don't think this change makes a huge difference either way - but probably just drop this patch」。无其他表态。

## 合入评估
*likelihood=low*。此前已获 Acked-by、方向明确，但今日唯一评审者 Gregory 明确建议丢弃该补丁，系列趋向被放弃。*blocking_issues*：Gregory 建议 drop；在单节点系统上收益存疑。*next_action*：作者确认是否按 Gregory 建议撤回该补丁。

## 效果评估
无 benchmark。属分支预测/静态 key 语义微优化，且今日被评审者指出在单节点系统上 key 默认关闭、实际收益甚微。

## 我可以参与的点
- *kind: discussion*：若在多节点 NUMA 系统上有该 tick 检查热路径的实测数据，可回帖说明是否有保留价值。

## 参考链接
- Gregory Price 今日回帖（建议 drop）: https://lore.kernel.org/all/179282331345.1990293.1612978888764380222.b4-reply@b4/
- 前文: sched-20261021-018

---
id: sched-20261024-010
date: 2026-10-24
subject: 'sched: use static_branch_likely() for the NUMA balancing tick check'
subsystem: sched
type: fix
status: superseded
severity: low
thread_root_msgid: '<20261019064157.29885-3-laoar.shao@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20261019064157.29885-3-laoar.shao@gmail.com/'
authors:
  - 'Yafang Shao'
maintainers_involved:
  - 'Gregory Price'
current_version: v3
patch_series:
  - version: v3
    msgid: '<20261019064157.29885-3-laoar.shao@gmail.com>'
    date: 2026-10-19
    summary: 'NUMA balancing tick 检查改用 static_branch_likely()'
    review_outcome: 'Gregory Price 复审后建议 drop'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - 'Gregory Price 建议 drop 该补丁'
  next_action: '作者确认是否撤回'
contribution_opportunities:
  - kind: discussion
    description: '提供多节点 NUMA 热路径实测数据，说明是否有保留价值'
generated_at: '2026-10-25T01:00:00'
source_email_count: 1
related_articles:
  - sched-20261021-018
tags:
  - numa_balancing
  - cfs
---