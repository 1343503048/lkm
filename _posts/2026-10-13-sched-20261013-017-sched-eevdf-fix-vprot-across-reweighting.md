---
id: sched-20261013-017
subject: 'sched/eevdf: Fix vprot across reweighting'
date: 2026-10-13
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261003114656.105721-1-kayracizmeci@gmail.com>
lore_url: https://lore.kernel.org/all/20261003114656.105721-1-kayracizmeci@gmail.com/
authors:
- Kayra Cizmeci
maintainers_involved:
- Vincent Guittot
current_version: v1
patch_series:
- version: v1
  msgid: <20261003114656.105721-1-kayracizmeci@gmail.com>
  date: 2026-10-03
  summary: rel_vprot 标志转/恢复相对量修已过期 protection 复活
  review_outcome: Christian Tested-by；Vincent/Prateek 质疑新标志，Kayra 另写更简 diff（未测）
upstream_commit: null
fixes_commit: 80390ead2080
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 新 diff 未测试；实现形态未定；trailer 待清理
  next_action: Kayra 验证新 diff 后形成 v2，交 Vincent/Christian 复审
contribution_opportunities:
- kind: testing
  description: 验证去掉 rel_vprot、enqueue 路径重建 vprot 的新 diff
- kind: review
  description: 复核新 diff 权重缩放与 cancel_protect_slice 调用的正确性
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261003-007
- sched-20261011-004
- sched-20261012-009
tags:
- eevdf
title: 'sched/eevdf: Fix vprot across reweighting'
layout: article
---

> **subject**：sched/eevdf: Fix vprot across reweighting

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/03/sched-20261003-007-sched-eevdf-fix-vprot-across-reweighting.html">sched-20261003-007</a>：Kayra Cizmeci 发重组后的独立补丁「Fix vprot across reweighting」（作者 Kayra、Christian Co-developed-by），用 `rel_vprot` 标志把 protection 在 reweight 时转/恢复相对量，修「已过期 protection 复活」。
- <a class="article-ref" href="/lkm/2026/10/11/sched-20261011-004-sched-eevdf-fix-vprot-across-reweighting.html">sched-20261011-004</a>：Christian Loehle 给 `Tested-by` 但要求移除其 SOB。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-009-sched-eevdf-fix-vprot-across-reweighting.html">sched-20261012-009</a>：Vincent Guittot 提出「根本不需要 `rel_vprot` 标志，curr 时直接 `se->vprot = se->vruntime` 即可」的更简方案；Prateek 也质疑为何需要新标志；Kayra 解释根因是 `sched_change_begin()` 把 `cfs_rq->curr` 置 NULL。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-017-sched-eevdf-fix-vprot-across-reweighting.html">sched-20261013-017</a>（今天）：Kayra 另起炉灶发一版**未测试**的替代 diff——`reweight_eevdf()` 里 `if (curr && protect_slice(se))` 放宽为 `if (curr)`，并在 `enqueue_task_fair()` 里用 `protect_slice()`/旧权重/`dist = vprot - vruntime` 在 reweight 后重建 `se->vprot`。

## 背景与问题
（承接 20261003-007 → 20261012-009）EEVDF slice protection 是绝对 vruntime 边界；reweight（nice/cgroup 权重变化）时 `reweight_eevdf()` 缩放存活 protection，但移动 vruntime 时「已过期」的 vprot 原样不动会复活；新交互是已合入 tip/sched/core 的 `819224e506bc`（"Remove dead code on enqueue_task_fair"）让 `reweight_eevdf()` 现在会被 curr 调用。`Fixes:` 指向 `80390ead2080` 与 `bcd74b2ffdd0`。

## 技术方案
（承接 20261012-009）原方案加 `rel_vprot` 标志；Vincent 主张更简（curr 时直接 `se->vprot = se->vruntime`）。今天 Kayra 回应 Vincent 的简化方向，给出新 diff（自述「深夜代码、未测试」）：
- `reweight_eevdf()`：把 dequeue 侧条件 `if (curr && protect_slice(se))` 放宽为 `if (curr)`，只要 curr 就 `se->vprot -= avruntime; rel_vprot = true;`（不再依赖 protect_slice）。
- `enqueue_task_fair()`：进 `reweight_eevdf()` 前捕获 `live = protect_slice(se)`、`old_weight = se->h_load.weight`、`dist = se->vprot - se->vruntime`；`place_entity()` 后 `if (!live) cancel_protect_slice(se); else { if (weight != old_weight) dist = div64_long(dist * old_weight, weight); se->vprot = se->vruntime + dist; }`。

即弃掉 `rel_vprot` 标志、改为在 enqueue 路径按权重变化就地重建 vprot。作者自述未测试、或有小问题。

## 版本演进与当前进展
仍为 v1（未发正式 v2）；今日为对 Vincent 简化建议的替代 diff 尝试，作者标注「Not even 1% tested」、将明日验证。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**（前日）：主张无需 `rel_vprot`，curr 时直接 `se->vprot = se->vruntime`。
- **K Prateek Nayak**（前日）：质疑为何需要新标志。
- **Kayra Cizmeci**（作者，今日）：按简化方向另写一版，但未测试、待验证。
- 焦点：能否用更简（无 `rel_vprot`）的实现替代，仍待验证与评审收敛。

## 合入评估
*likelihood=medium*。原方案有 Tested-by、方向获讨论，但实现形态（rel_vprot vs 更简重建）未定，今日新 diff 尚未测试。*blocking_issues*：Kayra 的新 diff 未测试；实现形态未定；trailer（Christian SOB）待清理。*next_action*：Kayra 验证新 diff 后形成 v2，交由 Vincent/Christian 复审。

## 效果评估
作者原测试方法（pin 两任务同核、nice 0/10 切换 3000 次、校验 `weight×(vprot−vruntime)` 不变量）：Base 下 Normal 6002/6002、NRTP 53/53 全错，补丁后 0/6003、0/55 全对。今日新 diff 无新数据。

## 我可以参与的点
- testing：帮 Kayra 验证「切掉 rel_vprot、enqueue 路径重建 vprot」的新 diff（作者自述未测）。
- review：评估新 diff 中 `dist = div64_long(dist * old_weight, weight)` 的缩放与 `cancel_protect_slice()` 调用的正确性。

## 参考链接
- 系列补丁 lore：https://lore.kernel.org/all/20261003114656.105721-1-kayracizmeci@gmail.com/
- 今日替代 diff：https://lore.kernel.org/all/20261012190027.9442-1-kayracizmeci@gmail.com/
