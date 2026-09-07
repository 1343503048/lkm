---
id: sched-20260907-001
date: '2026-09-07'
subject: 'sched/eevdf: Fix augmented max_slice'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <20260907123855.1297976-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20260907123855.1297976-1-vincent.guittot@linaro.org/
upstream_commit: null
fixes_commit: 6e3c0a4e1ad1
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Vincent Guittot
maintainers_involved: []
patch_series:
- version: v1
  msgid: <20260907123855.1297976-1-vincent.guittot@linaro.org>
  date: '2026-09-07'
  summary: '__enqueue_entity() 在 se->min_slice = se->slice 之后补 se->max_slice = se->slice，使新入队实体不带着上次作为树内部节点时的陈旧
    max_slice 参与增广计算；+2 行，带 Fixes: 6e3c0a4e1ad1 ("sched/fair: Fix lag clamp")。'
  review_outcome: 本日无人回帖，无 Ack 无 NAK，也未见 tip-bot 收录。
merge_assessment:
  likelihood: high
  blocking_issues:
  - 尚无 Peter Zijlstra 等维护者的 Ack/收录
  - commit log 未描述可观测症状，缺 benchmark 或复现证据，影响其定级（urgent 还是常规窗口）
  next_action: 等 review；或由社区用混合 slice 负载给出可观测数据后推动进 sched/urgent
contribution_opportunities:
- kind: testing
  description: 构造混合 slice 负载并借 /proc/sched_debug 或 ftrace 观察 entity_lag() 是否越出理论界，回帖提供修复前后数据
- kind: new_patch
  description: 回合到自家 OLK-6.6——该分支 kernel/sched/fair.c 的 __enqueue_entity() 同样只预置 min_slice，而
    min_vruntime_update() 已在算 max_slice；回合时 Fixes 需引用 OLK-6.6 自身的 commit
- kind: review
  description: 复查 rb_add_augmented_cached() 其它调用点是否也存在「入队前未预置被增广字段」的同源问题
source_email_count: 1
related_articles: []
tags:
- eevdf
- cfs
title: 'sched/eevdf: Fix augmented max_slice'
layout: article
---

## TL;DR

Vincent Guittot 在 09-07 20:38 发出单补丁：`__enqueue_entity()` 里只把 `se->min_slice` 初始化成 `se->slice`，漏了同样初始化 `se->max_slice`，于是新入队实体会带着上一次作为红树内部节点时被算大的 `max_slice`，并被 augment 回调沿路径传播上去，使 `cfs_rq_max_slice()` 偏大、`entity_lag()` 的 clamp 上界被放松。补丁 +2 行，`Fixes: 6e3c0a4e1ad1 ("sched/fair: Fix lag clamp")`。刚发出、本日无人回帖，但它修的是 EEVDF 公平性计算的正确性缺陷，且本地主线（v7.0+）与 OLK-6.6 分支里都还能看到这个漏初始化，值得跟一手。

## 背景与问题

`entity_lag()` 是 EEVDF 里给实体 lag 做钳制的地方：

```c
static s64 entity_lag(struct cfs_rq *cfs_rq, struct sched_entity *se, u64 avruntime)
{
	u64 max_slice = cfs_rq_max_slice(cfs_rq) + TICK_NSEC;
	s64 vlag, limit;

	vlag = avruntime - se->vruntime;
	limit = calc_delta_fair(max_slice, se);

	return clamp(vlag, -limit, limit);
}
```

由于 `V` 是树内实体的加权平均，增删/改权重会把 `V` 挪动，从而可能让实体的 lag 比钳制前还大；上游的钳制上界取自「本 rq 上最大的 slice」（稳态 EEVDF 的界是 `-r_max < lag < max(r_max, q)`）。这个 `max_slice` 追踪是 `6e3c0a4e1ad1 ("sched/fair: Fix lag clamp")` 补上的——按主线该提交的说明，起因正是 Vincent 报告混合 slice 负载下出现「不该有的 lag 钳制（undue lag clamping）」，Peter 顺手把 todo 注释里的 `max_slice` 追踪实现出来。

问题在于新增的 `max_slice` 只加进了红树增广回调，没跟上入队路径的预置代码。

## 技术方案

改动是在 `__enqueue_entity()` 里补两行：

```c
 	sum_w_vruntime_add(cfs_rq, se);
 	se->min_vruntime = se->vruntime;
 	se->min_slice = se->slice;
+	se->max_slice = se->slice;
+
 	rb_add_augmented_cached(&se->run_node, &cfs_rq->tasks_timeline,
 				__entity_less, &min_vruntime_cb);
```

作者一句话点出取舍：「Similarly to se->min_slice, init se->max_slice with se->slice before enqueueing the entity so the augmented callback computes it correctly at parent level.」也就是说沿用既有约定——`rb_add_augmented_cached()` 只对**新节点的祖先**跑 `min_vruntime_update()`，不会重算节点自身，所以 `min_vruntime`/`min_slice` 必须在入队前手工预置；`max_slice` 是后来才被塞进 `min_vruntime_update()` 的第三个量（`se->max_slice = se->slice; __max_slice_update(...)`），预置这一步没同步补上。

补充推断（邮件未展开，属我按代码所得）：误差方向偏「大」。一个实体若在上次在树里时是内部节点，其 `max_slice` 已被子树刷成较大值，出队时该字段不会被清；再以叶子身份入队时只有祖先被重算，自身仍是旧值，于是 `__max_slice_update()` 把这个偏大的值继续往上搬，`cfs_rq_max_slice()` 高估 → `limit` 偏大 → lag 少被钳制。这与原提交要修的「过度钳制」正好相反，属于同一处逻辑的镜像 bug。

## 版本演进与当前进展

- 09-07 20:38 Vincent Guittot 发出 v1（`<20260907123855.1297976-1-vincent.guittot@linaro.org>`），`kernel/sched/fair.c | 2 ++`。
- 本日邮件里没有任何人回帖，也没有 tip-bot 回复。
- 本地主线仓库（HEAD ≈ `v7.0-34367-g`）里 `__enqueue_entity()` 仍只赋 `min_slice`，`git log --grep='augmented max_slice'` 无结果，说明发出时该修复尚未进入主线。

## Maintainer 意见与讨论焦点

未获取到——本日该系列只有作者这一封邮件，无任何 review、无 Ack、无 NAK，讨论焦点尚未形成。可作参考的是历史脉络：`Fixes` 目标 `6e3c0a4e1ad1` 的报告者与测试者正是 Vincent 本人（该提交 trailer 含 `Reported-off-by`/`Tested-by: Vincent Guittot`），作者与原始问题的报告人是同一个人，这通常意味着方案不需要额外论证动机。目前没有已知的反对意见，也没有已知的未解决问题。

## 合入评估

`likelihood=high`。依据：改动 2 行、纯补漏初始化、带 `Fixes` 标签，且来自长期负责 fair/EEVDF 的维护者，本日无人反对。卡点只可能是流程性的——尚无 Peter Zijlstra/Neeraj Upadhyay 的 Ack，也尚未见 tip 收录。需要作者或社区补的东西不多，最有价值的是有人拿混合 slice 负载验证一下效果（见下节）。若确实如推断所说是「少钳」而非「多钳」，commit log 里没有描述可观测症状，进 `sched/urgent` 还是走常规窗口可能取决于有没有人报出实际影响；`next_action` 是等 review，或有人回帖附症状与数据。

## 效果评估

邮件里没有效果数据：没有 benchmark、没有 bug 复现日志、也没有「修复前后对比」，只有代码层面的必要性论证（属于作者主观判断，未见测试数据）。历史侧的证据来自 `Fixes` 目标那条提交——主线记录显示 `6e3c0a4e1ad1` 那次改动是为解决「mixed slice workload 下 undue lag clamping」，并被 Prateek Nayak、Shubhang Kaushik 等人测试过，可作为「这条 clamp 逻辑确实会影响真实负载公平性」的间接佐证，但与本补丁的新症状无关。

## 我可以参与的点

- 验证方向（review/testing）：这个漏初始化只影响 `entity_lag()` 读到的 `root->max_slice`，能落地的验证办法是构造混合 slice 的负载（不同 `sched_latency`/权重、频繁 enqueue-dequeue 让实体在树内部节点与叶子之间切换），观察 lag 是否越出理论界；`/proc/sched_debug` 与 `update_entity_lag()` 两侧都可下 ftrace。回帖给出数据对该补丁的定级（urgent vs 常规窗口）直接有用。
- 自家分支（new_patch）：我确认过 `~/code/olk-6.6` 里 `kernel/sched/fair.c` 同样只有 `se->min_slice = se->slice;`（第 1170 行附近），而 `min_vruntime_update()` 已经在算 `se->max_slice`（第 1151 行），即同样中招。这是一个可直接回合的 2 行修复；按 OLK 规范回合时 `Fixes` 要写 OLK-6.6 自己的 commit，不要抄上游的 `6e3c0a4e1ad1`。
- 顺手排查（review）：同一处约定（「增广回调不重算节点自身」）还要求 `min_vruntime`、`min_slice` 在其它绕过 `__enqueue_entity()` 的入队路径里被正确预置，可以把 `rb_add_augmented_cached()` 的其它调用点扫一遍确认没有第三处遗漏。

## 参考链接

- v1 邮件: https://lore.kernel.org/all/20260907123855.1297976-1-vincent.guittot@linaro.org/
- `Fixes` 目标（主线 `sched/fair: Fix lag clamp`，hash 与提交说明取自本地 `~/code/linux` 的 git log，非本日邮件）: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=6e3c0a4e1ad1
- tip-bot commit: 未获取到
- stable backport: 未获取到
