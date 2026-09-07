---
id: sched-20260907-010
date: '2026-09-07'
subject: 'sched_ext: scx_qmap: Fix pending partition work handoff'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <4c9a9c9cabc3547e23bae5ae00421a52@kernel.org>
lore_url: https://lore.kernel.org/all/4c9a9c9cabc3547e23bae5ae00421a52@kernel.org/
upstream_commit: null
fixes_commit: e9151ed5c944
merged_branch: sched_ext/for-7.3-fixes
current_version: v1
generated_at: '2026-09-07'
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
patch_series:
- version: v1
  msgid: <4c9a9c9cabc3547e23bae5ae00421a52@kernel.org>
  date: '2026-09-06'
  summary: 'tools/sched_ext/scx_qmap.bpf.c +40/-35。修复 qmap 分区工作交接空窗：新增 PART_REFRESH/PART_REDISTRIBUTE
    两个 flag，把排空循环抽成 execute_partition()（先 try_start 取守卫、取走 pending、需要时才 account/compute/apply，只有
    REDISTRIBUTE 才重建分区、否则仅 refresh_usable），并确立「请求先发布再抢 runner」「释放 part_busy 之后再检查
    pending」「所有持有者释放后都排空（含 flush_alloc 的 stats flush）」三条规则；rr_advance() 改为无条件 execute_partition()。Fixes:
    e9151ed5c944，Reported-by: Andrea Righi。'
  review_outcome: Andrea Righi 09-06 给 Reviewed-by（Looks good to me）；Tejun Heo 09-07
    06:40 回 Applied to sched_ext/for-7.3-fixes。无 v2、无返工，本线程未给出入树 commit hash。
merge_assessment:
  likelihood: merged
  blocking_issues:
  - 无技术卡点：一轮评审即合入 sched_ext/for-7.3-fixes
  - 本线程未给出入树后的 commit hash 与所进 -rc 序号；是否 -stable 回合未讨论
  next_action: 跟踪 sched_ext/for-7.3-fixes 拉取进主线的时点；给 qmap 追加功能时按新的「先发布再抢守卫」协议写发布点
contribution_opportunities:
- kind: testing
  description: 在 sched_ext/for-7.3-fixes 上跑 scx_qmap + 高频 cgroup effective-cap 调整与
    CPU 热插拔，量化分区收敛延迟是否仍与 round-robin 周期相关（本线程无任何复现/压测证据）
- kind: review
  description: 复核 else if (pending & PART_REFRESH) 的丢弃式合并是否总安全（REDISTRIBUTE 路径是否恒含
    refresh 语义），以及 execute_partition() 抢不到守卫即 break 是否可能与自身刚发布的请求互等
- kind: new_patch
  description: 把 publish-before-claim / release-before-check / all-holders-drain 这套交接不变量套到自家
    cpuset/cgroup 异步重分配路径做同类排查，必要时补注释或断言
source_email_count: 1
related_articles: []
tags:
- sched_ext
- cgroup
title: 'sched_ext: scx_qmap: Fix pending partition work handoff'
layout: article
---

## TL;DR

Tejun Heo 09-06 给自己维护的示例/自测调度器 `scx_qmap` 打了一个时序补丁：qmap 的分区（partition）更新采用「单 runner + pending 标志」的同步方式，但**请求的发布时机**和**runner 的检查时机**互相错开，存在一个把分区工作留在「有 pending、无 runner」状态的空窗，结果是这次分区更新要等到 round-robin 定时器下一次 tick 才生效。修复确立三条规则：请求**先发布再去抢 runner**、**释放 part_busy 之后再检查是否还有活**、**所有拿到过 runner 的人释放后都要排空 pending（包括只做 stats flush 的持有者）**；同时用 `PART_REFRESH` / `PART_REDISTRIBUTE` 两个 flag 把「刷新可用 mask」和「真正的重分区」分开，只在确实请求过重分区时才 `compute_partition()`。Andrea Righi（报告的正是他）给出 Reviewed-by，09-07 06:40 Tejun 回「Applied to sched_ext/for-7.3-fixes with Andrea's Reviewed-by.」——本线程已入分支。

## 背景与问题

`scx_qmap` 是 `tools/sched_ext/scx_qmap.bpf.c` 里的示例 BPF 调度器，同时充当 sched_ext 的自测载体。自 `e9151ed5c944` ("tools/sched_ext: scx_qmap - Expand hierarchical sub-scheduling") 之后它支持层级子调度：把 CPU 按 effective cap 在多个子调度器/cgroup 之间做分区，并且会 grant/revoke CPU。

分区状态 `qa.part` 会被并发上下文写入，补丁里列出的三类上下文互不被内核串行化：子调度器回调（`qmap_sub_ecaps_update()`，即 effective-cap 更新）、cgroup 相关回调（`flush_alloc()` 这条 stats 路径）、以及 `bpf_timer` 里的 rr 定时器回调 `rr_advance()`。原设计的同步手段是：

- 一个 single-runner 守卫 `part_busy`（`part_try_start()` / `part_end()`），一次只放一个写者进去，理由是「不能跨 grant/revoke kfunc 持锁」；
- 一个 `part_pending` 位图做合并（coalescing）：抢不到 runner 的调用者把请求挂到 `part_pending` 上，由持有者收尾时排干，rr 定时器作为兜底。
- 这两个变量刻意放在 `.bss` 而不是 arena：`rr_advance()` 跑在 bpf_timer 回调里，verifier 不接受对 arena 内存做原子操作。

问题出在交接（handoff）。commit message 的原文陈述是：

> qmap can leave partition work pending with no runner. The effective-cap callback publishes its request after failing to acquire part_busy, while redistribute() checks for pending work before releasing it. Either ordering can miss a request arriving as the current runner finishes, delaying the update until the round-robin timer runs.

对应到修复前的代码，两条丢请求的路径都能看清：

1. `qmap_sub_ecaps_update()` 走的是「先 `part_try_start()`，失败才 `__sync_fetch_and_or(&part_pending, 1)`」——即**在抢 runner 失败之后才发布请求**。此时若持有者已经做完最后一次 pending 检查，这个请求就没有主人接手。
2. 旧的 `redistribute()` 是在**仍持 part_busy 时**用 `bpf_for` 循环里的 `__sync_fetch_and_or(&part_pending, 0)` 判断是否继续，循环退出后才 `part_end()`——即**在释放守卫之前检查 pending**。在「最后一次检查」与「释放」之间发布的请求同样被漏掉。

任一顺序下，漏掉的请求最坏要等到 round-robin 定时器跑到才生效，也就是分区（哪个子调度器拿多少 CPU）会在一段时间内与实际下发的 effective cap 不一致。

## 技术方案

改动集中在 `tools/sched_ext/scx_qmap.bpf.c`，`40 insertions(+), 35 deletions(-)`（共 75 行变更），没有触碰内核侧代码。

1. **pending 位图语义化**：新增 `enum part_pending_flags { PART_REFRESH = BIT_U64(0), PART_REDISTRIBUTE = BIT_U64(1) }`，注释相应地从「coalesces repartition requests」改成「coalesces refresh and repartition requests」。
2. **把排空循环从 `redistribute()` 里抽出来**，改名 `execute_partition()`：每次迭代先 `part_try_start()`（抢不到就 break，说明别人在处理），然后 `pending = __sync_fetch_and_and(&part_pending, 0)` 一次性取走全部请求，`PART_REDISTRIBUTE` 才做 `account_alloc() + compute_partition() + apply_partition()`（先给旧分区计账再重建），否则只有 `PART_REFRESH` 时仅 `refresh_usable()`；接着 **先 `part_end()` 释放守卫，再 `if (!__sync_fetch_and_or(&part_pending, 0)) break;`**。代码里留下的注释正是这条设计不变量：

   > Requests are published before trying the guard. Releasing it before checking pending work ensures a racing request is either observed here or handled by a caller that acquires the guard.

   即「发布先于抢锁 + 检查后于释放」把两个窗口合成一个交接协议：竞争者要么被本次检查看到，要么自己抢到 runner 处理。
3. **所有发布点统一为「先 or 标志、再 execute」**：`redistribute()` 变成 `__sync_fetch_and_or(&part_pending, PART_REDISTRIBUTE); execute_partition();`；`qmap_sub_ecaps_update()` 尾部那段 if/else（约 12 行）整体替换为 `__sync_fetch_and_or(&part_pending, PART_REFRESH); execute_partition();`。
4. **所有持有者释放后都排空**：`flush_alloc()` 在 `part_try_start()` 成功的路径里做完 `account_alloc()` + `part_end()` 之后新增一次 `execute_partition()`（这就是 commit message 里的 "including the stats flush"）；`rr_advance()` 把原先的 `/* a resplit queued while we held the guard supersedes this rotation */ if (__sync_fetch_and_or(&part_pending, 0)) redistribute();` 直接换成无条件 `execute_partition()`，顺带避免了「rr 路径把一次 refresh 升级成 repartition」的旧副作用。
5. `bpf_for(i, 0, 1024)` 的迭代上限保留，注释明确「The rr timer is the backstop if the loop reaches its iteration limit.」——兜底仍是 rr 定时器，但只是异常路径，不再是正常延迟来源。

Fixes: `e9151ed5c944` ("tools/sched_ext: scx_qmap - Expand hierarchical sub-scheduling")，`Reported-by: Andrea Righi <arighi@nvidia.com>`，`Signed-off-by: Tejun Heo <tj@kernel.org>`。主题前缀直接写了目标分支 `[PATCH sched_ext/for-7.3-fixes]`。

## 版本演进与当前进展

- 09-06 06:53 Tejun Heo 投递（单补丁、无 v 号），已带 `Reported-by: Andrea Righi`，说明问题由 Andrea 先发现并在线下/其它渠道报给维护者。
- 09-06 22:02 Andrea Righi：「Looks good to me, thanks for fixing it.」+ `Reviewed-by: Andrea Righi <arighi@nvidia.com>`。
- 09-07 06:40 Tejun Heo：「Hello, Applied to sched_ext/for-7.3-fixes with Andrea's Reviewed-by.」——从投递到入分支约 24 小时，一轮评审、无返工、无 v2。
- 邮件正文中未给出入树后的 commit hash（该分支的 git 记录未出现在本线程里）。

## Maintainer 意见与讨论焦点

本线程没有技术分歧，讨论焦点其实是「这条维护惯例值不值得记下来」：

- **Tejun Heo（sched_ext 维护者）** 一人完成写、解释与合入，commit message 用词把问题定位成 *ordering*（"Either ordering can miss a request"）而不是某个具体分支条件，说明他判断根因是协议不对称，因此修法是把两条规则同时立起来，而不是打补丁式加一次额外检查。
- **Andrea Righi（报告者 + 评审者）** 只给了 Reviewed-by，没有提出补充意见。
- 值得注意的是**没有人在「refresh 会不会被 repartition 吞掉」这条新语义上发言**：新代码里 `else if (pending & PART_REFRESH)` 意味着当两个 flag 同时挂起时只做重分区、不再单独 `refresh_usable()`。这依赖 `compute_partition()/apply_partition()` 本身就隐含刷新可用 mask——邮件中未展开论证（属于按代码可读出的隐含前提）。

## 合入评估

`likelihood=merged`。已进入 `sched_ext/for-7.3-fixes`（带 Andrea 的 Reviewed-by），按 sched_ext 的 fixes 流程会随维护者拉取进入主线 -rc；具体 -rc 序号与本线程 commit hash 未获取到。

`severity=low`，理由：受影响对象只是 `tools/sched_ext/scx_qmap.bpf.c`（示例/自测用的 BPF 调度器），不在内核镜像里、不参与核心调度决策；后果也只是分区更新被推迟到下一个 round-robin tick，不产生崩溃、账目错误或 hung task。是否走 -stable 邮件中未提及（`Fixes:` 指向的 `e9151ed5c944` 若已进主线，理论上具备回合条件，但 tools/ 下的 BPF 自测程序通常不在 -stable 优先级上，本线程未见相关讨论）。

## 效果评估

邮件中没有 benchmark，也没有竞态复现步骤或统计数字——这类时序修复本来就没有可量化收益。可陈述的效果只有两点：

- **正确性/时效性**：effective-cap 变化到分区生效之间的延迟，从「最坏要等一个 round-robin 周期」变成「当场由任一排空者处理」；rr 定时器退化为循环迭代上限的兜底。
- **开销方向**：新逻辑区分 refresh 与 repartition 后，纯 effective-cap 更新在无 repartition 请求时不再走 `account_alloc() + compute_partition() + apply_partition()` 全量重建，只做 `refresh_usable()`；同时 `rr_advance()` 不再因为存在 pending refresh 而触发一次 repartition。这两处都是减少工作量，但没有实测数字支持（未获取到）。

## 我可以参与的点

- **这个交接模式与 cpuset/cgroup 的异步重分配是同构问题**：多个上下文（cgroup 迁移回调、定时器、cpu online/offline）并发请求「同一时刻只有一个执行者能重建分区，且不能持锁跨 kfunc」，解法空间就是 publish/claim 与 release/check 的四种排列。本补丁给出的组合（发布先于抢守卫、检查后于释放、所有持有者都排空）是一个可以直接照抄的范式，自家 cpuset/workqueue 风格的异步收敛路径如果也有「pending + single runner」结构，值得按这四条逐一对照是否有漏单窗口。
- **可以直接替维护者补的验证**：本线程没有任何复现或压测证据。有条件的话在 tip 的 `sched_ext/for-7.3-fixes` 上跑 `scx_qmap` 配合高频 cgroup effective-cap 调整（大量子组 + `rr_advance` 周期缩短到极小值）与 CPU 热插拔，观察分区收敛延迟是否还与 rr 周期相关，一个带数据的回帖会很有分量；这也是 sched_ext 自测体系目前明显缺的一环。
- **可提的评审点（本线程无人讨论）**：`else if (pending & PART_REFRESH)` 的丢弃式合并是否总是安全——即 `PART_REDISTRIBUTE` 路径是否在任何 cap 组合下都等价于一次 refresh；以及 `execute_partition()` 抢不到守卫时直接 break，是否可能与自己刚发布的请求形成「双方都以为对方会做」的活锁（按 commit message 的不变量论证应当不会，但把它写成注释或断言更好）。
- 关注 `sched_ext/for-7.3-fixes` 的拉取动作：本修复入主线后，`e9151ed5c944` 引入的层级子调度那套 pending 语义就算定型了，后续给 qmap 加功能应按新协议写发布点，别退回「抢到守卫再发布」的旧形状。

## 参考链接

- 补丁本体（09-06，Tejun Heo）: https://lore.kernel.org/all/4c9a9c9cabc3547e23bae5ae00421a52@kernel.org/
- Andrea Righi 的 Reviewed-by（09-06）: https://lore.kernel.org/all/ap1yb7oMEFeBNTPZ@gpd4/
- Tejun Heo 的 Applied 回执（09-07，本日）: https://lore.kernel.org/all/e08c5ec58b464ec684698bc59b864aeb@kernel.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到
- 相关代码：`tools/sched_ext/scx_qmap.bpf.c` 中 `struct part_pending_flags` / `execute_partition()` / `redistribute()` / `flush_alloc()` / `rr_advance()` / `qmap_sub_ecaps_update()`
- 被修复的 commit：`e9151ed5c944` ("tools/sched_ext: scx_qmap - Expand hierarchical sub-scheduling")
