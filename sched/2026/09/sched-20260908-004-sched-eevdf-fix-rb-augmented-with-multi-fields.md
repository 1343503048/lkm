# sched/eevdf: fix rb augmented with multi fields

## TL;DR

Vincent Guittot 09-08 21:55 发出的单补丁，补的是他前一天 `sched/eevdf: Fix augmented max_slice`（见 related_articles）背后的**同类根因**：EEVDF 运行树增广了 3 个字段（`min_vruntime`/`min_slice`/`max_slice`），但 `RB_DECLARE_CALLBACKS` 只支持一个 `RBAUGMENTED`，于是 `_copy` 与 `_rotate` 这两个回调只搬 `min_vruntime`，插入再平衡（`__rb_insert_augmented`）和 `rb_erase` 变色路径（`__rb_erase_color`）会把另外两个字段搬丢。补丁把模板泛化成 `RB_DECLARE_CALLBACKS_MULTI`（由调用方提供一个 copy 函数），并在 fair.c 里加 `min_vruntime_copy()` 一次拷三个字段。`Fixes: aef6987d8954`。我在本地主线核对过：`kernel/sched/fair.c:1034` 仍是单字段版本，问题依旧存在。

## 背景与问题

`sched/eevdf: Propagate min_slice up the cgroup hierarchy`（`aef6987d8954`）之后，`min_vruntime_update()` 每次要算三个量：

```c
se->min_vruntime = se->vruntime;   __min_vruntime_update(se, node->rb_right); ...
se->min_slice    = se->slice;      __min_slice_update(se, node->rb_right); ...
se->max_slice    = se->slice;      __max_slice_update(se, node->rb_right); ...
```

而增广模板里负责「节点身份被换掉时搬数据」的两个回调只认一个字段：

```c
RBNAME ## _copy(...)   { new->RBAUGMENTED = old->RBAUGMENTED; }
RBNAME ## _rotate(...) { new->RBAUGMENTED = old->RBAUGMENTED; RBCOMPUTE(old, false); }
```

`_copy` 由 `__rb_erase_augmented()` 在「用后继节点顶替被删节点」时调用（`rbtree_augmented.h` 里有两处 `augment->copy(node, successor)`），`_rotate` 由 `rb_insert_augmented()` 传给 `__rb_insert_augmented()`、以及 `__rb_erase_color()` 做重染色时调用——都是红黑树自身的再平衡路径。也就是说，只要树发生旋转或节点被后继顶替，`min_slice`/`max_slice` 就会被留在旧节点上、新节点带着陈旧值参与后续聚合，`cfs_rq_min_slice()`/`cfs_rq_max_slice()` 的读数随之失真。前者影响 lag 钳制下界，后者影响 `entity_lag()` 的钳制上界。

这与 09-07 那篇 `Fix augmented max_slice` 修的是同一条约定（"增广字段必须在节点身份变化时被完整维护"）的两个不同侧面：那天补的是入队前的预置漏了 `max_slice`，这次补的是树再平衡时只搬了 1/3 的字段。

## 技术方案

把模板拆成两层：

- 新增 `RB_DECLARE_CALLBACKS_MULTI(RBSTATIC, RBNAME, RBSTRUCT, RBFIELD, RBCOPY, RBCOMPUTE)`，参数里 `RBAUGMENTED` 换成 `RBCOPY`，`_copy`/`_rotate` 都改成调用 `RBCOPY(new, old)`。
- 原有 `RB_DECLARE_CALLBACKS` 保留为单字段的特例：它自己生成一个 `RBNAME ## _copy_single()` 再转调 MULTI，所以其它增广树的调用点零改动。
- fair.c 侧提供真正的多字段拷贝并切换宏：

```c
static inline void min_vruntime_copy(struct sched_entity *new, struct sched_entity *old)
{
	new->min_vruntime = old->min_vruntime;
	new->min_slice    = old->min_slice;
	new->max_slice    = old->max_slice;
}

RB_DECLARE_CALLBACKS_MULTI(static, min_vruntime_cb, struct sched_entity,
		     run_node, min_vruntime_copy, min_vruntime_update);
```

设计取舍很直接：作者没有去改 `RBCOMPUTE` 的语义（那会在每次旋转时多跑一遍三向重算，成本高且不精确），而是把「怎么拷贝」交给树的拥有者提供一个函数——拷贝是 O(1) 的字段搬运，与重算解耦。

## 版本演进与当前进展

- 09-08 21:55 v1（`<20260908135526.2783039-1-vincent.guittot@linaro.org>`），`include/linux/rbtree_augmented.h | 35 +++++---`、`kernel/sched/fair.c | 15 ++-`，合计 `+41/-9`。
- 发出时间在北京 21:55，本日邮件里没有任何人回帖，无 tip-bot、无 stable。
- 本地主线核对：`kernel/sched/fair.c` 仍在用 `RB_DECLARE_CALLBACKS(..., min_vruntime, min_vruntime_update)`，`git log --grep='rb augmented with multi fields'` 无结果，说明该修复尚未进主线。

## Maintainer 意见与讨论焦点

未获取到——v1 刚发出，尚无 review。可作为权重的是：作者 EEVDF/fair.c 的长期维护者身份，且补丁带 `Fixes: aef6987d8954`（该提交本身就是 Peter Zijlstra 写的）。需要社区补的是两件事：

1. **可观测症状**。commit log 只说了事实（"maintains 3 augmented fields but only one is currently copied when balancing the tree"），没给任何「因此发生了什么」——是错误 eligible 判定、lag 越界还是只是统计噪声，都没写。这与前一天那条 `Fix augmented max_slice` 的处境相同。
2. **一处明显的风格问题**：新增的 `min_vruntime_copy()` 上面那段注释是从下面 `min_vruntime_update()` 处复制来的，写的是 `se->min_vruntime = min(se->vruntime, {left,right}->min_vruntime)`，与「拷贝」这个动作无关，且紧邻两条相同注释。这类 `include/linux/` 通用宏改动通常还要 `rbtree` 的维护者（Peter Zijlstra）过一眼，目前邮件里没有 CC 之外的表态可考。

## 合入评估

`likelihood=high`。依据：改动小且向后兼容（单字段宏原样保留，其它用户不受影响）、`Fixes` 指向明确、作者是子系统维护者、当日无人反对。卡点是流程性的——没有 Peter 的 Ack，也没进 tip；以及缺少可观测症状描述，这会影响它被定级为 `sched/urgent` 还是走常规窗口。值得注意的是，`rbtree_augmented.h` 是被 mm/、lib/ 多处使用的公共头，虽然 `RB_DECLARE_CALLBACKS_MULTI` 是纯新增、`RB_DECLARE_CALLBACKS` 保持同名同参展开，回归风险很低，但仍需一次全树构建验证。

## 效果评估

暂无效果数据。邮件里没有 benchmark、没有 bug 复现日志、没有修复前后对比，也没有指出哪些负载会观测到偏差——只有代码层面的必要性论证（属作者主观判断，未见测试数据）。间接证据只有 `Fixes` 目标那条提交的动机本身（min_slice 向 cgroup 层级传播是为了让层级内的公平性判断正确），与本次要修的新症状无关。

## 我可以参与的点

- `testing`：这是最容易做出增量的一条。构造一个会让运行树频繁旋转的负载（大量不同 slice/权重的实体反复入队出队，例如混合 `sched_latency` + cgroup 份额动态调整），比较打补丁前后 `cfs_rq_min_slice()`/`cfs_rq_max_slice()` 的采样值与实体 lag 分布；若能给出任何一个可观测偏差，就直接补上了本补丁缺的症状证据。
- `review`：顺手把全树所有 `RB_DECLARE_CALLBACKS*` 用户扫一遍，确认还有谁的 `RBCOMPUTE` 实际维护了多个字段却只声明了一个——这个 bug 模式是通用宏设计缺陷导致的，EEVDF 未必是唯一受害者。另外可提醒作者修掉 `min_vruntime_copy()` 上方的复制粘贴注释。
- `new_patch`：回合到自家分支（OLK-6.6）时应把这一条与前一天的 `Fix augmented max_slice` 成对回合，两者都在维护同一个「增广字段完整性」不变式；按 OLK 规范，`Fixes` 需引用自家分支的 commit 而非上游 `aef6987d8954`。

## 参考链接

- v1 邮件: https://lore.kernel.org/all/20260908135526.2783039-1-vincent.guittot@linaro.org/
- `Fixes` 目标 `sched/eevdf: Propagate min_slice up the cgroup hierarchy`（hash 取自本地 ~/code/linux 的 git log，非本日邮件）: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=aef6987d8954
- 同作者的镜像修复 `sched/eevdf: Fix augmented max_slice`: https://lore.kernel.org/all/20260907123855.1297976-1-vincent.guittot@linaro.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260908-004
date: '2026-09-08'
subject: 'sched/eevdf: fix rb augmented with multi fields'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <20260908135526.2783039-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20260908135526.2783039-1-vincent.guittot@linaro.org/
upstream_commit: null
fixes_commit: aef6987d8954
merged_branch: null
current_version: v1
generated_at: "2026-09-09T00:45:00"
authors:
- Vincent Guittot
maintainers_involved: []
patch_series:
- version: v1
  msgid: <20260908135526.2783039-1-vincent.guittot@linaro.org>
  date: '2026-09-08'
  summary: 把 RB_DECLARE_CALLBACKS 泛化为 RB_DECLARE_CALLBACKS_MULTI（由调用方提供 RBCOPY），原单字段宏改为自动生成 _copy_single 后转调 MULTI；fair.c 新增 min_vruntime_copy() 同时搬运 min_vruntime/min_slice/max_slice，并改用 MULTI 声明 min_vruntime_cb。
  review_outcome: 本日无人回帖，无 Ack 无 NAK，也未见 tip-bot 收录。
merge_assessment:
  likelihood: high
  blocking_issues:
  - 尚无 Peter Zijlstra 等维护者 Ack，rbtree_augmented.h 属公共头需一次全树构建验证
  - commit log 未描述可观测症状（哪些判定/统计会偏、什么负载会暴露），影响 urgent 还是常规窗口的定级
  next_action: 等 review；或有人回帖附可观测偏差与数据，同时修掉 min_vruntime_copy() 上方复制粘贴的错误注释
contribution_opportunities:
- kind: testing
  description: 用不同 slice/权重实体高频入队出队（混合 sched_latency 与 cgroup 份额动态调整）比对补丁前后 cfs_rq_min_slice()/cfs_rq_max_slice() 采样与实体 lag 分布，补上缺失的症状证据
- kind: review
  description: 扫描全树其它 RB_DECLARE_CALLBACKS 用户，确认是否存在同样「RBCOMPUTE 维护多字段但只声明一个 RBAUGMENTED」的同源缺陷
- kind: new_patch
  description: '与前一日的 sched/eevdf: Fix augmented max_slice 成对回合到自家分支以恢复增广字段完整性不变式，Fixes 需引用自家分支 commit'
source_email_count: 1
related_articles:
- sched-20260907-001
tags:
- eevdf
- cfs
---
