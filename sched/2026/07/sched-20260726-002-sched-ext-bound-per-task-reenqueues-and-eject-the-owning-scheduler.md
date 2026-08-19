# sched_ext: Bound per-task reenqueues and eject the owning scheduler

## TL;DR
Tejun Heo 的 sched_ext 自我保护补丁 v2：给单个任务的 re-enqueue 次数设上限，超限即认定 BPF 调度器有缺陷并将其 eject 回退到默认调度。属于提升 SCX 健壮性的防御性机制，方向获认可，合入可能性较高。

## 背景与问题
sched_ext 允许用 BPF 自定义调度策略，但一个有 bug 的 BPF 调度器可能让任务在 enqueue → 被拒 → 再 enqueue 之间无限循环，消耗 CPU 却不推进任务，严重时拖垮整机。此前缺少针对这种"坏调度器"的兜底约束。本系列引入 per-task re-enqueue 的硬边界作为最后防线。

## 技术方案
为每个任务跟踪其在 SCX 内被 re-enqueue 的次数，设定一个上限；一旦越界，判定当前 owning BPF 调度器行为病态，触发 eject——卸载该 BPF 调度器并回退到内建默认调度类，保住系统可用性。关键取舍是阈值的选择：太低会误伤合法的高频 re-enqueue（某些设计确实会频繁重排），太高则失去保护意义。方案倾向把它定位为"防灾开关"而非常态限流。

## 版本演进与当前进展
v1 提出计数与上限思路；v2 明确超限后直接 eject 调度器并回退，把机制从"限制"升级为"自我保护+熔断"。当前处于 v2 review 阶段。

## Maintainer 意见与讨论焦点
作为 SCX 维护者 Tejun 本人主导，机制本身争议不大，被视为必要的健壮性改进。讨论焦点是：上限阈值取多少合理、如何避免误伤合法高频 re-enqueue 的调度器、以及 eject 发生时应给用户空间/运维何种可观测信号。未见 NAK。

## 合入评估
合入可能性较高，由 SCX 子系统维护者自己推动，方向明确。主要待定项是阈值与诊断信息细节，收敛后进入 sched_ext 分支的阻力不大。

## 效果评估
本系列属健壮性防护，非性能优化，邮件未给出性能数字。其价值在于把"坏 BPF 调度器拖死系统"这类故障从不可恢复转为自动降级，暂无量化数据，也不需要以性能数字衡量。

## 我可以参与的点
- 构造会触发高频 re-enqueue 的 BPF 调度器压测用例，验证上限触发与 eject 的可靠性及是否误伤正常负载
- 就 eject 时的诊断信息输出形式参与讨论

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched_ext: Bound per-task reenqueues and eject the owning scheduler"
id: sched-20260726-002
date: 2026-07-26
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<uid-476@qq-imap>"
lore_url: "unknown"
authors: [Tejun Heo]
maintainers_involved: [Tejun Heo, Andrea Righi, David Vernet]
current_version: v2
patch_series:
  - version: v1
    msgid: "unknown"
    date: unknown
    summary: "初版提出对每任务 re-enqueue 次数设上限，防止 BPF 调度器逻辑缺陷导致任务在 enqueue 路径无限打转。"
    review_outcome: "方向获认可，讨论集中在阈值取值与触发上限后如何处置（是否直接 eject 调度器）。"
  - version: v2
    msgid: "<uid-476@qq-imap>"
    date: 2026-07-26
    summary: "为 per-task reenqueue 设定边界，一旦超过上限即判定 owning BPF 调度器行为异常并将其 eject，回退到默认调度，避免系统被坏调度器拖死。"
    review_outcome: "作为自我保护机制被普遍认可，细节讨论围绕上限阈值与 eject 时的用户可观测性。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "re-enqueue 上限的具体阈值仍需社区确认，避免误伤合法的高频 re-enqueue 场景"
  next_action: "确认阈值与 eject 后的诊断信息输出，收敛后可望进入 sched_ext for-next"
contribution_opportunities:
  - kind: testing
    description: "编写会触发高频 re-enqueue 的 BPF 调度器压测用例，验证上限触发与 eject 是否可靠、是否误伤正常负载"
  - kind: discussion
    description: "就 eject 时向用户空间暴露何种诊断信息（dmesg/exit info）提出建议"
generated_at: "2026-07-27T01:10:00"
source_email_count: 2
related_articles: []
tags: [sched_ext]
---
