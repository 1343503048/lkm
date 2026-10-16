# sched/fair: Avoid overflow in place_entity()

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20260928-005：Hui Su 修 `place_entity()` s64 溢出——`lag * (load + weight) / load` 除法前中间乘积就可能溢出，破坏 EEVDF 虚拟 lag 放置；改为等价 `lag + lag * weight / load`。
- sched-20261015-006：Peter Zijlstra 回帖给出自己的等价改写并注释数学等价性，Hui Su 认可，方向收敛。
- sched-20261016-007（今天）：**Peter 合入 tip sched/urgent（commit 2f93bcb3f9aa）**，作为 urgent 修复进入发布流。

## 背景与问题
（承接 20260928-005）`place_entity()` 用 `lag * (load + weight) / load` 放大实体虚拟 lag；commit `4823725d9d1d` 把权重换成 `avg_vruntime_weight()` 后丢掉算术余量，即便最终商可表示，乘法本身也可能先溢出 s64。合入的 commit message 给出具体数值：HZ=1000、NICE_0_LOAD=1048576、最小尺度化层级权重 scale_load(2)=2048 时 lag 界为 891289600，114 个最大权重实体使 runqueue load 达 10361604096，中间乘积 891289600 × 10361604098 ≈ 9.23e18 超过 s64 上限。

## 技术方案
（承接 20260928-005）把 `lag * (load + weight) / load` 重写为等价 `lag + lag * weight / load`，避免把虚拟 lag 与总 runqueue weight 相乘；`entity_lag()` 把 vlag 界在实体有效权重上，剩余 `lag * weight` 保持有界。保留原 zero-load warning 语义（除数为 1 时先乘 lag 再乘 weight）。

## 版本演进与当前进展
- v1（2026-09-28）→ Peter 2026-10-15 给出等价改写 → 2026-10-16 合入 tip sched/urgent（`2f93bcb3f9aa`，committer Peter Zijlstra）。

## Maintainer 意见与讨论焦点
Peter Zijlstra 亲自改写并合入，`Fixes: 4823725d9d1d`。无分歧。

## 合入评估
*likelihood=merged*。已合入 tip sched/urgent（commit `2f93bcb3f9aa`）。*blocking_issues*：无。*next_action*：无（已合入 urgent，随 v7.3 发布）。

## 效果评估
v1 曾附 UBSAN、`__int128` oracle 十万随机用例、x86_64/i386/arm64 构建验证；溢出触发条件是理论推演，未见真实触发现场。

## 我可以参与的点
当前阶段已合入 urgent，无明显参与空间。

## 参考链接
- tip 合入通知：https://lore.kernel.org/all/179213734207.2666988.8900131874393139062.tip-bot2@tip-bot2/
- 原始补丁：https://lore.kernel.org/all/20260928124754.1692077-1-sh_def@163.com/

---
id: sched-20261016-007
date: 2026-10-16
subject: "sched/fair: Avoid overflow in place_entity()"
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<20260928124754.1692077-1-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/20260928124754.1692077-1-sh_def@163.com/"
authors: ["Hui Su"]
maintainers_involved: ["Peter Zijlstra"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260928124754.1692077-1-sh_def@163.com>"
    date: 2026-09-28
    summary: "place_entity() 无溢出等价改写：lag * (load + weight) / load → lag + lag * weight / load"
    review_outcome: "Peter 改写并合入 tip sched/urgent"
upstream_commit: "2f93bcb3f9aa"
fixes_commit: "4823725d9d1d"
merged_branch: "sched/urgent"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "无（已合入 urgent，随 v7.3 发布）"
contribution_opportunities: []
generated_at: "2026-10-17T01:30:00"
source_email_count: 1
related_articles: ["sched-20260928-005", "sched-20261015-006"]
tags: [eevdf, cfs]
---