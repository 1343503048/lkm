# sched/fair: Only apply cpufreq pressure where frequency is invariant

## TL;DR

本文为增量更新，完整背景与三条互斥修法的对比见 [[sched-20260907-006]]、[[sched-20260903-010]]、[[sched-20260902-008]]。09-08 本线程只有一封新邮件，但是第一封带**收敛结论**的：作者 Jianyong Wu（Hygon）在 15:19 回复 Prateek Nayak，明确采纳 Prateek 的 cpufreq 侧 `__resolve_freq()` 方案（自认自己原来那版更复杂），并给出第二平台实测——他的机器上 `cpuinfo_max_freq` 3100000 高于最高 `_PSS` 档 2700000，打上 Prateek 那版改动后 CPU capacity 回到 1024。同时他提出给 Prateek 加 `Suggested-by:`，并把「由谁署名发这版」的选择权交回给 Prateek。至此假压力的成因、复现平台（AMD 5900X + Hygon `_PSS`）、修法三者都对齐了，缺的只是正式提交与 cpufreq 维护者表态。

## 背景与问题

摘要（详见前文）：`get_actual_cpu_capacity()` 会无条件把 `cpufreq_get_pressure()` 与 `hw_load_avg()` 取 max 后从容量里扣掉。在非频率不变性平台上，`arch_scale_freq_ref()` 返回 0，代码回退用 `policy->cpuinfo.max_freq`——而该字段含 boost；acpi-cpufreq 的 `policy->max` 来自不含 boost 的 `_PSS`/OPP 表。于是 `policy->max < max_freq` 在系统毫无真实限频时被算成压力，容量凭空缩水。作者原始补丁走的是 sched 侧门控（只在 `arch_scale_freq_invariant()` 为真时才计入），被 Hongyan Xia 指出是在掩盖症状。

## 技术方案

本日无新代码提交，只有作者对既有方案的选择确认。Prateek 09-07 提出的改法（`drivers/cpufreq/cpufreq.c`，`cpufreq_update_pressure()` 里 `!max_freq` 的回退分支）保持原样：

```c
	max_freq = arch_scale_freq_ref(cpu);
	if (!max_freq) {
		max_freq = __resolve_freq(policy, policy->cpuinfo.max_freq,
					  policy->cpuinfo.min_freq, policy->cpuinfo.max_freq,
					  CPUFREQ_RELATION_H);
	}
```

含义是：没有频率不变性参考点时，把 `cpuinfo.max_freq` 按频率表内实际存在的档位归一化，从而不会被表外的 boost 档位顶高；对 cppc 类（amd-pstate、intel_pstate）无表驱动，`__resolve_freq()` 原样返回。作者在 09-07 答应「另发补丁」的那条路（给 `struct cpufreq_policy` 加 `boost_freqs_outside_table` + `table_max`）本日被他本人以「more complex than yours」为由放弃。

## 版本演进与当前进展

- 09-08 15:19 Jianyong Wu 回复（`<PUZPR04MB4922771B19195F4D1BF89EFEE3B12@PUZPR04MB4922.apcprd04.prod.outlook.com>`，`in-reply-to` 指向 Prateek 的 `<4e39e935-2339-442b-8b14-a688b605c35e@amd.com>`）：「I think this is the right way to resolve the issue. I had written a patch for it as well, but it is more complex than yours, so I have made a small change on top of your version instead.」
- 同封给出实测：「On my machine, where cpuinfo_max_freq (3100000) sits above the highest _PSS entry (2700000), the CPU capacity is back to 1024 with it applied.」
- 署名问题悬而未决：「I will add a Suggested-by: for you since the approach is yours - if you would rather post it under your own authorship, say the word and I will stay out of the way.」
- 本线程的 sched 侧 v1（`<20260821073927.455475-1-wujianyong@hygon.cn>`）仍未重投，版本号停在 v1，本日没有出现它的 diff 变化。

## Maintainer 意见与讨论焦点

本日新增意见一条，方向性明确（Prateek 的方案被采纳）：

- **Jianyong Wu（作者）**：认可 Prateek 的 cpufreq 侧改法是「the right way to resolve the issue」，撤销自己的复杂版本，并主动把方案归属让给 Prateek（`Suggested-by` 或换他本人署名）。
- 仍然没有表态的人：cpufreq 侧维护者（Rafael Wysocki / Viresh Kumar）自始至终未出现在线程里；Hongyan Xia 本日未发言；Vincent Guittot 在 08-21 提出的「到底要修什么问题」以及「util 同样能超过容量」的追问，本日仍未被正面回答。
- 未解决的争议：修复最终落在 cpufreq 侧之后，原 sched 侧门控是撤销还是作为独立防御保留，本日没有任何讨论。

## 合入评估

`likelihood=medium`——与 09-07 的判断同为 medium，但依据变了：从「三条互斥修法未定」变成「修法已收敛到 `__resolve_freq()` 且有两个平台的实测支撑」，剩下的卡点全是流程性的。`blocking_issues`：

1. 正式补丁尚未发出——本日只有邮件里的 diff 与口头采纳，没有带 `Fixes:`、签名与 CC 列表的提交。
2. cpufreq 维护者（Rafael Wysocki / Viresh Kumar）从未介入，而改动落在 `drivers/cpufreq/cpufreq.c`，需要他们认可「在非 FI 平台把 `cpuinfo.max_freq` 按表归一化」这个语义。
3. 作者原始 sched 侧 v1 的处置未定，两条改动是否同批进树没有共识。
4. 收益侧证据仍只有「capacity 回到 1024」这一量，缺对放置/misfit/迁移决策的可观测影响。

`next_action`：等 Prateek 或作者把 cpufreq 侧补丁正式发出来（含谁署名），并 CC cpufreq 维护者。

## 效果评估

本日的数字（作者自测）：`cpuinfo_max_freq` = 3100000 kHz，最高 `_PSS` 档 = 2700000 kHz，应用 Prateek 的改动后 CPU capacity 恢复为 1024。这是本线程第二份实测（第一份是 09-07 Hongyan Xia 在 AMD 5900X 上的 4680714 vs 3300000），并且它落在**另一台机器、另一个 `_PSS` 表结构**上，佐证了 Xia 当时「this is a wider problem than we realize」的判断——只是本日这台是 Hygon 而非 09-07 大家想要的 Intel。没有性能类数据（没有 benchmark，也没有容量缩水对吞吐影响的量化）。

## 我可以参与的点

- **补 Intel 侧数据（testing）**：09-07 我记录过这个缺口，本日仍然没被填上——现有两份实测分别来自 AMD（amd_pstate 与 ACPI OPP 两种配置）和 Hygon。找一台 Intel 机器 `intel_pstate=disable` 落到 acpi-cpufreq 并开 boost，验证 `__resolve_freq()` 是否把 `max_freq` 收敛到表内最高档、capacity 是否回到 1024，是当下最容易做的贡献。
- **推进收尾（discussion）**：谁署名这件事 Prateek 尚未回答，作者也在等。若有价值可以直接问一句「是否需要在同一批里同时撤销 sched 侧 v1」，把两条改动的关系摊开——这是本线程目前唯一没有答案的技术问题。
- **自查内部树（review）**：若内部树带了 `d2d5c129d07e` 的等价改动且机型是「表外 boost 的 acpi-cpufreq 类驱动」，会命中同一假压力。我可以在 `~/code/olk-6.6` 里核对 `cpufreq_update_pressure()` 的回退分支写法与自家机型的 `_PSS`/boost 关系，确认是否已受影响——在 cpufreq 侧修好之前不宜自行加 sched 侧门控，以免与上游分叉。

## 参考链接

- 本日回帖（Jianyong Wu 采纳 Prateek 方案 + 实测）: https://lore.kernel.org/all/PUZPR04MB4922771B19195F4D1BF89EFEE3B12@PUZPR04MB4922.apcprd04.prod.outlook.com/
- 被回复的 Prateek Nayak 方案帖: https://lore.kernel.org/all/4e39e935-2339-442b-8b14-a688b605c35e@amd.com/
- 系列原始补丁 v1: https://lore.kernel.org/all/20260821073927.455475-1-wujianyong@hygon.cn/
- tip-bot commit: 未获取到
- stable backport: 未获取到
---
id: sched-20260908-008
date: '2026-09-08'
subject: "sched/fair: Only apply cpufreq pressure where frequency is invariant"
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <20260821073927.455475-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/PUZPR04MB4922771B19195F4D1BF89EFEE3B12@PUZPR04MB4922.apcprd04.prod.outlook.com/
upstream_commit: null
fixes_commit: d2d5c129d07e
merged_branch: null
current_version: v1
generated_at: '2026-09-08'
authors:
- Jianyong Wu
maintainers_involved:
- K Prateek Nayak
patch_series:
- version: v1
  msgid: <20260821073927.455475-1-wujianyong@hygon.cn>
  date: '2026-08-21'
  summary: 'sched 侧门控（kernel/sched/fair.c +9/-2，只在 arch_scale_freq_invariant() 为真时计入 cpufreq 压力），带 Fixes: d2d5c129d07e。本日未重投、无 diff 变化。'
  review_outcome: '本日作者回帖明确放弃自己更复杂的 cpufreq_policy 加字段方案，采纳 Prateek 的 __resolve_freq() 改法并给出第二平台实测（3100000 高于最高 _PSS 2700000，修复后 capacity 回到 1024）；署名方式（Suggested-by 还是由 Prateek 自己发）待 Prateek 回答。'
merge_assessment:
  likelihood: medium
  blocking_issues:
  - cpufreq 侧正式补丁尚未发出，本日只有邮件内 diff 与口头采纳
  - cpufreq 维护者 Rafael Wysocki / Viresh Kumar 全程未介入，改动却落在 drivers/cpufreq/cpufreq.c
  - 原 sched 侧 v1 是撤销还是与 cpufreq 侧修复同批保留，无共识
  - 收益侧证据只到 capacity 恢复 1024，缺对放置/misfit/迁移决策的量化影响
  next_action: 等 Prateek 或作者正式发出 cpufreq 侧补丁（并确认署名），CC cpufreq 维护者
contribution_opportunities:
- kind: testing
  description: 在 Intel 机器上 intel_pstate=disable 落到 acpi-cpufreq 并开 boost，验证 __resolve_freq() 是否把 max_freq 收敛到表内最高档、capacity 是否回到 1024
- kind: discussion
  description: 追问 cpufreq 侧修复与 sched 侧 v1 门控是否同批进树，把两条改动的关系摊开
- kind: review
  description: 自查内部树（如 OLK-6.6）的 cpufreq_update_pressure() 回退分支与自家机型 _PSS/boost 关系，确认是否已受同一假压力影响
source_email_count: 1
related_articles:
- sched-20260907-006
- sched-20260903-010
- sched-20260902-008
tags:
- cpufreq
- cfs
- x86
---
