---
id: sched-20260903-014
date: '2026-09-03'
subject: 'sched_ext: don''t deliver duplicate ops.cgroup_set_idle() for same value'
subsystem: sched
type: discussion
status: merged_tip
severity: low
thread_root_msgid: <20260901124347.755904-1-cui.tao@linux.dev>
lore_url: https://lore.kernel.org/all/20260901124347.755904-1-cui.tao@linux.dev/
upstream_commit: null
fixes_commit: 347ed2d566da
merged_branch: sched_ext/for-7.3-fixes
current_version: v2
generated_at: '2026-09-07'
authors:
- Tao Cui
maintainers_involved:
- Tejun Heo
- Andrea Righi
patch_series:
- 'sched_ext: Don''t deliver duplicate ops.cgroup_set_idle() for same value'
merge_assessment:
  likelihood: merged
  blocking_issues:
  - for-7.3-fixes 与 for-7.4 上字段名分裂（scx.idle vs scx.sched_idle），合并时比较会被切换，并行改动需预期冲突
  - 无 selftest 锁定“等值写入不产生回调”这条约定
  next_action: 跟进 for-7.3-fixes 被拉入 tip/for-next 的时点，并补 selftest 与 knob 家族幂等性审计
contribution_opportunities:
- 审计 scx_group_set_* knob 家族是否还有缺等值守卫的下发路径
- 给 scx cgroup selftest 增加重复写同值不回调、真正变化恰好回调一次的断言
- 讨论读锁下比较 tg->scx.idle 与后续状态更新的并发正确性
- 回合时先确认自家 task_group 的 idle 字段名并记录上游分支命名分裂
source_email_count: 1
related_articles: []
tags:
- sched_ext
- cgroup
title: 'sched_ext: don''t deliver duplicate ops.cgroup_set_idle() for same value'
layout: article
---

## TL;DR

`ops.cgroup_set_idle()` 的文档语义是「cgroup 在 idle 与非 idle 之间转换时调用」，同族的 `scx_group_set_weight()` 也已经跳过等值写入，但 `scx_group_set_idle()` 对每次写入都无条件下发回调——重复写一个已经正确的 `cpu.idle` 值也会喂给 BPF 调度器一次转换事件，依赖 toggle 或计数的调度器会算错。Tao Cui 用 2 行改动镜像 weight 的守卫（在条件链尾追加 `tg->scx.sched_idle != idle`），v1 当天拿到 Andrea Righi 的 `Reviewed-by`，v2 只修了一个被吃掉的 `Link:` 域名。本日（09-03 01:48）Tejun Heo 把它 applied 到 `sched_ext/for-7.3-fixes`，并在应用时改了两处：标题首字母大写，以及把比较字段从 `tg->scx.sched_idle` 换成 `tg->scx.idle`——因为改名在 `for-7.4` 上，`for-next` 合并时会再切回去。

## 背景与问题

sched_ext 支持按 cgroup 打开 idle 偏好：`scx_cgroup_enabled` 时，`scx_group_set_idle(struct task_group *tg, bool idle)` 在 `percpu_down_read(&scx_cgroup_ops_rwsem)` 保护下取 `scx_tg_knob_sched(tg)`，若该调度器实现了 `cgroup_set_idle` op（`SCX_HAS_OP(sch, cgroup_set_idle)`）就通过 `SCX_CALL_OP()` 通知 BPF 侧，随后再更新 task group 自身的 idle 状态。

问题在于回调的下发条件里没有值变化判断：`cpu.idle` 被重复写入同一个值时（容器运行时、systemd 之类的幂等刷新很容易触发），BPF 调度器仍会收到一次「idle 转换」回调。而 `ops.cgroup_set_idle()` 的文档承诺的是转换事件，把等值写入也报成转换，会让以 toggle 或计数方式维护 idle 状态的调度器统计失真。

对照实现是现成的：权重路径 `scx_group_set_weight()` 早就跳过了等值写入（value-preserving writes），idle 路径只是漏了这一道守卫。

## 技术方案

`kernel/sched/ext/ext.c` 单点改动，2 增 1 删：

```
-	if (scx_cgroup_enabled && sch && SCX_HAS_OP(sch, cgroup_set_idle))
+	if (scx_cgroup_enabled && sch && SCX_HAS_OP(sch, cgroup_set_idle) &&
+	    tg->scx.sched_idle != idle)
 		SCX_CALL_OP(sch, cgroup_set_idle, NULL, tg_cgrp(tg), idle);
```

要点：

- 守卫挂在条件链尾部，只对「实现了该 op 且值真的变化」的情形下发回调，对未实现 `cgroup_set_idle` 的调度器零影响。
- 被跳过的只是 op 下发，task group 自身 idle 状态的更新仍在原位照常执行（改动下方的 `/* Update the task group's idle state */` 未动）。
- 补丁带 `Fixes: 347ed2d566da`（"sched/ext: Implement cgroup_set_idle() callback"），即修的是该回调引入时漏掉的守卫，`Link:` 指向对应的报告线程。
- 维护者应用时把字段名改为 `tg->scx.idle`（见下节），因为 v2 所基于的 `for-7.4` 上该字段已被改名，而 fixes 分支上仍是旧名。

## 版本演进与当前进展

- v1（09-01 11:11，`[PATCH] ...`，作者 `From: Tao Cui <cuitao@kylinos.cn>`，投递地址为 `cui.tao@linux.dev`）：代码即最终形态，`Link:` 标签少了 msgid 的域名部分。
- 09-01 15:25 Andrea Righi 指出链接坏了并给出正确形式，同时回 `Reviewed-by`（「Other than that looks good to me.」）；20:35 作者解释「Somehow my vim seems to have eaten the `@linux.dev` part of the Message-ID」。
- v2（09-01 20:43）：changelog 明确「Fix the Link: msgid (missing @linux.dev, Andrea)」，代码零改动。
- **本日 09-03 01:48 Tejun Heo 回复「Applied to sched_ext/for-7.3-fixes」**，应用时做了两处调整：标题首字母大写；把新加的比较改成 `tg->scx.idle != idle`，并说明「The rename to tg->scx.sched_idle is on for-7.4 and the for-next merge switches the comparison back.」
- 至此本补丁已落 tip 侧的 sched_ext fixes 分支，不再是待评审状态。

## Maintainer 意见与讨论焦点

- **Andrea Righi（NVIDIA，sched_ext 活跃维护者）**：唯一的实质意见是元数据正确性——`Link:` 必须指向可解析的 lore 消息，他直接给出正确 msgid 并附上 `Reviewed-by`。代码本身没有异议，说明「镜像 weight 守卫」这个方案是双方共识而非讨论结果。
- **Tejun Heo（sched_ext maintainer）**：接受方案并当天合入 `sched_ext/for-7.3-fixes`；他对补丁的两处修改本身就是有价值的信息：其一，他坚持把 `don't` 开头的标题大写（风格统一，`Link:` 与标题都属于他会当场改的范畴）；其二，他显式说明了字段名在分支间的分裂——`tg->scx.idle` 属于 `for-7.3-fixes`，`tg->scx.sched_idle` 属于 `for-7.4`，`for-next` 合并时比较会切回新名。
- 讨论焦点因此不在语义，而在**跨分支改名带来的时序耦合**：同一处代码在两条分支上引用不同字段名，任何后续对这段条件的修改（例如再加一个守卫）都要同时考虑两个形态，且合并方向决定最终文本。这类信息对下游回合尤其关键，也正是邮件里唯一「写了但不在 diff 里」的内容。
- 未出现的质疑：没有人质疑「用 `tg->scx.sched_idle` 作为比较基准」是否与下方状态更新之间存在读写竞态（两个 CPU 同时以不同值写入时是否可能都判定为变化或都判定为无变化），这一层在本线程未被讨论。

## 合入评估

likelihood: **likely**（已合入）。

依据：Tejun Heo 本日已明确 applied 到 `sched_ext/for-7.3-fixes`，带 `Reviewed-by: Andrea Righi`；改动 2 增 1 删、单函数、无 Kconfig 与 ABI 影响，且只收紧回调下发；`Fixes:` 指向引入该回调的提交，属于 fixes 通道。

卡点只剩分发与一致性两项：一是 `for-7.3-fixes` 到主线的时间由 sched 维护者的拉取节奏决定，`for-7.3-fixes` 与 `for-7.4` 合并时这段比较的字段名会被切换，任何并行改动都要预期一次文本冲突；二是本补丁没有 selftest 保护，「等值写入不产生回调」这一约定目前只靠一行条件维持，回归成本低但检测成本也低。邮件中也没有 stable 讨论，考虑到 `Fixes:` 指向的回调实现本身较新，是否向更早稳定树传播由维护者另行决定。

## 效果评估

邮件中未提供性能数据。作者给出的是功能验证：写了一个会打印每次回调的 probe 调度器，在一个已经处于 idle 的 cgroup 上连续两次写入 `cpu.idle=1`——修复前收到 2 次回调，修复后收到 0 次。

这条验证方式与缺陷形态匹配（回调次数可数，无需统计意义），但它只覆盖了「值未变」的正向情形，没有覆盖「值真的变化时仍必须恰好一次」这一侧；也没有给出频繁写 `cpu.idle` 场景下省下的开销量级（`SCX_CALL_OP` 是 BPF trampoline 调用，理论上有可测成本，邮件里没有数字）。

## 我可以参与的点

1. 顺着作者「mirror the weight guard」这条线索做一遍审计：把 `scx_group_set_weight()` / `scx_group_set_idle()` 之外的所有 cgroup knob 下发路径（`scx_tg_knob_sched()` 相关家族）过一遍，看是否还有第三处忘了等值守卫。这类补丁几乎不会被拒绝，且能立刻用上同一种 probe 调度器验证方法。
2. 给 selftests 补一条断言：在 scx cgroup selftest 里加「重复写同值不产生回调 + 真正变化时恰好一次」的用例。目前这条约定只有一行条件保护，无任何测试锁定，是明显的 low-hanging fruit。
3. 提一个未被人问过的问题：比较所读的 `tg->scx.sched_idle` 与下方的状态更新之间，在 `percpu_down_read()` 读锁下并发写入是否可能让两个 CPU 都看到「已变化」或都看到「无变化」。若有，则正确修法是把比较与更新放到同一把锁的写侧或改用 `cmpxchg`。这类回帖对 sched_ext 侧是有价值的，且不需要额外机器。
4. 回合视角：本补丁本身极小，适合随 `cgroup_set_idle` 回调一起回合；关键是先确认自家 `struct task_group` 里字段叫 `scx.idle` 还是 `scx.sched_idle`，并记录上游两条分支的命名分裂，避免后续同步 `for-7.4` 时被静默改回。cpuset/cgroup 侧还可把「等值重复写不产生转换事件」当成对容器运行时刷新行为的一条契约来验证。

## 参考链接

- 本补丁线程：
  - v1：https://lore.kernel.org/all/20260901031101.731943-1-cui.tao@linux.dev/
  - v2（被应用的版本）：https://lore.kernel.org/all/20260901124347.755904-1-cui.tao@linux.dev/
  - Andrea Righi 的链接修正与 Reviewed-by：https://lore.kernel.org/all/apZ-B__OiVcZW46Z@gpd4/
  - 本日 Tejun Heo 的应用通告（含字段改名说明）：https://lore.kernel.org/all/a8b5c606e0e52a93f8bee7e6d6a7f78c@kernel.org/
