---
id: sched-20261007-004
date: '2026-10-07'
subject: 'sched_ext: Clear a sub-scheduler''s caps before ops.sub_detach()'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <b46300eda6da03d56262fcdcbfc9b4fa@kernel.org>
lore_url: https://lore.kernel.org/all/b46300eda6da03d56262fcdcbfc9b4fa@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <b46300eda6da03d56262fcdcbfc9b4fa@kernel.org>
  date: '2026-10-07'
  summary: ops.sub_detach() 前清空子级全部 caps（pshard 先行、ecaps 直清、竞争 grant 拒绝）
  review_outcome: 随邮件 Applied to for-7.4（Tejun 自认过早）；次日 Tao Cui Tested-by/Reviewed-by
upstream_commit: null
fixes_commit: 86094b95efcf
merged_branch: sched_ext/for-7.4
merge_assessment:
  likelihood: high
  blocking_issues:
  - apply 早于 review，存在被 rework 的可能
  next_action: 随 for-7.4 进 7.4；关注后续 review
generated_at: '2026-10-08T01:00:00'
contribution_opportunities:
- kind: review
  detail: 补丁跳过了正常 review 窗口，复核锁序与早退路径
- kind: testing
  detail: grant 与 disable 竞争压力测试 -ENODEV 路径
source_email_count: 2
related_articles:
- sched-20261004-004
- sched-20261006-006
tags:
- sched_ext
- cgroup
title: 'sched_ext: Clear a sub-scheduler''s caps before ops.sub_detach()'
layout: article
---

> **subject**：`sched_ext: Clear a sub-scheduler's caps before ops.sub_detach()`

## TL;DR

Tejun Heo 落实其三小时前对 Tao Cui 系列的裁决（<a class="article-ref" href="/lkm/2026/10/07/sched-20261007-003-sched-ext-reset-cpuperf-target-when-a-sub-loses-scx-cap-perf.html">sched-20261007-003</a>）：cpuperf target 是 last-writer-wins 状态、恢复是父调度器在 `ops.sub_detach()` 里的责任，但当前父级无法依赖这一点——垂死的子调度器要到 `ops.exit()` 之后才被标记 dead，此前一直持有全部 caps，其 `ops.exit()` 或迟到 timer 可以在父级清理**之后**继续写入。本补丁在 `ops.sub_detach()` 之前清掉子级全部 caps：先清 pshard caps（pending sync 会从它们重算 ecaps）、再直接清零 ecaps；与 clear 竞争的 grant 在子级 pshard 锁下因 `child->aborting` 被拒（`-ENODEV`）。+52/−4，`Fixes: 86094b95efcf`。补丁随邮件即被应用进 `sched_ext/for-7.4`——Tejun 随后自认这次 apply「是个事故、为时尚早」，但决定保留原样，有问题再喊。

## 背景与问题

sched_ext 子调度器可以在被委派的 cid 上留下 standing state（cpuperf target 是最明显的一类），内核不跟踪写入者。裁决确立的契约是：恢复归父级、`ops.sub_detach()` 是恢复的位置。但这个契约今天不可执行——子级从开始退场到 `ops.exit()` 之后被标记 dead 之间仍持有所有 caps，`scx_bpf_cidperf_set()` 等 cap-gated kfunc 对它仍然放行；子级的 `ops.exit()` 或残留 timer 可以在父级于 `ops.sub_detach()` 里恢复完 target 之后再写一次，把父级的恢复覆盖掉。这正是 Tao Cui v2 里用「垂死写者拒绝」封住的窗口（<a class="article-ref" href="/lkm/2026/10/06/sched-20261006-006-sched-ext-reset-cpuperf-target-when-a-sub-loses-scx-cap-perf.html">sched-20261006-006</a>），只是方向不同：Tao 封窗口是为了保护内核复位值，Tejun 封窗口是为了保护父级恢复值。

## 技术方案

`kernel/sched/ext/{internal.h,sub.c}` +52/−4：

1. **`clear_all_caps()`**（sub.c 新增）：先遍历子级所有 pshard，在各自 `raw_spinlock_irqsave` 下清空全部 cap cmask——顺序有讲究，pending sync 会从 pshard caps 重算 ecaps，必须先清源头；再逐 CPU 持 rq 锁把 `pcpu->ecaps` 直接 `WRITE_ONCE` 清零，供 cap 检查即读即生效。`pshard` 未分配（enable 早失败）时直接返回。
2. **调用点**：`scx_sub_disable()` 路径里 `scx_unlink_sched(sch)` 之后、放 `scx_enable_mutex` 之前调用——保证 `ops.sub_detach()` 被调用时子级已无任何 cap。
3. **竞争封闭**：`scx_bpf_sub_grant()` 在子级 pshard 锁临界区新增 `READ_ONCE(child->aborting)` 检查，垂死/禁用中的子级返回 `-ENODEV`，grant 不会把刚清掉的 caps 发回来；返回值语义扩展（0 / -EPERM 部分 cid 被拒 / -ENODEV 子级没了）。
4. **API 文档**（internal.h）：`ops.sub_detach()` 注释明确「此时子级不持有任何 cap、无法再影响任何 cid；委派出去的东西（如 cpuperf target）由父级在此恢复」；`ops.exit()` 注释明确「运行时子级无 caps，cap-gated kfuncs 被拒」。

## 版本演进与当前进展

- v1（10-07 04:31，本篇）：如上方案，随邮件直接 Applied to `sched_ext/for-7.4`。
- 10-07 06:14 Tejun 自我更正：「Applying this was an accident and premature. I'm going to leave it as-is but please holler if you see any issues.」——apply 是误操作且早于 review，但不回滚，欢迎挑刺。
- 10-08（后续，见 <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-004-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261008-004</a>）：Tao Cui 实测「父级在 sub_detach 恢复 `SCX_CPUPERF_ONE`」场景行为正确（子级 exit/timer 不再抢跑），给 Tested-by + Reviewed-by；Tejun 在其上继续堆 `ops.sub_child_ecaps_updated()` 系列。

## Maintainer 意见与讨论焦点

Tejun Heo（作者 + sched_ext 维护者）单方面推进：裁决 → 一小时内出补丁 → 即刻应用 → 两小时后自认 apply 早了。唯一记录在案的维护者态度是流程性的（不回滚、欢迎 review），技术上无争议。焦点问题留给后续：`clear_all_caps()` 逐 CPU 拿 rq 锁的代价在子级覆盖大量 CPU 时的开销，以及 grant 的 `-ENODEV` 语义对 BPF 侧调用者的可见性（此前只有 0/-EPERM 两态）。

## 合入评估

*likelihood=high*。已在 `sched_ext/for-7.4`（作者即维护者、自我应用）；`Fixes:` 指向 86094b95efcf；次日获得独立实测（Tao Cui Tested-by/Reviewed-by，<a class="article-ref" href="/lkm/2026/10/08/sched-20261008-004-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261008-004</a>）；并成为 10-08 `ops.sub_child_ecaps_updated()` 系列的直接基线。*blocking_issues*：apply 早于 review（Tejun 自认「premature」），理论上存在被 rework 的可能。*next_action*：随 for-7.4 进 7.4 合并窗口；关注是否出现要求拆分/改写的 review。

## 效果评估

无 benchmark（正确性/API 补全）。预期效果：父级在 `ops.sub_detach()` 里做的恢复不再被垂死子级的迟到写入覆盖。次日 Tao Cui 的实测印证：子级存活期写 target 1、SIGTERM 后父级写回 1 并保持，子级 exit/timer 不再抢跑，两轮 lockdep 干净（<a class="article-ref" href="/lkm/2026/10/08/sched-20261008-004-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261008-004</a>）。

## 我可以参与的点

- `review`：补丁因「事故性 apply」跳过了正常 review 窗口，正缺一双独立眼睛——重点看 `clear_all_caps()` 的锁序（pshard 锁 → rq 锁的嵌套是否与 grant/revoke 路径的既有序一致）与「enable 早失败时 `pshard` 为 NULL」之外还有没有早退路径漏清。
- `testing`：构造「grant 与 disable 竞争」的压力场景，验证 `-ENODEV` 拒绝路径无泄漏（caps 没被部分发回）。
- 回合视角：OLK-6.6 无 sub-scheduler，不适用。

## 参考链接

- 补丁: https://lore.kernel.org/all/b46300eda6da03d56262fcdcbfc9b4fa@kernel.org/
- Tejun 的 apply 更正: https://lore.kernel.org/all/5db00088481030c82f8ad1a6aa59e581@kernel.org/
- 相关文章：<a class="article-ref" href="/lkm/2026/10/07/sched-20261007-003-sched-ext-reset-cpuperf-target-when-a-sub-loses-scx-cap-perf.html">sched-20261007-003</a>（触发本补丁的裁决）、<a class="article-ref" href="/lkm/2026/10/04/sched-20261004-004-sched-ext-reset-cpuperf-target-when-a-sub-scheduler-loses-sc.html">sched-20261004-004</a>/<a class="article-ref" href="/lkm/2026/10/06/sched-20261006-006-sched-ext-reset-cpuperf-target-when-a-sub-loses-scx-cap-perf.html">sched-20261006-006</a>（Tao Cui 系列，被本补丁取代）、<a class="article-ref" href="/lkm/2026/10/08/sched-20261008-004-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261008-004</a>（后续演进）
