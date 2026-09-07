---
id: sched-20260901-013
subject: 'sched_ext: Skip per-CPU data allocation for built-in DSQs'
date: '2026-09-01'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260827082329.3368255-1-fangqiurong@kylinos.cn>
lore_url: https://lore.kernel.org/all/20260901013258.1822890-1-fangqiurong@kylinos.cn/
authors:
- Qiurong Fang
- Zhan Xusheng
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Zhan Xusheng
current_version: v2
patch_series:
- version: v1
  msgid: <20260827082329.3368255-1-fangqiurong@kylinos.cn>
  date: '2026-08-27'
  summary: 'scx_init_dsq() 对 built-in DSQ 跳过 alloc_percpu(struct scx_dsq_pcpu)，exit_dsq()
    加 !dsq->pcpu 早退；带 Fixes: 标签'
  review_outcome: 'Zhan Xusheng：浪费量级是 nr_cpu_ids^2 而非线性；Fixes: 会把纯内存优化路由到 stable，建议去掉；邮件头与
    Signed-off-by 姓名不一致'
- version: v2
  msgid: <20260901013258.1822890-1-fangqiurong@kylinos.cn>
  date: '2026-09-01'
  summary: '按 Tejun 意见把 ->pcpu 改名 ->pcpu_user；changelog 描述改为二次方；去掉 Fixes: 标签（明确无正确性影响）'
  review_outcome: Zhan Xusheng Reviewed-by，代码正确性逐点确认；仍建议 changelog 写出总节省量而非按每 DSQ
    描述
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v2 发出后 Tejun Heo 当日未回复，无 Applied 回执；未进入 sched_ext-for-7.3-rc1-fixes pull
  - changelog 未明确总节省量（Zhan 唯一的遗留意见）
  next_action: 等 Tejun 收取到 sched_ext/for-7.4；作者可补一句 nr_cpu_ids^2 的总量描述
contribution_opportunities:
- kind: testing
  description: 在大规格机器（128/256 CPU）上量 sched_ext 加载前后 per-CPU 内存占用，补上线程里缺失的绝对数字
- kind: review
  description: 关注 scx_init_dsq() 早退位置与 exit_dsq() 的 !pcpu_user 判断这两个不变量，回合时勿删
- kind: review
  description: 字段改名 pcpu -> pcpu_user 会冲突掉自家触碰 scx_dispatch_q 的 out-of-tree 补丁
source_email_count: 5
related_articles:
- sched-20260901-012
tags:
- sched_ext
- perf
generated_at: '2026-09-07'
title: 'sched_ext: Skip per-CPU data allocation for built-in DSQs'
layout: article
---

## TL;DR

Qiurong Fang（KylinOS）去掉 built-in DSQ 上无用的 `nr_cpu_ids` 个 per-CPU 结构：deferred reenqueue 只对 user DSQ 有意义，而 `scx_init_dsq()` 过去给每个 DSQ 都 `alloc_percpu(struct scx_dsq_pcpu)`。v2 已按 Tejun Heo 要求把 `->pcpu` 改名 `->pcpu_user`，并拿到 Zhan Xusheng 的 `Reviewed-by`；改动只有 2 文件 +15/-7，属纯内存优化（作者按意见去掉了 `Fixes:` 标签）。大核数机器上这是平方级的浪费，值得跟一下是否进 `sched_ext/for-7.4`。

## 背景与问题

`schedule_dsq_reenq()` 的 deferred reenqueue 跟踪只服务两类对象：local DSQ 走 `sch->pcpu->deferred_reenq_local`，其余只有 **非 built-in**（user）DSQ 走 `dsq->pcpu` 里的 `deferred_reenq_user`；对所有其它 built-in DSQ id 它直接拒绝。但 `scx_init_dsq()` 不区分，一律分配 `nr_cpu_ids * sizeof(struct scx_dsq_pcpu)`。

Zhan Xusheng 在第一轮把浪费的量级说清楚——它不是线性而是**二次方**，因为 built-in DSQ 的个数本身也随 `nr_cpu_ids` 增长：

> It is quadratic rather than linear, which is worth saying. The number of built-in DSQs scales with nr_cpu_ids too, because most of them are initialised inside for_each_possible_cpu()

具体是 `SCX_DSQ_LOCAL`、`SCX_DSQ_REJECT`（`CONFIG_EXT_SUB_SCHED`）、`SCX_DSQ_BYPASS`、`SCX_DSQ_RESCUE`（per rq，`scx_rescue_init()`）各每 CPU 一个，只有 `SCX_DSQ_GLOBAL` 是单实例。所以省下来的是 `nr_cpu_ids^2` 量级的 `struct scx_dsq_pcpu`。对高核数（sched_ext 的目标场景之一）平台，这是一笔白付的 per-CPU 内存。

## 技术方案

`scx_init_dsq()` 里对带 `SCX_DSQ_FLAG_BUILTIN` 的 id 直接 `return 0`，跳过 `alloc_percpu()`；`exit_dsq()` 加 `if (!dsq->pcpu_user) return;`。Zhan 论证了这个早退不是「顺手加的保护」而是**必需**的：`per_cpu_ptr(NULL, cpu)` 会给出带偏移的指针，随后的 `list_empty()` 会去读它，所以不能指望 `free_percpu(NULL)` 兜住。

同时按 Tejun 的意见把字段改名 `->pcpu` → `->pcpu_user`，让「这份 per-CPU 数据只属于 user DSQ」在类型上自解释。被否掉的备选：保留分配、只在读取处判空——被排除的原因是读取点 `ext.c:1130` 本来就在 `!(dsq->id & SCX_DSQ_FLAG_BUILTIN)` 之下，保留分配纯属浪费。

## 版本演进与当前进展

- **v1**（08-27，`<20260827082329.3368255-1-fangqiurong@kylinos.cn>`）：跳过分配，带 `Fixes:` 标签。
- 08-27 Zhan Xusheng 回帖：量级应为二次方；`Fixes:` 会把一个纯内存优化路由到 stable，除非能讲出正确性影响；顺带指出邮件头 `Qiurong Fang` 与 `From:`/`Signed-off-by:` 的 `fangqiurong` 不一致。
- 09-01 00:13 Tejun Heo：`Let's rename it to dsq->pcpu_user while at it.`
- **v2**（09-01 09:32，`<20260901013258.1822890-1-fangqiurong@kylinos.cn>`）：改名 + 按 Zhan 的意见把浪费描述为二次方 + **去掉 `Fixes:` 标签**（changelog 明确「plain memory saving with no correctness impact」）。
- 09-01 10:20 Zhan Xusheng `Reviewed-by`，同时留一条未闭环意见：v2 的 changelog 说明里写了二次方，但正文仍按「每 DSQ」描述，建议把 `nr_cpu_ids^2` 的总量写出来，「因为那才是省下来的东西」。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext 维护者）**：只对命名表态，未质疑方案本身，也未要求补数据。改名要求已在 v2 落实。
- **Zhan Xusheng（Xiaomi）**：事实上的深度评审者。两轮都逐行核对了正确性边界（`scx_init_dsq()` 先 memset 再设 `lock/list/id/sched` 才早退，所以 built-in id 需要的字段一个都没被跳过；`exit_dsq()` 的三处调用点 7101/5367/7334 都会传 built-in DSQ；唯一读者 `ext.c:1130` 已在 complement 条件之下）。遗留分歧只有一条**表述级**的：changelog 是否明确总节省量。
- 无人 NAK，无人要求拆分，无人要求 benchmark。
- 值得注意的是定级共识：作者与维护者都倾向把它当作优化而非修复（去 `Fixes:`），这意味着它走 7.4 的新特性窗口，而不是 urgent/fixes。

## 合入评估

`likelihood = high`。理由：改动面极小且只碰 `include/linux/sched/ext.h` + `kernel/sched/ext.c`；维护者的唯一要求（改名）已满足；`Reviewed-by` 到位；无任何反对。卡点：v2 发出后 Tejun 当日未再回复，**尚未见 Applied 回执，也未进 09-01 的 `sched_ext-for-7.3-rc1-fixes` pull**（该 pull 顶端是 08-31 的 kernel-doc 修复），因此预期落点是 `sched_ext/for-7.4`。由于是纯优化，被顺手合入的概率高于被要求返工。

## 效果评估

**无实测数据**。唯一的量化陈述是 Zhan 的结构推导：省约 `nr_cpu_ids^2` 个 `struct scx_dsq_pcpu`（`struct scx_dsq_pcpu` 大小邮件里未给出，因此绝对字节数在本日邮件中无法算出，属**未验证的量级判断**）。作者与维护者均未提供 kmem 统计前后对比。若要给它加说服力，一个 `nr_cpu_ids` 较大机器上 `slabinfo`/per-CPU 区用量前后对比就足够。

## 我可以参与的点

- **补上缺的那组数字**：在大规格（128/256 CPU）机器上量一次 sched_ext 加载前后的 per-CPU 内存占用，回帖给 Zhan 提的「把总量写进 changelog」——这是当前线程里唯一悬空且零成本可做的事。
- **回合注意**：字段改名 `pcpu` → `pcpu_user` 会冲掉自家任何触碰 `scx_dispatch_q`/`scx_dsq_pcpu` 的 out-of-tree 补丁；若在 OLK 类分支上跟这个改动，要一并检查 `exit_dsq()` 的早退是否被误删——那是唯一会引入 NULL 偏移解引用的点。
- **顺手 review**：这是典型的可以跟着读一遍的小补丁，`scx_init_dsq()` 的早退位置（在 `memset` 与四个字段赋值之后）是唯一需要盯的不变量。

## 参考链接

- lore thread (v1): https://lore.kernel.org/all/20260827082329.3368255-1-fangqiurong@kylinos.cn/
- Tejun Heo 改名要求: https://lore.kernel.org/all/apWoF6Czswh-sO6V@slm.duckdns.org/
- Zhan Xusheng 第一轮（二次方 + Fixes 意见）: https://lore.kernel.org/all/20260827093838.532352-1-zhanxusheng1024@gmail.com/
- v2: https://lore.kernel.org/all/20260901013258.1822890-1-fangqiurong@kylinos.cn/
- Reviewed-by: https://lore.kernel.org/all/20260901022004.1824584-1-zhanxusheng@xiaomi.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到（作者按评审意见去掉了 `Fixes:` 标签）
