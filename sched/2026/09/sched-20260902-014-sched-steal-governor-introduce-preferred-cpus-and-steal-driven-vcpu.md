# sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff

## TL;DR

steal_governor 已推进到 v12（00/13），9/2 是 v11 05/12 的多方往返。作者自述这套东西已从 arch-specific
RFC 长成「调度机制 + 虚拟化配套」，但 preferred CPU 是否该进入 `is_cpu_allowed()` 这类通用可运行性判断
仍未收口。值得投入跟进的一条线。

## 背景与问题

（本文为增量更新，完整背景见 related_articles 中 08-25 的文章）

steal_governor 系列（v11，引入 preferred CPUs 与 steal 驱动的 vCPU backoff）本期有
新的评审/讨论（Re: UID 73310，对应 v11 05/12 `sched/core: Try to use a preferred CPU
in is_cpu_allowed`）。

## 技术方案

- 延续 08-25 的 v11 系列：在 `is_cpu_allowed()` 中优先使用 preferred CPU、load balance
  仅在 preferred CPUs 间进行等。
- 本期为针对 05/12 等子补丁的评审交流，未见新版本号。

## 版本演进与当前进展

- 当前状态：**under_review / 讨论中**（增量更新，无新版本）。
- 合入可能性 medium（大系列，需多轮评审）。

## Maintainer 意见与讨论焦点

- 9/2 16:33 Shrikanth Hegde 回 `Re: [PATCH v11 05/12] sched/core: Try to use a preferred CPU in
  is_cpu_allowed`（73311），引文链依次是 Dietmar Eggemann → Vincent Guittot → Yury Norov（8/31、9/1 发言）
  ——一条至少 4 方、跨 3 天的分歧线，作者本人在答复三人。
- 封面自我总结："This patch series represents the result of multiple iterations, redesigns and community
  feedback. What started as an arch-specific RFC has evolved into a scheduler mechanism paired with a
  virtua…"（截断）。
- 缓存里看不到任何一方的具体反对理由，也看不到 ack/NAK。
- 版本轨迹 v10（00/12）→ v11（00/12）→ v12（00/13）均有邮件记录，说明意见在被吸收，但补丁数还在增加。

## 合入评估

**中偏低**。卡点：(1) `is_cpu_allowed()` 是所有调度类共用的可运行性判断，往里塞 preferred CPU 概念
的反对意见（Dietmar Eggemann / Vincent Guittot / Yury Norov 三方）未被正面回答；(2) 系列从 12 个扩到
13 个补丁，范围仍在变大。要合入需要给出性能收益数字与对 RT/DL 的影响分析。

## 效果评估

缓存内无可引用的效果数据。v10/v11/v12 的封面按惯例应有 benchmark，但当日缓存未保留正文，
无法确认作者给过什么数字——这点必须查lore 后再评。

## 我可以参与的点

- 这条线最值得投入：在 v12 上针对 05/12 的分歧给量化数据（guest steal% vs 迁移次数、
  `is_cpu_allowed()` 改动对 RT/DL 任务 placement 的影响）。
- 在 KVM guest + 超卖宿主上做一轮 repro，目前线程里没有任何独立测试者。
- 明确 x86 与 arm64 上的行为差异（作者来自 IBM Power、Yury Norov 来自 NVIDIA/arm64），把差异写成表回帖。

## 参考链接

- 08-25 008 steal_governor v11 主文
- 001 Proxy Execution 批合并入（同属 guest/steal 调度方向）

---
id: sched-20260902-014
date: '2026-09-02'
subject: 'sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff'
subsystem: sched
type: feature
status: under_review
severity: medium
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v12
generated_at: null
authors:
- Shrikanth Hegde
- Yury Norov
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: low_medium
  blocking_issues:
  - "is_cpu_allowed() 引入 preferred CPU 的语义争议跨 4 方（Dietmar Eggemann、Vincent Guittot、Yury Norov）未收口"
  - "系列从 12 个补丁扩到 13 个，范围仍在增长"
  - "无独立测试者结果；封面是否有 benchmark 无法从当日缓存确认"
  next_action: "在 v12 上针对 05/12 提供 steal% 与迁移次数的量化数据，并评估对 RT/DL placement 的影响"
contribution_opportunities:
- "在 v12 上量化 is_cpu_allowed() 引入 preferred CPU 后的 steal%、迁移次数与 RT/DL placement 变化"
- "在 KVM guest + 超卖宿主上提供独立 repro 结果，该线程目前无第三方测试"
- "整理 x86 / arm64 / Power 三侧行为差异表回帖，收敛跨 3 天的分歧"
source_email_count: 5
related_articles:
- sched-20260825-008-sched-steal-governor-v11.md
tags:
- sched/core
- sched/fair
- preempt
---
