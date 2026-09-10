---
id: sched-20260909-012
date: '2026-09-09'
subject: 'sched/fair: Only apply cpufreq pressure where frequency is invariant'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <20260821073927.455475-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/a2466e7d-2dd7-4de9-963f-6eb8c58d4a49@amd.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-10T01:00:00'
authors:
- Jianyong Wu
maintainers_involved:
- K Prateek Nayak
- Hongyan Xia
patch_series:
- version: v1
  msgid: <20260821073927.455475-1-wujianyong@hygon.cn>
  date: '2026-08-21'
  summary: sched 侧门控：仅在 arch_scale_freq_invariant() 为真时计入 cpufreq 压力。作者已于 09-08 采纳
    Prateek 的 cpufreq 侧 __resolve_freq() 方案并放弃本版本；该 cpufreq 侧补丁截至本日尚未发出。
  review_outcome: 09-09 Hongyan Xia 给出 LGTM 并建议缓存最高可达 OPP 而非每次全量 __resolve_freq()；Prateek
    认可并明确落点为 policy 对象、在 cpufreq_policy_online() 时更新，同时把发版优先权推回作者，称若不发他下周初发。
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 达成共识的 cpufreq 侧补丁至今未出现在邮件列表中，没有可评审的对象，也无法确认是否带 Fixes 标签
  - 改动落在 drivers/cpufreq/，需 cpufreq 维护者 ack，sched 侧意见不能替代
  - 「谁来署名发这版」到当天结束未有人回应，Prateek 已设下下周初的兜底时点
  - 缓存失效点是否覆盖 policy->max 的全部变更路径（如用户态写 scaling_max_freq）尚无人论证
  next_action: 由 Jianyong Wu 或 Prateek Nayak 正式发出含 policy 对象缓存的 cpufreq 侧补丁并 CC cpufreq
    维护者
contribution_opportunities:
- kind: new_patch
  description: 在 Prateek 承诺的下周初之前，自行实现 cpufreq 侧改动（__resolve_freq 上界不越过 policy 可给频率
    + 在 cpufreq_policy_online() 时把最高可达 OPP 缓存进 policy 对象）并发出，这个位置已达成共识但无人写
- kind: testing
  description: 在 arch_scale_freq_ref() 返回 0 的 x86 acpi-cpufreq 机器上核对 _PSS 表与 cpu_capacity，确认是否存在无真实限频却容量小于
    1024 的现象，以扩大受影响平台清单
- kind: discussion
  description: 在邮件里追问缓存失效点是否覆盖 policy->max 的全部变更路径（用户态写 scaling_max_freq 等），这决定实现是否还需在别处同步失效
source_email_count: 2
related_articles:
- sched-20260908-008
- sched-20260907-006
- sched-20260903-010
- sched-20260902-008
tags:
- cpufreq
- cfs
- topology
title: 'sched/fair: Only apply cpufreq pressure where frequency is invariant'
layout: article
---

## TL;DR

本文为增量更新，完整背景、三个互斥修法（sched 侧门控 / cpuutil 信号改用 arch_scale_freq_ref / cpufreq 侧 `__resolve_freq()`）的对比见 related_articles 中的 sched-20260908-008 / sched-20260907-006 / sched-20260903-010 / sched-20260902-008。09-08 作者已经表态采纳 Prateek 的 cpufreq 侧方案，09-09 出现两件推进：**Hongyan Xia（Transsion）给出 LGTM** 并提出把每次全量 `__resolve_freq()` 换成缓存；Prateek 认可并具体化为「在 `cpufreq_policy_online()` 时缓存进 policy 对象」，同时把发版归属推给 Jianyong Wu，明说若对方不发、他下周初自己发。也就是说方案侧现在无异议了，缺的仍是那枚还没被任何人正式发出的补丁。

## 背景与问题

摘要（详见前文）：`get_actual_cpu_capacity()` 无条件把 `cpufreq_get_pressure()` 与 `hw_load_avg()` 取 max 后从容量里扣除。非频率不变性平台上 `arch_scale_freq_ref()` 返回 0，代码回退使用 `policy->cpuinfo.max_freq`——它含 boost；而 acpi-cpufreq 的 `policy->max` 来自不含 boost 的 `_PSS`/OPP 表。于是系统毫无真实限频时 `policy->max < max_freq` 被算成压力，CPU capacity 凭空缩水。原始补丁（Jianyong Wu，Hygon）走的是 sched 侧门控（只在 `arch_scale_freq_invariant()` 为真时才计入），被 Hongyan Xia 指出是在掩盖症状；Prateek 提出改在 cpufreq 侧，让 `__resolve_freq()` 的上界不要越过 policy 实际能给的频率。两个平台已实测复现（AMD 5900X 与 Hygon，后者 `cpuinfo_max_freq` 3100000 高于最高 `_PSS` 档 2700000）。

## 技术方案

本日没有新代码，推进的是一个**实现细节的收敛**：

- Hongyan Xia 12:09："LGTM. NIT: I do wonder if we need a full __resolve_freq() each time. We could cache the highest achievable OPP on max_freq updates, but that's future optimization."（`<a9dc111b-21cb-4bcb-ac91-f6be04bc2e06@transsion.com>`）
- Prateek 18:04 回应："Sure! We can cache it in the policy object during `cpufreq_policy_online()`. Jianyong Wu would like to take a stab at it? If not, I can send it out early next week."（`<a2466e7d-2dd7-4de9-963f-6eb8c58d4a49@amd.com>`）

缓存位置被明确到 policy 对象、更新时机被明确到 `cpufreq_policy_online()`。这条落点合理：`policy->max` 只在 policy 上线与 `store_min_freq`/`store_max_freq`（限频变更）时变，热路径上每次 `get_actual_cpu_capacity()` 都跑一遍完整的 OPP 解析是不必要的开销。

顺带值得留意的是，本线程里对「谁来署名发这版」的处理方式：09-08 作者提出给 Prateek 加 `Suggested-by` 并把选择权交回，09-09 Prateek 又把发版优先权推回给作者、自己只作兜底。这个来回本身说明两边都认这版补丁的归属清晰，不再有方案之争。

## 版本演进与当前进展

- Jianyong Wu 的原始 sched 侧门控补丁（09-08 线程根 `<20260821073927.455475-1-wujianyong@hygon.cn>`）实际上已被放弃：作者本人在 09-08 采纳 Prateek 的 cpufreq 侧方向。
- 本线程 09-09 有两封回帖，全部是关于 cpufreq 侧改法的评论，**cpufreq 侧那版补丁至今仍未出现在邮件列表里**（当天缓存中不存在）。
- 无 tip-bot，无 stable。

## Maintainer 意见与讨论焦点

- **Hongyan Xia（Transsion，本缺陷在另一平台上的相关方）首次明确表态 LGTM**，方向之争至此结束：既不是 sched 侧门控（她此前就说过那是掩盖症状），也不是继续讨论，而是 cpufreq 侧改 `__resolve_freq()`。
- **Prateek 接受缓存优化**，并把它从「future optimization」直接提到「可以放进这一版」——他给出的落点（policy 对象 + `cpufreq_policy_online()`）比 Hongyan 的表述更具体。
- 唯一还没解决的问题仍然是**署名与发版**：Prateek 问「Jianyong Wu 愿意发吗？不愿意我下周初发」。这句话本质是一个待认领的 TODO，截至当天结束没有回应。
- 历史上这个线程的争议（三个互斥修法哪一个是正的、要不要同时改 cpuutil 信号）本日无人再提。

## 合入评估

`likelihood=medium`。方向上已经有两位非作者方（Prateek Nayak 提议 + Hongyan Xia LGTM）认可，症状成因、复现平台（AMD 5900X + Hygon 的 `_PSS`）与修法三者对齐，看起来应该很快能合。但严格说：**目前没有任何一份可评审的补丁存在**——被讨论的是「Prateek 建议的 cpufreq 侧改动」，而它不在邮件列表里，因此无法评估它是否带 `Fixes:`、是否需要 cpufreq 维护者（Rafael Wysocki / Viresh Kumar）的 ack。此外这版补丁改的位置在 `drivers/cpufreq/`，跨了子系统，sched 侧维护者的意见不能替代 cpufreq 侧的。

`next_action`：需要有人（Jianyong Wu 或 Prateek 本人）把 cpufreq 侧改动连同「policy 对象缓存 + `cpufreq_policy_online()` 时更新」一起正式发出，并 CC cpufreq 维护者。

## 效果评估

本日没有新数据。既有数据仍只有 09-08 作者给的那一组：其平台上 `cpuinfo_max_freq` 3100000 与最高 `_PSS` 档 2700000 之间的差值会被误算成压力，应用 Prateek 那版改动后 CPU capacity 回到 1024。缓存 `__resolve_freq()` 这条优化本身**没有任何性能数字**——它是显然合理的（把热路径上的 OPP 全量解析换成查表），但 Prateek 与 Hongyan 都没有给出收益量级，属主观判断。

## 我可以参与的点

- `new_patch`：这是当天最明确的一个「无人认领的补丁」。Prateek 已经说「若作者不发，我下周初发」——如果你有 Hygon 或 AMD 这类 `cpuinfo_max_freq > 最高 _PSS 档` 的机器，自己把这版 cpufreq 侧改动做出来（含 policy 对象里缓存最高可达 OPP、`cpufreq_policy_online()` 时更新）并在下周之前发出，等于抢在一个已达成共识、但还没人写的位置上。回帖里带上 `Reported-by`/`Suggested-by` 的既有脉络即可。
- `testing`：在自家非频率不变性平台（`arch_scale_freq_ref()` 返回 0 的 x86 acpi-cpufreq 机器基本都是）上检查 `scaling_cur_freq`/`_PSS` 表与 `cpu_capacity` 是否出现「无真实限频却容量 <1024」的现象，这能直接把受影响平台清单扩大，也是这类补丁最需要的支持证据。
- `discussion`：如果确实要发这版，`policy->max` 变更路径不止 `cpufreq_policy_online()` 一处（用户态写 `scaling_max_freq` 也会改），可以在邮件里先问清楚缓存的失效点是否覆盖完整——这决定了实现是否需要在别处同步失效。

## 参考链接

- 本线程根（Jianyong Wu 的原补丁，sched 侧门控版本已被放弃）: https://lore.kernel.org/all/20260821073927.455475-1-wujianyong@hygon.cn/
- Hongyan Xia 的 LGTM 与缓存建议: https://lore.kernel.org/all/a9dc111b-21cb-4bcb-ac91-f6be04bc2e06@transsion.com/
- Prateek Nayak 的落点与发版认领: https://lore.kernel.org/all/a2466e7d-2dd7-4de9-963f-6eb8c58d4a49@amd.com/
- cpufreq 侧改动补丁: 未获取到（尚未发出）
- tip-bot commit: 未获取到
- stable backport: 未获取到
