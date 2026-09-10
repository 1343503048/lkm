# sched/cache: Per-task control of cache aware scheduling via prctl

## TL;DR

本文为增量更新，RFC 的 7 个补丁与「把决定权交给用户态」的设计取舍见 related_articles 中的 sched-20260831-008 / sched-20260829-002。09-09 20:57 Shrikanth Hegde（IBM）第一次正面质询这个 prctl 方案的可用性前提，问了四个当天没人能答的问题：用户态现在有什么工具能做这个决定？应用开发者凭什么判断该不该把任务分到一组？能不能在应用已经跑起来之后再分组？之前否掉 cgroup 的理由是否仍然成立？这个系列是当天热度最高的 CAS 讨论线里唯一一份**没人回答**的新意见。

## 背景与问题

摘要（详见前文）：Tim Chen 的 RFC 给 cache-aware scheduling 加一个 prctl 级别的 per-task 控制，让应用/运行库自己告诉内核「这些任务应当被看作同一缓存域的一组」或相反，因为内核在异构 L3 与大小核场景下无法可靠推断意图。它的前置事实是 CAS 在 AMD 大小核上表现不佳这一持续报告（见 sched-20260909-009 那条线）。

Shrikanth 的开宗明义是「我一直在追赶进度，还没读完，可能有傻问题，请多包涵」，然后落到关键处：

> So, As you said, this is effectively asking user to make the decision. But what tools do user space have today to make effective decisions? Application changes could turn out to be tricky to do and how an application developer will know whether to group them together or not? What's guidance there?

## 技术方案

本日无新代码，是对既有设计的可用性审查。Shrikanth 提出的四点，其中两点是**新的、此前 RFC 里没有正面回答过的**：

1. **决策依据缺失**：用户态今天靠什么判断？（不是「能不能调用 prctl」，而是「知不知道该传什么」）
2. **运行后分组**：能不能像「把这些 pid 捆成一组」那样，在应用已经跑起来之后再决定分组？——如果只能由应用在自身启动时设置，那么对不能改代码的二进制（以及绝大多数现网负载）这条路是死的。
3. **cgroup 是否真的不行**："I remember you guys discussed about cgroup and decided it is not a good option. That argument is still holds?" ——要求重新检验那个结论，理由是 cgroup 天然是「外部可管理、可运行时调整、有现成策略工具」的位置，而 prctl 是「必须改应用」的位置。
4. 显式承认自己可能漏了上下文，因此欢迎被纠正。

这四条与当天另一条 prctl 系（Li Zhe 的 per-process NUMA balancing 开关，见 sched-20260908-007）撞在同一个问题上：**per-task 接口在没有配套用户侧决策工具时到底能不能落地**。

## 版本演进与当前进展

- RFC 0/7 由 Tim Chen 发出（线程根 `cover.1787955777.git.tim.c.chen@linux.intel.com`），08-29 与 08-31 的两次日报已覆盖其内容与初轮反应。
- 09-09 20:57 Shrikanth Hegde 回帖（`<f0b6a0c3-4fa6-4f8c-99a0-a3c1a73507f3@linux.ibm.com>`），是当天该系列唯一一封邮件。
- 无 v2 迹象、无 tip-bot、无 stable。RFC 状态未变。

## Maintainer 意见与讨论焦点

本日没有任何来自 Intel 侧（补丁作者方）的回应。这在评估上很重要：Shrikanth 的四条里有两条是**要求提供材料**（guidance 与 cgroup 结论的再检验），而不是要求改代码。这类问题若不被回答，RFC 会一直停在「设计未定」；若被回答成「需要用户自己判断」，那等于承认这个接口目前只能服务能改代码的少数负载。

同时要注意提问者的分量：Shrikanth 是前面那封「preferred CPU / steal_governor」系列的作者、IBM 侧调度器贡献者，且他明确点名要 Tim **和 Peter** 一起看（"Hi Tim/Peter"），说明他也把 Peter Zijlstra 视为需要给出判断的一方。所以这不是外围噪音提问。

## 合入评估

`likelihood=unknown`。它是 RFC，且当天新出现的是一批**尚未被回答的前置问题**，而不是评审意见的收敛。要判断合入可能性，至少需要作者先答复：(a) 运行后能否分组（决定不改代码的应用是否可用）；(b) 用户态依据什么决策；(c) 为什么 cgroup 仍不是更好的载体。这三个答案会直接决定接口形状，现在都是空的。

## 效果评估

本日无数据。RFC 线程至今也没有出现可比较的收益数字——这一点与 09-09 CAS 那条 bug 报告线（sched-20260909-009）的处境是同一个：**CAS 在异构平台上「效果不好」这件事已被反复报告了十几天，但仍然没有一份归因清楚的对照数据**，因此为它开的这个 per-task 逃生口能带来多少收益也就无法评估。

## 我可以参与的点

- `discussion`：Shrikanth 的四问到当天结束无人接。任何一条都能推进，其中最有价值的是第 2 条（运行后分组）：如果有内核外的手段能做到（例如 `prctl` 由外部通过 `process_vm` 类机制注入显然不行，但 cgroup 或 `sched_setattr` 扩展可以），把这条具体化就等于替代方案设计的一部分。
- `testing`：给出「用户态到底有没有工具做这个决策」的实证答案——比如在一个真实的多线程应用（memcached、gem5、数据库类）上，看仅凭 `perf`/`/proc/schedstat`/L3 命中率能否判定哪些线程该同组。如果测下来「需要 profile 才能判」，那就直接支持了「这个接口不该让应用自己调」的立场。
- `review`：把 cgroup 方案的否决理由重新拿出来检验。当天另一条线（per-process NUMA balancing 开关用 prctl）正面对照了同样的选择，两份接口如果不一致，本身就是需要问的问题。
- `new_patch`：若结论是「prctl 不足以覆盖不改代码的负载」，一个 cgroup 或 `sched_setattr` 扩展版本的候选补丁是明显可做的增量。

## 参考链接

- RFC 线程根（cover letter）: https://lore.kernel.org/all/cover.1787955777.git.tim.c.chen@linux.intel.com/
- 本日 Shrikanth Hegde 的四问: https://lore.kernel.org/all/f0b6a0c3-4fa6-4f8c-99a0-a3c1a73507f3@linux.ibm.com/
- 同日相关的 CAS 效果报告线: https://lore.kernel.org/all/e17ef3af-c1cd-4360-ba4b-9900ccc36ef6@computerix.info/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: "sched-20260909-016"
date: "2026-09-09"
subject: "sched/cache: Per-task control of cache aware scheduling via prctl"
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: "cover.1787955777.git.tim.c.chen@linux.intel.com"
lore_url: "https://lore.kernel.org/all/f0b6a0c3-4fa6-4f8c-99a0-a3c1a73507f3@linux.ibm.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: "2026-09-10T01:10:00"
authors:
  - "Tim Chen"
maintainers_involved:
  - "Shrikanth Hegde"
patch_series:
  - version: v1
    msgid: "cover.1787955777.git.tim.c.chen@linux.intel.com"
    date: "2026-08-27"
    summary: "RFC 0/7：为 cache-aware scheduling 增加 prctl 级别的 per-task 控制，把「哪些任务应视为同一缓存分组」的决定权交给应用/运行库，以应对内核无法在异构 L3 与大小核上推断意图的问题。"
    review_outcome: "09-09 20:57 Shrikanth Hegde 提出四个尚未被回答的前置问题：用户态现有工具能否支撑该决策、应用开发者依据什么判断是否分组、能否在应用运行后再分组、此前否决 cgroup 的理由是否仍成立；作者方当天未回应。"
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "作者尚未回答 Shrikanth 的四问，其中「运行后能否分组」直接决定不改代码的负载是否可用该接口"
    - "此前否决 cgroup 作为载体的理由未被重新检验，而 cgroup 恰好具备运行时可管理与现成策略工具"
    - "CAS 在异构平台上效果不佳至今仍无归因清楚的对照数据，因此该逃生口的收益无法量化"
  next_action: "作者需回答接口形状相关三问（决策依据、运行后分组、cgroup 再评估），并最好给出一个不改应用代码也能受益的具体用例"
contribution_opportunities:
  - kind: discussion
    description: "把「能否在应用启动后再分组」这条具体化，给出 cgroup 或 sched_setattr 扩展等可行的运行时分组手段，这是 RFC 目前缺失的替代方案论证"
  - kind: testing
    description: "在真实多线程应用上验证仅凭 perf/proc/schedstat 与 L3 命中率能否判定线程分组，从而用数据回答用户态到底有没有决策依据"
  - kind: review
    description: "对照同期 Li Zhe 的 per-process NUMA balancing prctl 方案，检查两个 per-task 接口在 cgroup 与 prctl 上的取舍是否一致"
  - kind: new_patch
    description: "若结论是 prctl 无法覆盖不可改代码的负载，可提交一个基于 cgroup 或 sched_setattr 的扩展版本作为替代方案"
source_email_count: 1
related_articles:
  - "sched-20260831-008"
  - "sched-20260829-002"
  - "sched-20260908-007"
tags:
  - "load_balance"
  - "topology"
  - "cgroup"
---
