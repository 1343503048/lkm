# sched/fair: Only apply cpufreq pressure where frequency is invariant

## TL;DR

Jianyong Wu（Hygon）的单补丁：只在 `arch_scale_freq_invariant()` 为真时才把 cpufreq pressure 计入
`get_actual_cpu_capacity()`。9/2 这天的实质结论是**作者承认标题里的因果口径错了**——他对 Hongyan Xia
说 "I will re-phrase the problem statement in the next version"，真正的病根是 `policy->max` 与
`policy->cpuinfo.max_freq` 对 boost 频率的语义差异，而不是频率不变性；同时他把修复方向推到 cpufreq 侧，
提出给 `struct cpufreq_policy` 加 `boost_freqs_outside_table` / `table_max`。Hongyan 当天反问「这可能是个
比我们认为更宽的问题」。**没有发新版本，没有新数据。**

## 背景与问题

补丁自己的问题陈述（v1 正文，`<20260821073927.455475-1-wujianyong@hygon.cn>`）：cpufreq pressure 按
「当前可达最高频率 / 可达最高频率」的比值降 capacity；只有频率不变（frequency invariant）的架构上 utilization
才带同样的缩放，否则一个满载 CPU 无论跑在什么频率都会累积到 `SCHED_CAPACITY_SCALE`。于是在非不变平台上
"Reducing capacity on such a system scales one side of the comparison and not the other, and a fully busy CPU
ends up reporting more utilization than it is credited with being able to run."

触发点是 `d2d5c129d07e ("cpufreq: Make cpufreq_update_pressure() fall back to cpuinfo.max_freq")`——在此之前这类
平台的 pressure 恒为 0，所以这是该 commit 打开的行为面。补丁带 `Fixes: d2d5c129d07e`。

但 Hongyan Xia（8/25）把因果拆开：`cpuinfo.max_freq` 含 boost、`policy->max` 不含，于是
`policy->max < cpuinfo.max_freq` 这个算术比较在**系统根本没有压降**时也给出非 0 pressure。她的结论是
"So this is not frequency-invariance-related. This basically boils down to the definition of different
policy->fields"，并要求重写问题描述。Vincent Guittot 更早（8/21）就问过 "What issue do you try to fix?"
并指出 "Even with frequency invariance, utilization can exceed capacity, only the time to reach it will change."

## 技术方案

v1 的实现很小（`kernel/sched/fair.c`，+9/-2），只改 `get_actual_cpu_capacity()`：

```c
 unsigned long capacity = arch_scale_cpu_capacity(cpu);
+unsigned long pressure = hw_load_avg(cpu_rq(cpu));
-
-capacity -= max(hw_load_avg(cpu_rq(cpu)), cpufreq_get_pressure(cpu));
+	/*
+	 * Utilization only follows frequency where the architecture is
+	 * frequency invariant. Elsewhere, lowering the capacity would
+	 * scale one side of the comparison and not the other.
+	 */
+	if (arch_scale_freq_invariant())
+		pressure = max(pressure, cpufreq_get_pressure(cpu));
+	return capacity - pressure;
```

9/2 作者主推的却是 **cpufreq 侧**的方案（原样引自 73359）：给 `struct cpufreq_policy` 增加

- `boost_freqs_outside_table`: the boost frequency is not present in the frequency table;
- `table_max`: the highest frequency inside the frequency table.

然后用

```c
      if (policy->boost_freqs_outside_table &&
          policy->boost_enabled &&
          policy->max == policy->table_max)
              capped_freq = max_freq;
```

识别「其实没有被 cap」的情形；一旦确认未被 cap，`cpufreq_update_pressure()` 就用 `cpuinfo.max_freq`
而不是 `policy->max` 作为 `capped_freq`。作者的措辞是希望 cpufreq 的人来评判："Input from the cpufreq folks
would be very welcome."

这两条路线是**互斥的**：前者在 sched 侧按 invariance 屏蔽 pressure，后者在 cpufreq 侧把 pressure 算对。

## 版本演进与当前进展

- 8/21 15:39 Jianyong Wu 发 v1（单补丁，带 `Fixes: d2d5c129d07e`）。
- 8/21 17:26 Vincent Guittot 质疑问题本身（"What issue do you try to fix?"）。
- 8/24：Hongyan Xia、Jianyong Wu 各有一封（本地缓存里这两封正文为空，msgid 为占位符，**内容未获取到**）。
- 8/25 15:40 Hongyan Xia 给出「这不是 frequency-invariance 问题，而是 policy 字段语义问题」的判断并要求重写
  problem statement。
- 9/2：作者两封（16:49 向 Vincent 重推 cpufreq 侧方案；17:00 向 Hongyan 承诺下一版重写问题描述）；
  17:37 Hongyan 提出这可能是更广的问题，并举 Ryzen 7840U（acpi-cpufreq、只有 3 个 OPP、boost 远高于表内最高档）
  作为可复现机器。
- 版本仍是 v1，9/2 当天没有 v2。
- 后续（供判断走向用，属 9/2 之后的缓存日）：9/3 作者回复说自己只在自有机器上观测到、不愿过度声称，准备用
  `intel_pstate=disable / amd_pstate=disable` 强制 acpi-cpufreq 去复现并回报数字；9/7 Hongyan 在 AMD 5900X 上用
  `trace_printk` 实测到 `max_freq 4683471, max 4683471`（amd-pstate，无假 pressure）vs
  `max_freq 4680714, max 3300000`（强制 acpi-cpufreq 后，boost 不在 _PSS 表内，因此无压降也产生 pressure），
  结论 "yes, this is a wider problem than we realize"；同日 K Prateek Nayak（AMD）提出第三种改法——直接改
  `cpufreq_update_pressure()` 里 `arch_scale_freq_ref()` 为 0 时的回退，用 `__resolve_freq()` 依据 freq_table
  把 `cpuinfo.max_freq` 收敛到表内最高档。

## Maintainer 意见与讨论焦点

- **Vincent Guittot（sched/fair 维护者）**：从 8/21 起就没接受「非不变平台 util 不能超过 capacity」这个前提，
  9/2 也没有对作者的新方案表态。他是最关键的沉默方。
- **Hongyan Xia（Transsion，非维护者但把问题定义清楚的人）**：9/2 的发言价值在于把讨论从「口径」推向「可复现证据」，
  并主动给出候选机器（7840U）。她 8/25 的意见实际改变了补丁的标题语义——标题说 frequency invariant，正文争论的是
  boost 与 `_PSS` 表的定义。
- **Jianyong Wu（作者）**：姿态是承认表述不清（"I will re-phrase the problem statement in the next version"）并把
  修复点往 cpufreq 侧移；同时明确在等 cpufreq 维护者输入。
- 焦点因此变成**改哪一侧**：sched 侧用 `arch_scale_freq_invariant()` 门控 vs cpufreq 侧把 `capped_freq` 算对。
  9/2 无人 NAK，也无人给 `Reviewed-by`/`Acked-by`。

## 合入评估

**unclear**。方向上「acpi-cpufreq + boost 不在 `_PSS` 表内时会算出假 pressure」已被后续实测坐实，这确实是个真 bug，
而且带 `Fixes:` 标签，有进 `sched/urgent` 或 cpufreq fixes 的理由。但当前这个补丁本身的合入路径基本被讨论否掉了：
标题与因果口径错的（作者已承认），Vincent 从未认可，而 9/7 出现的 cpufreq 侧改法（Prateek 的 `__resolve_freq()`
方案）与作者提的 `boost_freqs_outside_table`/`table_max` 方案都在**同一个函数**里解决问题，一旦 cpufreq 侧算对，
sched 侧的门控就不需要了。要合入，前提是先确定修在哪一侧、并由 cpufreq 维护者（作者自己也在等这个输入）表态。

## 效果评估

9/2 当天**零实测数据**，全部是语义与概念论证。这一点正是线程的短板，也是 Hongyan 反复推的方向。可用的量化证据
出现在 9/7（Hongyan 的 5900X trace，上面已引用）：同样开着 boost，amd-pstate 下 `policy->max == cpuinfo.max_freq`、
acpi-cpufreq 下 `3300000 vs 4680714`，即假 pressure 幅度约 29% 的频率跨度。补丁效果（capacity 修正后对
`util_fits_cpu()` / 选核的影响）至今没有测量。

## 我可以参与的点

- **补数据**：在非频率不变平台（或强制 `acpi-cpufreq` 的 x86 机器）上量化 pressure 开/关对
  `get_actual_cpu_capacity()` → `util_fits_cpu()` → pick/migrate 决策的影响，这是线程目前最缺的一环，作者自己
  承诺了要做但还没做。
- **在三个方案之间给意见**：sched 侧 `arch_scale_freq_invariant()` 门控 / `cpufreq_policy` 新增两个字段 /
  `cpufreq_update_pressure()` 回退时用 `__resolve_freq()` 收敛到 freq_table。第三方案改动面最小，值得被推动。
- **对 cpuset/cgroup 用户的实际影响**：`hw_load_avg` 与 `cpufreq_get_pressure` 取 max 后一起从 capacity 里减，
  在非不变平台上会让 CPU 看起来「装不下」任务，进而影响 cpuset 内的摆放与均衡判断；OLK-6.6 若已带
  `d2d5c129d07e`，这个假 pressure 的回合风险要自己评估一次。
- **语义表**：把 `policy->max` / `policy->cpuinfo.max_freq` / `_PSS` 表最高档 / boost / CPPC `highest_perf` /
  `arch_scale_freq_ref()` 的关系写成一张判定表回帖，讨论已经证明这件事能省很多往返。

## 参考链接

- v1 原始补丁：https://lore.kernel.org/all/20260821073927.455475-1-wujianyong@hygon.cn/
- 9/2 Jianyong Wu 向 Vincent Guittot 重推 cpufreq 侧方案：https://lore.kernel.org/all/SI2PR04MB4931F65C44962845CE345B79E3B72@SI2PR04MB4931.apcprd04.prod.outlook.com/
- 9/2 Jianyong Wu 承诺重写 problem statement：https://lore.kernel.org/all/SI2PR04MB4931F26A705BEC756ED56EC8E3B72@SI2PR04MB4931.apcprd04.prod.outlook.com/
- 9/2 Hongyan Xia 提出「更广的问题」+ Ryzen 7840U：https://lore.kernel.org/all/44993024-f1bb-4b4f-802b-a22f95101171@transsion.com/
- 8/25 Hongyan Xia 的定性（本线程内引用，原始 msgid）：https://lore.kernel.org/all/49233994-f46f-4d41-99b3-b40cc23bcbc7@transsion.com/
- 8/25 Vincent Guittot 的邮件（本线程引用，原始 msgid）：https://lore.kernel.org/all/CAKfTPtCxMA-7BX20LNhdOT+BQysdnOxOALrLvhTFNYJLbdsoCA@mail.gmail.com/
- 相关：[[sched-20260821-004]]（v1 首发当日）、[[sched-20260824-004]]、[[sched-20260825-010]]（同一线程的 8/24、8/25 讨论）

---
id: sched-20260902-008
date: '2026-09-02'
subject: 'sched/fair: Only apply cpufreq pressure where frequency is invariant'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260821073927.455475-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/20260821073927.455475-1-wujianyong@hygon.cn/
upstream_commit: null
fixes_commit: d2d5c129d07e
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Jianyong Wu
maintainers_involved:
- Vincent Guittot
- Hongyan Xia
- K Prateek Nayak
patch_series:
- '[PATCH] sched/fair: Only apply cpufreq pressure where frequency is invariant'
merge_assessment:
  likelihood: unclear
  blocking_issues:
  - 作者已承认问题描述口径错误（frequency invariant 并非真正病根），标题与实现都需要重做
  - Vincent Guittot 自 8/21 起未认可前提，9/2 对作者新方案也未表态
  - 修复点存在 sched 侧 / cpufreq 侧 / __resolve_freq 回退三条互斥路线，尚未选定
  - 9/2 当天无任何实测数据，作者在等 cpufreq 维护者输入
  next_action: 等作者 v2 或 cpufreq 侧方案；关键是 cpufreq 维护者对 capped_freq 语义表态并给出实测数据
contribution_opportunities:
- 在非频率不变或强制 acpi-cpufreq 的平台上量化假 cpufreq pressure 对 util_fits_cpu()/选核的影响
- 在 sched 侧门控、cpufreq_policy 新增字段、__resolve_freq 回退三种方案之间给出评审意见
- 整理 policy->max / cpuinfo.max_freq / _PSS / boost / CPPC highest_perf 的语义判定表
- 评估 d2d5c129d07e 在 OLK-6.6 等长期分支上是否引入同样的假 pressure
source_email_count: 3
related_articles:
- sched-20260824-004-sched-fair-cpufreq-pressure-invariant.md
- sched-20260825-006-sched-fair-cpufreq-pressure-invariant.md
- sched-20260826-003-sched-cpufreq-reevaluate-tickless-idle.md
tags:
- schedutil
- sched/fair
- regression
---
