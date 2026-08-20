---
id: sched-20260801-002
date: 2026-08-01
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <uid-13680@qq-imap>
lore_url: https://lore.kernel.org/all/20260731090334.2911948-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Kuba Piecuch
current_version: v3
patch_series:
- version: v1
  msgid: unknown
  date: 2026-07-26
  summary: 在 allowed_cpus selftest 内部初始化 idle mask，规避 ops.init() 期间 idle 状态不准确的问题
  review_outcome: Kuba Piecuch 指出这属于 sched_ext 核心问题，不应在 selftest 里绕过，应移到核心修复
- version: v2
  msgid: unknown
  date: 2026-07-31
  summary: 把 idle mask 初始化从 selftest 移入 sched_ext 核心；新增专用 idle-tracking static key，使得调度器完全启用前就能跟踪
    idle 状态转换；重写 allowed_cpus selftest，改为校验稳定的本地 CPU-idle 不变式
  review_outcome: Kuba Piecuch 建议不必新增专用 static key，复用已有的 built-in idle-selection static
    key 即可；并对 selftest 检查点提出细化意见
- version: v3
  msgid: <uid-13680@qq-imap>
  date: 2026-08-01
  summary: 复用 built-in idle-selection static key（不再新增专用 key）；在 ops.select_cpu() 与
    ops.enqueue() 两处都检查本地 CPU-idle 不变式；只读取 idle mask 而不修改，且把检查放在 scx_bpf_select_cpu_and()
    调用之前
  review_outcome: Kuba Piecuch 在 2/2 上继续讨论 idle task 与 idle bit 的边界语义，作者已认可其指正
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Tejun Heo 拉入 sched_ext/for-7.3，或 Kuba 对 v3 的最终确认
contribution_opportunities:
- kind: testing
  description: 在 SMT 与非 SMT 机器上反复运行 allowed_cpus selftest，确认 v3 改写后的本地不变式检查不再出现偶发失败
- kind: review
  description: 核对『在 ops.init() 之前开启 idle 跟踪、但抑制 ops.update_idle() 通知』这一拆分是否在所有 BPF
    调度器加载路径上都成立
generated_at: '2026-08-02T00:55:00'
source_email_count: 4
related_articles: []
tags:
- sched_ext
- idle
- affinity
title: 'selftests/sched_ext: Make allowed_cpus idle validation race-free'
layout: article
---

## TL;DR

sched_ext 的 built-in idle mask 在初始化时把所有 online CPU 一律标记为 idle，但真正的 idle 跟踪要等调度器完全启用后才开始，导致 `ops.init()` 期间以及某些 CPU 下一次 idle 转换之前，繁忙 CPU 被错误地宣称为 idle。v3 把跟踪时机提前并顺带修掉了一个 selftest 的固有竞态，方案已按 review 意见收敛，接近可合入状态。

## 背景与问题

两个相关但独立的问题：

**1. idle mask 与真实状态不一致（核心 bug）**。built-in idle mask 初始化时把所有 online CPU 置为 idle，而 idle 跟踪只在 sched_ext 完全 enable 之后才启动。这段窗口内：`ops.init()` 看到的 idle 信息是假的；一个从始至终都在忙的 CPU，在它下一次真正进入 idle 之前，会一直被 mask 宣称为 idle。BPF 调度器如果在 `ops.init()` 里依据 idle mask 做初始放置决策，拿到的就是错误输入。

**2. allowed_cpus selftest 存在固有竞态**。该测试校验「远程选中的 CPU 不应再出现在 idle mask 中」。但一次 idle-to-idle 的重新选取可能在测试执行检查之前就把该 CPU 重新标记为 idle，于是这个断言本身就是不可靠的——它检查的是一个瞬态量，而不是不变式。

## 技术方案

**核心侧**：在 `ops.init()` 之前就开启 built-in idle 跟踪，并在 rq lock 保护下逐个刷新每个 online CPU 的真实状态。关键的设计拆分是：**早期跟踪只更新 built-in mask，而 `ops.update_idle()` 回调通知仍然抑制到调度器完全启用之后**。这样既保证了 mask 从一开始就准确，又避免了在调度器尚未就绪时向 BPF 侧投递回调。

**selftest 侧**：放弃「远程 CPU 不在 idle mask 中」这种瞬态断言，改为校验一个稳定的本地不变式——依托上面已经变得可靠的 idle mask 状态来做判断。

v2 到 v3 的一个重要取舍是 static key 的选择：v2 引入了一个专用的 idle-tracking static key，Kuba Piecuch 认为没必要，复用已有的 built-in idle-selection static key 就够了，v3 采纳了这个简化。

改动规模不大：`ext.h` 5 行、`idle.c` 35 行、`allowed_cpus.bpf.c` 49 行，共 3 文件 78 增 11 删。

## 版本演进与当前进展

- **v1**（07-26）：在 selftest 内部初始化 idle mask。Kuba Piecuch 指出这是在测试里绕过核心问题，应当在 sched_ext 核心修复。
- **v2**（07-31）：按意见把初始化移入核心，新增专用 idle-tracking static key，并重写 selftest 校验本地不变式。
- **v3**（08-01 02:23）：复用已有的 built-in idle-selection static key 而非新增专用 key（Kuba）；在 `ops.select_cpu()` 和 `ops.enqueue()` 两处都检查本地 CPU-idle 不变式（Kuba）；只读取 idle mask 不修改，且把检查前移到 `scx_bpf_select_cpu_and()` 调用之前（Kuba）。

三个版本的每一次改动都是直接回应 Kuba Piecuch 的具体意见，迭代方向非常收敛。

## Maintainer 意见与讨论焦点

Kuba Piecuch 是本系列事实上的主要 reviewer，v1→v2→v3 的全部关键改动都出自他的意见。当日（08-01 18:35）他在 2/2 上继续讨论一个语义边界：CPU 停止运行 idle task 时的时序问题——按他的说法，「观察到一个 idle task 但其 idle bit 已被清除」是合法状态。作者 Andrea Righi 明确回复认可（"Right, thanks for pointing that out."）。

目前没有 NAK，也没有未解决的分歧。需要如实说明的是：Tejun Heo 作为 sched_ext maintainer 在当日邮件中未对本系列表态，因此最终合入决定尚未出现。

## 合入评估

合入可能性 **high**。理由：修复的是一个明确的正确性问题（假 idle 状态）；三轮迭代已把 reviewer 的意见全部消化，v3 的改动是简化而非扩张；改动面小且局限在 sched_ext 内部；作者 Andrea Righi 是 sched_ext 的活跃贡献者。

当前无已知阻塞项，剩下的是 Tejun Heo 拉入 `sched_ext/for-7.3` 的常规流程。

## 效果评估

暂无量化效果数据。这是正确性修复而非性能优化，邮件中未给出 benchmark。selftest 竞态的修复效果也没有给出「修复前失败率 vs 修复后」的统计数字，只有机制层面的论证。

## 我可以参与的点

- **测试**：在 SMT 与非 SMT 机器上反复运行 allowed_cpus selftest（大循环次数），确认 v3 改写后的本地不变式检查不再出现偶发失败——这类竞态修复最有说服力的证据就是长时间压测的失败率数据。
- **Review**：核对「ops.init() 之前开启跟踪、但抑制 update_idle() 通知」这个拆分在所有 BPF 调度器加载路径上是否都成立，特别是加载失败回滚路径上 idle 跟踪的开关时序。

## 参考链接

- lore thread (v2): https://lore.kernel.org/all/20260731090334.2911948-1-arighi@nvidia.com/
- lore thread (v1): https://lore.kernel.org/all/20260726064754.378671-1-arighi@nvidia.com/
- lore thread (v3): 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
