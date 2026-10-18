# sched/eevdf: Move to a single runqueue

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260923-001 / 20261007-009：Aishwarya Rambhadran（ARM）报告 v7.2→v7.3 在 AWS Graviton3 上个别 schbench 线程配置 p99 回退 ~30%，bisect 指向「sched/eevdf: Move to a single runqueue」commit；后续怀疑点收敛到 WA_WEIGHT/task_h_load，社区提议试 NO_WA_WEIGHT 与 cgroup_mode 规避。
- sched-20261012-022：Mike Galbraith 以 7.2+flat 对照观察到 cgroup vs cgroup 的 CPU 分配抖动被放大，但未给数字。
- sched-20261016-002：Jakub Okoński 给出可复现的量化回归——单运行队列疑似破坏 `cpu.idle` cgroup 的 wakeup preemption 语义，wakelat p99 从 12µs 恶化到 2029µs。
- sched-20261018-009（今天）：Mike Galbraith 用 wakelat+awk 脚本拿到清晰信号并 bisect 定位——他观察到的抖动**与 single-runqueue（sched-flat）无关**（7.2.11 在有无 sched-flat 时都存在），而是一条独立的回归：commit `333238da9a19`（"sched: Update time before requeueing delayed entities"，Vincent Guittot）。revert 该 commit 后 7.2.11 抖动消失，master 上需连 `68e37487810a` + `333238da9a19` 一起 force revert 才消除。

## 背景与问题

（承接 20260923-001/20261007-009/20261012-022/20261016-002）单运行队列改动落地 v7.3 后，社区一直追查 schbench/wakelat 上的 p99 尾延迟回退，之前的方向是「single-runqueue 改动本身」或 WA_WEIGHT/cgroup_mode。今天 Mike Galbraith 给出了一个关键分流：他长期看到的那条抖动（wakelat）**与 sched-flat 系列无关**——在 7.2.11 上无论是否打 sched-flat 补丁都存在；真正的来源是一条晚近进入的延迟实体 requeueing 修正 commit `333238da9a19`，它在 7.2.11 stable 里也在。

该 commit 的动机本是「给 delayed entity 在 requeueing 前更新时间到 now，否则它看起来更年轻、获得的滞后补偿更少」——即修正补偿量，却引入了 jitter 回退。

## 技术方案

（承接，今日为定位而非补丁）Mike 的方法：把 wakelat + awk 塞进脚本取得「完全清晰的信号」后做 bisect，确认 `333238da9a193ffc58792995f3e951e4cb87bfd2` 是第一个 bad commit。他特别注明「以下是 box 把抖动来源指出来，未必是 breakage」。revert 该 commit 后 7.2.11 抖动消失；master 上需同时 force revert `68e37487810a` + `333238da9a19` 才消除。

## 版本演进与当前进展

*current_version: null*（系列已合入，本日为诊断性回帖，无新补丁版本）。

## Maintainer 意见与讨论焦点

无维护者（Peter Zijlstra / Vincent Guittot）对本条的新回复。Mike 的表态是「这条抖动跟你们（single-runqueue 讨论）看到的不是同一条，且来源是 `333238da9a19`」。这实际上把 single-runqueue 从「他这条 jitter」的嫌疑中摘出，同时把矛头指向延迟实体补偿修正的 jitter 回退。作者措辞谨慎（「未必是 breakage」），尚无 maintainer 认可/处理。

## 合入评估

*likelihood=merged*（针对 single-runqueue 系列本身：已合入主线并随 v7.3 出货）。今日新增的实质进展是另一条独立的疑似回归（`333238da9a19`）被定位出来，与 single-runqueue 系列无直接合入关系。*blocking_issues*：`333238da9a19` 的 jitter 回退尚未被 maintainer 接手，需进一步复现/确认是否为预期内的补偿权衡。*next_action*：Mike 或受影响方把 `333238da9a19` 的 jitter 复现与数据整理后单独开线程（或回复本线程）提请 Vincent Guittot/Peter Zijlstra 评估。

## 效果评估

今日给出的证据是「revert/force revert 后抖动消失」的对照（作者称 bisect 确认 `333238da9a19` 为第一 bad commit），但未贴具体 wakelat 数值与本线程回复；此前 Jakub（20261016-002）的 wakelat 12µs→2029µs p99 恶化是与之相关的量化锚点。`333238da9a19` 的 jitter 幅度数字未在今日邮件中给出。

## 我可以参与的点

- `testing`：在 7.2.11 / master 上复现 wakelat 抖动，独立验证「revert `333238da9a19` 后抖动消失」的结论，并给出量化数据（p99/p50 前后对比）。
- `discussion`：`333238da9a19` 的「延迟实体 requeueing 前更新时间」补偿是否会放大 wakeup 抖动，可结合 delayed dequeue 语义在邮件列表提出分析或修复思路。

## 参考链接

- 系列根线程：https://lore.kernel.org/all/20260605105513.354837583@infradead.org/
- Mike Galbraith 今日 bisect 定位：https://lore.kernel.org/all/b1002150c3e4f877d04790cd8e85d2149d17722f.camel@gmx.de/

---
id: sched-20261018-009
date: 2026-10-18
subject: "sched/eevdf: Move to a single runqueue"
subsystem: sched
type: discussion
status: merged_stable
severity: none
thread_root_msgid: "<20260605105513.354837583@infradead.org>"
lore_url: "https://lore.kernel.org/all/20260605105513.354837583@infradead.org/"
authors: ["Peter Zijlstra"]
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: merged
  blocking_issues: ["分支下 333238da9a19 的 jitter 回退待 maintainer 接手复现确认"]
  next_action: "把 333238da9a19 的 jitter 复现数据单独提请 Vincent Guittot/Peter Zijlstra 评估"
contribution_opportunities:
  - kind: testing
    description: "复现 wakelat 抖动并独立验证 revert 333238da9a19 后消失，给出 p99/p50 量化数据"
  - kind: discussion
    description: "分析 333238da9a19 延迟实体补偿与 wakeup 抖动的关系并提出修复思路"
generated_at: "2026-10-19T09:00:00"
source_email_count: 1
related_articles: ["sched-20261007-009", "sched-20261012-022", "sched-20261016-002"]
tags: [eevdf, regression]
---