---
id: sched-20261018-004
date: 2026-10-18
subject: 'sched_ext: Make ops.cpu_acquire/release() reliable'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <cover.1792248922.git.jpiecuch@google.com>
lore_url: https://lore.kernel.org/all/cover.1792248922.git.jpiecuch@google.com/
authors:
- Kuba Piecuch
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <cover.1792248922.git.jpiecuch@google.com>
  date: 2026-10-18
  summary: RFC 五补丁：将 cpu_acquire/release 可用性归约到 donor 类，修 RT 唤醒/远端提升/热插拔等缺口，反弃用并加
    selftests
  review_outcome: 暂无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - RFC 契约语义待维护者认同
  - forced-idle 是否算可用等讨论点未决
  next_action: 等待 sched_ext 维护者与 BPF 调度器作者对方案与契约的 review 表态
contribution_opportunities:
- kind: review
  description: challenge「可用性 = donor 类」归约与远端触发/rq 锁语义边界
- kind: testing
  description: 用自有 BPF 调度器在 CONFIG_EXT_SUB_SCHED+SCHED_CORE 上验证回调时序
generated_at: '2026-10-19T09:00:00'
source_email_count: 6
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Make ops.cpu_acquire/release() reliable'
layout: article
---

## TL;DR

Kuba Piecuch 发往 `sched_ext/for-7.4` 的 RFC 五补丁系列：修复并「反弃用」`ops.cpu_acquire()/ops.cpu_release()`——这两个回调本应告诉 BPF 调度器某 CPU 何时可用/被收回，但现状存在 RT 唤醒不触发 release、无上下文切换的 sched_setscheduler/PI 提升不触发、acquire 投机发出被高优先级类任务抢走、`cpu_released` 跨调度器残留、热插拔未处理等缺口。方案把可用性判定归约到 `rq->donor` 的类，不动 `kernel/sched/core.c`。RFC 首日发出，暂无回帖。

## 背景与问题

`ops.cpu_acquire()` 与 `ops.cpu_release()` 旨在告诉 BPF 调度器 CPU 何时变得可用、何时被收回。现状不可靠：

- RT 任务在 idle CPU 上被唤醒不触发 `ops.cpu_release()`——release 只从 `put_prev_task_scx()` 发出（即 SCX 任务被切出时）。
- 运行中的 SCX 任务经 `sched_setscheduler()` 或 PI 提升进入更高类时不触发，因为不发生上下文切换。
- `ops.cpu_acquire()` 从 `dispatch_one()` 投机发出；若其后高优先级类任务赢得 pick（dispatch 掉了 rq 锁、`RETRY_TASK`、core-sched 为 sibling 挑任务），CPU 持续「acquired」而 RT 任务在其上运行。
- `rq->scx.cpu_released` 从上一个调度器残留到下一个，且 CPU 热插拔未处理。

commit a3f5d4822253（"sched_ext: Allow scx_bpf_reenqueue_local() to be called from anywhere"）曾弃用这两个回调，因当时认为补全这些缺口需要一个「无视调度类的钩子」。本系列证明不需要。

## 技术方案

核心观察：CPU 是否对 BPF 调度器可用只取决于 `rq->donor` 的类——SCX 任务或 idle 任务在其上跑时可用，stop/DL/RT/fair（partial 模式）任务在其上跑时释放。每次可用性变化，切换两侧必有一侧是 SCX 任务或 idle 任务，因此 ext 与 idle 类各自的 `put_prev_task()`/`set_next_task()` 能看到全部变化；更高类任务之间的切换从不改变可用性。唯一剩余情形——运行任务无上下文切换地离开 SCX——由 `switched_from_scx()` 捕获。`kernel/sched/core.c` 完全不动，idle 类在其现有 `scx_update_idle()` 调用旁边加两处调用，`sched.h` 加一个新 `scx_rq` 标志。

重点讨论点（作者列出）：
- core-sched forced idle 算「可用」：任务能否放上 forced-idle CPU 取决于该任务 cookie，应由 BPF 调度器判断。
- `ops.cpu_acquire()` 从「`ops.dispatch()` 之前」移到「CPU 真正切到 SCX 任务或 idle」的时刻，故 `ops.dispatch()` 现在可能在一个已 release 的 CPU 上跑；dispatch 前的投机 acquire 无法在不加全局钩子的前提下可靠。
- 回调可为**远端** CPU 触发（该 CPU 的 rq 已锁）：`sched_setscheduler()`/PI 提升他人 CPU 上的任务、调度器 enable。补丁 1 让 legacy `scx_bpf_reenqueue_local()` 重入队「持锁 rq」的本地 DSQ，而非假定 `smp_processor_id()`。
- 每个 CPU 初始为 released，每个可用 online CPU 在调度器 enable 时被 acquired；回调只在 `ops.cpu_online()` 与 `ops.cpu_offline()` 之间触发（因 CPU 上线时 `rq_online_scx()` 先于 `ops.cpu_online()` 运行，需新 `SCX_RQ_OPS_ONLINE` 标志而非 `SCX_RQ_ONLINE`）。
- 未实现回调的调度器只需付一个 static branch。
- 回调保持 cpu-form only，天然 root-only；cid-form 变体与 sub-scheduler fan-out（以 `SCX_CAP_BASE` 门控，像 `ops.update_idle()`）如有人感兴趣可跟进。

五补丁：1/5 legacy reenqueue 定向持锁 rq；2/5 在真实转换上发回调并处理 enable/disable 与热插拔；3/5 运行任务离开 SCX 时释放 CPU；4/5 反弃用并写契约文档；5/5 加 selftests（`cpu_avail`、`cpu_avail_core`）。virtme-ng 下 PROVE_LOCKING/DEBUG_ATOMIC_SLEEP/SCHED_CORE/EXT_SUB_SCHED 全开、全套 sched_ext selftest 无 splat 通过；新测试在 base 内核（idle→RT）与仅 1–2 时（远端类变更）失败，证明有效。

## 版本演进与当前进展

*current_version: v1*。RFC 首日发出（2026-10-18，`cover.1792248922.git.jpiecuch@google.com`），暂无 review 回帖。

## Maintainer 意见与讨论焦点

暂无回帖（RFC 当日新发）。作者预留的讨论点（forced-idle 是否算可用、acquire/dipatch 时序、远端触发语义）将是后续焦点。

## 合入评估

*likelihood=unknown*。RFC 无人表态、无 test/review 回帖，且涉及 `ops.cpu_acquire/release` 语义契约变更（此前被弃用），社区是否认同「归约到 donor 类 + ext/idle 两侧捕获」这一方案尚待维护者（Tejun Heo / David Vernet）评估。*blocking_issues*：契约语义是否被接受、RFC 讨论点未决。*next_action*：等待 sched_ext 维护者与 BPF 调度器作者对方案与契约的 review 表态。

## 效果评估

无性能 benchmark；作者以「新 selftest 在 base/部分补丁下失败、全套通过」作为正确性证据。属功能性/可靠性改进，非性能优化。

## 我可以参与的点

- `review`：这是把被弃用 API 重新扶正的语义变更，对「可用性 = donor 类」这一归约、以及远端触发/rq 锁语义的边界很值得有 sched_ext 实战经验的调度器作者来 challenge。
- `testing`：用自己的 BPF 调度器在 `CONFIG_EXT_SUB_SCHED` + SCHED_CORE 上验证 cpu_acquire/release 时序（idle→RT、远端 setscheduler、PI 提升、热插拔、partial 模式）。

## 参考链接

- RFC 封面信：https://lore.kernel.org/all/cover.1792248922.git.jpiecuch@google.com/
