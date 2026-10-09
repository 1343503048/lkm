---
id: sched-20261002-011
date: '2026-10-02'
subject: 'sched/fair: Rework/fix task_h_load()'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260929084923.092062266@infradead.org>
lore_url: https://lore.kernel.org/all/20261001211615.249877-1-kayracizmeci@gmail.com/
authors:
- Peter Zijlstra
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <20260929084923.092062266@infradead.org>
  date: '2026-09-29'
  summary: 4 补丁 v2：back-link 移入 for_each_sched_entity()、持锁重算 h_load
  review_outcome: 10-02 Kayra 给出 root-cfs_rq 捷径 sketch（untested），Peter 未回应
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter 对 v2 后续动作未明
  - Kayra 捷径未测试未回应
  next_action: Peter 回应 Kayra 的 sketch
contribution_opportunities:
- kind: testing
  description: 应用 Kayra diff 在混合负载下验证 task_h_load() 值分布与开销
- kind: review
  description: 分析根队列 h_load 更新位点与捷径的一致性
generated_at: '2026-10-03T01:00:00'
source_email_count: 1
related_articles:
- sched-20260902-007
- sched-20260929-012
- sched-20260930-011
tags:
- fair
- cgroup
title: 'sched/fair: Rework/fix task_h_load()'
layout: article
---

> **subject**：`sched/fair: Rework/fix task_h_load()`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/02/sched-20260902-007-sched-fair-rework-fix-task-h-load.html">sched-20260902-007</a>：Peter Zijlstra 的 4 补丁系列中 `4/4` 重做 `task_h_load()`，v1 的 `for_each_sched_entity_bl()` 在 `set_next_task_fair()` 里 clobber `se`/`cfs_rq`，致 192 核机器启动 panic（Chen Yu、Vincent 双独立复现）。
- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-012-sched-fair-rework-fix-task-h-load.html">sched-20260929-012</a>：Peter 重发 v2（完整 4 补丁）——修复编译/运行期失败，back-link 机制移入 `for_each_sched_entity()`。
- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-011-sched-fair-rework-fix-task-h-load.html">sched-20260930-011</a>：多名 reviewer 澄清 v2 设计语义——删除 `update_cfs_rq_h_load()`（调用方不持 `rq->lock`）是初衷、root 更新频率变化有意、`h_load` 懒传播。
- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-011-sched-fair-rework-fix-task-h-load.html">sched-20261002-011</a>（今天）：Kayra Cizmeci 在 v2 4/4 讨论线上给出一个 root-cfs_rq 捷径 sketch：`task_h_load()` 里若 `cfs_rq` 即根队列直接返回 `p->se.avg.load_avg`、`__update_cfs_rq_h_load()` 里父为根时直接用 `se->avg.load_avg`——理由是 v2 后 root 只在 `list_for_each_entry_reverse()` 块里被更新，「旧代码最多 1 jiffy 过期（但 broken）、新代码 less broken 但没有过期清晰度」。自评「半夜写的、untested」；Peter 当日未回帖。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-011-sched-fair-rework-fix-task-h-load.html">sched-20260930-011</a>）`task_h_load()` 计算任务沿 cgroup 调度层级的层级负载。v2 把 back-link 跟踪移入 `for_each_sched_entity()` 并在持锁位点重算 h_load；09-30 的讨论确认了 root 更新变少、懒传播、`update_cfs_rq_h_load()` 删除三处取舍。今天的增量：Kayra 指出 root cfs_rq 的 `h_load` 在 v2 下只在 `__update_cfs_rq_h_load()` 的 `list_for_each_entry_reverse()` 块里被更新——对挂在根队列上的任务（无 cgroup 层级），`task_h_load()` 仍走 `div64_ul(p->se.avg.load_avg * cfs_rq->h_load, ...)` 的通用除法路径，而根队列的 h_load 语义上就是根自身的 `avg.load_avg`，除法是冗余的且引入不必要的陈旧窗口。

## 技术方案

（承接 v2 主体）Kayra 的 sketch（`<20261001211615.249877-1-kayracizmeci@gmail.com>`，对 v2 4/4 线程的回复，附 diff）：

```c
static inline void __update_cfs_rq_h_load(struct cfs_rq *cfs_rq, ...)
{
	...
	if (p_cfs_rq == &p_cfs_rq->rq->cfs)
		load = se->avg.load_avg;
	else
		load = div64_ul(p_cfs_rq->h_load * se->avg.load_avg,
				p_cfs_rq->avg.load_avg + 1);
}

static unsigned long task_h_load(struct task_struct *p)
{
	struct cfs_rq *cfs_rq = task_cfs_rq(p);

	if (cfs_rq == &cfs_rq->rq->cfs)
		return p->se.avg.load_avg;

	return div64_ul(p->se.avg.load_avg * READ_ONCE(cfs_rq->h_load),
			cfs_rq_load_avg(cfs_rq) + 1);
}
```

要点：根队列任务绕过除法与 h_load 读，直接返回任务自身 load_avg。Kayra 自评：「I done this in the middle of the night, untested. I should sleep. Ah..」；并自我吐槽旧代码「maximum 1 jiffy obsolescence (But it was broken, as you say it) while the new one is less broken but doesn't gives any obsolescence clarity」。

## 版本演进与当前进展

- v1（8/28，`<20260828074059.232353141@infradead.org>`）：4 补丁，4/4 引入 panic（<a class="article-ref" href="/lkm/2026/09/02/sched-20260902-007-sched-fair-rework-fix-task-h-load.html">sched-20260902-007</a>）。
- v2（9/29，`<20260929084923.092062266@infradead.org>`）：4 补丁齐全（<a class="article-ref" href="/lkm/2026/09/29/sched-20260929-012-sched-fair-rework-fix-task-h-load.html">sched-20260929-012</a>）。
- 09-30：Peter/Prateek/Kayra 澄清式 review（<a class="article-ref" href="/lkm/2026/09/30/sched-20260930-011-sched-fair-rework-fix-task-h-load.html">sched-20260930-011</a>）。
- 10-02（今天）：Kayra 的 root 捷径 sketch（`IRT: <20260930114416.211829-1-kayracizmeci@gmail.com>`）。Peter 未回帖；无新版本。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci**（独立 reviewer）：延续 09-30 的语义讨论，给出具体代码方案而非只提问题；明确未测试。
- **Peter Zijlstra**（作者/sched 维护者）：当日未回帖。待决问题：root 捷径是否与 v2 的懒更新模型兼容（根队列 h_load 的更新位点是否因此需要调整）、`cfs_rq_load_avg()` 在根上的语义。
- 无 NAK；属 v2 收尾期的优化讨论。

## 合入评估

*likelihood=medium*（指 v2 系列整体）。v2 由 Peter 本人署名、修复 192 核 panic 的实际故障、经多轮语义澄清；Kayra 的捷径是增量优化、未测试、未获回应，能否折入 v2 或单独成补丁待定。*blocking_issues*：Peter 对 v2 的后续动作（是否还有 v3）未明；Kayra 捷径未测试未回应。*next_action*：Peter 回应 Kayra 的 sketch（采纳为 v3 增量或说明为何不需要）。

## 效果评估

本日无数据。Kayra 的捷径收益是机制性的（根队列任务少一次除法与陈旧读），未给量化对比；v2 系列整体无 benchmark（正确性修复为主）。

## 我可以参与的点

- `testing`：把 Kayra 的 diff 应用到 v2 之上，在深 cgroup 层级 + 根队列任务混合负载下对比 `task_h_load()` 返回值分布与调用开销（perf stat / ftrace 统计），替她补上「untested」缺的验证。
- `review`：分析根队列 h_load 更新位点与捷径的一致性——若 `__update_cfs_rq_h_load()` 对根也短路，`list_for_each_entry_reverse()` 块的 root 更新是否可整体移除。

## 参考链接

- Kayra 的 root 捷径 sketch: https://lore.kernel.org/all/20261001211615.249877-1-kayracizmeci@gmail.com/
- Peter 的 v2（9/29）: https://lore.kernel.org/all/20260929084923.092062266@infradead.org/
