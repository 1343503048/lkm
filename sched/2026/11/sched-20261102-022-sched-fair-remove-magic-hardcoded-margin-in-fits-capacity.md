# sched/fair: Remove magic hardcoded margin in fits_capacity()

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260923-003：Qais 的 capacity-aware v2 04/13（fits_capacity 魔数 1280/1024 换 per-rq 阈值）被 Zhan Xusheng 指出与主线交互隐患。
- sched-20261005-006：Zhan 回复 Tim Chen，采纳 `x*5 < y*4` 形式并给完整溢出论证，压后到 04/13 排队之后。
- sched-20261102（今天）：Qais 回帖致谢抓出问题（否则 vN 会漏掉），表示「happy to split，但不乐见又出现一个用 magic number 的新 user」，请作者发个拆分补丁并讨论细节。此与同日 Zhan 的新单补丁（`sched/cache: Don't use fits_capacity() to compare thread and CPU counts`）直接联动。

## 背景与问题

（承接）fits_capacity 签名变更会使 `invalid_llc_nr()` 静默误传 CPU 数；Zhan 想抽独立 helper 保 margin，Qais 更想顺手删掉 margin。

## 技术方案

（承接）无新代码；Qais 明确表态：支持拆分、反对新增 magic number（他正在去除这些数字）。拆分 patch 待作者发。

## 版本演进与当前进展

v2 系列持续推进；今日为原作者对拆分提议的回应。

## Maintainer 意见与讨论焦点

原作者 Qais 认可「拆分 + 讨论」路径，但坚持去掉硬编码 margin 的方向。

## 合入评估

likelihood=medium。协作顺利，但 margin 去留仍待作者（Tim/Chen Yu）定。

## 效果评估

（承接）无性能数据（等价重写）。

## 我可以参与的点

- new_patch：发「拆分 fits_capacity helper」补丁并推动 margin 移除讨论。
- discussion：就 margin 是否可安全移除给出实测。

## 参考链接

- lore thread: https://lore.kernel.org/all/20260504020003.71306-5-qyousef@layalina.io/

---
type: feature
status: under_review
severity: none
thread_root_msgid: <20260504020003.71306-5-qyousef@layalina.io>
authors:
- Qais Yousef
maintainers_involved: []
current_version: v2
patch_series: []
merge_assessment:
  likelihood: medium
  blocking_issues:
  - margin 去留未定，拆分补丁待发
  next_action: 作者发拆分补丁并讨论 margin 是否移除
contribution_opportunities:
- kind: new_patch
  description: 发 fits_capacity helper 拆分补丁并推动 margin 移除
- kind: discussion
  description: 就 margin 移除给出实测依据
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles:
- sched-20260923-003
- sched-20261005-006
tags:
- cfs
- load_balance
id: sched-20261102-022
subject: 'sched/fair: Remove magic hardcoded margin in fits_capacity()'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
