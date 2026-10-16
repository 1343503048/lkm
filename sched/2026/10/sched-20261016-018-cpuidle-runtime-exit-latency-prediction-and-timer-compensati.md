# cpuidle: runtime exit latency prediction and timer compensation

## TL;DR
Cong Zhang（高通）发 RFC，提出在内核运行时测量并预测 CPU idle exit latency，并用该预测来「补偿」hrtimer 到期与回调真正执行之间的延迟（hrtimer rooster 方案），取代当前来自设备树的静态 worst-case 延迟。想法源自 2026 LPC 议题。Christian Loehle 回帖抛出一串关键问题（与硬件 C-state pre-wake 的共存、cluster-off 双峰延迟、真实收益与功耗影响、采样方法论、是否该动 QoS 约束）。

## 背景与问题
hrtimer 回调可能晚于其「到期时间」才执行：到期只意味着 IRQ 会在对应时刻产生，回调还要等唤醒、恢复与其余 timer IRQ 处理路径。CPU idle 时 hrtimer 到期，从收到 IRQ 到内核开始执行的这段时间被作者称为「idle exit latency」。内核目前用设备树里的静态 idle exit latency（描述 worst case），不反映当前条件下的真实延迟；更准确的估计能减少误判与功耗影响。作者主张在运行时动态测量并预测。

## 技术方案
RFC 方向（无完整代码进本批缓存）：内核运行时测量/预测 idle exit latency，并据此减少「期望 hrtimer 到期时间」与「回调实际执行」之间的延迟（作者称「hrtimer rooster timer solution」）。想法在 2026 LPC 上已宣讲（lpc.events/event/20/contributions/2595/）。

## 版本演进与当前进展
RFC 首版（<2a5dd3fd-a03f-4ffb-827c-2937bf664c75@oss.qualcomm.com>），本批含 Christian Loehle 的回复，无代码审阅。

## Maintainer 意见与讨论焦点
Christian Loehle（ARM，cpuidle/pm 领域活跃 reviewer）抛出的关键问题：
1. 与现有硬件缓解（如 Intel C-state pre-wake）如何共存；
2. 没有 OS-coordinated cluster state 的平台如何（platform-coordinated cluster-off 会看到两档延迟：真 cluster-off vs 实际只是 CPU-off）；
3. 是否有真实 workload 关心、性能提升与功耗影响如何、尤其相对现有 latency 约束；
4. 采样方法论（缓解生效时还采不采样、如何区分观测到的 exit latency 与预测误差、首个醒来的 CPU 非 cluster 唤醒发起者、因缓解过早唤醒会否再次进 idle 循环影响 governor）；
5. 若「取代静态 idle exit latency」也涵盖 QoS 约束，则不应做——那本就有意取 worst-case。

## 合入评估
*likelihood=unknown*。早期 RFC，无维护者明确表态，方向面临多个待答问题。*blocking_issues*：硬件缓解共存、cluster 语义、真实收益与功耗数据、采样方法论、是否动 QoS 约束均未答。*next_action*：作者回应 Christian 的清单并给出代码与数据。

## 效果评估
无量化数据；作者仅描述方向（减少到期与执行间的延迟），未见测量。

## 我可以参与的点
- *discussion*：就「是否应取代静态 idle exit latency 的 QoS 约束语义」发表看法；或对采样方法论（如何在预测与实测间区分误差）提供意见。

## 参考链接
- RFC：https://lore.kernel.org/all/2a5dd3fd-a03f-4ffb-827c-2937bf664c75@oss.qualcomm.com/
- Christian 的回复：https://lore.kernel.org/all/81963d52-0d49-4fb5-b9c8-e1199999aeb4@arm.com/

---
id: sched-20261016-018
date: 2026-10-16
subject: "cpuidle: runtime exit latency prediction and timer compensation"
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<2a5dd3fd-a03f-4ffb-827c-2937bf664c75@oss.qualcomm.com>"
lore_url: "https://lore.kernel.org/all/2a5dd3fd-a03f-4ffb-827c-2937bf664c75@oss.qualcomm.com/"
authors: ["Cong Zhang"]
maintainers_involved: ["Christian Loehle"]
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["硬件缓解共存、cluster 语义、收益数据、采样方法论、是否动 QoS 约束均未答"]
  next_action: "作者回应 Christian 的清单并给出代码与数据"
contribution_opportunities:
  - kind: discussion
    description: "对是否取代静态 idle exit latency 的 QoS 约束语义、采样方法论提供意见"
generated_at: "2026-10-17T01:30:00"
source_email_count: 2
related_articles: []
tags: [idle, cpufreq]
---