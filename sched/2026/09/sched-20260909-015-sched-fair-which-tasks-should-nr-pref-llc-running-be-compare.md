# sched/fair: which tasks should nr_pref_llc_running be compared against?

## TL;DR

本文为增量更新，计数口径之争的前几轮见 related_articles 中的 sched-20260830-003 / sched-20260828-004 / sched-20260827-018。09-09 19:40 Chen Yu（Intel）在认可当前版本「looks good now」之后，提出了**第三种候选口径**：拿 `env->src_rq->cfs.h_nr_queued` 而不是 `nr_running` 来比，并追问为什么没选它；同时把 Lu Wang 的 active load balance guard 补丁拉进来，问在新守卫之下原来的顾虑是否还成立。这条追问到当天结束无人回答。

## 背景与问题

`alb_break_llc()` 要判断「源 rq 上的任务是否全都偏好这个 LLC」，以此决定是否允许跨 LLC 的主动负载均衡。判断形式是 `env->src_rq->nr_pref_llc_running == <某个分母>`，争议一直在**分母该用什么**：用 `nr_running` 会因 `DELAY_DEQUEUE` 下被延迟出队的任务不计入 `nr_running` 而误判；而 `nr_pref_llc_running` 本身此前是「running」语义，Xu Sheng Zhan 的另一条改动把它挪到 runnable 域（见 sched-20260828-004）之后，分子分母的口径必须重新对齐。

## 技术方案

本日无新代码。Chen Yu 提出的候选是：

```c
if (env->src_rq->nr_pref_llc_running == env->src_rq->cfs.h_nr_queued) {
	...
}
```

他自己随即给出了这个口径的失败场景，并要求确认：设 3 个排队任务 p1、p2 偏好 `src_rq`，p3 是一个 delayed 任务、也偏好 `src_rq`。当前实现下 `nr_pref_llc_running` 是 3、`h_nr_queued` 是 2，于是 `alb_break_llc()` 可能返回 false → 触发主动负载均衡 → p1 或 p2 被迁移走，而这正是这个判断本要防止的。他真正问的是后半句：**"However, would this still be a problem after Lu Wang's active load balance guard patch has been applied?"**（链接 `20260903020656.3793626-1-wanglu.priv@gmail.com`）

也就是说他的问题是两层：(1) `h_nr_queued`（CFS 组层级下带 `nr_delayed` 的排队总数）是否比 `nr_running` 更合适；(2) 如果 ALB 侧另有守卫，那这个计数口径之争是否已经不必要。

## 版本演进与当前进展

- 08-27 Xu Sheng Zhan 最早提出该问题（线程根 `<20260827135000.735138-1-zhanxusheng@xiaomi.com>`）。
- 08-28 ~ 09-03 之间，`nr_pref_llc_running` 被移入 runnable 域、Lu Wang 发出 ALB guard 补丁（`20260903020656.3793626-1`），本线程的当前版本得到 Chen Yu 本日「looks good now」的评价。
- 09-09 19:40 Chen Yu 追加上述 `h_nr_queued` 追问；当天无人回复。

## Maintainer 意见与讨论焦点

- Chen Yu 是**先认可再追问**："Yes, I think this version looks good now." 所以当前版本的方向不是争议对象，争的是「还有没有更简单/更准的分母」。这类「勉强通过 + 一个没人答的问题」状态在调度器讨论里通常会拖很久，因为作者必须回答才能推进。
- 关键点是这个问题**目前处于无人应答状态**，而且它同时牵动两条线：本线程的计数口径，以及 Lu Wang 的 ALB guard 是否已经把这类误判挡在下游。如果答案是「guard 已经覆盖了」，那么本线程里为分母做的所有精细化就有一部分是冗余的——这是维护者通常不喜欢的情形，也是为什么这个问题不回答就会卡住。
- 我的判断（**属于本文推断，邮件中无人这么说**）：`cfs.h_nr_queued` 是 CFS 侧的层级排队数，在 `FAIR_GROUP_SCHED=n` 或非 CFS 任务的 rq 上语义不完整，直接当分母会引入新的口径不一致；而 Chen Yu 举的 p3 例子里，问题恰恰出在「delayed 任务被算进分子却不进分母」，所以真正需要的是分子分母在同一域内定义——这与 08-28 把 `nr_pref_llc_running` 挪进 runnable 域是同一个动作的两半。

## 合入评估

本线程不是一枚独立可评估的补丁系列，而是围绕既有改动的开放追问，因此不给 `likelihood`（frontmatter 标 `unknown`）。实际推进条件是：作者回答 Chen Yu 的两问（为何不用 `h_nr_queued`、Lu Wang 的 guard 是否已消除该场景），或明确说明已考虑过该 guard 并给出理由。

## 效果评估

无数据。整段讨论都是口径正确性推理，没有任何 benchmark 或实测的 `alb_break_llc()` 误判案例。Chen Yu 的 p1/p2/p3 场景是构造出来的逻辑反例，不是观测到的现象；把它当作已证实的缺陷来引用会超出邮件给出的证据。

## 我可以参与的点

- `discussion`：这是当天最明确的「无人回应的问题」，谁回答都能推进。要答的不是立场而是两件事实：(a) Lu Wang 的 ALB guard 具体在哪一层挡跨 LLC 迁移、是否覆盖 `h_nr_queued` 分母下的那个 p1/p2/p3 场景；(b) `cfs.h_nr_queued` 在 `CONFIG_FAIR_GROUP_SCHED=n` 与混合调度类场景下是否可用作分母。
- `testing`：构造 Chen Yu 描述的 3 任务场景（两个偏好本 LLC 的可运行任务 + 一个 delayed 且偏好本 LLC 的任务），在 `DELAY_DEQUEUE` 开启下观察 `perf bench sched` 或直接看 `/proc/sched_debug` 里的迁移决策，验证跨 LLC 迁移是否真会发生。这一条同时能回答 017 那篇里 `sched_delayed` 相关的统计问题，两处用的是同一个复现环境。
- `review`：把本线程的计数口径改动、08-28 的 `nr_pref_llc_running` runnable 域改动与 Lu Wang 的 ALB guard 三者放在一起看，确认是否有一个统一不变式（「分子分母同域」）可以被写成注释固化下来，避免下次再改一处就破另一处。

## 参考链接

- 线程根（Xu Sheng Zhan，08-27）: https://lore.kernel.org/all/20260827135000.735138-1-zhanxusheng@xiaomi.com/
- 本日 Chen Yu 的追问: https://lore.kernel.org/all/aqFFu1Xo52cQV3iy@fengwei-dev/
- 本线程此前的一封关键回帖（Tim Chen，Chen Yu 引用其内容为当前版本）: https://lore.kernel.org/all/2b0a35122ee615c6fa51076e5d79330e633755ac.camel@linux.intel.com/
- Lu Wang 的 active load balance guard: https://lore.kernel.org/all/20260903020656.3793626-1-wanglu.priv@gmail.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: "sched-20260909-015"
date: "2026-09-09"
subject: "sched/fair: which tasks should nr_pref_llc_running be compared against?"
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: "20260827135000.735138-1-zhanxusheng@xiaomi.com"
lore_url: "https://lore.kernel.org/all/aqFFu1Xo52cQV3iy@fengwei-dev/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: "2026-09-10T01:10:00"
authors:
  - "Xu Sheng Zhan"
maintainers_involved:
  - "Chen Yu"
patch_series:
  - version: v1
    msgid: "20260827135000.735138-1-zhanxusheng@xiaomi.com"
    date: "2026-08-27"
    summary: "讨论 alb_break_llc() 中 nr_pref_llc_running 应与哪个计数比较；当前版本已把 nr_pref_llc_running 移入 runnable 域以与 DELAY_DEQUEUE 对齐。"
    review_outcome: "09-09 19:40 Chen Yu 认可当前版本，但另提 cfs.h_nr_queued 作为候选分母并给出 3 任务反例，追问 Lu Wang 的 ALB guard 是否已使该问题不成立；到当天结束无人回答。"
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "作者尚未回答 Chen Yu 的两个问题：为何不采用 cfs.h_nr_queued 作分母，以及 Lu Wang 的 ALB guard 是否已覆盖该失败场景"
    - "分母口径与 08-28 的 nr_pref_llc_running runnable 域改动、ALB guard 三处之间没有成文的统一不变式"
    - "本线程不是独立补丁，推进依赖另一条 ALB guard 系列的结论"
  next_action: "由作者回帖回答 h_nr_queued 与 ALB guard 两点，或给出把「分子分母同域」写进注释的统一方案"
contribution_opportunities:
  - kind: discussion
    description: "回答 Chen Yu 的两问：确认 Lu Wang 的 ALB guard 在哪一层阻断跨 LLC 迁移、是否覆盖 h_nr_queued 分母下的 p1/p2/p3 场景，并核实 cfs.h_nr_queued 在 CONFIG_FAIR_GROUP_SCHED=n 下能否作分母"
  - kind: testing
    description: "构造两个偏好本 LLC 的可运行任务加一个 delayed 且偏好本 LLC 的任务，在 DELAY_DEQUEUE 开启下用 /proc/sched_debug 观察是否真会发生跨 LLC 主动迁移"
  - kind: review
    description: "把计数口径改动、nr_pref_llc_running 的 runnable 域改动与 ALB guard 合并审视，提炼一个可写进注释的不变式，避免后续改一处破另一处"
source_email_count: 1
related_articles:
  - "sched-20260830-003"
  - "sched-20260828-004"
  - "sched-20260827-018"
tags:
  - "load_balance"
  - "cfs"
---
