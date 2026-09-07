# sched: Lift cgroup update locking to core to prevent CFS/SCX divergence

## TL;DR

本文为增量更新（完整背景见 related_articles）。Michal Blaszczyk 的 `[PATCH v3]` 在 09-01 拿到 Tejun Heo 的 `Acked-by`，并且 Tejun 当场**否决了 Andrea Righi 并行的 `sched_ext: Serialize cgroup knob updates` 方案**（"This is the same race … I'm inclined to go with that one"），转而请 Peter Zijlstra 把这份「把 cgroup 旋钮更新的锁提升到 core」的补丁收走。cgroup CPU 旋钮的 CFS/SCX 一致性修复路线就此收敛到一条。

## 背景与问题

`cpu.weight`、`cpu.idle`、`cpu.max` 等 cgroup CPU 旋钮由 core 的写处理函数落到具体调度类的回调（`scx_group_set_weight()` / `scx_group_set_idle()` / bandwidth 回调）。问题在于并发写：核心调度器状态变更与对应的 `ops.cgroup_set_*()` BPF 回调可能以不同顺序完成，使 BPF 调度器看到的 cgroup 状态与核心调度器不一致（CFS/SCX divergence）。该竞态由 Sashiko bot 报出，因此社区当天有**两条并行修复**：

- Andrea Righi：在 sched_ext 侧给每个 `task_group` 加 `knob_mutex`，串行化 weight/idle/bandwidth 写入（发到 `sched_ext/for-7.3-fixes`）。
- Michal Blaszczyk：把 fair 侧的更新锁**提升到 core 的写处理函数**，让两类更新跑在同一把锁下（走 sched/core）。

## 技术方案

选型的关键取舍是**修在哪一层**：sched_ext 内部加锁只能让 SCX 自己的回调彼此串行，无法保证「core 的状态变更」与「SCX 回调」之间对 CFS 也保持一致；把锁提升到 `kernel/sched/core.c` 的 cgroup 旋钮写入口，则 CFS 与 SCX 两条路径天然共用同一把锁，从结构上消除分歧。Tejun 09-01 的原话即是这个判断：

> This is the same race Michal's patch fixes by lifting the fair locking into the core write handlers so that both updates run under the same lock … I'm inclined to go with that one.

Andrea 那份 `knob_mutex` 方案因此被归为同一竞态的重复实现，被替代而非互补。历史版本上，Peter Zijlstra 在 08-22 曾就锁的具体形态给过改名建议（见 related_articles 的 08-22 篇），v3 即在其上迭代。

## 版本演进与当前进展

- v2：2026-08-21，`<20260821140818.1559100-1-michalblk@google.com>`。
- v3：2026-08-24，`<20260824074913.2468177-1-michalblk@google.com>`；Andrea Righi 08-24 回帖。
- **2026-09-01 06:36**：Tejun Heo 在 v3 上给出 `Acked-by: Tejun Heo <tj@kernel.org>`，并直接点名收取者——"Peter, would you mind picking this up?"
- **2026-09-01 06:37**：Tejun 在 Andrea 的 serialize 补丁上回帖，说明二者是同一竞态、倾向 Michal 的方案。
- 状态：`under_review` → 实质上已 `acked`，等待 sched/core 侧（Peter/Ingo）落地；本日未见 tip 回执。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext 维护者）**：本日的决定性表态。既给了 `Acked-by`，又主动替这个方案去争收取渠道（请 Peter 拿）。对 Andrea 的方案，他没有要求 Andrea 改动或补充，而是直接说明「同一竞态、走那份」。
- **Andrea Righi（sched_ext 另一维护者 / 被替代方案作者）**：本日为他的 serialize 补丁发帖的是 Tejun 的回复，未见他本人对撤回自己方案的公开表态；他此前对 Michal v3 的回帖（08-24）亦未构成反对。
- **Peter Zijlstra**：被点名请求收取，**09-01 未回复**。这是本条唯一的外部依赖。
- 未解决的分歧：锁提升到 core 后，cgroup 旋钮写路径的锁顺序与睡眠属性（`task_group` 路径能否睡眠、与 `cgroup_threadgroup_rwsem`/rq 锁的嵌套）在本日邮件里没有展开讨论；Michal 的 v3 邮件正文未进入本日缓存，无法确认这两点是否已在补丁说明里回答。

## 合入评估

`likelihood = high`。依据：sched_ext 一侧的所有权已由 Tejun 明确表态（`Acked-by` + 请 Peter 收取），并且竞争方案（Andrea 的 `knob_mutex`）已被同一位维护者公开让路，社区不存在遗留反对意见。卡点纯粹在 sched/core 侧：Peter Zijlstra / Ingo Molnar 是否接受把 fair 的更新锁上移到 core 写处理函数，以及是否要求就锁顺序与睡眠安全性补充说明。需要满足的条件：Peter 的 `Acked-by`/`Reviewed-by` 或他直接 pick；如果 sched_ext 的 `ops.cgroup_set_*()` 需要 sleepable（Tao Cui 的相关补丁依赖这个竞态先修好），两侧顺序也要一并确认。

## 效果评估

本日邮件中**无效果数据**。这条修复的收益是结构性/正确性导向的：消除 CFS 与 SCX 在 cgroup 旋钮更新上的状态分歧，使 BPF 调度器观察到的 `cpu.weight`/`cpu.idle`/`cpu.max` 变化与核心调度器实际状态一致。竞态本身由 Sashiko bot 报告，未附带可量化影响（例如错误率、性能偏差），因此「修好后能避免多严重的后果」目前缺乏数据支撑。相关依赖项（Tao Cui 的 sleepable 回调补丁）也尚未合入，无法从合入序列上佐证其紧迫度。

## 我可以参与的点

- **cpuset/cgroup 视角的 review（与你主线最贴）**：这条改动落在 `kernel/sched/core.c` 的 cgroup 旋钮写入口，与 cpuset 的 `cpuset.cpus`/`cpuset.mems` 更新共用同一层 task_group 序列化语义。可以在 Peter 回复之前，就「上移后的锁与 `cpuset`/`cgroup_threadgroup_rwsem` 的嵌套顺序、以及在持锁上下文中能否睡眠」给出分析或代码走查回帖——讨论里目前恰好缺这一层。
- **分支影响评估**：若 OLK-6.6 已把 sched_ext 回合过，就需要预判这一改动对 `cpu.weight`/`cpu.idle` 写入路径的侵入（它改的是 core，不是 ext），并检查自家是否已有类似的 `knob_mutex` 变体需要一并去掉。
- **跟踪连带项**：Tao Cui 的 `ops.cgroup_set_weight/idle()` sleepable 补丁依赖本竞态修复；可一并跟踪，判断何时可以干净跟进。

## 参考链接

- v3（本日获 Acked-by 的补丁）: https://lore.kernel.org/all/20260824074913.2468177-1-michalblk@google.com/
- Tejun 的 Acked-by + 请 Peter 收取: https://lore.kernel.org/all/e9cd7bd7c303b57d8716c4a8cab35058@kernel.org/
- Tejun 否决 serialize 方案的回帖: https://lore.kernel.org/all/16ad7666875543a33b88609ea444fddc@kernel.org/
- 被替代的 Andrea 方案: http://lkml.kernel.org/r/20260825092153.2602809-1-arighi@nvidia.com
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched: Lift cgroup update locking to core to prevent CFS/SCX divergence"
id: sched-20260901-003
date: '2026-09-01'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260824074913.2468177-1-michalblk@google.com>"
lore_url: "https://lore.kernel.org/all/20260824074913.2468177-1-michalblk@google.com/"
authors: [Michal Blaszczyk, Tejun Heo, Andrea Righi]
maintainers_involved: [Tejun Heo, Andrea Righi, Peter Zijlstra]
current_version: v3
patch_series:
  - version: v2
    msgid: "<20260821140818.1559100-1-michalblk@google.com>"
    date: '2026-08-21'
    summary: '把 fair 的 cgroup 更新锁提升到 kernel/sched/core.c 的写处理函数，使 CFS 与 SCX 的旋钮更新共用同一把锁'
    review_outcome: 'Peter Zijlstra 就锁的命名/形态给建议'
  - version: v3
    msgid: "<20260824074913.2468177-1-michalblk@google.com>"
    date: '2026-08-24'
    summary: '按 08-22 意见迭代；Andrea Righi 08-24 回帖'
    review_outcome: '2026-09-01 Tejun Heo Acked-by 并请 Peter Zijlstra 收取；同日 Tejun 以「同一竞态」为由让 Andrea 的 sched_ext knob_mutex 方案让路'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - "sched_ext 侧已 Acked-by，但 sched/core 侧 Peter Zijlstra 被点名后本日未回复，尚未进 tip"
  - "上移后的锁顺序与睡眠安全性（与 cpuset/cgroup_threadgroup_rwsem 的嵌套）在邮件里未展开讨论"
  next_action: "Peter Zijlstra/Ingo Molnar ack 或 pick；必要时补充锁顺序与可睡眠上下文说明"
contribution_opportunities:
  - kind: review
    description: "从 cpuset/cgroup 控制器视角走查上移后的锁嵌套顺序与持锁睡眠约束，在 Peter 回复前回帖补充"
  - kind: new_patch
    description: "评估该改动对已回合 sched_ext 的自有分支的侵入（改在 core 而非 ext），并清理自家可能存在的 knob_mutex 变体"
  - kind: discussion
    description: "跟踪依赖本竞态修复的 ops.cgroup_set_weight/idle() sleepable 补丁（Tao Cui）"
source_email_count: 2
related_articles:
  - "sched-20260821-001"
  - "sched-20260822-005"
  - "sched-20260824-005"
  - "sched-20260825-003"
tags:
- cgroup
- sched_ext
- cfs
generated_at: '2026-09-07'
---
