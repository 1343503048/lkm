# sched_ext: Add ops.sub_child_ecaps_updated()

## TL;DR

Tejun Heo 为 sched_ext 的 sub-scheduler（父子调度器）capabilities 机制补上关键一环：grant/revoke 只记录「目标 caps」，真正生效要等 cid 下一次 dispatch，而父调度器此前无从得知生效时刻——导致子调度器在一个 cid 上留下的低 `cpuperf` 目标在 PERF 被回收后仍然残留（内核只在 root enable 时重置目标）。新增 `ops.sub_child_ecaps_updated()` 回调，在子调度器自身的 `sub_ecaps_updated()` 之后立即通知直接父级。当日 v1→v2 快速迭代（v2 砍掉 disable 报告与嵌套 dispatch 门控），并吸收 Tao Cui 对前身补丁的实测与 Tejun 对「cpuperf target 属 last-writer-wins」的裁决。

## 背景与问题

sched_ext 的 sub-scheduler 分层模型里，父调度器通过 grant/revoke 向子调度器委派 caps（如 `SCX_CAP_PERF`、`SCX_CAP_ENQ_IMMED`）。但 grant/revoke 只记录目标值，实际在 cid 下一次 dispatch 才生效，且没有任何机制告诉父调度器「何时生效」。后果：① 子调度器把某个 cid 的 cpuperf target 写低后，PERF 被回收时内核不会重置（只在 root enable 时重置），父调度器无法及时把这个残留目标复位；② 父调度器也不知道何时能再次在该 cid 上调度。这直接延续自 Tejun 此前的两个前身补丁——「Clear a sub-scheduler's caps before ops.sub_detach()」（Tao Cui 已实测并给 Tested-by/Reviewed-by）与 Tao Cui 自己发的「Reset cpuperf_target when a sub loses SCX_CAP_PERF or dies」（后被 Tejun 说服放弃）。

## 技术方案

- patch 1（`kernel/sched/ext/`）：新增 `ops.sub_child_ecaps_updated()`，在子调度器自身的 `ops.sub_ecaps_updated()` 之后、同一 dispatch 上下文里投递给直接父级，携带子 cgroup id 与「变更前/后」caps。子级 bypass 期间两条投递都被抑制、bypass 解除后一起重放；disabled 子级不报告（由父级在 `ops.sub_detach()` 里恢复其曾委派的状态）。同时让 sub 在链接前先进入 enable bypass，使 `ops.sub_attach()` 排队的 grant 在 bypass 中被消费、待启用后再重放给子级与父级。
- patch 2（`tools/sched_ext/scx_qmap.bpf.c`）：scx_qmap 在 `sub_child_ecaps_updated()` 中检测到 PERF 被回收（`before & ~after` 含 `SCX_CAP_PERF`）时把 cid 的 cpuperf target 复位为 `SCX_CPUPERF_ONE`；detach 场景因不报告，改为在 `ops.sub_detach()` 里复位 detaching 子级的 cids（含其可能持有的 pool）。
- v2 关键取舍：放弃 v1 的「disable 报告」——它要求报告在 dispatch 路径之外运行（需为 kfuncs 搭上下文、运行时门控嵌套 sub dispatch），且为避开 PM bypass 要持一把可能卡住 suspend 的锁。既然父级知道自己委派了什么，改由 `ops.sub_detach()` 恢复即可，同时砍掉 sleep lock 与 nested-dispatch gate。
- 与此配套的裁决（来自 Tao Cui 的实测回帖 28）：cpuperf target 属「last-writer-wins」状态，内核只在 enable 时初始化；回收后的恢复责任归「grant 了该 cap 的那一方」。Tao Cui 据此放弃了自己的 Reset cpuperf_target 补丁。

## 版本演进与当前进展

- v1（当日 08:03，`<20261008000352.1689057-1-tj@kernel.org>`）：disable 报告在 dispatch 路径外运行 + `scx_sub_disable()` 持 system sleep lock + sub 链接前进入 enable bypass。
- v2（当日 17:32，`<20261008093228.2015427-1-tj@kernel.org>`，基线 `sched_ext/for-7.4` `3d7c2f550eef`）：砍掉 disable 报告及其 sleep lock/嵌套 dispatch 门控，父级从 `ops.sub_detach()` 恢复；scx_qmap 对 detaching 子级也改从 `sub_detach()` 复位 cids。
- 前身补丁实测（Tao Cui，当日 12:37/12:39）：caps-clear 补丁在「父级于 sub_detach 里恢复 SCX_CPUPERF_ONE」时行为正确（子级存活期写 target 1，SIGTERM 后父级写回 1 并保持，子级的 exit/timer 不再抢跑），两轮 lockdep 干净。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者 + 作者）：主导方向，v2 主动简化——把「disable 时报告」换成「父级从 sub_detach 恢复」，理由是报告跑到 dispatch 路径外代价过高（kfuncs 上下文 + 运行时门控 + suspend 锁），而父级本就掌握委派记录。
- **Tao Cui**（sub-scheduler 早期使用者，非维护者）：实测 caps-clear 补丁（Tested-by + Reviewed-by），并接受 Tejun 的 last-writer-wins 契约、主动放弃自己的 Reset cpuperf_target 补丁。
- 无 NAK；分歧点是实现取舍（报告时机/恢复归属），已通过 v2 收敛。

## 合入评估

*likelihood=high*。这是 Tejun 自己维护的 sched_ext/for-7.4 特性、作者即维护者，v2 已按 self-review 简化，前身补丁有独立 Tested-by/Reviewed-by 背书，无外部争议。*blocking_issues*：暂无硬阻塞；`ops.sub_child_ecaps_updated()` 本身尚缺第二人独立测试。*next_action*：等该 patchset 在 sched_ext/for-7.4 上落地（Tejun 自合并），并吸引 sub-scheduler 使用者复测。

## 效果评估

无性能数据（属 API/正确性补全）。Tao Cui 的实测是正确性验证：恢复型父级在子级退出后能稳定把 cpuperf target 复位且不再被抢跑、lockdep 干净。

## 我可以参与的点

- `testing`：在 for-7.4 + 本 patchset 上跑 sub-scheduler caps/cpuperf 全流程（含「父级不恢复」路径，验证 last-writer-wins 契约下残留目标符合预期）。
- `review`：审 v2 中「disable 不再报告、统一由 sub_detach 恢复」是否覆盖了所有 revoke/bypass 路径（尤其 PM transition 与 CPU offline 掉 caps 的场景）。

## 参考链接

- v2 封面: https://lore.kernel.org/all/20261008093228.2015427-1-tj@kernel.org/
- v1 封面: https://lore.kernel.org/all/20261008000352.1689057-1-tj@kernel.org/
- Tao Cui 的 caps-clear 实测: https://lore.kernel.org/all/8fd657b9-4bd4-48a4-a359-62096ba14bec@linux.dev/
- Tao Cui 放弃 Reset cpuperf_target: https://lore.kernel.org/all/0cca2cd5-b45d-4658-a690-40e54720b952@linux.dev/

---
id: sched-20261008-004
subject: 'sched_ext: Add ops.sub_child_ecaps_updated()'
date: '2026-10-08'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20261008093228.2015427-1-tj@kernel.org>'
lore_url: 'https://lore.kernel.org/all/20261008093228.2015427-1-tj@kernel.org/'
authors:
  - 'Tejun Heo'
maintainers_involved:
  - 'Tejun Heo'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20261008000352.1689057-1-tj@kernel.org>'
    date: '2026-10-08'
    summary: '新增 ops.sub_child_ecaps_updated()；disable 报告在 dispatch 路径外运行并持 sleep lock'
    review_outcome: 'self-review 后认为 disable 报告代价过高'
  - version: v2
    msgid: '<20261008093228.2015427-1-tj@kernel.org>'
    date: '2026-10-08'
    summary: '砍掉 disable 报告与 sleep lock/nested-dispatch gate，父级从 sub_detach 恢复'
    review_outcome: '待独立测试'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - 'ops.sub_child_ecaps_updated() 尚缺第二人独立测试'
  next_action: '在 sched_ext/for-7.4 落地并吸引使用者复测'
contribution_opportunities:
  - kind: testing
    description: '跑 sub-scheduler caps/cpuperf 全流程，含父级不恢复路径'
  - kind: review
    description: '审 v2 的 sub_detach 恢复是否覆盖所有 revoke/bypass 路径'
generated_at: '2026-10-09T01:00:00'
source_email_count: 8
related_articles:
  - sched-20261004-004
tags:
  - sched_ext
  - cgroup
---