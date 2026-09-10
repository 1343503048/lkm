# sched/fair: Only apply cpufreq pressure where frequency is invariant

## TL;DR
本文为增量更新，完整背景见 related_articles 中的 sched-20260909-012 / sched-20260908-008。讨论从「谁来发 cpufreq 侧补丁」推进到语义层：Vincent Guittot 给出硬约束——压力参考频率必须在 boost 开/关下保持固定；Jianyong Wu 随即指出 intel_pstate（可能还有 amd-pstate）下 cpuinfo.max_freq 随 boost 状态变化（4GHz vs 3GHz 例子），现有 __resolve_freq 方案救不了无频率表的驱动，并提出以「最大可持续频率」为固定参考的新方向，遗留问题是该频率从哪里取。

## 背景与问题
原补丁（Jianyong Wu，08-21）针对非频率不变（freq invariance 不成立）平台上 cpufreq 压力计算失真的问题，sched 侧用 arch_scale_freq_invariant() 门控。09-08 起讨论转向 Prateek Nayak 提出的 cpufreq 侧方案（__resolve_freq() 上界不越过 policy 可给频率），09-09 Hongyan Xia 建议把最高可达 OPP 缓存进 policy 对象、在 cpufreq_policy_online() 时更新，但补丁始终无人正式发出。

## 技术方案
本日新增的设计输入（均为讨论，无代码）：
- Vincent 的语义约束："As long as the reference frequency used in cpufreq_update_pressure remains fixed whatever boost is enabled or not this is ok. We don't want the pressure to change when boost is enabled or disabled, only when policy->max changes."——压力只能随 policy->max 变化，不能随 boost 状态跳变。
- Jianyong 的反例推演：设 boost 频率 4GHz、最大可持续频率 3GHz、policy 上限 2GHz。boost 开启时 cpuinfo.max_freq=4GHz，关闭时=3GHz；以 cpuinfo.max_freq 为参考会得到 1-2/4 与 1-2/3 两个不同压力值，尽管 policy->max 没变。且 intel_pstate 没有频率表，__resolve_freq() 原样返回 cpuinfo.max_freq，无法解决——这不是新补丁引入的问题，现有 cpuinfo.max_freq 回退路径本来就有。
- Jianyong 的提议：用一个排除 boost、且不随 boost 开关变化的固定 max_sustainable_freq 作参考；policy->max 继续作为当前有效上限。语义自检：boost 开启未限频时 policy->max > max_sustainable_freq、关闭未限频时相等、限频时小于——现有 max_freq <= capped_freq 判断在两种未限频情形都给零压力，限频低于可持续频率时压力与 boost 状态无关。遗留问题（作者原话）："the next question might be how to obtain the max_sustainable_freq."

## 版本演进与当前进展
current_version: v1（sched 侧原补丁，作者已放弃、转向 cpufreq 侧方案）。cpufreq 侧补丁仍未发出；09-09 共识（policy 对象缓存最高可达 OPP）现在需要叠加「boost 不变参考频率」的新约束，方案实际上要重新设计——单纯缓存 __resolve_freq() 上界不满足 Vincent 的约束（intel_pstate 场景）。Prateek 的「下周初兜底发版」时点临近，但发出前需先回答 max_sustainable_freq 的获取问题。

## Maintainer 意见与讨论焦点
- Vincent Guittot（09-10）：给出 boost 不变性硬约束，认可「参考频率固定即可」的方向。
- Jianyong Wu（09-10，原作者）：完成 intel_pstate/amd-pstate 的语义推演，提出 max_sustainable_freq 参考方案并公开征询「是否符合预期语义」——截至当天结束无人回复该问题。
- 关联动态：同日出现 okerixx 的 cpufreq 侧系列 v2/v3（含 "cpufreq: update capacity_freq_ref when the boost state changes"），处理的正是 boost 状态与容量参考频率的联动；该系列属 drivers/cpufreq，按本报收录边界排除，但两条线的问题域重叠，值得对照阅读。
- 未决焦点：max_sustainable_freq 的数据来源（驱动回调？policy 缓存？ACPI/固件表？）无人给出。

## 合入评估
likelihood: medium（语义方向在收敛，但可评审的补丁仍未出现，且新约束推翻了 09-09 方案的完备性）。blocking_issues：cpufreq 侧补丁未发出；max_sustainable_freq 获取机制无答案；intel_pstate/amd-pstate 这类无频率表驱动的支持路径未定；改动落 drivers/cpufreq/ 需 cpufreq 维护者 ack。next_action：先在线程回答 Jianyong 的语义确认问题，确定参考频率来源后由作者或 Prateek 发出 cpufreq 侧补丁。

## 效果评估
本日无 benchmark。既有问题数据（x86 acpi-cpufreq 机器上无真实限频但容量小于 1024 的现象）见 related_articles。Jianyong 的 4GHz/3GHz/2GHz 推演为语义分析，非实测。

## 我可以参与的点
- 回答「max_sustainable_freq 从哪里取」：梳理 intel_pstate（HWP  nominal perf）、amd-pstate（highest/non-boost perf）、acpi-cpufreq（_PSS 表去 boost 项）各自能提供的「不含 boost 的最大频率」接口，汇总成线程回复——这是当前明确无人认领的关键缺口（discussion）。
- 在 intel_pstate passive/active 模式机器上实测 boost 开/关切换时 arch_scale_freq_ref()/capacity 的跳变，给 Vincent 的约束提供量化证据（testing）。
- 共识形成后实现 cpufreq 侧补丁（含 policy 缓存 + boost 不变参考），Prateek 的兜底时点在下周初，窗口有限（new_patch）。

## 参考链接
- lore thread（原补丁根）: https://lore.kernel.org/all/20260821073927.455475-1-wujianyong@hygon.cn/
- Vincent 的 boost 不变性约束: https://lore.kernel.org/all/CAKfTPtBji8dkr5ixhtZjkyrWLA68TF-KHLrNYWoewPWLyuUd4A@mail.gmail.com/
- Jianyong 的 intel_pstate 推演与新提议: https://lore.kernel.org/all/SI2PR04MB4931989689C248FFE72602B3E3BF2@SI2PR04MB4931.apcprd04.prod.outlook.com/

---
id: sched-20260910-009
date: 2026-09-10
subject: "sched/fair: Only apply cpufreq pressure where frequency is invariant"
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: "<20260821073927.455475-1-wujianyong@hygon.cn>"
lore_url: "https://lore.kernel.org/all/CAKfTPtBji8dkr5ixhtZjkyrWLA68TF-KHLrNYWoewPWLyuUd4A@mail.gmail.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: "2026-09-11T10:35:00"
authors:
  - "Jianyong Wu"
maintainers_involved:
  - "Vincent Guittot"
patch_series:
  - version: v1
    msgid: "<20260821073927.455475-1-wujianyong@hygon.cn>"
    date: "2026-08-21"
    summary: "sched 侧门控方案已被作者放弃，转向 cpufreq 侧 __resolve_freq + policy 缓存方案；该补丁至今未发出。"
    review_outcome: "09-10 Vincent 给出参考频率 boost 不变性硬约束；Jianyong 指出 intel_pstate 无频率表导致 __resolve_freq 方案失效，提出 max_sustainable_freq 固定参考并征询语义确认，当天无人回复。"
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "cpufreq 侧补丁仍未发出，无可评审对象"
    - "max_sustainable_freq 的获取机制无人回答，09-09 的 policy 缓存共识不满足 boost 不变性约束（intel_pstate 场景）"
    - "改动落 drivers/cpufreq/，需 cpufreq 维护者 ack"
  next_action: "先确认 Jianyong 提议的语义，再确定参考频率来源，由作者或 Prateek（其兜底时点为下周初）发出 cpufreq 侧补丁"
contribution_opportunities:
  - kind: discussion
    description: "梳理 intel_pstate/amd-pstate/acpi-cpufreq 各自「不含 boost 的最大频率」接口并回复线程——max_sustainable_freq 来源是当前无人认领的关键缺口"
  - kind: testing
    description: "在 intel_pstate 机器实测 boost 开/关切换时频率参考与容量的跳变，为 Vincent 的约束提供量化证据"
  - kind: new_patch
    description: "共识形成后实现 cpufreq 侧补丁（policy 缓存 + boost 不变参考），赶在 Prateek 下周初兜底之前"
source_email_count: 2
related_articles:
  - "sched-20260909-012"
  - "sched-20260908-008"
  - "sched-20260907-006"
tags:
  - cpufreq
  - cfs
---
