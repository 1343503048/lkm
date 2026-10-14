# sched_ext: sub-scheduler tasks are severely under-scheduled vs root-owned tasks

> **subject**：sched_ext: sub-scheduler tasks are severely under-scheduled vs root-owned tasks

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261008-006：Tao Cui 报告疑似 dispatch 饥饿：父子 cid 调度里，busy-loop 任务在子调度器 attach 前进 cgroup 时，子调度器每轮 claim 到该任务但 duty 仅 ~0.3%，同属 root 的等价任务 ~100%；Tejun 要求补调度器源码与完整复现步骤。
- sched-20261009-014：Tao Cui 交出完整材料（`scx_k2` 源码、KVM 环境、11 步复现流程）。
- sched-20261010-013：Tejun 定位完毕——饥饿来自两个调度器的用法（父级从不 `scx_bpf_sub_dispatch()`、grant 缺 `SCX_CAP_ENQ`），**非内核缺陷**。
- sched-20261014-015（今天）：报告者 Tao Cui 承认 Tejun 的定位，解释自己此前追错方向（以为 core 会自动把 balance 路由给 child），并表示会更新调度器（父级 sub_dispatch + 授 `SCX_CAP_ENQ`）后重跑测试。报告进入确认收尾。

## 背景与问题
（承接 20261008-006 → 20261010-013）父子 cid 调度最小复现里，busy-loop 任务在子调度器 attach 前进 cgroup 时，子调度器每轮 claim 到该任务但 duty 只有 ~0.3%，同属 root 的等价任务 ~100%。今日报告者确认根因（用法问题）并解释自己此前的误判。

## 技术方案
无补丁。Tao Cui 今日确认 Tejun 的定位并自我澄清两处此前没看懂的契约：

- child 的 `ops.dispatch()` 只在父级显式调 `scx_bpf_sub_dispatch()` 委派时才运行——此前误以为 core 会在 child 拥有任务后自动把 balance 路由给它，因而追错了方向。
- `SCX_CAP_ENQ` vs `SCX_CAP_ENQ_IMMED` 的区分解释了为何自己的 A/B 实验没证明想证明的东西——没注意到 `scx_bpf_dsq_move_to_local()` 需要 `SCX_CAP_ENQ`，所以 reject/reenqueue 路径现在完全说得通。

作者计划：更新调度器使其按意图 dispatch 到 child、并在合适处授 `SCX_CAP_ENQ`，然后重跑测试。

## 版本演进与当前进展
单条 `[REPORT]`，无补丁。今日报告者确认根因（用法问题）并表态将修正调度器后复测，报告趋于结案。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（sched_ext 维护者，前日）：定位为两个调度器的用法问题（父级不 sub_dispatch、grant 缺 ENQ），非内核缺陷。
- **Tao Cui**（报告者，今日）：认可定位、解释自身误判来源，将修正调度器后重跑。
- 无分歧；仅剩复测确认（可能附带文档/示例改进需求）。

## 合入评估
*likelihood=unknown*。无补丁；根因已被维护者定位为使用问题、报告者亦确认，因此无「合入」可言。*blocking_issues*：待报告者按修正用法复测确认。*next_action*：Tao 复测确认；若 `sub_dispatch + SCX_CAP_ENQ` 契约易误用，可考虑文档/示例澄清。

## 效果评估
此前 Tejun 定位：修正用法后 spinner 在 child 下满 duty 运行（此前 ~0.3%）。今日无新增数据，为报告者确认与表态。

## 我可以参与的点
- discussion：若认为「父级必须显式 sub_dispatch + 授 ENQ」的契约易误用，可提议补充 scx_qmap 示例注释或 internal.h 文档，降低后续调度器作者的踩坑成本。

## 参考链接
- 报告：https://lore.kernel.org/all/163e2397-0e3e-4cc0-842b-0d36598d13d7@linux.dev/
- Tejun 定位回帖：https://lore.kernel.org/all/14824587e8eb436b2621fef1bb681cce@kernel.org/
- 今日报告者回应：https://lore.kernel.org/all/e0cdb928-5e4d-487e-90ca-694a11b4ade1@linux.dev/

---
id: sched-20261014-015
subject: 'sched_ext: sub-scheduler tasks are severely under-scheduled vs root-owned tasks'
date: 2026-10-14
subsystem: sched
type: bug
status: under_review
severity: none
thread_root_msgid: '<163e2397-0e3e-4cc0-842b-0d36598d13d7@linux.dev>'
lore_url: 'https://lore.kernel.org/all/163e2397-0e3e-4cc0-842b-0d36598d13d7@linux.dev/'
authors:
  - 'Tao Cui'
maintainers_involved:
  - 'Tejun Heo'
current_version: report
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '待报告者按修正用法复测确认'
  next_action: 'Tao 复测确认；必要时补充 sub_dispatch/SCX_CAP_ENQ 契约文档'
contribution_opportunities:
  - kind: discussion
    description: '提议补充 sub_dispatch/SCX_CAP_ENQ 契约的文档或 scx_qmap 示例注释'
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 1
related_articles:
  - sched-20261008-006
  - sched-20261009-014
  - sched-20261010-013
tags: [sched_ext]
---