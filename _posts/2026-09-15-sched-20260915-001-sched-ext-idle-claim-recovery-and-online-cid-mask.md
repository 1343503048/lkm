---
id: sched-20260915-001
date: '2026-09-15'
subject: 'sched_ext: Idle claim recovery and online cid mask'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260914234259.3585373-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20260915082725.3881071-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Andrea Righi
current_version: v2
patch_series:
- version: v1
  msgid: <20260914234259.3585373-1-tj@kernel.org>
  date: '2026-09-15'
  summary: idle-to-idle 通知（SCX_OPS_UPDATE_IDLE_TO_IDLE，cid-form 自动/CPU-form opt-in）+
    scx_bpf_online_cmask() 新 kfunc
  review_outcome: Andrea Righi 质疑 idle-to-idle 通知改变 update_idle 语义，建议改从 ops.dispatch()
    恢复；对 cmask 仅文档意见
- version: v2
  msgid: <20260915082725.3881071-1-tj@kernel.org>
  date: '2026-09-15'
  summary: 删除 idle-to-idle 通知补丁，改为 scx_qmap 从 ops.dispatch() 恢复 claim + 文档；重写 cmask
    getter kerneldoc
  review_outcome: Andrea Righi Reviewed-by，无遗留争议
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等 Tejun 将 v2 收入 sched_ext/for-7.3-fixes 分支
contribution_opportunities:
- kind: review
  description: 在自家 cid-form 调度器上核对 ops.dispatch() 恢复 claim 模式是否覆盖所有 kick 未派发任务的路径
- kind: testing
  description: 在含 CPU hotplug 场景回归测试 scx_bpf_online_cmask() 掩码与 cid_online/offline
    回调顺序
generated_at: '2026-09-16T01:05:00'
source_email_count: 10
related_articles: []
tags:
- sched_ext
- idle
title: 'sched_ext: Idle claim recovery and online cid mask'
layout: article
---

## TL;DR
Tejun Heo 为 cid 接口补两个漏洞：idle CPU 被 reserve+kick 后无任务到达、再选 idle 时无状态转换导致自维护 idle 的 cid-form 调度器「丢 CPU」，以及自装 cid 映射的调度器无法得知哪些 cid 在线。v1 用 idle-to-idle 通知方案，被 Andrea Righi 指出会改变 update_idle 语义后，v2 改为公认的「从 ops.dispatch() 恢复未用 claim」模式（修 scx_qmap + 文档），并保留 scx_bpf_online_cmask() 新 kfunc。v2 已获 Andrea Righi Reviewed-by，基于 sched_ext/for-7.3-fixes，合入概率高。

## 背景与问题
作者在转换一个自维护 idle 与 online 跟踪的 cid-form 调度器时暴露了 cid 接口的两个洞：

1. **idle 状态跟踪漏洞**：idle CPU 可被 `scx_bpf_pick_idle_cpu()` + `scx_bpf_kick_cpu()` 保留并唤醒而不实际收到任务；当它再次选 idle 时，builtin idle 掩码能恢复保留位，但 `ops.update_idle()` 不会被调用，于是自维护 idle 掩码的 BPF 调度器会把该 CPU 一直当作 busy，直到有无关任务在其上运行才恢复。
2. **在线 cid 集合不可知**：默认映射下 `[0, nr_online_cids)` 即在线集合；但通过 `scx_bpf_cid_override()` 自装映射的调度器无法得知哪些 cid 在线——count 不再标识成员，而 CPU-form 的 cpumask 在 cid 程序里不可用。

## 技术方案
v1 的 patch 1 采用 idle-to-idle 通知：新增 `SCX_OPS_UPDATE_IDLE_TO_IDLE` flag，cid-form 调度器自动启用、CPU-form opt-in，用 static key 承载。patch 2 新增 `scx_bpf_online_cmask()`——内核在调度器 arena 里维护的 cmask，随 SCX hotplug 通知（`ops.cid_online/offline()` 之前）更新，指针从 `ops.init()` 到 `ops.exit()` 期间有效。

Andrea Righi 指出 v1 patch 1 会改变 cid-form 调度器 `ops.update_idle()` 的语义（可能连续收到多个 idle=true 而无中间 idle=false），而「从 ops.dispatch() 末尾恢复未用 claim」是已有公认模式（如 scx_cidland）。v2 据此**放弃 idle-to-idle 通知补丁**，改为：patch 1 修 scx_qmap 在 `ops.dispatch()` 无 `@prev` 可跑、CPU 回 idle 时用 `cmask_set(cid, &qa.idle_cids.mask)` 恢复 claim，并在 `ops.update_idle()` 文档中明确「只报告真实状态转换」；patch 2 保留 `scx_bpf_online_cmask()` 并重写 getter kerneldoc。

## 版本演进与当前进展
- **v1**（"Idle repick notifications and online cid mask"，`<20260914234259.3585373-1-tj@kernel.org>`）：2 patches——idle-to-idle 通知 + `scx_bpf_online_cmask()`。
- **v2**（本日 16:27，`<20260915082725.3881071-1-tj@kernel.org>`）：按 Andrea 意见删掉 idle-to-idle 通知补丁，替换为 scx_qmap 从 ops.dispatch() 恢复 claim + 文档；重写 online cmask getter kerneldoc。分支 `tj/sched_ext.git cid-online-cmask-v2`，基于 `c7a1c6e8004a`。

## Maintainer 意见与讨论焦点
- **Andrea Righi**（v1 回帖）：质疑 idle-to-idle 通知改变 update_idle 语义、建议走 dispatch 恢复模式；对 patch 2 仅提文档用词建议，并给 Reviewed-by。
- **Andrea Righi**（v2 回帖）：对整系列 "Looks good"，给出 `Reviewed-by: Andrea Righi <arighi@nvidia.com>`。
- 无分歧遗留：v1 的语义争议已通过换方案消解。

## 合入评估
*likelihood=high*。Tejun Heo 本人是 sched_ext 维护者、系列直接基于 for-7.3-fixes 分支，v2 已获共同维护者 Andrea Righi Reviewed-by，无阻塞项。*blocking_issues*：无。*next_action*：等 Tejun 将 v2 收入 `sched_ext/for-7.3-fixes` 分支并入 7.3。

## 效果评估
作者验证方式（cover 自述）：构建并加载同时消费两个新接口的 cid-form 调度器；本地 selftest 覆盖带/不带 flag 的 CPU-form 与 cid-form idle 通知；本地 selftest 在 VM 中 offline/online 一个 CPU 并逐步检查掩码与回调。未见 benchmark 数字，属功能正确性验证。

## 我可以参与的点
- kind=review：在自家 cid-form 调度器（或 scx_cidland）上核对「从 ops.dispatch() 恢复未用 claim」模式是否覆盖所有 kick 未派发任务的路径。
- kind=testing：在含 CPU hotplug 的场景下回归测试 `scx_bpf_online_cmask()` 的掩码与 `ops.cid_online/offline()` 回调顺序是否一致。

## 参考链接
- v1 cover：https://lore.kernel.org/all/20260914234259.3585373-1-tj@kernel.org/
- v2 cover：https://lore.kernel.org/all/20260915082725.3881071-1-tj@kernel.org/
- Andrea Righi v2 Reviewed-by：https://lore.kernel.org/all/aqk5pfKCXWudIBAD@gpd4/
