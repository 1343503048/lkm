---
id: sched-20260907-003
date: '2026-09-07'
subject: 'arm64/cpufreq: report and track frequencies above 4.19 GHz'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <cover.1788712186.git.okerixx@gmail.com>
lore_url: https://lore.kernel.org/all/cover.1788712186.git.okerixx@gmail.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Oleg Keri
maintainers_involved: []
patch_series:
- version: v1
  msgid: <cover.1788712186.git.okerixx@gmail.com>
  date: '2026-09-07'
  summary: '2 补丁。patch 1（arm64: topology: fix arch_freq_get_on_cpu() overflow above
    4.19 GHz）修 arch_freq_get_on_cpu() 里 u64 乘积被截成 unsigned int 再右移导致的回绕，触发条件是参考频率高于
    2^32 / SCHED_CAPACITY_SCALE = 4194304 kHz。patch 2（cpufreq: update capacity_freq_ref
    when the boost state changes）把 capacity_freq_ref 的更新从 init_cpu_capacity_callback()
    抽成 topology_update_freq_ref() 并在 policy_set_boost() 中调用，使其跟随 boost 状态。base-commit
    9d80aa4617b32f5054c5aa471d06b66704854935，8 files changed, 29 insertions(+), 8
    deletions(-)。作者强调 patch 1 必须与 patch 2 同批或更早合入。'
  review_outcome: 截至本日无回帖、无 Acked-by/Reviewed-by、无 v2；正文亦无 Fixes 标签。
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 本日内零 review，cpufreq 与 drivers/base/arch_topology 两侧维护者均未表态
  - patch 2 的 hook 无条件生效，与 ACPI/CPPC 路径下 capacity_freq_ref 另有来源（cppc_perf_to_khz(highest_perf)）的关系未论证
  - capacity_freq_ref 变为运行时可改，但 cpu_capacity 只在 boot 期归一化一次，一致性未讨论；作为 bug 修复没有 Fixes
    标签
  - 仅一台机型（Snapdragon X2 Elite / Glymur）的数据，缺外部复现
  next_action: 继续观察是否有维护者回应；若作者发 v2，重点看 patch 1 是否补 Fixes、以及是否回答 CPPC/ACPI 路径与 cpu_capacity
    一致性这两个问题
contribution_opportunities:
- kind: review
  description: 跨 arch 对照影响面——x86 走 arch/x86/kernel/cpu/aperfmperf.c（u64 换算、参考量是含 boost
    的 arch_max_freq_ratio）不受这两个问题影响，riscv/arm 共用 capacity_freq_ref 但不提供 arch_freq_get_on_cpu()，因此
    patch 1 实际只影响 arm64；可回贴帮作者把标题与影响面写准
- kind: testing
  description: 在 boost 默认关闭的 arm64 机器（DT + 含 CPUFREQ_BOOST_FREQ 表项的驱动，或 cppc_cpufreq）验证
    capacity_freq_ref 是否停在持续最大频率、开 boost 后 cpuinfo_avg_freq 是否被钉住
- kind: testing
  description: 在 ACPI/CPPC arm64 平台上做 boost 开关前后对照，确认 arch_update_freq_ref() 改写 CPPC
    侧锁存值是否引入 cpu_capacity 与 arch_max_freq_scale 的不一致
- kind: new_patch
  description: 若自家分支也在 arm64 上依赖 AMU FIE 做频率不变性，可先按该系列思路在本地修 policy_set_boost 处的 ref
    刷新，并带着自己机型的数据参与上游讨论
source_email_count: 2
related_articles:
- sched-20260902-008
tags:
- cpufreq
- arm64
- topology
title: 'arm64/cpufreq: report and track frequencies above 4.19 GHz'
layout: article
---

## TL;DR

Oleg Keri 在 09-07 00:37 发出 2 补丁系列：Snapdragon X2 Elite（Glymur）是他见到的第一颗 boost OPP（4723200 kHz）越过 4194304 kHz 的 arm64 笔记本芯片，这条线正好是 `2^32 / SCHED_CAPACITY_SCALE`，于是一次性暴露两个独立 bug——`arch_freq_get_on_cpu()` 里 u64 乘积在右移之前被截成 `unsigned int` 而回绕，以及 `capacity_freq_ref` 只在 `CPUFREQ_CREATE_POLICY` 时锁存一次、开机时 boost 关着的机器会永远停在持续最大频率。两者叠加的后果都是「内核认为 boost 中的 CPU 比实际更慢」：AMU 算出的 scale 饱和在 1024，调度器分不清 boost 中的核与停在持续上限的核。作者给了完整的钉频实测表（`cpuinfo_avg_freq` 从 524283 → 4032000 → 4718587）。本日无人回帖、无任何 review。

## 背景与问题

作者的触发点是硬件代际：Glymur 的 boost OPP 是 4723200 kHz，持续（sustained）OPP 是 4032000 kHz，而 arm64 的频率不变性刻度是以 `capacity_freq_ref` 为分母的。cover 与 2/2 正文把两个问题分开陈述：

- **溢出（patch 1）**：`arch_freq_get_on_cpu()` 反算频率时，「频率刻度 × 参考频率」这个 u64 乘积在右移回 kHz 之前被截断成 `unsigned int`，因此任何参考频率高于 `2^32 / SCHED_CAPACITY_SCALE = 4194304 kHz` 就会回绕。按本地主线源码核对，该函数里 `freq` 确实声明为 `unsigned int`，语句是 `freq = scale * arch_scale_freq_ref(cpu); freq >>= SCHED_CAPACITY_SHIFT;`，与 cover 的描述一致（`arch/arm64/kernel/topology.c`）。
- **锁存时机（patch 2）**：`capacity_freq_ref` 由 `init_cpu_capacity_callback()` 在 `CPUFREQ_CREATE_POLICY` 时从 `policy->cpuinfo.max_freq` 取一次，之后从不更新；而 `cpufreq_frequency_table_cpuinfo()` 在 boost 关闭时会排除 `CPUFREQ_BOOST_FREQ` 条目，所以开机时 boost 关着的机器锁到的就是非 boost 最大值，之后再打开 boost，`policy->cpuinfo.max_freq` 上去了，ref 留在原地。

在 arm64 上由于频率不变性由 AMU 驱动，作者列出两条后果：`amu_scale_freq_tick()` 会把算出的 scale 上限截到 `SCHED_CAPACITY_SCALE`，跑在 `capacity_freq_ref` 以上的 CPU 饱和在 1024，于是「boost 中的核」与「停在持续上限的核」在调度器眼里完全一样、utilization 被低估；同时 `arch_freq_get_on_cpu()` 反算时也报不过 `capacity_freq_ref`，`cpuinfo_avg_freq` 被钉在非 boost 最大值。作者的实测结论是硬件一直按请求频率在跑，错的只是内核的看法。

## 技术方案

patch 1（`arm64: topology: fix arch_freq_get_on_cpu() overflow above 4.19 GHz`，改 `arch/arm64/kernel/topology.c`，本批缓存里没有 1/2 正文，具体写法未获取到）修上述截断。patch 2（`cpufreq: update capacity_freq_ref when the boost state changes`）把更新逻辑从 `init_cpu_capacity_callback()` 里提出来做成 `topology_update_freq_ref(const struct cpumask *cpus, unsigned int max_freq)`（`drivers/base/arch_topology.c`，`EXPORT_SYMBOL_GPL`，内部同时刷新 `freq_inv_set_max_ratio()`），原回调改为调用它；新 hook 放在 `policy_set_boost()` 里 `cpufreq_driver->set_boost()` 与 `freq_qos_update_request()` 都成功之后，作者的理由是 `policy_set_boost()` 是「全局 boost 开关、per-policy 开关和 CPU online 路径的共同入口」。为承接这个 hook，`arch/arm`、`arch/arm64`、`arch/riscv` 的 `topology.h` 各自把 `arch_update_freq_ref` 映射到 `topology_update_freq_ref`，`include/linux/cpufreq.h` 补一个 `__always_inline` 空 stub。整个系列 diffstat 为 8 files changed, 29 insertions(+), 8 deletions(-)，base-commit `9d80aa4617b32f5054c5aa471d06b66704854935`。

作者特别强调顺序依赖：只有 patch 2 才会把 `capacity_freq_ref` 抬过 4194304 kHz，所以 patch 1 必须与它同批或更早合入——否则 patch 2 反而把 arm64 推进 patch 1 的回绕路径。

## 版本演进与当前进展

- 09-07 00:37 Oleg Keri 发出 v1（cover `<cover.1788712186.git.okerixx@gmail.com>` + 2/2），2/2 带 `Signed-off-by`，正文里没有 `Fixes` 标签；缓存只保留正文、邮件头已剥离，收件人列表未获取到。
- 本批缓存里只有 cover 与 2/2 两封，1/2 正文未取到；截至本日邮件结束，无任何回帖、无 v2、无维护者表态。
- 作者在同一封 cover 里主动划清了一条边界：这台机器在 boost OPP 上 `cpuinfo_cur_freq` 仍报 4032000 kHz，那是 `scmi_dvfs_freq_get()` 问固件当前性能等级的另一条路径，内核侧没有 clamp，本系列不处理。

## Maintainer 意见与讨论焦点

本日无 review 意见，因此没有真实的争议记录。以下是结合主线源码对该系列值得提问之处的整理（均为我方阅读，不是邮件内容）：

- **与 CPPC/ACPI 路径的交互值得先问清**。主线 `register_cpufreq_notifier()` 在 `!acpi_disabled` 时直接返回 `-EINVAL`，即 `init_cpu_capacity_callback()` 这条锁存路径只在 DT 系统上跑；ACPI arm64 的 `capacity_freq_ref` 来自 `topology_init_cpu_capacity_cppc()`，值是 `cppc_perf_to_khz(caps, raw_capacity[cpu])`（`raw_capacity` 取自 `highest_perf`，本身就含 boost）。而 patch 2 的 hook 是无条件的，第一次 boost 切换就会把它改写成 `policy->cpuinfo.max_freq`。`cppc_cpufreq_set_boost()` 在 boost 关时用的正是 `nominal_perf`，所以语义上大概是对的方向，但「两条来源不同的 ref 是否总是一致」需要作者或 cppc 维护者确认。
- **`cpu_capacity` 不会跟着刷新**。主线 `topology_normalize_cpu_scale()` 用 `raw_capacity * capacity_freq_ref` 归一化静态 capacity，且只在 boot 期跑一次；ref 变成运行时可改之后，capacity 与 ref 的一致性由谁保证，邮件里没有讨论。
- **并发与锁**。`topology_update_freq_ref()` 直接写 `per_cpu(capacity_freq_ref, cpu)`，其他 CPU 上的 `arch_scale_freq_ref()` 读者（cpufreq core 在 `cpufreq_freq_transition_end()`/`fast_switch` 里就把它当 max 传给 `arch_set_freq_scale()`）没有任何同步，是否需要在意。
- **流程层面**：作为 bug 修复没有 `Fixes` 标签，且 `policy_set_boost()` 开头是 `if (policy->boost_enabled == enable) return 0;`（只在真正变化时才更新 ref），这两个点都可能被维护者挑。

## 合入评估

`likelihood=medium`。有利因素：patch 1 是无争议的纯 bug 修复（溢出条件明确、可独立成立），patch 2 有完整的钉频实测数据支撑、改动形态也克制（抽函数 + 单点 hook，没有引入新状态）。卡点：本日零 review，而 patch 2 同时改 `drivers/cpufreq/cpufreq.c` 与 `drivers/base/arch_topology.c`，需要 cpufreq 与 base/arch_topology（arm64 侧）两边都认可；arm64 AMU/FIE 与 capacity 语义的相关维护者都没出现。按性质它应进 `tip:sched` 或 cpufreq 树的 `next`，而非 fixes 流（无 `Fixes`、且现象只在 >4.19 GHz 的新硬件上出现）。可期望的结局是：patch 1 被要求补 `Fixes` 后单独收走，patch 2 因缺少受影响机型而慢热。

## 效果评估

数据全部来自作者在 Lenovo Yoga Slim 7x Gen 11（Glymur，持续 4032000 kHz / boost 4723200 kHz）上的实测：把 policy 钉在单个 OPP 上、在其中一个 CPU 跑固定负载计时。

| 钉住的 OPP | 计时 | `cpuinfo_avg_freq` |
| --- | --- | --- |
| 4032000 kHz | 2.011 s | 4031325（偏低 0.02%） |
| 4723200 kHz | 1.726 s | 524283（修复前） |
| 4723200 kHz | 1.726 s | 4032000（仅 patch 1） |
| 4723200 kHz | 1.726 s | 4718587（两个补丁，偏低 0.10%） |

三行对照恰好证明这是两个独立且互相掩盖的问题：修复前是回绕出的荒谬值 524283；只修溢出后数字不再离谱但被非 boost 的 ref 钉在 4032000；两个都修才报出 4718587。作者同时用计时比 2.011/1.726 = 1.165 对照频率比 4723200/4032000 = 1.171，说明硬件行为自始至终正确，被修的是内核的观察。2/2 正文里另给了一组同结论的数字：CPU 实际跑 4723200 时 `cpuinfo_avg_freq` 读到 4032000，固定负载 1.72 s 完成而不是该频率应有的 2.01 s。调度器侧（util 低估幅度、EAS/负载均衡收益）没有量化数据。

## 我可以参与的点

- **arch 对照（最省力的实质贡献）**：我按本地主线源码核对过，x86 这两个问题都不成立——`arch/x86/kernel/cpu/aperfmperf.c` 的 `arch_freq_get_on_cpu()` 是 `div64_u64((cpu_khz * acnt), mcnt)`，全程 u64 且参考量不是 `capacity_freq_ref`；x86 的 FI 参考是 `arch_max_freq_ratio`，由 `turbo_freq`/`base_freq` 算出（注释里明确写了 freq_max 若小于 1C turbo ratio 就会 `>1` 而被 clip 到 1），即天生含 boost。反过来，`riscv`/`arm` 也通过 `topology_get_freq_ref` 走同一份 `capacity_freq_ref`，但 `arch_freq_get_on_cpu()` 只有 arm64 与 x86 提供（其余是 `drivers/cpufreq/cpufreq.c` 里的 `__weak` 版本），所以 patch 1 的影响面其实只在 arm64。这条边界可以直接回贴给作者，帮他把 patch 1 的标题与影响面写准。
- **在自己机器上复现 patch 2**：任何 boost 默认关闭的 arm64 平台（DT + 带 `CPUFREQ_BOOST_FREQ` 表项的驱动，或 cppc_cpufreq）都能验——boot 后确认 `capacity_freq_ref` 是否等于持续最大频率、打开 boost 后 `cpuinfo_avg_freq` 是否被钉住不动。这是该系列目前最缺的外部证据。
- **替维护者问 CPPC 那一问**：ACPI arm64 机器上 ref 来自 `cppc_perf_to_khz(highest_perf)` 而非 cpufreq notifier，补丁的无条件 hook 会改写它；如果有 CPPC 机器，跑一次 boost 开关前后 `cpu_capacity`、`arch_max_freq_scale` 与 util 采样的对照，比任何评论都有说服力。
- 提醒性质的两条流程建议：patch 1 属明确的 bug 修复，值得补 `Fixes` 以便 stable 回收；另外缓存里没有邮件头，是否已 CC 全 cpufreq 与 `drivers/base/arch_topology` 侧维护者无法核对，若 v2 仍只发在少数人身上，这类跨两个子系统的小系列很容易沉底。

## 参考链接

- v1 cover letter（含实测表与顺序说明）: https://lore.kernel.org/all/cover.1788712186.git.okerixx@gmail.com/
- v1 2/2 `cpufreq: update capacity_freq_ref when the boost state changes`: https://lore.kernel.org/all/44b381bd07c299a3551037e57fdd5fa9f272dc25.1788712186.git.okerixx@gmail.com/
- v1 1/2 `arm64: topology: fix arch_freq_get_on_cpu() overflow above 4.19 GHz`: 本批缓存中缺该邮件，未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
- 相关：[[sched-20260902-008]]
