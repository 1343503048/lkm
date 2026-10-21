# sched_ext: Make ops.cpu_acquire/release() reliable

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20261018-004：Kuba Piecuch 发往 `sched_ext/for-7.4` 的 RFC 五补丁——修复并「反弃用」`ops.cpu_acquire/release()`，把 CPU 可用性判定归约到 `rq->donor` 的类；RFC 首日无回帖。
- sched-20261019-015：作者主动复盘 v1 语义缺陷（漏 RT→RT 切换永不释放），提出 `scx_settle_pick()` 钩子方向。
- sched-20261020-004：Tejun Heo 正式表态——看不到这两个回调太多价值、IMMED 可覆盖、要求作者把 IMMED 修复单独发。
- sched-20261021-013（今天）：Kuba 补充动机——Google 的 BPF 调度器由 subscheduler 组成、显式跟踪「哪个 subscheduler 拥有哪个 CPU」，可靠的 CPU 抢占回调对迁移到 sched_ext 很有用；Tejun 则进一步给出替代方案——与其把「CPU 是否被高于 SCX 的类占用」这种**全局系统状态**塞进 sched_class，不如加一个跟踪每个 CPU 当前生效 sched_class 的 tracepoint，兼顾 scx_pair 与该用例。

## 背景与问题
（承接 sched-20261018-004 → sched-20261020-004）作者想把 `ops.cpu_acquire()/cpu_release()` 修到可靠、反弃用，用于「哪个 subscheduler 拥有哪个 CPU」的跟踪（Google BPF subscheduler 组合场景）。今日 Kuba 明确这是主要动机之一，并说明 `ops.cpu_acquire()` 在 dispatch 路径同步调用、`cpu_release()` 在 `rq->donor` 的类升到 ext 之上时（`__schedule()` 或改任务类时）触发，并不特别异步。Tejun 的反对点在于：这类「CPU 是否被更高类占用」是全局系统状态，不该内建进 sched_class，acquire/release 语义也不是它的合适载体。

## 技术方案
（今日为设计方向讨论，无新补丁）Tejun 提出替代：加一个「跟踪每个 CPU 当前生效 sched_class」的 tracepoint（若 `sched_switch` 不够的话），既能覆盖 scx_pair 的 hack 需求，也对 sched_ext 之外有用。作者此前提议的 `scx_settle_pick()` 单钩子方向仍在桌上，但 Tejun 倾向在系统事件层面钩子化、而非给 SCX 加专用回调语义。

## 版本演进与当前进展
*current_version: v1（RFC）*（无新版本，今日为设计方向交锋）。

## Maintainer 意见与讨论焦点
- Kuba Piecuch（作者）：强调 `cpu_release()` 不只是重入队本地 DSQ，还能 kick sibling（scx_pair）、可去掉不可靠的 `sched_switch` hack；主要动机是 Google BPF subscheduler 的 CPU 归属跟踪。
- Tejun Heo（维护者）：不认可把「CPU 被高于 SCX 的类占用」这一全局状态建模进 sched_class；建议 tracepoint 跟踪每 CPU 当前 sched_class，覆盖 scx_pair 与作者用例，且对 sched_ext 之外也有用。分歧未解决。

## 合入评估
*likelihood=low*。维护者 Tejun 持续否定该回调的建模方式，方向尚未对齐；作者动机充分但实现载体被拒。*blocking_issues*：Tejun 不认可 acquire/release 语义承载 CPU 占用状态，建议改走 tracepoint。*next_action*：作者回应 Tejun 的 tracepoint 方案或论证专用回调的必要性；同时先把 IMMED 修复单独发出。

## 效果评估
无 benchmark 数据。属调度器 API 设计讨论。

## 我可以参与的点
- `discussion`：Tejun 的「每 CPU 当前 sched_class tracepoint」方案 vs 专用 `cpu_acquire/release` 回调的取舍，可结合 scx_pair / Google subscheduler 的实际需求提供判断依据。

## 参考链接
- Tejun 的 tracepoint 建议：https://lore.kernel.org/all/ba9d879aa8b0474d09577b82a1d68940@kernel.org/
- Kuba 的动机回复：https://lore.kernel.org/all/DM9V2QCIFVGI.3VSJXUCU94ICW@google.com/

---
id: sched-20261021-013
date: 2026-10-21
subject: "sched_ext: Make ops.cpu_acquire/release() reliable"
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<DM9V2QCIFVGI.3VSJXUCU94ICW@google.com>"
lore_url: "https://lore.kernel.org/all/DM9V2QCIFVGI.3VSJXUCU94ICW@google.com/"
authors: ["Kuba Piecuch"]
maintainers_involved: ["Tejun Heo"]
current_version: v1
patch_series:
  - version: v1
    msgid: null
    date: 2026-10-18
    summary: "RFC 五补丁：修复并反弃用 ops.cpu_acquire/release()"
    review_outcome: "Tejun 否定建模方式，建议 per-CPU sched_class tracepoint"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues: ["Tejun 不认可 acquire/release 语义承载 CPU 占用状态"]
  next_action: "作者回应 tracepoint 方案或论证专用回调必要性，先单发 IMMED 修复"
contribution_opportunities:
  - kind: discussion
    description: "评估 tracepoint 方案 vs 专用回调的取舍"
generated_at: "2026-10-22T01:30:00"
source_email_count: 2
related_articles: ["sched-20261020-004"]
tags: [sched_ext]
---