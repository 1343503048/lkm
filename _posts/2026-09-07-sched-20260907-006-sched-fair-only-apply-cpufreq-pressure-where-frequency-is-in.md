---
id: sched-20260907-006
date: '2026-09-07'
subject: 'sched/fair: Only apply cpufreq pressure where frequency is invariant'
subsystem: sched
type: bug
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
- Hongyan Xia
- K Prateek Nayak
- Vincent Guittot
patch_series:
- version: v1
  msgid: <20260821073927.455475-1-wujianyong@hygon.cn>
  date: '2026-08-21'
  summary: 'kernel/sched/fair.c +9/-2：get_actual_cpu_capacity() 先取 pressure = hw_load_avg()，仅当
    arch_scale_freq_invariant() 为真时才 max() 上 cpufreq_get_pressure()；带 Fixes: d2d5c129d07e。'
  review_outcome: Guittot 08-21 追问要修什么问题；Xia 08-25 把根因改写成 policy 字段语义并要求重写描述；09-07
    Xia 在 AMD 5900X 上以 trace_printk 实测复现（4683471/4683471 vs 4680714/3300000），Prateek
    Nayak 同日提出改 cpufreq_update_pressure() 回退分支为 __resolve_freq()，作者确认非 AMD 独有并宣布另发补丁。本日无
    tag、未重投。
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 作者已表示要在另一补丁里处理该问题，本补丁（sched 侧门控）的范围与是否保留未定
  - boost 语义在 cpufreq 各驱动间不一致，需 cpufreq 维护者（Rafael Wysocki / Viresh Kumar）同步表态，本线程至今无其痕迹
  - Vincent Guittot 关于 util 同样能超容量、以及要修什么问题的追问仍未被正面回答，标题与提交说明已被要求重写
  - 仅有假压力存在的确证数据，缺少对放置/misfit/迁移的可观测影响量化，也无 Intel 侧实测
  next_action: 跟作者的 separate patch（cpufreq 侧修法）与 Prateek 的 __resolve_freq 方案二选一；在其出现前本补丁不宜再推进，只需确认
    sched 侧门控是否随之撤销
contribution_opportunities:
- kind: testing
  description: 在 Intel 机器上用 intel_pstate=disable 落到 acpi-cpufreq、开 boost，按同样字段打点，验证作者与
    Xia 关于「Intel + ACPI cpufreq 同样中招」的怀疑并验证 __resolve_freq 是否收敛到表内最高档
- kind: discussion
  description: 在三条互斥路线（sched 侧 arch_scale_freq_invariant() 门控 / cpufreq_policy 新增
    boost_freqs_outside_table+table_max / cpufreq_update_pressure 回退改用 __resolve_freq）之间给出取舍意见，目前线程内只有
    AMD 与 Transsion 发言
- kind: testing
  description: 量化假 cpufreq 压力对 get_actual_cpu_capacity() → util_fits_cpu() → misfit/迁移决策的实际影响（绑小
    cpuset + schedutil + 表外 boost），补上目前完全缺失的收益侧证据
- kind: review
  description: 自查内部树：若已带 d2d5c129d07e 等价改动且机型使用表外 boost 的 acpi-cpufreq 类驱动，会命中同一假压力；在
    cpufreq 侧修好前不应自行在 sched 侧加门控以免与上游分叉
source_email_count: 4
related_articles:
- sched-20260902-008
- sched-20260903-010
tags:
- cpufreq
- cfs
- x86
title: 'sched/fair: Only apply cpufreq pressure where frequency is invariant'
layout: article
---

## TL;DR

本文为增量更新，完整背景见 [[sched-20260902-008]] 与 [[sched-20260903-010]]。09-07 这个线程第一次出现了**实测数字**：Hongyan Xia（Transsion）在 AMD 5900X 上用 `trace_printk` 打出 cpufreq pressure 更新，`amd_pstate` + boost 时 `policy->cpuinfo.max_freq` 与 `policy->max` 相同（4683471 vs 4683471，不产生压力），强制关掉 pstate、改用 ACPI OPP + schedutil 而仍开 boost 时变成 4680714 vs 3300000（3300000 是最高非 boost OPP），于是 `policy->max < cpuinfo.max_freq` 在系统毫无真实限频时凭空算出压力，她的结论是「this is a wider problem than we realize」并怀疑 Intel 上用 ACPI cpufreq 的机器同样中招。同日 K Prateek Nayak（AMD）顺着 `cpufreq_policy_init_qos()` 读代码，指出 `cpuinfo.max_freq` 含 boost 与 `cpufreq_update_pressure()` 里 `max_freq <= capped_freq` 的语义彼此矛盾，给出两条修法（x86 实现 `arch_scale_freq_ref()`，或改 `!max_freq` 回退分支为 `__resolve_freq()`）。作者 Jianyong Wu 确认不是 AMD 独有，并承诺「I will address that in a separate patch」——修复重心正式从 sched 侧移到 cpufreq 侧。

## 背景与问题

`get_actual_cpu_capacity()` 无条件从容量里扣掉 `max(hw_load_avg, cpufreq_get_pressure())`，作者的 v1 把它改成只在 `arch_scale_freq_invariant()` 为真时计入 cpufreq 压力，带 `Fixes: d2d5c129d07e`（该提交让 `cpufreq_update_pressure()` 在 `arch_scale_freq_ref()` 返回 0 时回退到 `policy->cpuinfo.max_freq`，此前这类平台压力恒为 0）。

但问题在 08-25 已被 Hongyan Xia 重新定性：真正的病根不是频率不变性，而是 cpufreq 各 policy 字段对 boost 的语义在不同驱动下不一致——`cpuinfo.max_freq` 含 boost，acpi-cpufreq 的 `policy->max` 来自不含 boost 的 ACPI `_PSS`/OPP 表，两者一比就凭空产生「被限频」的假象。本日的 5900X 实测正是这条论断的第一份硬数据。

## 技术方案

现存的三条互斥修法（本日新增第三条）：

1. **sched 侧门控（当前补丁 v1）**：`kernel/sched/fair.c` +9/-2，只在 `get_actual_cpu_capacity()` 里给 cpufreq 压力加 `arch_scale_freq_invariant()` 条件。它掩盖症状而不修正压力的计算，且作者已承认标题里的因果口径不成立。
2. **cpufreq policy 新增字段（作者 09-02 提出）**：给 `struct cpufreq_policy` 加 `boost_freqs_outside_table` 与 `table_max`，用 `policy->boost_freqs_outside_table && policy->boost_enabled && policy->max == policy->table_max` 识别「实际未被限频」。
3. **改 `cpufreq_update_pressure()` 的回退（Prateek 本日提出）**：`drivers/cpufreq/cpufreq.c` 里把
   ```
   if (!max_freq)
       max_freq = policy->cpuinfo.max_freq;
   ```
   换成用 `__resolve_freq()` 收敛。他第一版贴的是 `__resolve_freq(policy, policy->cpuinfo.max_freq, policy->max, policy->min, CPUFREQ_RELATION_H)`，30 分钟后自我更正：「My bad, that should have been other way around and use the cpuinfo fields to prevent capping based on policy limits」，最终形态是在 `policy->cpuinfo.min_freq..policy->cpuinfo.max_freq` 区间做 `CPUFREQ_RELATION_H`，即**不随 policy 限幅**。他的预期效果：有 freq_table 的驱动（acpi-cpufreq）会把 `cpuinfo.max_freq` 收敛到表内最高档，用 CPPC 的驱动（amd-pstate、intel_pstate）则原样返回。

Prateek 的论证路径值得记下来：他读 `cpufreq_policy_init_qos()` 后认为 `policy->cpuinfo.max_freq` 按定义**应当**含 boost 范围，而 `cpufreq_update_pressure()` 里的注释与逻辑（「Handle properly the boost frequencies, which should simply clean the cpufreq pressure value.」，判据为 `max_freq <= capped_freq`）却假设可以在 `cpuinfo.max_freq` 与 `policy->max` 之间直接比出限幅程度——两者不能同时成立。因此要么 x86 提供 `arch_scale_freq_ref()`（这样就不走回退分支，且能区分 boost 开/关），要么让回退分支自己把 boost 折回表内最高档。

## 版本演进与当前进展

- 08-21 15:39 Jianyong Wu 首发单补丁（无版本号），当天 Vincent Guittot 追问「What issue do you try to fix?」。
- 08-24 / 08-25 Hongyan Xia 把根因从频率不变性改写成 policy 字段语义，要求重写提交说明；作者承诺 re-phrase。
- 09-02 作者提出 `boost_freqs_outside_table` / `table_max` 方案并向 cpufreq 侧求输入；同日 Xia 给出 Ryzen 7840U 假设并怀疑问题面更宽。
- 09-03 10:04 作者承诺在 Intel/AMD 上用 `intel_pstate=disable` / `amd_pstate=disable` 复现并回报数字。
- **09-07 本日**：10:32 Hongyan Xia 给出 5900X 上的复现与两组 `trace_printk` 数字（即作者 09-03 承诺、但由她先做出来的那份测量）；16:07 / 16:37 K Prateek Nayak 给出 `cpufreq_update_pressure()` 侧改法并自我更正一次；22:57 作者确认非 AMD 独有、声明另发补丁处理。
- 补丁本体**仍是 v1、未重投**，本线程至今没有任何 `Acked-by`/`Reviewed-by`/`Tested-by`，cpufreq 维护者（Rafael Wysocki、Viresh Kumar）依旧缺席。

## Maintainer 意见与讨论焦点

- **Hongyan Xia（Transsion，本日复现者）**：给出独立复现与具体数字，并明确「So you can see policy->max includes no boost frequencies (3300000 is the highest OPP) and will trigger policy->max < policy->cpuinfo.max_freq, hence applying pressure when there is actually no pressure.」结论是问题比目前认知的更宽，怀疑 Intel + ACPI cpufreq 同样受影响。这条回帖把 08-25 提出的定性从推理升级成了可复现事实。
- **K Prateek Nayak（AMD）**：把争论从「该在哪一侧门控」推进到「`cpuinfo.max_freq` 的语义到底是什么」。他给的两条出路里，`arch_scale_freq_ref()` 那条会牵动 x86 CPPC/amd-pstate 的调度器反馈接口，`__resolve_freq()` 那条只在 `drivers/cpufreq/cpufreq.c` 一处改动、影响面最小。他本人以「Thoughts?」收尾，本日无人反驳。
- **Jianyong Wu（作者）**：接受更广的影响面判定——「I agree it is not AMD-specific: any driver that reports a non-boost policy->max while cpuinfo.max_freq includes boost will hit the same path, so ACPI cpufreq on Intel should be affected as well」，并把后续工作切开：「I will address that in a separate patch and we can continue the discussion there.」这意味着本补丁的范围悬空：若 cpufreq 侧把压力算对，sched 侧这行 `arch_scale_freq_invariant()` 门控就不再必要。
- **Vincent Guittot（sched/fair 容量侧维护者）**：自 08-21 提问后本线程中再未表态，本日的两条新路线他也没有回应——这是本补丁能否被承认「值得修」的关键沉默。
- 讨论焦点：本补丁与「另一个补丁」的关系（谁承载修复）、以及 boost 语义在 cpufreq 各驱动之间由谁定义（`cpuinfo.max_freq` 含 boost 是否要成为契约）。

## 合入评估

`likelihood=medium`。

正向：问题已被独立实测坐实，且带 `Fixes:` 标签，属于会产生错误容量判断的行为缺陷，具备走 fixes 通道的理由；本日的 `__resolve_freq()` 方案改动面很小，与作者承诺的「separate patch」方向一致，推进节奏明显比 09-02 之前快。

卡点：一是作者已表示要在另一个补丁里处理，本补丁（sched 侧门控）的范围与是否继续保留都未定，存在「被自己后续版本替换」的高概率；二是 boost 语义在 cpufreq 各驱动间不一致，需要 cpufreq 侧同步甚至定义契约，而 cpufreq 维护者至今未进这个线程；三是 Vincent Guittot 08-21 的质疑（即使有频率不变性 util 也能超过容量）与「到底要修什么问题」仍未被正面回答，标题与提交说明已被要求重写；四是实测只证明了「假压力存在」，没有证明它对放置/均衡决策造成可观测影响——调度器侧的收益仍是空白。

## 效果评估

本日的价值全在**问题确证**，不在收益量化：

- AMD 5900X + `amd_pstate` + boost：`cpufreq_set_policy` 打点显示 `CPU 1 has max_freq 4683471, max 4683471`，两者相等 → 无假压力。
- 同机强制关闭 pstate、改用 ACPI OPP + schedutil、仍开 boost：`CPU 1 has max_freq 4680714, max 3300000`，3300000 是最高 OPP → `policy->max < cpuinfo.max_freq` 成立，无真实限频也产生 cpufreq 压力。

仍未获取到的部分：假压力的具体毫瓦/毫赫兹量级以外的调度后果——没有 benchmark、没有 `perf`/`sched_debug` 采样、没有 `util_fits_cpu()` misfit 次数或迁移计数的对比，也没有 Intel 机器的复现（作者的「separate patch」与 Intel 侧假设都还是口头）。作者自己 09-03 承诺要给的「无约束负载下是否出现非零压力」数据，本日是由 Hongyan Xia 代为给出的。

## 我可以参与的点

- 直接补 Intel 那一格：作者与 Xia 都怀疑 Intel + acpi-cpufreq 同样中招但无人实测。手边 Intel 机器上用 `intel_pstate=disable` 落到 acpi-cpufreq、开 boost，用同样两个字段（`policy->cpuinfo.max_freq` / `policy->max`）打点，即可把「问题有多宽」从推测变成表格；顺带能验证 Prateek 关于「有 freq_table 的驱动会被 `__resolve_freq()` 收敛到表内最高档」的预期是否真成立。
- 参与方案选择（这是目前最缺意见的地方）：三条路线中，`__resolve_freq()` 版本体积最小但把「boost 不算压力」写死在 cpufreq 侧；`arch_scale_freq_ref()` 更正确但需要 x86 定义 boost 开/关时参考频率如何变化；新增 policy 字段最啰嗦却语义最清楚。回帖给出取舍意见本身就是有效贡献，且线程里目前只有 AMD 一家发言。
- 补收益侧证据（调度器真正关心的部分）：在非频率不变或强制 acpi-cpufreq 的机器上量化假压力对 `get_actual_cpu_capacity()` → `util_fits_cpu()` → pick/misfit 的影响，比如绑核到小 cpuset、开 boost 且 governor 为 schedutil 时统计 misfit 与迁移次数。这条数据一旦给出，本 bug 的严重性才算钉死。
- 自家分支风险自查：只要内部树带 `d2d5c129d07e` 等价改动、且机型走 acpi-cpufreq/表外 boost，就会命中同一假压力；这属于可以现在就排查的兼容性问题，不需要等上游结论。同时留意结论走向——若上游最终在 cpufreq 侧修，则不要在 sched 侧自行加门控，避免与上游分叉。

## 参考链接

- 本日邮件：
  - Hongyan Xia 的 5900X 复现与数字：https://lore.kernel.org/all/f38d55b1-68f8-4cfa-8b97-47fe58bd9ed7@transsion.com/
  - K Prateek Nayak 的 `__resolve_freq()` 方案（含 `cpufreq_policy_init_qos()` 论证）：https://lore.kernel.org/all/d709498b-9572-44bd-a93e-bbed23fd7372@amd.com/
  - 同一帖的自我更正（改用 cpuinfo 区间、不随 policy 限幅）：https://lore.kernel.org/all/4e39e935-2339-442b-8b14-a688b605c35e@amd.com/
  - 作者确认非 AMD 独有并宣布另发补丁：https://lore.kernel.org/all/SI2PR04MB49318F9F4DB71CC11F8E0AD4E3B22@SI2PR04MB4931.apcprd04.prod.outlook.com/
- 历史与补丁本体：
  - v1 补丁（含 `Fixes: d2d5c129d07e`）：https://lore.kernel.org/all/20260821073927.455475-1-wujianyong@hygon.cn/
  - Hongyan Xia 将该问题重定性为 policy 字段语义：https://lore.kernel.org/all/49233994-f46f-4d41-99b3-b40cc23bcbc7@transsion.com/
  - 作者承诺复现（09-03）：https://lore.kernel.org/all/SI2PR04MB49315D05AB89CFA3B0E41BF3E3B62@SI2PR04MB4931.apcprd04.prod.outlook.com/
- 相关代码：`drivers/cpufreq/cpufreq.c` `cpufreq_update_pressure()` / `cpufreq_policy_init_qos()` / `__resolve_freq()`；`kernel/sched/fair.c` `get_actual_cpu_capacity()`
- 相关：[[sched-20260902-008]]、[[sched-20260903-010]]
