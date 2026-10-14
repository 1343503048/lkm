# sched/eevdf: Fix vprot across reweighting

> **subject**：sched/eevdf: Fix vprot across reweighting

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261003-007：Kayra Cizmeci 发独立补丁「Fix vprot across reweighting」，用 `rel_vprot` 标志把 protection 在 reweight 时转/恢复相对量，修「已过期 protection 复活」。
- sched-20261011-004：Christian Loehle 给 `Tested-by` 但要求移除其 SOB。
- sched-20261012-009：Vincent Guittot 提出无需 `rel_vprot`、curr 时直接 `se->vprot = se->vruntime` 的更简方案；Prateek 质疑为何要新标志。
- sched-20261013-017：Kayra 另起炉灶发一版未测试的替代 diff（`reweight_eevdf()` 放宽为 `if (curr)`、`enqueue_task_fair()` 里重建 `se->vprot`）。
- sched-20261014-006（今天）：Kayra 正式发 **v2**——彻底弃掉 `rel_vprot` 标志，采纳 Vincent 的简化（on_rq 路径简化、enqueue 路径按权重变化就地重建 vprot），补双 `Fixes:` 与 `Suggested-by: Vincent Guittot`，并自测「base 的问题在补丁版全部消失」（仅残留 3/1500 任务 vprot 滑动 >5%、且复测回 0，原因不明）。

## 背景与问题
（承接 20261003-007 → 20261013-017）EEVDF slice protection 是绝对 vruntime 边界；reweight（nice/cgroup 权重变化）时 `reweight_eevdf()` 缩放存活 protection，但移动 vruntime 时「已过期」的 vprot 原样不动会复活；新交互是已合入 tip/sched/core 的 `819224e506bc`（"Remove dead code on enqueue_task_fair"）让 `reweight_eevdf()` 现在会被 curr 调用。`Fixes:` 现指向 `80390ead2080`（Separate se->vlag from se->vprot）与 `bcd74b2ffdd0`（Only set slice protection at pick time）。

## 技术方案
（承接 20261013-017）v2（`<20261014150251.30099-1-kayracizmeci@gmail.com>`，`kernel/sched/fair.c` +24/−3）最终形态：

- **弃掉 `rel_vprot` 标志**（Prateek 与 Vincent 的意见）：`reweight_eevdf()` 的 `on_rq` 分支改为 `if (rel_vprot) se->vprot += avruntime; else if (curr) se->vprot = se->vruntime;`——curr 时直接以 vruntime 重建 vprot。
- **enqueue 路径就地重建**：`enqueue_task_fair()` 里先记录 `live = protect_slice(se) && running`、`old_weight`、`dist = se->vprot - se->vruntime`，调用 `reweight_eevdf()` 与 `place_entity()` 后，`if (live) { if (weight != old_weight) dist = div64_long(dist * old_weight, weight); se->vprot = se->vruntime + dist; } else if (running) cancel_protect_slice(se);`。

## 版本演进与当前进展
v1（10-03）→ 今日 **v2**（10-14）。v1→v2 改动：扔 `rel_vprot`（回应 Prateek/Vincent）、按 Vincent 建议简化 `reweight_eevdf()` 的 on_rq 路径、在 `enqueue_task_fair()` 内本地重算 entity 权重。作者自测（与 v1 不同的测试）：base 的问题在补丁版全部消失；唯一残留是「3/1500（补丁版 2/1500）任务 vprot 滑动 >5%」，复测又回到 0、原因不明（作者自述可能此前没测 on_rq 路径）。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**（前日）：主张无需 `rel_vprot`、curr 时直接 `se->vprot = se->vruntime`——v2 已采纳并加 `Suggested-by`。
- **K Prateek Nayak**（前日）：质疑为何要新标志——v2 已移除。
- 无 NAK；焦点从「rel_vprot 是否必要」收敛到「简化版是否测试充分」。今日无新 review 回帖，待 Vincent/Christian 对 v2 复审。

## 合入评估
*likelihood=medium*。v2 已按 Vincent/Prateek 意见删掉 `rel_vprot` 并补双 `Fixes:` + `Suggested-by`，方向与维护者期望一致；但残留「3/1500 滑动 >5%」现象原因未明、且尚无对 v2 的正式 review。*blocking_issues*：v2 未获 review；残留滑动未解释。*next_action*：Vincent/Christian 复审 v2；作者澄清 3/1500 滑动是否为真实缺陷。

## 效果评估
作者自测（方法未详述，仅说明与 v1 不同）：补丁版下 base 的问题全部消失；另有 3/1500（base）vs 2/1500（补丁）任务 vprot 滑动 >5%，复测时归 0、原因未知。v1 时代方法（nice 0/10 切换 3000 次、校验 `weight×(vprot−vruntime)`）在本文未重跑。

## 我可以参与的点
- testing：跑 v1 的方法（pin 两任务同核、nice 0/10 切换、校验 `weight×(vprot−vruntime)` 不变量）来独立验证 v2，并尝试复现「3/1500 滑动 >5%」的残留现象。
- review：评估 v2 中 `else if (curr) se->vprot = se->vruntime` 与 enqueue 侧 `div64_long(dist * old_weight, weight)` 缩放、`cancel_protect_slice()` 调用在 curr/on_rq 各组合下的正确性。

## 参考链接
- v2 lore：https://lore.kernel.org/all/20261014150251.30099-1-kayracizmeci@gmail.com/
- v1 lore：https://lore.kernel.org/all/20261003114656.105721-1-kayracizmeci@gmail.com/

---
id: sched-20261014-006
subject: 'sched/eevdf: Fix vprot across reweighting'
date: 2026-10-14
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20261003114656.105721-1-kayracizmeci@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20261014150251.30099-1-kayracizmeci@gmail.com/'
authors:
  - 'Kayra Cizmeci'
maintainers_involved:
  - 'Vincent Guittot'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20261003114656.105721-1-kayracizmeci@gmail.com>'
    date: 2026-10-03
    summary: 'rel_vprot 标志转/恢复相对量修已过期 protection 复活'
    review_outcome: 'Christian Tested-by；Vincent/Prateek 质疑新标志'
  - version: v2
    msgid: '<20261014150251.30099-1-kayracizmeci@gmail.com>'
    date: 2026-10-14
    summary: '弃 rel_vprot，on_rq 简化 + enqueue 路径按权重就地重建 vprot，补双 Fixes/Suggested-by'
    review_outcome: '当日无 review；作者自测 base 问题全消失，残留 3/1500 滑动原因不明'
upstream_commit: null
fixes_commit: '80390ead2080'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'v2 未获正式 review'
    - '残留 3/1500 任务 vprot 滑动 >5% 原因未明'
  next_action: 'Vincent/Christian 复审 v2；作者澄清残留滑动'
contribution_opportunities:
  - kind: testing
    description: '用 v1 方法独立验证 v2 并尝试复现 3/1500 滑动残留'
  - kind: review
    description: '评估 curr 分支 vprot=vruntime 与 enqueue 侧权重缩放/cancel_protect_slice 正确性'
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 1
related_articles:
  - sched-20261003-007
  - sched-20261011-004
  - sched-20261012-009
  - sched-20261013-017
tags: [eevdf]
---