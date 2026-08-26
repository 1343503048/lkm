# sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff

## TL;DR

steal_governor 系列推进到 **v11**（12 个 patch），引入 "preferred CPU" 机制：在虚拟化环境中，当某些 vCPU 的 steal time 显著高于其他 vCPU 时，调度器优先在低 steal time 的 CPU 上运行任务，减少因 vCPU 被抢占导致的锁持有者抢占、TLB/cache 失效等代价。作者明确表示系列已收敛，请求 Peter/Ingo 考虑在 7.3-rc 期间纳入 sched/core，目标 7.4 合入。

## 背景与问题

在虚拟化环境（KVM）中，vCPU 被 hypervisor 抢占（steal time）不仅损失 CPU 时间，还会导致：
- **锁持有者被抢占**（lock-holder preemption）：持锁的 vCPU 被暂停，所有等待者空转
- **TLB/cache 失效**：被抢占后恢复时缓存状态已丢失
- **数据库负载特别敏感**：OLTP/OLAP 混合负载中，上述代价尤为突出

现有的 steal_governor 已提供基本的 steal time 感知，但缺乏"preferred CPU"概念——即标记哪些 CPU 的 steal time 较低、适合优先调度。

## 技术方案

v11 的核心设计：
1. **cpu_preferred_mask**：每个调度域维护一个 cpumask，标记 steal time 低于阈值的 CPU
2. **steal-driven vCPU backoff**：高 steal time 的 CPU 上的任务主动让出，迁移到低 steal time 的 CPU
3. **12 个 patch 覆盖**：cputime helper（01/12）、文档（02/12）、fair.c 负载均衡（06/12）、core.c 选核逻辑（05/12, 07/12）、debug 统计（08/12）等

关键取舍：
- 机制保持**架构无关**（不依赖特定虚拟化扩展），后续计划增加 arch-specific 接口
- 对纯 CPU-time 负载可能略有回退（作者如实说明）
- PowerPC 上已验证性能提升，s390/x86 在 KVM 场景也有测试数据

## 版本演进与当前进展

v11 是当前最新版本，作者 Shrikanth Hegde 在 cover letter 中明确表示：
> "I believe the series has now converged and is ready for merge consideration."

请求在 7.3-rc 期间进入 tip tree，目标 7.4 合入。后续计划：
- 设计 arch-specific 接口以获取额外性能收益
- 构建测试框架

## Maintainer 意见与讨论焦点

- 作者直接 @Peter Zijlstra 和 @Ingo Molnar 请求合入考虑
- 系列经过多轮社区反馈迭代（从 arch-specific RFC 演进为通用机制）
- 当前无明确 NAK，但 Peter/Ingo 尚未在邮件中明确回应（截至缓存邮件范围）

## 合入评估

- **likelihood: high** — 作者明确表示请求合入考虑，系列已迭代到 v11，实现刻意保持简单
- **blocking_issues**: 无明确阻塞，等待 Peter/Ingo review
- **next_action**: 等待 maintainer review 和 ack；merge window 期间发出可能需要 rebase 到 7.3-rc1

## 效果评估

作者声称在 PowerPC 虚拟化环境中的数据库负载上有性能提升，s390 和 x86 KVM 也有早期测试数据。但具体 benchmark 数字未在本次缓存的邮件正文中出现。作者承认对纯 CPU-time 负载可能略有回退。

## 我可以参与的点

- **在 x86/s390 KVM 环境跑测试**：作者提到 x86 测试是"earlier testing"，如果能在主流 KVM 环境补充最新 benchmark 数据并回帖，有助于推进合入
- **review 文档 patch（02/12）**：Preferred CPU 概念的文档化需要准确反映设计意图，可以帮忙审阅

## 参考链接

- lore thread: https://lore.kernel.org/r/20260825045053.57937-1-sshegde@linux.ibm.com
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260825-001
date: 2026-08-25
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260825045053.57937-1-sshegde@linux.ibm.com>"
lore_url: "https://lore.kernel.org/r/20260825045053.57937-1-sshegde@linux.ibm.com"
authors: [Shrikanth Hegde]
maintainers_involved: [Peter Zijlstra, Ingo Molnar]
current_version: v11
patch_series:
  - version: v11
    msgid: "<20260825045053.57937-1-sshegde@linux.ibm.com>"
    date: 2026-08-25
    summary: "12-patch 系列：引入 preferred CPU 机制 + steal-driven vCPU backoff"
    review_outcome: "作者请求合入考虑，等待 Peter/Ingo review"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 Peter Zijlstra / Ingo Molnar review，可能需要在 7.3-rc1 上 rebase"
contribution_opportunities:
  - kind: testing
    description: "在 x86/s390 KVM 环境补充 benchmark 数据并回帖到邮件列表"
  - kind: review
    description: "审阅文档 patch（02/12 Preferred CPU 概念文档化）"
generated_at: "2026-08-27T10:00:00"
source_email_count: 7
related_articles: []
tags: [load_balance, topology, perf]
---
