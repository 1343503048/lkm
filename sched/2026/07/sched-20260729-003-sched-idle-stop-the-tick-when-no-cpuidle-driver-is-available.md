---
id: sched-20260729-003
date: 2026-07-29
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: "<0b9b9c3d-8ba0-4329-9504-b9d33c627649@arm.com>"
lore_url: "https://lore.kernel.org/r/0b9b9c3d-8ba0-4329-9504-b9d33c627649@arm.com"
authors: [Christian Loehle, Zhan Xusheng]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<0b9b9c3d-8ba0-4329-9504-b9d33c627649@arm.com>"
    date: 2026-07-29
    summary: "无 cpuidle driver 路径恢复无条件 tick_nohz_idle_stop_tick()，修复 f4c31b07b136 引入的 sysbench 回退；单 idle state 路径保留 got_tick 启发式。"
    review_outcome: "v1 刚发出；同日 Zhan Xusheng 在 REGRESSION 线程给出了回退机理分析，与修复方向一致。"
upstream_commit: null
fixes_commit: "f4c31b07b136"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "作者自己仍存疑：'I'd still be curious about why this happens here'——机理确认可能影响最终方案形态"
  next_action: "Oracle 报告方复测确认恢复；社区确认 Zhan 的机理分析后合入"
contribution_opportunities:
  - kind: testing
    description: "在无 cpuidle driver 的 VM（如 OCI 小规格、QEMU 裸 halt）上复测 sysbench threads，验证补丁恢复性能，回帖测试数据"
  - kind: discussion
    description: "作者明确表示对回退机理仍有疑问，Zhan 的 got_tick/hypervisor 分析尚待确认，可补充不同 HZ/架构的对比数据支持或修正该分析"
generated_at: "2026-07-30T09:30:00"
source_email_count: 2
related_articles: []
tags: [idle, nohz, regression]
---

## TL;DR

f4c31b07b136 让"无 cpuidle driver"路径也走 got_tick 启发式，导致 Oracle 在 OCI 小规格 VM 上 sysbench 回退最多 -29%；Christian Loehle（ARM）发出单行修复恢复无条件停 tick，Zhan Xusheng 同日给出机理分析。影响虚拟化场景明显，值得测试参与。

## 背景与问题

Commit f4c31b07b136 ("sched: idle: Consolidate the handling of two special cases") 把无 cpuidle driver 的特殊路径合并进 tick 唤醒启发式（`idle_call_stop_or_retain_tick(stop_tick)`）。Oracle 的 Joseph Salisbury 报告：OCI 小规格 VM（无 cpuidle driver）上 sysbench threads 明显回退，revert 后恢复。

Zhan Xusheng 的分析指出机理：`do_idle()` 每个 idle episode 开头把 `got_tick` 重置为 false，第一次迭代必然走 retain 分支——旧代码在此路径是无条件停 tick 的。于是 guest 每个 idle episode 开头都留着周期 tick：

> "a guest that leaves its tick running keeps a ~1/HZ timer pending, so the host sees an imminent timer and keeps waking/scheduling the vCPU instead of letting it idle."

数据形状与之吻合：x86 HZ=1000 回退 -29%，arm HZ=250 回退 -10%（tick 越密集干扰越大）。

## 技术方案

单行修复：`cpuidle_not_available()` 路径把 `idle_call_stop_or_retain_tick(stop_tick)` 换回 `tick_nohz_idle_stop_tick()`。理由是裸 halt 路径没有 governor/state 选择，保留 tick 没有任何收益，无条件停 tick 严格更优。单 idle state 场景仍保留启发式。带 `Fixes:` 与 `Reported-by:` 标签。

## 版本演进与当前进展

v1 刚发出，暂无 review 意见。作者附言 "I'd still be curious about why this happens here"——修复先行，机理仍开放；Zhan 的分析正是回应这一疑问。

## Maintainer 意见与讨论焦点

尚无维护者回复。焦点问题：Zhan 的 hypervisor 干扰解释是否成立（他提供了 forcing false/true 的对照实验：强制 retain 仍回退、强制 stop 恢复，逻辑自洽但尚无维护者背书）。

## 合入评估

likelihood: high。带 Fixes 标签的回退修复、影响真实生产环境（OCI）、改动一行且语义回到旧行为，通常会较快进入 tip/sched/urgent。风险点仅在于如果社区想"彻底理解机理"再合入，可能多一轮讨论。

## 效果评估

- 回退幅度：sysbench threads x86/HZ=1000 约 -29%，arm/HZ=250 约 -10%（Zhan 提供）
- revert 与本补丁均可恢复性能（Oracle 与 Zhan 的对照实验）

## 我可以参与的点

- 复现门槛低：任何无 cpuidle driver 的 KVM guest 都可验证（`cpuidle_not_available` 路径），跑 sysbench threads 对比补丁前后并回帖——修复类补丁的 Tested-by 很有价值。
- 机理讨论开放中：可用 ftrace/trace-cmd 抓 guest tick 行为 + host 侧 vCPU 唤醒次数，为 Zhan 的分析补硬数据。

## 参考链接

- 修复补丁: https://lore.kernel.org/r/0b9b9c3d-8ba0-4329-9504-b9d33c627649@arm.com
- 回退报告（Closes）: https://lore.kernel.org/all/096b42fa-107f-450d-b3b1-03bcad3f1e04@oracle.com/
- 机理分析: https://lore.kernel.org/r/20260729022930.318742-1-zhanxusheng1024@gmail.com
