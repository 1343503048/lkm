# sched_clock: Add option to use absolute time against hardware clock reset

## TL;DR

Feng Tang（阿里）建议给 sched_clock 加一个选项，在硬件计数器复位时改用绝对时间基准。arm64
计时/KVM 维护者 Marc Zyngier 明确表示这个方案名不副实，争议在概念层而非实现。当前状态是被质疑，未被拒。

## 背景与问题

`sched_clock` 在某些平台上基于硬件计数（如 arch timer）。当硬件时钟发生复位（reset）
时，基于相对计数的 sched_clock 会跳变，造成时间回溯/不连续。本期（UID 73297）提出
新增一个选项，使 sched_clock 在硬件时钟复位时改用绝对时间基准，避免跳变。

## 技术方案

- `sched_clock: Add option to use absolute time against hardware clock reset`：引入配置
  选项/机制，在探测到硬件时钟复位时切换到绝对时间模式。
- 配套 Re: 讨论（UID 74455）。

## 版本演进与当前进展

- 当前状态：**under_review**（新补丁）。
- 合入可能性 medium；影响时间基准稳定性，需平台维护者评审。

## Maintainer 意见与讨论焦点

- Marc Zyngier 9/2 23:32 先回（74431），9/3 上午继续追问："The other thing is that your "absolute"
  clock isn't absolute at all. This doesn't consider SW running a…"（缓存中截断）——这是本轮最重的一句反对。
- 参与人还包括 Yao Yuan（阿里）与 Thomas Gleixner（计时维护者），后者在线但未见到折衷方案（缓存中无正文）。
- 作者的问题陈述（73291）："Currently sched_clock shows the relative time to the boot starting of kernel,
  while there could be long firmware start time before it and after the hardware reset." 需求本身是真实的
  （启动可观测性），但改的是所有 sched_clock 消费者的时间语义。无正式 NAK，也未有人附和。

## 合入评估

**低**。要合入必须先回答 Marc 的反驳（所谓 absolute 并不绝对、未考虑软件运行期间），并论证为什么不能在
boot 时间戳 / clocksource 侧解决而必须动 sched_clock 语义；同时需要 Thomas Gleixner 作为计时维护者表态。
目前这三项都缺。

## 效果评估

无数据。线程内没有任何人在真实硬件上验证过「加了选项后时间跳变消失」，只有问题描述。

## 我可以参与的点

- 站在调度侧发言：整理一份「哪些调度代码假设 sched_clock 从 0 起算 / 单调相对 boot」的清单
  （tracing、sched_clock_irqtime、cputime、watchdog、PELT 起始点等），这是对 Marc 质疑最有效的补充。
- 提议替代方案：用 boot 侧的 firmware/absolute 时间戳暴露需求，而不是给 sched_clock 加分支语义。
- 若有相应服务器硬件，可以量化一次「固件长时间启动 + 硬件计数器复位」在 sched_clock 上的实际跳变幅度。

## 参考链接

- 002 sched/core 清理（同属调度核心改动）

---
id: sched-20260902-013
date: '2026-09-02'
subject: 'sched_clock: Add option to use absolute time against hardware clock reset'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Marc Zyngier
- Feng Tang
- Yao Yuan
- Thomas Gleixner
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: low
  blocking_issues:
  - "Marc Zyngier 指出所称 absolute clock 并非绝对，未考虑软件运行期间的推进"
  - "需求属启动可观测性，是否必须改 sched_clock 语义未论证"
  - "计时维护者 Thomas Gleixner 与调度维护者均未表态"
  - "无真机实测数据"
  next_action: "整理依赖 sched_clock 从 0 起算的调度/tracing 代码清单回帖，并提出 clocksource 侧替代方案"
contribution_opportunities:
- "汇总假设 sched_clock 相对 boot 从 0 起算的内核消费者清单，从调度侧回应 Marc Zyngier"
- "提出把绝对时间需求放在 boot 时间戳/clocksource 层而非 sched_clock 的替代方案"
- "在受影响服务器上量化硬件计数器复位造成的 sched_clock 跳变，补上目前缺失的实测"
source_email_count: 9
related_articles: []
tags:
- sched/core
---
