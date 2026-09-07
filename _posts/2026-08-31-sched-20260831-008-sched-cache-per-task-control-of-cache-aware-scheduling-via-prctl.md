---
id: sched-20260831-008
date: '2026-08-31'
subject: 'sched/cache: Per-task control of cache aware scheduling via prctl'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <cover.1787955777.git.tim.c.chen@linux.intel.com>
lore_url: https://lore.kernel.org/all/apWSGWzDXikBI7GT@three-body/
authors:
- Tim Chen
- Chen Yu
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
- Chen Yu
current_version: v1
patch_series:
- version: v1
  msgid: <cover.1787955777.git.tim.c.chen@linux.intel.com>
  date: 2026-08-28
  summary: 7 补丁 RFC：通过 prctl 提供 per-task 的 CAS 控制，作者就 prctl vs QoS 属性、kernel-owned
    cookie、always/advise/never 模型征求 review
  review_outcome: Peter Zijlstra 要求先给出使用者与负载动机；Chen Yu 8/31 以腾讯云 KV-cache 场景作答，并指出阈值也需按组单独调
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 接口层级未定：用例本质是 per-cgroup，方案是 per-task prctl
  - 维护者尚未评价 prctl vs QoS 属性、kernel-owned cookie、always/advise/never 模型
  - 缺少可复现数据说明默认 CAS 阈值会拒绝内存密集组的聚合
  next_action: 作者需就 per-task 接口能否承载 per-group 需求给出结论，并决定是否改为/追加 cgroup 侧属性
contribution_opportunities:
- kind: discussion
  description: 从 cpu/cpuset 控制器侧回答该特性是否应做成 cgroup 属性，以及与 cpuset/root domain 的层级继承语义
- kind: testing
  description: 构造同进程两类线程（密集共享 vs 不共享）+ 高内存足迹负载，量化默认 CAS 阈值拒绝聚合的损失
- kind: review
  description: 就作者点名的三个接口问题（prctl vs QoS 属性、kernel-owned cookie、always/advise/never
    组合）回帖表态
generated_at: '2026-09-07T21:16:22'
source_email_count: 1
related_articles: []
tags:
- load_balance
- cgroup
title: 'sched/cache: Per-task control of cache aware scheduling via prctl'
layout: article
---

## TL;DR

Tim Chen（Intel）8/28 发的 7 补丁 RFC 想让 cache-aware scheduling（CAS）支持**按任务**开关/调档，接口候选是 prctl；Peter Zijlstra 8/29 只问了一句"谁会用？什么负载逼你这么做？"。8/31 Chen Yu 给出迄今最具体的动机答复：腾讯云场景里**同一进程内不同线程组的数据共享模式不同**，KV-cache 一类内存密集组既要能单独打开 CAS、又要能单独调聚合阈值——而"这些组在实践中就是 cgroup"。这句话对本系列的接口形态是关键信息：需求是组粒度的，方案提的却是 per-task prctl。

## 背景与问题

CAS 目前是全局/系统级的启发式：内核自行决定哪些任务值得为了 L3 局部性做聚合，阈值（如聚合容忍度）也是全局的。问题在于同一进程内部并不均质：

- 线程组 A 内部有密集数据共享（Chen Yu 举的例子是 KV-cache 相关负载），聚合有明确收益；
- 线程组 B 不共享数据，聚合只会带来约束；
- 更麻烦的是 A 恰恰因为内存足迹大，**默认的 CAS 阈值会拒绝为它做聚合**——于是 A 不仅需要"单独打开"，还需要"单独调阈值参数"。

因此诉求有两层：按组/按任务启停 CAS；按组/按任务调整聚合阈值。

## 技术方案

补丁本体（7 篇）不在当日缓存中，可确认的接口形态来自 cover 里作者自己点名的三个待评审问题：

- **接口形态**：`prctl` 还是"一个 QoS 属性"（作者原文：Feedbacks very welcome, especially on the interface shape (prctl vs. a QoS attribute)）。
- **cookie 归属**：kernel-owned cookie 的选择是否正确。
- **策略模型**：`always/advise/never` 三态策略的组合是否是正确的模型。

本日新增的不是代码，而是**用例**：Chen Yu 用生产侧描述把"要不要 per-task"从抽象的灵活性讨论，转成了"哪一类负载需要、需要调什么参数"。需要注意的是这个用例的粒度天然是 cgroup（"Typically, in Vern's environment, group A and group B are cgroups"），而 prctl 是 per-task/per-mm 的，两者并不自动等价——这决定了后续最可能出现的分歧。

## 版本演进与当前进展

- 8/28：Tim Chen 发出 `[RFC PATCH 0/7]`（cover `<cover.1787955777.git.tim.c.chen@linux.intel.com>`），主动征求接口意见。
- 8/29：Peter Zijlstra 追问使用者与负载（`<20260829092721.GB776954@noisy.programming.kicks-ass.net>`）。
- 8/31 22:39：Chen Yu 回帖给出腾讯云用例并引用 Vern Hao 此前的讨论（`<7d5bb7c4-abc5-470e-84fe-72a3b1d3a2f4@gmail.com>`）。
- 仍是 RFC v1，未出现 v2，也没有任何 `Reviewed-by`/`Acked-by`。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：唯一的 maintainer 意见是一个前置性问题——"Who would be using this -- what workload prompted you do do this etc." 这类问题本身就是一种态度：在没有真实用户故事之前，他不准备讨论接口细节。本日线程内他**没有**对 prctl/QoS 属性、kernel-owned cookie、always/advise/never 模型表态。
- **Chen Yu（CAS 主要作者之一）**：站在需求侧支持"要有细粒度控制"，并额外指出**阈值也需要单独调**——这把需求范围从"开关"扩大到"参数族"。
- 未解决：接口层级（prctl vs cgroup/QoS 属性）没有正面回答，因为举出的用例本身就是 cgroup 粒度的；"内存密集组被默认阈值拒绝"这一具体限制是否应改成启发式自适应（而不是交给用户调参），也没人提。

## 合入评估

**unclear**。这是 RFC v1，作者自己把接口形态列为开放问题，维护者的第一反应是要用例而非评审实现；用例已被给出但指向的层级与本系列接口不一致（组 vs 任务），意味着接口很可能还要重做。卡点：① 接口层级未定（prctl / QoS 属性 / cgroup 文件）；② 只读用例不足以推动，需要至少一个能演示"默认 CAS 在 KV-cache 型负载上误判"的可复现数据；③ 阈值参数目前只能通过 debugfs 一类全局入口调，per-cgroup 暴露需要 cpu 控制器侧的配合。`next_action`：由维护者就"per-task 接口能否满足实际是 per-group 的需求"给结论，作者据此决定是重做成 cgroup 属性还是保留 prctl 并补一个组级默认。

## 效果评估

暂无效果数据。Chen Yu 的描述是需求陈述，没有任何基准数字（既没有"默认阈值拒绝了聚合"的量化，也没有开启后的收益）。本系列连"改进前后"的对照组都还不存在。

## 我可以参与的点

- **最直接相关的一条**：需求被明确表述为"组 A/组 B 就是 cgroup"，而接口走 prctl。可以从 cpu/cpuset 控制器侧回答"这是否应该做成 cgroup 属性、语义如何与 `cpuset`/root domain 交互、层级继承怎么做"，这正是本系列目前缺的角色。
- **补生产形态的复现数据**：构造"同进程两类线程（一类密集共享、一类不共享）+ 高内存足迹"的负载，展示默认 CAS 阈值拒绝聚合的具体表现（迁移次数、L3 miss、吞吐），把用例从叙述变成可验证事实。
- **参与接口之争**：作者点名征求 prctl vs QoS 属性的意见；若认为阈值参数族也需要 per-cgroup 暴露，现在提出比 v2 之后便宜得多。

## 参考链接

- lore thread（RFC 0/7 cover）: https://lore.kernel.org/all/cover.1787955777.git.tim.c.chen@linux.intel.com/
- Peter Zijlstra 的追问: https://lore.kernel.org/all/20260829092721.GB776954@noisy.programming.kicks-ass.net/
- Chen Yu 本日用例答复: https://lore.kernel.org/all/apWSGWzDXikBI7GT@three-body/
- 被引用的腾讯云侧讨论（邮件内给出）: https://lore.kernel.org/all/7d5bb7c4-abc5-470e-84fe-72a3b1d3a2f4@gmail.com/
- 补丁 1–7 本体: 未获取到（不在当日邮件缓存中）
- tip-bot commit: 未获取到
- stable backport: 未获取到
