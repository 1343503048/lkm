# arm64/cpufreq: report and track frequencies above 4.19 GHz

## TL;DR
增量更新：Oleg Keri 推出 v4，针对 Snapdragon X2 Elite（boost 4723200 kHz > 4194304 kHz）修复 arm64 频率上报与跟踪的两处溢出/失真：arch_freq_get_on_cpu() 的 u64 乘积被截断为 unsigned int 导致回绕，以及 capacity_freq_ref 不包含 boost 频率导致调度器无法区分 boost 与持续频率。Dietmar Eggemann 就 v3 的 capacity_freq_ref 讨论补充了 cpufreq pressure 的机制与实测数据。

## 背景与问题
背景见 sched-20260907-003：首个 boost OPP 超 4194304 kHz 的 arm64 笔记本（Glymur），两处独立问题都让内核误判 boost 后的 CPU 比实际更慢。v4 明确了两枚补丁的因果顺序。

## 技术方案
- patch 1：修 arch_freq_get_on_cpu() 溢出——频率 scale 与参考频率的 u64 乘积在右移前被截断为 unsigned int，任何参考频率超 2^32/SCHED_CAPACITY_SCALE（4194304 kHz）即回绕。
- patch 2：让 capacity_freq_ref 包含 boost 频率。频率表驱动在 CPUFREQ_CREATE_POLICY 时从 policy->cpuinfo.max_freq 锁定，该值在 boost 关闭时不含 boost 条目，导致"boost 关闭启动"的机器永远把持续最大值当参考；以 boost 最大值为参考后，禁用 boost 反而以 cpufreq pressure 表达，与 CPPC 系统的 highest_perf 行为一致。
- 顺序约束：patch 2 会把参考推到 4194304 kHz 以上，因此 patch 1 必须先落地。

## 版本演进与当前进展
- v1–v3：见 sched-20260907-003（v1 首版）及此前演进。
- v3（09-10）：patch 2 命名为"cpufreq: update capacity_freq_ref when the boost state changes"。
- v4（09-17，`<20260917125112.2283-1-okerixx@gmail.com>`）：重命名并重排为上述两枚。

## Maintainer 意见与讨论焦点
- **Dietmar Eggemann（回 v3 patch 2）**：展开 cpufreq pressure 机制——cpu_capacity 基于 highest_perf 计算，cpufreq_pressure = Cmax*(1-fcapped-fmax)；给出 RADXA Orion 06 实测：boost=0 时 pressure=173，boost=1 后 pressure=0，说明把 boost 最大值纳入 capacity_freq_ref 后压力归一化正确。这是对 patch 2 设计取向的支持性论证。
- 无 NAK；方向获资深成员认可。

## 合入评估
*likelihood=medium*。溢出修复路径清晰、获 Dietmar 机制层面支持；但 cpufreq/arm64 维护者尚未正式 Ack，且 capacity_freq_ref 语义变更需确认与 CPPC 路径的一致性。*blocking_issues*：缺 cpufreq/arm64 维护者 Ack；patch 2 语义变更待确认。*next_action*：等待维护者评审，尤其确认 capacity_freq_ref 语义与两补丁顺序。

## 效果评估
Glymur 上以临时 /proc/schedstat 采样验证；Dietmar 给出 RADXA Orion 06 的 pressure 数字（173 → 0）。属正确性修复，无直接性能提升数据。

## 我可以参与的点
- kind=testing：在其它 boost OPP > 4.19 GHz 的 arm64 设备（scmi-cpufreq/CPPC）上验证频率上报不再回绕。
- kind=review：评估 patch 2 对 CPPC 系统（已用 highest_perf 做参考）是否引入行为变化。

## 参考链接
- lore（v4 cover）: https://lore.kernel.org/all/20260917125112.2283-1-okerixx@gmail.com/

---
id: sched-20260917-014
date: '2026-09-17'
subject: 'arm64/cpufreq: report and track frequencies above 4.19 GHz'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: '<20260917125112.2283-1-okerixx@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20260917125112.2283-1-okerixx@gmail.com/'
authors:
  - 'Oleg Keri'
maintainers_involved:
  - 'Dietmar Eggemann'
current_version: v4
patch_series:
  - version: v4
    msgid: '<20260917125112.2283-1-okerixx@gmail.com>'
    date: '2026-09-17'
    summary: '修 arch_freq_get_on_cpu 溢出 + capacity_freq_ref 纳入 boost 频率'
    review_outcome: 'Dietmar 从 cpufreq pressure 机制角度支持 patch 2 取向'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '缺 cpufreq/arm64 维护者 Ack'
    - 'patch 2 语义变更与 CPPC 路径一致性待确认'
  next_action: '等待维护者评审并确认两补丁顺序'
contribution_opportunities:
  - kind: testing
    description: '在其它 boost > 4.19 GHz 的 arm64 设备验证频率上报'
  - kind: review
    description: '评估 patch 2 对 CPPC 系统是否引入行为变化'
generated_at: '2026-09-18T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260907-003
tags:
  - cpufreq
  - arm64
---