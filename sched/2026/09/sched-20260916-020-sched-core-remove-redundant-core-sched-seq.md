# sched/core: Remove redundant core_sched_seq

## TL;DR
Hui Su 的单枚整洁性补丁：删掉 `struct rq` 里的 `core_sched_seq` 字段。作者论证它与 `core_pick` 重复——一次 core-wide 选择后 `core_pick` 非空即可表明该 rq 还有待消费的 pick，`core_sched_seq` 只是同一条状态的一份冗余拷贝。无功能性改动。本日暂无 review，合入可能性未知。

## 背景与问题
`core_sched_seq` 记录的是「该 rq 是否已消费上次 core-wide 选择的 pick」。作者指出 `rq->core_pick` 本身就携带同样的 per-rq 状态：core-wide 选择只为仍待消费的 sibling 留下非空 `core_pick`，当前 CPU 消费、sibling 已运行所选任务、fastpath 消费 pending pick、CPU offline 路径都会清掉它。而 `core_task_seq` 与 `core_pick_seq` 另有职责（任务集变化时的序号与选择时的任务序号），二者相等即可确立 pending `core_pick` 仍然有效。因此 `core_sched_seq` 是冗余状态。

## 技术方案
删除 `core_sched_seq` 字段，直接把 `core_pick` 非空作为「还有 pick 待消费」的标记：`pick_next_task()` 里 `core_pick_seq == core_task_seq && core_pick` 即进入 fastpath 消费；提交 core-wide 选择时不再写 `core_sched_seq`。改动 `kernel/sched/core.c`（10 行改动）与 `kernel/sched/sched.h`（删 1 字段），共 4 insertions / 7 deletions。

## 版本演进与当前进展
- v1（本日 104888，`<20260915163138.2973969-1-sh_def@163.com>`）：首次发出，暂无 review 回复。

## Maintainer 意见与讨论焦点
本日暂无维护者或 reviewer 回复。补丁自带测试说明（instrumented 对比新旧 pending 谓词、core-cookie 生命周期、forced idle、CPU hotplug 压测），但需等待 core scheduling（Peter Zijlstra 等）确认语义等价性。

## 合入评估
likelihood=unknown。纯整洁性改动、有自测支撑，但 core-sched 的 pending/pick 语义相当微妙，去掉一个字段的正确性需维护者在这个领域确认，暂无任何表态。blocking_issues：无明确阻塞，但缺 core-sched 维护者评审。next_action：等 Peter 或 core scheduling 相关维护者评审确认 `core_pick` 可完全替代 `core_sched_seq`。

## 效果评估
无性能数据；属代码整洁性改动，作者侧自测表示新旧谓词无分歧、无新增告警。

## 我可以参与的点
- kind=review：核对 core-sched 的 `pick_next_task()` 各路径（含 preemption 多次 pick 同一任务集）下 `core_pick` 是否严格等价于原 `core_sched_seq` 的语义。
- kind=testing：在 core scheduling 压测 + CPU hotplug + forced idle 场景复跑，确认无谓词分歧与告警。

## 参考链接
- patch：https://lore.kernel.org/all/20260915163138.2973969-1-sh_def@163.com/

---
id: sched-20260916-020
date: '2026-09-16'
subject: 'sched/core: Remove redundant core_sched_seq'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260915163138.2973969-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20260915163138.2973969-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260915163138.2973969-1-sh_def@163.com>'
    date: '2026-09-15'
    summary: '删除冗余的 core_sched_seq，用 core_pick 直接作 pending 标记'
    review_outcome: '暂无回复'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: '等 core scheduling 维护者评审确认语义等价'
contribution_opportunities:
  - kind: review
    description: '核对各 pick_next_task 路径下 core_pick 与 core_sched_seq 的语义等价性'
  - kind: testing
    description: '在 core scheduling 压测 + hotplug + forced idle 场景复跑验证'
generated_at: '2026-09-17T09:00:00'
source_email_count: 1
related_articles: []
tags:
  - core_sched
---