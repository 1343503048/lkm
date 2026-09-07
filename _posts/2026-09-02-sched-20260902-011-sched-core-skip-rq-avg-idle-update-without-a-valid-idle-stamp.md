---
id: sched-20260902-011
date: '2026-09-02'
subject: 'sched/core: Skip rq->avg_idle update without a valid idle_stamp'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20260807-master-v3-1-c328354efed3@gentwo.org>
lore_url: https://lore.kernel.org/all/20260807-master-v3-1-c328354efed3@gentwo.org/
upstream_commit: c6dcd97c8be75f052a1ca52cf79b03e7292962f1
fixes_commit: 4b603f1551a73
merged_branch: tip/sched/urgent
current_version: v3
generated_at: '2026-09-07'
authors:
- Shubhang Kaushik (Ampere)
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
- John Stultz
- K Prateek Nayak
- Zhan Xusheng
patch_series:
- '[PATCH v3] sched/core: Skip rq->avg_idle update without a valid idle_stamp'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 tip/sched/urgent；线程中无 Cc stable，可提议补标签
contribution_opportunities:
- 确认 OLK-6.6 是否含 4b603f1551a73；若含则此守卫几乎必回合（配置无关、零风险）
- 量化修复前后 sched_balance_newidle() 进入次数与 newidle 均衡频率，补齐线程缺的实测
- '提议为 c6dcd97c8be7 补 Cc: stable'
- 按 Zhan Xusheng 的口径自查 rq->idle_stamp 唯一写入点与 ttwu_pending 早退的相对位置
source_email_count: 1
related_articles: []
tags:
- sched/core
- compatibility
title: 'sched/core: Skip rq->avg_idle update without a valid idle_stamp'
layout: article
---

## TL;DR

Shubhang Kaushik（Ampere）的 urgent 修复：`update_rq_avg_idle()` 在没有有效 `rq->idle_stamp` 时必须早退，
否则会把 `rq_clock(rq)` 当成一次 idle 时长喂进 `update_avg()`，一次命中就把 `rq->avg_idle` 顶到上限。
9/2 15:22 tip-bot2 通告 Peter Zijlstra 已把它合入 **tip/sched/urgent**（Commit-ID
`c6dcd97c8be75f052a1ca52cf79b03e7292962f1`，CommitterDate 02 Sep 2026 09:17:49 +0200）。三轮迭代（v1→v3）由
Zhan Xusheng 的两次分析推动：真正的触发路径不是 proxy exec / core scheduling，而是 `sched_balance_newidle()`
在 `ttwu_pending` 处的早退——这让 bug 与配置无关。

## 背景与问题

`4b603f1551a73 ("sched: Update rq->avg_idle when a task is moved to an idle CPU")` 把 `rq->avg_idle` 的记账
从唤醒路径移到 `put_prev_task_idle()`，意图是「idle 任务被换下时就消费掉这段 idle 区间」。但它同时丢掉了原来
的合法性检查——旧代码包在 `if (rq->idle_stamp)` 里，新 helper 无条件算：

```c
-	if (rq->idle_stamp) {
-		u64 delta = rq_clock(rq) - rq->idle_stamp;
+void update_rq_avg_idle(struct rq *rq)
+{
+	u64 delta = rq_clock(rq) - rq->idle_stamp;
```

`idle_stamp` 为 0 时，`delta` 就等于整个 `rq_clock(rq)`，即开机以来的时间。Zhan Xusheng 给出了后果的量级：
`update_avg()` 每次加 `diff/8`，运行几分钟的机器上 `rq_clock()` 约 `~1e12`，一次就推动 `avg_idle` 约
`~1.25e11`，而 clamp 上界 `2*max_idle_balance_cost` 只有 `1e4..1e5` 量级——**一次命中即饱和**。

更关键的是可达性。作者最初举的两个例子（`find_proxy_task()`、force-idling）都需要 proxy exec 或
`CONFIG_SCHED_CORE`；Zhan Xusheng 8/7 指出有一条无需任何配置的路径，而且很可能就是 hackbench 追踪实际命中的那条：

```
	if (this_rq->ttwu_pending)
		return 0;
	...
	this_rq->idle_stamp = rq_clock(this_rq);
```

`rq->idle_stamp` 只有一个写入点（`fair.c:14563`）且位于 `ttwu_pending` 早退（`fair.c:14555`）之下，所以
"the reachable set is not the three examples but any path into idle that misses that one line"；又因为
`update_rq_avg_idle()` 退出时把字段清零，每次这样的进入都从零开始。9/1 他补上 `Reviewed-by` 并强调
"The trigger moved on purpose... The guard came off with it, and nothing about that fails to compile."

后果方向也讲清了：`avg_idle` 的两个消费者（`fair.c:14504`、`fair.c:14584`）在 `avg_idle` 虚高后不再拦住
newidle 均衡，"It only ever adds newidle balancing, never removes it, which fits latency reports rather than
wrong results." 另外 Zhan 顺带确认过 **不存在陈旧 stamp 的问题**：`14674` 在真正拉到任务时清零、另一处写是
`sched_init()`，所以字段非 0 即本次 idle 的 `rq_clock`，恢复守卫正好切在这个二分上。

## 技术方案

`kernel/sched/core.c`，+8/-2，v3 最终形态（把 `unlikely()` 去掉了）：

```c
 void update_rq_avg_idle(struct rq *rq)
 {
-	u64 delta = rq_clock(rq) - rq->idle_stamp;
-	u64 max = 2*rq->max_idle_balance_cost;
+	u64 idle_stamp = rq->idle_stamp;
+	u64 delta, max;
+
+	if (!idle_stamp)
+		return;
+
+	delta = rq_clock(rq) - idle_stamp;
 
 	update_avg(&rq->avg_idle, delta);
 
+	max = 2 * rq->max_idle_balance_cost;
 	if (rq->avg_idle > max)
 		rq->avg_idle = max;
 	rq->idle_stamp = 0;
```

设计定位（作者自己写的）：这是早先提案的**窄化版本**——只在 `update_rq_avg_idle()` 里恢复 `rq->idle_stamp`
守卫，**故意不**从 `set_next_task_idle()` 去打 idle 时间戳，从而保留现有 newidle 记账模型、绕开 force-idle /
proxy-exec 记账争议。相关的更早提案见下面的 `firelzrd` 链接（正文引用）。注意 `rq->idle_stamp = 0` 在守卫
失效时是 no-op（本来就是 0），所以早退与原来语义等价——Zhan 明确论证了这一点，且 `update_rq_avg_idle()`
只有一个调用者。

## 版本演进与当前进展

- 7/28 v1（`base-commit: 3b5f4b83c4abc0c9b0a7b9e2b44e816611b7f2ec`）：只描述 `rq_clock - idle_stamp` 问题，
  附 "Temporary tracing under hackbench load confirmed that update_rq_avg_idle() can be reached with
  rq->idle_stamp == 0. Hackbench showed no material regression versus v7.2-rc5 mainline."
- 7/29 K Prateek Nayak（AMD）给 `Reviewed-by`，并指出 "we switch to idle context without a newidle balance
  during find_proxy_task() and also during force-idling."
- 8/6 v2：加入 Prateek 标签、把 `find_proxy_task()` / force-idling 写进 changelog、Cc John Stultz。
- 8/7 John Stultz（Google，被改动 commit 的作者）给 `Acked-by`。
- 8/7 v3：按 Zhan Xusheng 的意见 (a) 以 `sched_balance_newidle()` 的 `ttwu_pending` 早退为主要示例、
  proxy/core 路径降为 "Other paths"，(b) 去掉 `unlikely()`（Zhan 的 nit：若 `ttwu_pending` 才是常见触发，
  `unlikely()` 方向是反的），(c) 加 `Acked-by`。
- 8/18 作者 ping，补做多轮 hackbench：与 v7.2-rc5 主线相比 "stayed within about 1.5% mean delta, with similar
  baseline run-to-run variation."
- 9/1 作者主动问 "whether it is suitable for the sched/core tree for v7.3, or whether further work is needed?"；
  同日 Zhan Xusheng 给出上面那段完整机制分析并 `Reviewed-by`。
- 9/2 Peter Zijlstra 合入 tip/sched/urgent（**不是** sched/core），最终标签为
  `Reviewed-by: K Prateek Nayak` / `Reviewed-by: Vincent Guittot` / `Acked-by: John Stultz`。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：以 committer 身份接受，路由到 `sched/urgent` 而非作者期望的 `sched/core`——即按回归修复处理，
  不入 7.3 的新行为窗口。
- **John Stultz**：被改动影响的原始 commit 作者，`Acked-by`，无附加条件。
- **K Prateek Nayak（AMD）**：最早的 `Reviewed-by`，也是 proxy-exec / force-idle 可达性的提出者。
- **Zhan Xusheng（Xiaomi）**：本线程事实上影响最大的评审者，两轮意见（8/7、9/1）直接改写了 v3 的 changelog 与
  问题定性：从「proxy exec/core sched 的边缘路径」升级为「配置无关、一次命中即饱和的 newidle 过度均衡」。
  他的 `Reviewed-by` 出现在 9/1 回帖中，但**未出现在合入提交的标签里**。
- **Vincent Guittot 的 `Reviewed-by`** 出现在合入提交里，本地缓存中**未见其给出该标签的帖子**（缺 8/27–8/30 缓存段）。
- 无 NAK；唯一的实质分歧是「该不该同时从 `set_next_task_idle()` 打时间戳」，作者选择了不做，理由是保留既有记账模型。

## 合入评估

**已合入**（tip/sched/urgent），会随紧急修复窗口进主线。`Fixes: 4b603f1551a73` 齐全，线程里**没有出现
`Cc: stable`**——`4b603f1551a73` 若已进入已发布版本，这条按机制（唤醒密集负载 → newidle 均衡被放大）是 stable
候选，值得后续留意是否补标签。

## 效果评估

作者给的对比都是「无回归」而非「有提升」：v1 的临时追踪确认 `idle_stamp == 0` 时确实会进
`update_rq_avg_idle()`，hackbench 相对 v7.2-rc5 主线 "no material regression"；8/18 的多轮重复实验给到
thread/process 两种 case **平均差约 1.5% 以内**、与基线波动同量级。真正的收益是消除 `avg_idle` 饱和导致的
多余 newidle 均衡，线程里没有人测过修复前后 newidle balance 次数或唤醒延迟的变化——这也符合「urgent 修复只求
不坏」的定位。

## 我可以参与的点

- **回合判断（对 OLK-6.6 最直接）**：检查目标分支是否含 `4b603f1551a73`；若含，这条几乎必回合（配置无关、
  一行守卫、零风险）。可用 Zhan 的口径自查：`rq->idle_stamp` 唯一写入点是否在 `ttwu_pending` 早退之下。
- **补上线程里缺的量化**：修复前后 `sched_balance_newidle()` 的进入次数 / `sd->max_newidle_lb_cost` 早退命中率，
  或 newidle 平衡次数计数。唤醒密集（如网络中断 + cgroup）场景最容易放大差异。
- **`avg_idle` 语义本身值得盯**：`rq->avg_idle` / `idle_stamp` 这一对是唤醒侧「值不值得做 newidle balance」的
  主要依据，本线程暴露的是「守卫与更新对象不一致」这类结构性风险。cpuset/隔离核场景下，`avg_idle` 饱和会直接
  表现为隔离 CPU 上多余的均衡。
- **提议补 `Cc: stable`**：线程里无人提出，而机制上属于纯回归修复。

## 参考链接

- v1：https://lore.kernel.org/all/20260728-master-v1-1-f95d9b0147d2@gentwo.org/
- v2：https://lore.kernel.org/all/20260806-master-v2-1-e1f3a1a0c903@gentwo.org/
- v3（合入版本，本线程 root）：https://lore.kernel.org/all/20260807-master-v3-1-c328354efed3@gentwo.org/
- Prateek 的 Reviewed-by：https://lore.kernel.org/all/39ff2c76-d533-4b6c-9449-de19ed18e44a@amd.com/
- Zhan Xusheng 的机制分析与 Reviewed-by（9/1）：https://lore.kernel.org/all/20260901024438.1830934-1-zhanxusheng@xiaomi.com/
- 作者 ping（含多轮 hackbench 数据）：https://lore.kernel.org/all/2bef9a46-0f37-c4d1-f1d3-b69639dc0ebe@gentwo.org/
- 作者询问路由（9/1）：https://lore.kernel.org/all/746602fd-e9d5-128f-bd6c-e5ce7c756916@gentwo.org/
- 更早的被替代提案（正文引用）：https://lore.kernel.org/all/20260423023322.1293923-1-firelzrd@gmail.com/
- tip-bot2 合入通告（本日邮件，UID 73115）：https://lore.kernel.org/all/178833372225.3717435.14998513490997823879.tip-bot2@tip-bot2/
- commit：https://git.kernel.org/tip/c6dcd97c8be75f052a1ca52cf79b03e7292962f1 （引自合入通告正文）
- 注：8/7 Zhan Xusheng 那条 `ttwu_pending` 原始回帖在本地缓存里 msgid 为占位符（`uid-26000@qq-imap`），
  其 lore 链接**未获取到**；内容通过 v3 changelog 与后续引用还原。
