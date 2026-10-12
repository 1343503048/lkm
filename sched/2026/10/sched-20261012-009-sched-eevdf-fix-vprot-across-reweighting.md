# sched/eevdf: Fix vprot across reweighting

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261003-007：Kayra 发重组后的独立补丁「Fix vprot across reweighting」——`rel_vprot` 标志让 reweight 时 protection 转/恢复相对量，修掉「已过期 protection 复活」。
- sched-20261011-004：Christian Loehle 给 `Tested-by` 但要求移除其 SOB；Kayra 同意 v2 清理 trailer。
- sched-20261012-009（今天）：讨论升级——Vincent Guittot 提出「根本不需要 `rel_vprot` 标志，curr 时直接 `se->vprot = se->vruntime` 即可」的更简方案（附两个 diff）；Prateek 也质疑为何需要新标志；Kayra 解释 `on_rq` 会变 false、「alive protection」让单独 diff 不成立，并指出根因是 `sched_change_begin()` 把 `cfs_rq->curr` 置 NULL。

## 背景与问题

（承接 20261003-007/20261011-004）EEVDF slice protection 是绝对 vruntime 边界；reweight（nice/cgroup 权重变化）时 `reweight_eevdf()` 缩放存活 protection，但「已过期」的 vprot 原样不动会复活。今日新增的关键交互：已合入 tip/sched/core 的 819224e506bc（"Remove dead code on enqueue_task_fair"）让 `reweight_eevdf()` 现在会被 curr 调用，改变了此前「curr 时 always true」的假设。

## 技术方案

（承接 20261003-007）原方案给 `struct sched_entity` 加 `rel_vprot` 标志，dequeue 侧把 `vprot -= avruntime` 并置标志、re-enqueue 侧加回。今日 Vincent 给出两版更简 diff：(A) 在 `reweight_eevdf()` 的 `if (on_rq)` 分支把 `if (rel_vprot) se->vprot += avruntime` 改为 `if (rel_vprot) ... += avruntime; else if (curr) se->vprot = se->vruntime;`；(B) 把 dequeue 侧 `if (curr && protect_slice(se))` 放宽为 `if (curr)`。Kayra 回帖引用此前 lore 讨论，说明 `on_rq` 会变 false、alive protection 使「这个 diff 单独不成立」，并解释 bug 路径：`sched_change_begin()` 把 `cfs_rq->curr = NULL`，进入 `enqueue_task_fair()` 时 curr/on_rq 都 false，权重已改而 vprot 未被触及，`set_next_task_fair()` 才重新成为 curr。

## 版本演进与当前进展

- v1（10-03）落地 `rel_vprot` 方案。
- 10-11：Christian 给 `Tested-by` + 要求移除 SOB。
- 10-12：Vincent/Prateek 质疑方案复杂度并提简化 diff，Kayra 解释根因；尚未收敛到新版本。

## Maintainer 意见与讨论焦点

- **Vincent Guittot**：认为 `rel_vprot` 与一堆改动不必要，提出「curr 时 `se->vprot = se->vruntime`」即可（附两版 diff）；并指出 819224e506bc 之前 reweight_eevdf 不会为 curr 调用。
- **K Prateek Nayak**：质疑为何需要新 `se->rel_vprot`——protection 只需给当前实体、`set_next_task()` 会覆盖，不清楚为何关心迁移路径。
- **Kayra Cizmeci**：坚持 alive protection 与 `on_rq=false` 使单独 diff 不够，承认「可能有更干净的方式」。
- **Christian Loehle**：此前 `Tested-by` 与 SOB 移除意见仍在。

## 合入评估

*likelihood=medium*。问题真实（两作者验证 + 与新合入 commit 交互），但实现方案正被两位维护者质疑、可能整体简化重写。*blocking_issues*：rel_vprot 方案 vs Vincent 简化方案未收敛。*next_action*：Kayra 用 Vincent 的 diff 实测并回应，确定最小实现后发 v2。

## 效果评估

今日无新 benchmark；此前 Kayra 自测（pin 两任务、改 nice 3000 次）Base 下 Normal 6002/6002、NRTP 53/53 全错 → 加补丁 0/6003、0/55 全对。Vincent/Prateek 的质疑是方案正确性层面，未见反证数据。

## 我可以参与的点

- `review`：严格比较 Vincent「curr 时 `se->vprot = se->vruntime`」与 `rel_vprot` 方案在 throttle/unthrottle、alive-protection 复活路径上的等价性。
- `testing`：补「dead protection 复活」与「cgroup reweight + throttle」组合用例。
- `discussion`：厘清 819224e506bc 合入后 `reweight_eevdf()` 被 curr 调用的新语义。

## 参考链接

- lore（v1）: https://lore.kernel.org/all/20261003114656.105721-1-kayracizmeci@gmail.com/
- lore（Vincent 简化 diff）: https://lore.kernel.org/all/CAKfTPtC_DjYGmnHuV8x9HEoea87pfrpfNWwHT=sGeSP8UOL2Og@mail.gmail.com/
- lore（Prateek 质疑）: https://lore.kernel.org/all/95dba20d-ad01-43a3-b870-4a696563c41a@amd.com/
- lore（Kayra 解释根因）: https://lore.kernel.org/all/20261012150121.6516-1-kayracizmeci@gmail.com/

---
id: sched-20261012-009
date: '2026-10-12'
subject: 'sched/eevdf: Fix vprot across reweighting'
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
- Christian Loehle
- K Prateek Nayak
current_version: v1
patch_series:
- version: v1
  msgid: <20261003114656.105721-1-kayracizmeci@gmail.com>
  date: '2026-10-03'
  summary: rel_vprot 标志：reweight 时 protection 转/恢复相对量
  review_outcome: Vincent/Prateek 质疑 rel_vprot 必要性，提出更简化的实现；方案未定
fixes_commit: 80390ead2080
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Vincent 提出无需 rel_vprot 的更简 diff，Prateek 质疑为何需要新标志
  - 实现方案可能整体简化重写
  next_action: Kayra 回应 Vincent 的简化 diff 并收敛实现方向后改版
contribution_opportunities:
- kind: review
  description: 评估 Vincent 的「curr 时 se->vprot = se->vruntime」简化方案与 rel_vprot 方案的等价性
- kind: testing
  description: 补「dead protection 复活」路径的测试（作者此前明说未覆盖）
- kind: discussion
  description: 澄清 reweight 与已合入 819224e506bc（Remove dead code）交互后 curr 路径的行为
generated_at: '2026-10-13T01:40:00'
source_email_count: 5
related_articles:
- sched-20261003-007
- sched-20261011-004
tags:
- eevdf
- regression
---
