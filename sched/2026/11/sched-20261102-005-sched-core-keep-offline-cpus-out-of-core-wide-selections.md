# sched/core: keep offline cpus out of core-wide selections

## TL;DR

Ahmed Abdelraoof（Amazon）修复 hotplug 期间 core scheduling 的窄竞态：新进 CPU 已加入 sibling 集但尚未把 `rq->core` 指向组 leader 期间，在线 CPU 的 `pick_next_task()` 会错误地读写这个离线 CPU 的 runqueue，导致静默数据破坏乃至 `cookie_equals()` 解引用 NULL 崩溃。方案是在首轮 core-wide pick 中跳过离线 CPU。Peter Zijlstra 已回复，建议三处迭代统一用一种写法、避免一个补丁三种风格。

## 背景与问题

CPU hotplug 时 `start_secondary()` 里 `set_cpu_sibling_map()`（ap_starting）先把新 CPU 加入 core-sched sibling 集，随后 `notify_cpu_starting()` 的 `sched_core_cpu_starting()` 才把它的 `rq->core` 指向组 leader，最后才 `set_cpu_online()`。窗口内：在线 CPU o 做 core-wide 选择时碰到「已入 sibling 集但 `rq->core` 未指向 leader」的新 CPU i，只在持有 o 的 rq lock 的情况下调用 `pick_task()` 并写 i 的 `rq->core_pick`（没有持有 i 的 rq lock）；另一种顺序则让 `set_cpu_sibling_map()` 先发布 i，o 第二轮 walk 读到 i 的 NULL `rq->core_pick` 并传进 `cookie_equals()` 解引用崩溃。

## 技术方案

首轮 core-wide pick 中加 `if (!cpu_online(i)) continue;` 跳过离线 CPU，并用得到的非 NULL `rq->core_pick` 标识后续各轮参与 CPU（online mask 在各轮之间会变）；顺手也从单轮 forced-idle 记账里排除离线 CPU。`Fixes: 539f65125d20`（core wide task selection）、`Fixes: bc9ffef31bf5`（simplify core-wide task selection），Cc stable。

## 版本演进与当前进展

v1 刚发出（2026-11-01），Peter Zijlstra 已回：问能否像最后一处 hunk 那样统一三处写法（「一个补丁里三种迭代方式很遗憾」）。

## Maintainer 意见与讨论焦点

Peter 的反馈是代码风格/一致性层面，未否定修复本身。作者需把 `pick_next_task()` 里三处（首轮、后续轮、forced-idle 单轮）的迭代统一成同一套「跳过离线/无 pick」逻辑。

## 合入评估

likelihood=medium（偏 high）。修复方向被认可、竞态真实且在 hotplug 下可 crash，但需按 Peter 意见重构成一致写法后再评。

## 效果评估

作者在正文给出竞态时序描述（静默破坏 + `cookie_equals()` NULL 解引用崩溃），未附独立测试数据。

## 我可以参与的点

- review：审阅三处迭代统一写法后的版本，确认 `smt_mask` 变化的语义（online 变化期间 `core_pick` 快照是否自洽）。
- testing：在 SMT 机器上反复 hotplug CPU，验证 core-sched 路径无 crash/无数据破坏。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261101221219.118052-1-araoof@amazon.de/

---
type: fix
status: under_review
severity: high
thread_root_msgid: <20261101221219.118052-1-araoof@amazon.de>
authors:
- Ahmed Abdelraoof
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261101221219.118052-1-araoof@amazon.de>
  date: '2026-11-01'
  summary: 首轮 core-wide pick 跳过离线 CPU，后续轮以非 NULL core_pick 识别参与者
  review_outcome: Peter 建议三处迭代统一一种写法
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter 要求统一三处迭代写法后再评
  next_action: 作者按 Peter 意见重构为一致写法并重发
contribution_opportunities:
- kind: review
  description: 审阅统一写法后的版本与 online 变化时 core_pick 快照自洽性
- kind: testing
  description: SMT 机上反复 hotplug 验证 core-sched 无 crash/无破坏
upstream_commit: null
fixes_commit: 539f65125d20
merged_branch: null
source_email_count: 2
related_articles: []
tags:
- core_sched
- topology
- x86
id: sched-20261102-005
subject: 'sched/core: keep offline cpus out of core-wide selections'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
