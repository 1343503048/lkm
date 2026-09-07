---
subject: 'sched_ext: don''t deliver duplicate ops.cgroup_set_idle() for same value'
id: sched-20260901-008
date: '2026-09-01'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/20260901124347.755904-1-cui.tao@linux.dev/
authors:
- Tao Cui
- Andrea Righi
maintainers_involved:
- Andrea Righi
- Tejun Heo
current_version: v2
patch_series:
- version: v1
  msgid: <20260901031101.731943-1-cui.tao@linux.dev>
  date: '2026-09-01'
  summary: scx_group_set_idle() 增加 tg->scx.sched_idle != idle 守卫，使等值 cpu.idle 写入不再下发
    ops.cgroup_set_idle() 回调，与 scx_group_set_weight() 的既有行为对齐
  review_outcome: 'Andrea Righi 认可并给 Reviewed-by，仅指出 Link: 标签的 Message-ID 缺 @linux.dev
    后缀'
- version: v2
  msgid: <20260901124347.755904-1-cui.tao@linux.dev>
  date: '2026-09-01'
  summary: '仅修正 Link: 标签并携带 Reviewed-by，代码与 v1 相同'
  review_outcome: 本日尚未看到 Tejun Heo 的应用回帖
upstream_commit: null
fixes_commit: 347ed2d566da
merged_branch: null
merge_assessment:
  likelihood: likely
  blocking_issues:
  - 等待 Tejun Heo 应用到 sched_ext/for-7.3-fixes（本日尚无回帖）
  - 等值判断依赖同 tg 旋钮写入已被序列化，该前提与 sched-20260901-003 的锁层改动相关，尚未有人明确说明
  next_action: maintainer 应用；或作者补一句说明该守卫与 cgroup 旋钮序列化路径的关系
contribution_opportunities:
- kind: new_patch
  description: 把 weight/idle 两条旋钮路径的等值跳过收敛为统一 helper，防止后续旋钮重复同类问题
- kind: extend
  description: 把作者的一次性探针调度器整理成 tools/sched_ext 或 selftests 中的 "cgroup 旋钮 → ops 回调"
    契约测试，覆盖 weight/idle/bandwidth
- kind: review
  description: 评估该守卫与 sched-20260901-003（把 fair/cgroup 锁提升到 core）叠加后的并发语义是否需要额外说明
source_email_count: 4
related_articles:
- sched-20260901-003
- sched-20260901-018
- sched-20260901-019
- sched-20260903-014
tags:
- sched_ext
- cgroup
generated_at: '2026-09-07'
title: 'sched_ext: don''t deliver duplicate ops.cgroup_set_idle() for same value'
layout: article
---

## TL;DR

`scx_group_set_idle()` 把每一次 `cpu.idle` 写入都无条件转发给 BPF 调度器的 `ops.cgroup_set_idle()`，即使值没变；而同一族的 `scx_group_set_weight()` 早就跳过了等值写。Tao Cui 用一行条件把 weight 的守卫镜像过来，Andrea Righi 当日给 `Reviewed-by`，唯一意见是 `Link:` 标签少了 `@linux.dev`——v2 当天就发了。属于「已定案、等 maintainer 应用」的小修。

## 背景与问题

sched_ext 的 cgroup CPU 旋钮（`cpu.weight`、`cpu.idle`）变化时要通知当前注册的调度器。`ops.cgroup_set_idle()` 的文档语义是「cgroup 在 idle 与非 idle 之间**转换**时调用」，但实现上 `scx_group_set_idle()` 对每次写入都下发一次回调。后果是：把 `cpu.idle=1` 重复写两次，调度器就收到两次「进入 idle」转换。对任何用这个回调做 **toggle 计数或时间/额度统计** 的 BPF 调度器，计数会凭空翻倍——回调次数不再等于状态转换次数。

同文件里的 `scx_group_set_weight()` 已经有等值跳过，两者行为不一致，因此这不是设计选择而是遗漏。

## 技术方案

在 `kernel/sched/ext/ext.c:scx_group_set_idle()` 的下发条件上加一个状态比较：

```
-	if (scx_cgroup_enabled && sch && SCX_HAS_OP(sch, cgroup_set_idle))
+	if (scx_cgroup_enabled && sch && SCX_HAS_OP(sch, cgroup_set_idle) &&
+	    tg->scx.sched_idle != idle)
		SCX_CALL_OP(sch, cgroup_set_idle, NULL, tg_cgrp(tg), idle);
```

状态更新本身照旧进行，只是回调只在真实转换时下发。方案的全部取舍就是「**用 `tg->scx.sched_idle` 这个既有状态位做幂等判断**」，不引入新字段、不加锁；这也意味着它与并发的旋钮写入序列化方式强相关——本日没人讨论这一点（见「Maintainer 意见」末段）。

被放弃的备选：无。作者直接把 weight 路径的既有守卫复制过来。

## 版本演进与当前进展

- **v1（2026-09-01 11:11）**：Andrea Righi 15:25 回：`This link seems broken, I think the right one is: Link: https://lore.kernel.org/r/b53c61a1-4d7d-4232-941f-d48b0563d4ed@linux.dev` + `Other than that looks good to me. Reviewed-by: Andrea Righi <arighi@nvidia.com>`。
- 作者 20:35 解释成因并致谢：`Somehow my vim seems to have eaten the @linux.dev part of the Message-ID.`
- **v2（2026-09-01 20:43）**：仅修正 `Link:` 标签并带上 `Reviewed-by`，changelog 写 `v1 -> v2: Fix the Link: msgid (missing @linux.dev, Andrea).`，代码与 v1 完全相同。

v2 在本日尚未看到 Tejun Heo 的应用回帖。

## Maintainer 意见与讨论焦点

- **Andrea Righi**：唯一意见是 `Link:` 消息 ID 不完整（缺 `@linux.dev` 后缀，导致链接指向不存在的短消息 ID），其余认可并给出 `Reviewed-by`。这是纯标签正确性问题，说明 review 已读完代码。
- 作者对「什么场景会被这个 bug 影响」给了明确类别：**toggle 型或计数型的 BPF 调度器**（`which toggle- or accounting-based schedulers miscount`），并用自己的探针调度器验证。
- **本日无人讨论的一点**：该守卫读的是 `tg->scx.sched_idle`，而调用发生在 `percpu_down_read(&scx_cgroup_ops_rwsem)` 之下。等值判断与随后的状态更新之间是否有窗口、是否依赖上层旋钮写入串行化，正是同一天 Michal Blaszczyk 的 `sched: Lift cgroup update locking to core to prevent CFS/SCX divergence`（sched-20260901-003）与 Andrea 自己的 `sched_ext: Serialize cgroup knob updates`（被 Tejun 判定为被前者取代）在解决的那一类问题。这片修复不改变锁结构，但它的新语义建立在「同 tg 的旋钮写入被序列化」这一前提上，值得在后续版本中写明。

## 合入评估

`likelihood = likely`。改动 1 行、有 `Fixes:` 标签（`347ed2d566da ("sched/ext: Implement cgroup_set_idle() callback")`）、有 `Reviewed-by`、维护者当日无其他要求，且 sched_ext 的 `for-7.3-fixes` 通道正在收小修（同一天 Tejun 在该分支应用了 4 个同类补丁并发了 v7.3-rc1 的 pull，见 sched-20260901-018）。剩下唯一风险是被 003/序列化那条线顺带覆盖——如果旋钮更新最终统一挪到 core 层锁内，这片仍可作为独立修复存在，因为它改的是回调语义而非锁。

## 效果评估

作者给出了定性的复现结论：**`Verified with a probe scheduler printing each callback: rewriting cpu.idle=1 twice on an already-idle cgroup delivered two callbacks before and none after.`** 这是本片中唯一的数据——回调次数从 2 变 0，属行为验证而非性能测量。**没有**任何性能或开销数字；「减少冗余 BPF 回调」的收益幅度未量化。

## 我可以参与的点

- **可直接代做的后续**：把 `scx_group_set_weight()` 与 `scx_group_set_idle()` 的等值守卫统一成一个 helper（或明确注释二者必须一致），避免第三条旋钮路径重蹈覆辙。这类「一致性」小补丁在 sched_ext 的 fixes 通道接受度较高。
- **写一个可复用的探针调度器**：作者的验证方式是自写探针调度器打印每次回调。把它整理进 `tools/sched_ext/` 或 selftests，作为「cgroup 旋钮 → ops 回调」的契约测试，能同时保护 weight/idle/bandwidth 三条路径（`ops.cgroup_set_bandwidth()` 也在这天的 pull 里被改成允许 sleepable）。
- **补一层语义文档**：`cpu.idle` 的回调契约（是否保证幂等、是否允许等值下发）目前靠代码行为约定，与 1/2 文档片（sched-20260901-009 同作者的另一条线）一样属于可补的空白。
- **回合判断**：OLK-6.6 无 sched_ext，本片不直接相关；但「等值写不产生转换通知」这条原则同样适用于我们自己的 cgroup 旋钮转发路径（cpuset/cpu.max），值得作为实现纪律吸收。

## 参考链接

- v1: https://lore.kernel.org/all/20260901031101.731943-1-cui.tao@linux.dev/
- Andrea Righi（Link 标签修正 + Reviewed-by）: https://lore.kernel.org/all/apZ-B__OiVcZW46Z@gpd4/
- 作者回复: https://lore.kernel.org/all/2da859e8-2025-4926-99f4-8ba595e25abf@linux.dev/
- v2: https://lore.kernel.org/all/20260901124347.755904-1-cui.tao@linux.dev/
- 被修复的原始讨论（`Link:` 所指）: https://lore.kernel.org/all/b53c61a1-4d7d-4232-941f-d48b0563d4ed@linux.dev/
- tip-bot commit: 未获取到
- stable backport: 未获取到
