---
id: sched-20260729-008
date: 2026-07-29
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260729061549.13419-1-tianyaxiong@kylinos.cn>"
lore_url: "https://lore.kernel.org/lkml/20260729061549.13419-1-tianyaxiong@kylinos.cn"
authors: [Yaxiong Tian]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: "<20260729061549.13419-1-tianyaxiong@kylinos.cn>"
    date: 2026-07-29
    summary: "6 patch：QoS notifier 订阅 + per-CPU resume QoS 失效 + 聚合值按 CPU 缓存 + 2 个 selftest；v1 改动点未在本日缓存邮件中体现"
    review_outcome: "v2 刚发出，暂无 review 意见"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "尚无任何 reviewer 回复，cpuidle 维护者（Rafael Wysocki）未表态"
    - "缓存失效路径（QoS notifier）与现有 QoS 更新语义的正确性需要 review 确认"
  next_action: "等待 linux-pm/cpuidle 维护者 review；作者可考虑补充多平台数据"
contribution_opportunities:
  - kind: testing
    description: "在 x86/arm64 机器上跑系列自带的两个 cpuidle selftest，并用 ftrace function_graph 复测 menu_select 中 cpuidle_governor_latency_req 占比，把数据回帖"
  - kind: review
    description: "审查 QoS notifier 失效路径是否覆盖所有约束更新入口（全局 CPU latency、wakeup latency、per-CPU resume latency），有无缓存过期窗口"
generated_at: "2026-07-30T11:20:00"
source_email_count: 6
related_articles: []
tags: [idle, perf]
---

## TL;DR
Yaxiong Tian（麒麟）的 v2 系列把 cpuidle governor 的 latency QoS 约束聚合值按 CPU 缓存、经 QoS notifier 失效，将 cpuidle_governor_latency_req() 在 menu_select() 中的耗时占比从 19.9%（~1.9us/次）降到 4.2%（~0.3us/次）。idle 热路径优化方向合理，但暂无任何社区回复，需持续观察。

## 背景与问题
cpuidle_governor_latency_req() 在每次 idle 状态选择时都会执行，它反复调用 get_cpu_device()、pm_qos_read_value()、cpu_latency_qos_limit()、cpu_wakeup_latency_qos_limit() 来聚合 per-CPU resume latency 与全局 CPU/wakeup latency QoS 限制。作者用 ftrace function_graph 量化：在 menu governor 下该函数占 menu_select() 总耗时的 19.93%（16718 次调用共 ~32ms），单次约 1.9us——对每秒可能进出 idle 数千次的 CPU 来说是可观的热路径开销。QoS 约束本身变化频率远低于 idle 选择频率，重复聚合是浪费。

## 技术方案
6 个 patch（本日缓存中有 cover + patch 2-6，patch 1/6 未捕获到，其内容未知）：
- patch 2：cpuidle 订阅全局 latency QoS notifier，约束变化时使缓存失效；
- patch 3：per-CPU resume latency QoS 变化时按 generation 失效对应 CPU 的缓存；
- patch 4：核心——把聚合后的 governor latency 约束按 CPU 缓存，idle 路径只在缓存失效时才重新聚合；
- patch 5/6：新增两个 selftest（latency_req QoS idle-state 选择测试、idle-state disable 测试）。
设计要点是"读多写少"场景的经典缓存+失效模式：热路径读缓存，QoS 更新（慢路径）通过 notifier 打 generation 标记。

## 版本演进与当前进展
当前为 v2（2026-07-29 发出）。v1 及 v1→v2 的改动说明未出现在本日邮件缓存中，无法给出演进细节。v2 发出当天无人回复。

## Maintainer 意见与讨论焦点
暂无任何 review 意见。潜在关注点（个人判断，非邮件内容）：QoS notifier 失效是否覆盖所有约束更新入口、缓存与 QoS 更新之间是否存在短暂过期窗口（idle 选择读到旧约束的后果）、以及该复杂度换 ~1.6us/次是否值得——这些都需要 Rafael Wysocki 等 cpuidle 维护者表态。

## 合入评估
likelihood: unknown。方向（削减 idle 热路径重复计算）有先例可循，且附带 selftest 是加分项；但系列无人回复、作者非社区常客、cpuidle 对正确性（错选 idle state 影响延迟保证）敏感，在维护者表态前无法判断。若 review 中确认失效路径无漏洞，前景中性偏乐观。

## 效果评估
作者给出 ftrace function_graph 前后对比：cpuidle_governor_latency_req 占 menu_select 的比例 19.93% → 约 4.2%，单次调用 ~1.9us → ~0.3us，约 6 倍降低（作者实测数据，测试平台未在 cover letter 中明确说明）。未给出端到端功耗/唤醒延迟收益数据。

## 我可以参与的点
- 复测：在手头 x86/arm64 平台用 ftrace function_graph 复现 menu_select 剖析，验证优化幅度并回帖——该系列目前零回复，第一个独立测试数据对推进很有价值。
- review 失效路径完整性：排查是否所有 QoS 约束更新入口都会触发缓存失效，是否存在读旧值窗口及其影响。

## 参考链接
- lore thread: https://lore.kernel.org/lkml/20260729061549.13419-1-tianyaxiong@kylinos.cn
- tip-bot commit: 未获取到
