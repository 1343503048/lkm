# sched/fair: Only apply cpufreq pressure where frequency is invariant

## TL;DR

`get_actual_cpu_capacity()` 无条件从容量里扣掉 `max(hw_load_avg, cpufreq_get_pressure())`，但只有频率不变（`arch_scale_freq_invariant()` 为真）的架构上 util 才会随频率同比例缩放；在没有频率不变性的机器上，满载 CPU 无论跑多高频率都会累计到完整 `SCHED_CAPACITY_SCALE`，于是「只缩放比较的一侧」，满载 CPU 报告出的 util 超过它被认可能运行的容量。Jianyong Wu 的一行门控修复带 `Fixes: d2d5c129d07e`（该提交让 `cpufreq_update_pressure()` 回退到 `cpuinfo.max_freq`，此前这类平台压力恒为 0，问题才刚变得可达）。Vincent Guittot 当日追问「What issue do you try to fix?」，Hongyan Xia 随后把问题重新定性为「与频率不变性无关，实质是 cpufreq 各 policy 字段语义在驱动之间不一致」——`cpuinfo.max_freq` 含 boost，而 acpi-cpufreq 的 `policy->max` 来自不含 boost 的 ACPI `_PSS`，两者相减就凭空产生压力。本日作者回贴承诺在 Intel/AMD 机器上用 `intel_pstate=disable` / `amd_pstate=disable` 强制 acpi-cpufreq 复现并给出实测数字。

## 背景与问题

`util_fits_cpu()` 用 `get_actual_cpu_capacity()` 得到 CPU 的可用容量，再从其中扣除硬件负载压力与 cpufreq 压力：

- 在频率不变的架构上，`arch_scale_freq_capacity()` 会让 util 随实际频率缩放，因此容量端按频率折算是对称的，扣减成立。
- 在没有频率不变性的架构上，util 与频率无关，满载 CPU 累计的 util 会一路顶到 `SCHED_CAPACITY_SCALE`；此时只在容量侧扣减 cpufreq 压力，等于「缩放了比较的一侧而不缩放另一侧」，一个满载 CPU 会被判成超载（`util > capacity`），进而影响放置与 `select_idle_capacity()` 一类的容量适配判断。

这个问题是 `d2d5c129d07e`（"cpufreq: Make cpufreq_update_pressure() fall back to cpuinfo.max_freq"）引入的可达性：在此之前这类平台的 cpufreq 压力一直是 0。作者在提交说明里明确「是否真正有影响取决于频率不变性，而不是这个回退本身」。

讨论中问题被换了定性：Hongyan Xia 指出，在作者的系统上真正的原因是 `cpuinfo.max_freq` 包含 boost 频率而 `policy->max` 不包含，于是 `policy->max < cpuinfo.max_freq` 这个算术比较在系统毫无实际限频时也算出了非零压力。Guittot 补充了驱动侧语义：Intel 与多数 AMD 机器上 `policy->max` 就是最高可达频率（开 boost 时即 boost 频率），而 acpi-cpufreq 的 `policy->max` 由 ACPI `_PSS` 表解析，表里没有 boost 频率。所以同一份调度器代码在不同 cpufreq 驱动下看到的「压力」含义并不一致。

## 技术方案

v1 只有 1 个补丁、`kernel/sched/fair.c` 9 增 2 删，改动点全部在 `get_actual_cpu_capacity()`：先取 `pressure = hw_load_avg(cpu_rq(cpu))`，只有 `arch_scale_freq_invariant()` 为真时才 `pressure = max(pressure, cpufreq_get_pressure(cpu))`，最后 `return capacity - pressure`。也就是把 cpufreq 压力的计入条件收紧到「util 也跟着频率缩放」的架构上，硬件负载压力保持不变。

这只是止血。作者在 09-02 提出的根治方向是把「CPU 是否真的被限频」的判定信息交给 cpufreq 侧，建议给 `struct cpufreq_policy` 增加两个字段：

- `boost_freqs_outside_table`：boost 频率不在频率表中；
- `table_max`：频率表内的最高频率。

然后用 `policy->boost_freqs_outside_table && policy->boost_enabled && policy->max == policy->table_max` 识别「未被限频」的情形，此时 `cpufreq_update_pressure()` 应以 `cpuinfo.max_freq` 作为 `capped_freq` 而不是 `policy->max`。该方案尚停留在邮件里的伪代码，作者明确请求 cpufreq 维护者输入，本 thread 中还没有 cpufreq 侧的人回应。

## 版本演进与当前进展

- 08-21 15:39 Jianyong Wu 以 `wujianyong@hygon.cn` 首发单补丁（无版本号，标题即 `[PATCH] ...`）；17:26 Vincent Guittot 当天追问要修什么问题。
- 08-24 / 08-25 Hongyan Xia 介入，把根因从频率不变性重述为 cpufreq policy 字段语义问题，并要求作者重写提交说明；作者 09-02 承诺「I will re-phrase the problem statement in the next version」。
- 09-02 作者另发一封给 Guittot，提出 `boost_freqs_outside_table` / `table_max` 的 cpufreq 侧方案；同日 Xia 给出 Ryzen 7840U 线索（acpi-cpufreq 只有 3 个 OPP，boost 频率不在这 3 个之内且远高于它们），怀疑「Maybe this is a broader issue than we realize」。
- 本日（09-03 10:04）作者回贴：承认目前只在自己的机器上观测到，不愿过度推广；认同触发条件是驱动而非厂商；承诺用 `intel_pstate=disable` / `amd_pstate=disable` 强制 acpi-cpufreq，在开 boost 的情况下对比实测频率与 `policy->max`，看无约束负载下是否出现非零 cpufreq 压力，「I will report back with the numbers once I have them」。本线程该回帖改用了 Outlook 地址而非补丁署名地址。
- 截至本日代码只有一个版本、未重投，也没有任何 tag。

## Maintainer 意见与讨论焦点

- **Vincent Guittot（sched/fair 容量与 util 侧维护者）**：08-21 的两句话基本决定了这个补丁的命运——「Even with frequency invariance, utilization can exceed capacity, only the time to reach it will change.」以及「What issue do you try to fix?」。前一句直接削弱了「满载 CPU 报告出的 util 超过它被认可的容量」这个论证的独特性：容量与 util 不匹配在有频率不变性的平台上同样存在，只是收敛时间不同；换句话说，作者给出的必要性还没有和现象对应起来。
- **Hongyan Xia（Transsion）**：08-25 把讨论从调度器侧搬到 cpufreq 侧——「So this is not frequency-invariance-related. This basically boils down to the definition of different policy->fields, which might be better commented by people working often with boost frequencies.」并且明确要求「You might want to re-phrase the problem better as it took me quite a while to understand it.」09-02 进一步给出可复现平台假设（Ryzen 7840U + acpi-cpufreq + 3 个 OPP + 表外 boost），并怀疑问题面比目前认识到的更宽。
- 焦点因此分裂成两层：**表象**（哪一侧被缩放）与**根因**（`cpuinfo.max_freq` / `policy->max` / boost 的跨驱动语义不一致）。Guittot 与 Xia 都没有认可「在 `get_actual_cpu_capacity()` 里按 `arch_scale_freq_invariant()` 分支」是正确层次——若根因在 cpufreq 侧，调度器里加的这个分支会在根治后被撤掉。
- cpufreq 维护者（Rafael Wysocki、Viresh Kumar 等）截至本日完全缺席，而这恰是 `boost_freqs_outside_table` 方案能否成立的关键读者。
- 本日无 `Acked-by` / `Reviewed-by`，也不存在 `Reported-by`/`Tested-by` 交换。

## 合入评估

likelihood: **unclear**。

依据（正向）：问题定位是可信的——`Fixes: d2d5c129d07e` 明确指出了可达性来源，改动只有 9 增 2 删且被 `arch_scale_freq_invariant()` 门控，对 x86/arm64 主流平台（均有频率不变性）零行为变化，属于纯收敛性修补，作为 `fixes` 路线的候选并不昂贵。

卡点：一是维护者的必要性提问未被正面回答，Guittot 的「即使有频率不变性 util 也能超过容量」这句质疑至今没有对应论证，作者 12 天后仍在承诺复现而非给出证据；二是问题的归类已被 Xia 改写到 cpufreq 子系统，本补丁的修法有可能被判定为「在错误的层次止血」，若走 `boost_freqs_outside_table` 路线则需要 cpufreq 侧改动并重新拉进 Rafael/Viresh，调度器这行门控未必保留；三是提交说明本身被要求重写，作者也已承诺；四是缺少第二平台复现，收益与被触发的概率都没有量化。

## 效果评估

邮件中未提供效果数据。本补丁没有任何 benchmark、没有 `perf`/`sched_debug` 采样，也没有「修复前后 util 与 capacity 数值对比」这类最小证据——这恰是 Guittot 追问的形态。

可作为量化的只有平台描述性信息：作者的系统上 `cpuinfo.max_freq` 含 boost 而 `policy->max` 不含，因而 `policy->max < cpuinfo.max_freq` 直接算出非零压力；Xia 提到的 Ryzen 7840U 是 acpi-cpufreq、`_PSS` 只有 3 个 OPP、boost 远高于最高 OPP，属于同一形状的假设案例但截至本日无人实测。作者 09-03 承诺的正是这组缺失的数据（实测频率 vs `policy->max`、无约束负载下的 cpufreq 压力是否非零）。

## 我可以参与的点

1. 直接补上最缺的那块证据：在手边的 Intel/AMD 机器上按作者给的方法做——`intel_pstate=disable` 或 `amd_pstate=disable` 落到 acpi-cpufreq，开 boost，跑一个不绑核、不限频的满载负载，打印 `cpuinfo.max_freq`、`policy->max`、实测运行频率，以及 `get_actual_cpu_capacity()` 相对 `capacity_orig` 实际扣掉了多少，确认无约束场景下是否真出现非零 cpufreq 压力。这类数据目前全线程只有作者的自述，任何一份独立复现都能直接推进讨论。
2. 把 `Fixes: d2d5c129d07e` 的影响面量化：除了容量比较本身，`util_fits_cpu()` 的 misfit 判定与 EAS 路径在非频率不变平台上都会随这行门控变化，值得列一张「哪些判定会因为多了这行门控而变化」的清单回帖。
3. cpuset/cgroup 视角：生产上的两类限制来源完全不同——cgroup `cpu.max` 与 cpuset 绑核走的是带宽/亲和性（反映在 `hw_load_avg` 一侧，本补丁不动它），真实限频来自 cpufreq 侧（`userspace` governor、`cpupower frequency-set`、thermal/QoS 上限）。值得验证的是：在被真实限频的机器上，这行 `arch_scale_freq_invariant()` 门控不会连带把 `cpufreq_get_pressure()` 变成不可见，也就是确认「只在非频率不变架构上跳过」的边界写对了。
4. 回合判断：OLK-6.6 若已有 `cpufreq_update_pressure()` 回退到 `cpuinfo.max_freq` 的等价改动，本补丁可作为小体积 fixes 直接评估（单函数、单文件、无新增符号）；若 6.6 未回合压力链，则只需记录「非频率不变平台上容量折算与 util 折算不对称」这条判据，避免自行加 `cpuinfo.max_freq` 回退。

## 参考链接

- 补丁与关键回帖：
  - v1 补丁本体（含 `Fixes: d2d5c129d07e` 与 diff）：https://lore.kernel.org/all/20260821073927.455475-1-wujianyong@hygon.cn/
  - Vincent Guittot 的追问：https://lore.kernel.org/all/CAKfTPtAxY7ABQMF+-uZJK2=nN21f-yQ8Pst_Mm9XP3dGJmHk_A@mail.gmail.com/
  - Hongyan Xia 把问题重定性为 policy 字段语义：https://lore.kernel.org/all/49233994-f46f-4d41-99b3-b40cc23bcbc7@transsion.com/
  - 作者提出 `boost_freqs_outside_table` / `table_max` 方案：https://lore.kernel.org/all/SI2PR04MB4931F65C44962845CE345B79E3B72@SI2PR04MB4931.apcprd04.prod.outlook.com/
  - Hongyan Xia 的 Ryzen 7840U 复现线索：https://lore.kernel.org/all/44993024-f1bb-4b4f-802b-a22f95101171@transsion.com/
  - 本日作者的复现承诺：https://lore.kernel.org/all/SI2PR04MB49315D05AB89CFA3B0E41BF3E3B62@SI2PR04MB4931.apcprd04.prod.outlook.com/
- 相关文章：[[sched-20260902-008]]（同一线程在 09-02 的讨论）。

---
id: sched-20260903-010
date: '2026-09-03'
subject: 'sched/fair: Only apply cpufreq pressure where frequency is invariant'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: '<20260821073927.455475-1-wujianyong@hygon.cn>'
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
patch_series:
- "sched/fair: Only apply cpufreq pressure where frequency is invariant"
merge_assessment:
  likelihood: unclear
  blocking_issues:
  - "Guittot 关于 util 同样能超容量、以及要修什么问题的追问至今未被正面回答"
  - "根因被重新定性到 cpufreq policy 字段语义，调度器侧门控可能被判定为错误层次"
  - "boost_freqs_outside_table/table_max 方案缺 cpufreq 维护者表态，本 thread 无 Rafael/Viresh"
  - "提交说明被要求重写；无任何 tag，也无第二平台复现数据"
  next_action: "等作者给出 acpi-cpufreq 强制复现的实测数字与重写后的问题描述，再判断走调度器 fixes 还是 cpufreq 侧改动"
contribution_opportunities:
- "在 Intel/AMD 上用 intel_pstate=disable/amd_pstate=disable 复现非零 cpufreq 压力并给出 policy->max 对比数据"
- "梳理非频率不变平台上受容量折算影响的判定清单（util_fits_cpu、misfit 分类、EAS 路径）"
- "在 cgroup cpu.max/cpuset 限频场景验证本补丁不会把真实限频误判为无限频"
- "评估 OLK-6.6 回合面：是否已具备 cpufreq_update_pressure() 回退到 cpuinfo.max_freq 的前提"
source_email_count: 1
related_articles:
- sched-20260902-008
tags:
- cpufreq
- schedutil
- sched/fair
---
