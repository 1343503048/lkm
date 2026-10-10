# sched_ext: sub-scheduler tasks are severely under-scheduled vs root-owned tasks

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261008-006：Tao Cui 报告疑似 dispatch 饥饿：父子 cid 调度里，busy-loop 任务在子调度器 attach **之前**进 cgroup 时，子调度器每轮都 claim 到该任务但运行 duty 只有 ~0.3%（10s 窗口 0 或 ~20-27 tick），同属 root 的等价任务 ~100%；attach 之后移入则正常，饥饿比约 300x。Tejun 要求补调度器源码与完整复现步骤。
- sched-20261009-014：Tao Cui 交出完整材料——`scx_k2` 源码、KVM 环境、for-7.4 内核 + caps-clear 补丁的具体 commit、11 步复现流程。待 Tejun 定位。
- sched-20261010-013（今天）：**Tejun 定位完毕，结论是「饥饿来自两个调度器，而非内核」**——child 的 `ops.enqueue()` 把每个任务塞进自己的 user DSQ，其唯一消费者是 child 的 `ops.dispatch()`，而后者只在父级从自己 `ops.dispatch()` 调 `scx_bpf_sub_dispatch()` 时才运行，`scx_k2` 的父级从不调用；且即便调用，`scx_bpf_dsq_move_to_local()` 也因 grant 缺 `SCX_CAP_ENQ` 全被拒。修正使用方式（父级调 sub_dispatch + 授 SCX_CAP_ENQ）后 spinner 在 child 下满 duty 运行。属使用问题，非内核缺陷。

## 背景与问题
（承接 sched-20261008-006 → 20261009-014）父子 cid 调度的最小复现里，busy-loop 任务在子调度器 attach 前进 cgroup 时，子调度器每轮 claim 到该任务但 duty 只有 ~0.3%，而同属 root 的等价任务 ~100%。今天 Tejun 给出根因：子调度器的任务吞吐由「父级是否调 `scx_bpf_sub_dispatch()`」以及「grant 是否含 `SCX_CAP_ENQ`」决定，`scx_k2` 的父级两者都没做，任务在 child 的 DSQ 里排队却无人消费。

## 技术方案
无补丁。Tejun 的定位（Claude 生成分析，`<14824587e8eb436b2621fef1bb681cce@kernel.org>`）：

- child 的 `ops.enqueue()` 把每个任务插进自己的 user DSQ，唯一消费者是 child 的 `ops.dispatch()`；
- child 的 dispatch 只在父级从自己 `ops.dispatch()` 调 `scx_bpf_sub_dispatch()` 时运行——`scx_k2` 的父级从不调用（可对照 `scx_qmap` 如何 dispatch 其 children）；
- 即便父级调了 sub_dispatch，`scx_bpf_dsq_move_to_local()` 也因 grant 缺 `SCX_CAP_ENQ` 被拒（`SCX_CAP_ENQ_IMMED` 只覆盖 IMMED 插入），任务进 reject DSQ 被重排队，`SCX_EV_REENQ_REPEAT` 攀升、仍饥饿；
- 同时补 sub_dispatch 调用 + 授 `SCX_CAP_ENQ` 后，spinner 在 child 下满 duty 运行；初期的「看似健康」窗口是 attach 期间排空的 bypass DSQ 经 keep-last 路径的表现。

## 版本演进与当前进展
单条 `[REPORT]`，无补丁。今天 Tejun 完成根因定位并给出「非内核 bug、属使用问题」的结论与修复方向（父级调 `scx_bpf_sub_dispatch()` + 授 `SCX_CAP_ENQ`）。球回到 Tao Cui 侧确认。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（sched_ext 维护者）：基于完整材料定位——饥饿来自两个调度器的用法（父级从不 sub_dispatch、grant 缺 ENQ），而非内核；给出修正方向并附 SysRq-D dump 证据（stall 期间 spinner 在 child DSQ 0 满 slice、cpu0 跑 root 任务）。
- **Tao Cui**（报告者）：尚未回应。
- 未决：待 Tao 按修正用法复测确认后，本报告即告结（可能附带文档/示例改进需求）。

## 合入评估
*likelihood=unknown*。无补丁；根因已被维护者定位为使用问题，非内核缺陷，因此无「合入」可言。*blocking_issues*：待报告者按修正用法复测确认。*next_action*：Tao 按「父级 sub_dispatch + 授 SCX_CAP_ENQ」复测；若 API 语义易误用，可考虑文档/示例澄清。

## 效果评估
Tejun 的定位提到：修正用法后 spinner 在 child 下满 duty 运行（此前 ~0.3%）；stall watchdog 此前在作者 6s 窗口外抓到「k2 disabled（runnable task stall），sh[1401] failed to run for 30.696s」。均为定性/观测描述，无新增基准数据。

## 我可以参与的点
- 按 Tao 的 11 步复现 + Tejun 的修正用法（父级 sub_dispatch + 授 SCX_CAP_ENQ）验证饥饿消失；
- 若认为「父级必须显式 sub_dispatch + 授 ENQ」的契约易误用，可提议补充文档或 scx_qmap 示例注释。

## 参考链接
- 报告: https://lore.kernel.org/all/163e2397-0e3e-4cc0-842b-0d36598d13d7@linux.dev/
- Tejun 定位回帖: https://lore.kernel.org/all/14824587e8eb436b2621fef1bb681cce@kernel.org/

---
id: sched-20261010-013
date: '2026-10-10'
subject: 'sched_ext: sub-scheduler tasks are severely under-scheduled vs root-owned tasks'
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
    - '待报告者按修正用法（父级 sub_dispatch + 授 SCX_CAP_ENQ）复测确认'
  next_action: 'Tao 复测确认；必要时补充文档/示例澄清该契约'
contribution_opportunities:
  - kind: discussion
    description: '验证修正用法后饥饿消失，或提议补充 sub_dispatch/ENQ 契约的文档'
generated_at: '2026-10-11T09:00:00'
source_email_count: 1
related_articles:
  - sched-20261008-006
  - sched-20261009-014
tags:
  - sched_ext
---