# Improving latency of short slice tasks

## TL;DR
本文为增量更新，完整背景见 sched-20260921-001。Vincent Guittot 的 8 补丁 EEVDF 短切片延迟改进系列当天收到 Peter Zijlstra 的多条深入 review：对 patch 4/8（衰减睡眠实体的正 lag）质疑其「全量睡眠时间参与衰减」会让衰减过快、建议至少用 `W+w` 甚至完整衰减权重和，并提出「第二棵树 + 零 lag 点前进」的激进替代方案；对 patch 5/8（idle 唤醒时重置 lag）给出 `vlag_seq` 的代码草案；对 6/8 建议把缓存放 `struct rq` 避免 cache miss；对 8/8 建议复用 `select_idle_sibling` 已有扫描。Vincent 表示会研究并部分采纳，系列仍处 review 迭代中。

## 背景与问题
背景见 sched-20260921-001。核心是修正 EEVDF 下短切片任务/睡眠实体 lag 处理的一系列边角问题，改善调度延迟。

## 技术方案
方案总体见 sched-20260921-001。本日 review 聚焦四个 patch 的取舍：
- **patch 4/8 衰减睡眠实体正 lag**：Peter 指出睡眠任务 runnable 时本应只占 `w/W` 的 runtime 份额而非 `w/w`，直接用全量睡眠时间衰减会过快；且 MIGRATED 情形重要，可近似 `(W1+W2)/2 + w`。
- **patch 5/8 idle 唤醒重置 lag**：Peter 给出 `vlag_seq` 草案（`se->vlag_seq = cfs_rq->idle_seq`，`place_entity()` 中序号不匹配即置 0），能覆盖 `rq->curr == rq->idle` 及其它情形。
- **patch 6/8 per-cpu cached min_slice**：Peter 建议放入 `struct rq`、靠近 `select_idle_siblings()` 已访问的数据，避免缓存缺失。
- **patch 8/8 选 CPU 时 min slice 检查**：Peter 认为与 `select_idle_siblings()` 重复、建议复用初次扫描记录的最小 slice CPU，避免重复扫描。

## 版本演进与当前进展
系列仍为 v1（0/8 cover `<20260921152238.3804392-1-vincent.guittot@linaro.org>`）。本日为密集 review 讨论，无新版发出。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（多条）：核心关注点集中在 patch 4/8——「Is not this a rather prevalent case?」「Urgh, are we going to try and bring back all that sleep time stuff again?」，认为衰减应至少用 `W+w`、理想是全部衰减权重和；提出第二棵树方案但自评「Definitely non-trivial, and I'm not at all sure its worth it」，并问 Juri 是否 BFQ 有过类似做法。对 5/8 给出 `vlag_seq` 草案并提醒「migration case is broken」。
- **Vincent Guittot**（多条回复）：承认取 prev rq 时钟代价高所以想从简；自述思考后认同 Peter 的「把睡眠任务留在另一棵树算零衰减 vruntime」才是正解，但担心管理新树与跨 rq 取锁开销；表示会进一步研究（「I'm going to study this further」），并倾向于把 `select_idle_capacity/select_idle_cpu/select_slice_cpu` 合并为单循环。
- **Kayra Cizmeci**：在 patch 5/8 线程参与讨论（`<20260922143230.5383-1-kayracizmeci@gmail.com>`）。

## 合入评估
likelihood=medium。系列目标明确、有完整 benchmark 支撑（见 sched-20260921-001），但 patch 4/8 的 lag 衰减算法存在实质分歧（近似 vs 第二棵树 vs load_avg），Peter 尚未认可当前近似方向。blocking_issues：patch 4/8 衰减算法设计分歧未收敛；若干 patch 的实现位置/重复扫描待调整。next_action：Vincent 按 Peter 意见改进 patch 4/8 与 8/8，重新发版。

## 效果评估
无本日新增数据；系列整体 benchmark（99th/99.9th/max 延迟改善、hackbench +11%~+30%）见 sched-20260921-001。

## 我可以参与的点
- **review**：对 patch 4/8 的衰减算法（`W+w`、完整权重和、`(W1+W2)/2+w`、第二棵树、load_avg 近似）做理论/数值对比，帮助在近似与复杂度之间定夺。
- **testing**：复现系列 benchmark（cyclictest/hackbench），尤其验证 patch 4/8 改动后的延迟与 hackbench 增益是否保持。

## 参考链接
- lore thread（cover）: https://lore.kernel.org/all/20260921152238.3804392-1-vincent.guittot@linaro.org/
- Peter 对 4/8 回复: https://lore.kernel.org/all/20260922100233.GP776954@noisy.programming.kicks-ass.net/
- Peter 对 5/8 草案: https://lore.kernel.org/all/20260922101304.GQ776954@noisy.programming.kicks-ass.net/
- Peter 对 8/8 回复: https://lore.kernel.org/all/20260922104609.GS776954@noisy.programming.kicks-ass.net/

---
id: sched-20260922-011
date: '2026-09-22'
subject: 'Improving latency of short slice tasks'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260921152238.3804392-1-vincent.guittot@linaro.org>'
lore_url: 'https://lore.kernel.org/all/20260921152238.3804392-1-vincent.guittot@linaro.org/'
authors:
  - 'Vincent Guittot'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260921152238.3804392-1-vincent.guittot@linaro.org>'
    date: '2026-09-21'
    summary: '8 补丁 EEVDF 短切片延迟改进（详见 sched-20260921-001）'
    review_outcome: 'Peter 对 4/8 衰减算法、5/8 idle 重置、6/8 缓存位置、8/8 扫描去重提出意见'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'patch 4/8 lag 衰减算法设计分歧未收敛'
    - '6/8、8/8 的实现位置/重复扫描待调整'
  next_action: 'Vincent 按 Peter 意见改进 patch 4/8 与 8/8 后重发'
contribution_opportunities:
  - kind: review
    description: '对 lag 衰减算法（W+w、权重和、第二棵树、load_avg）做对比分析'
  - kind: testing
    description: '复现 cyclictest/hackbench benchmark，验证 patch 4/8 改动后增益是否保持'
generated_at: '2026-09-23T00:00:00'
source_email_count: 16
related_articles:
  - sched-20260921-001
tags:
  - eevdf
  - cfs
  - perf
---