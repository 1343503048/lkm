---
id: sched-20260804-006
date: 2026-08-04
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: <unknown>
lore_url: unknown
authors:
- K Prateek Nayak
- Chen Yu
- Madadi Vineeth Reddy
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
- Ingo Molnar
current_version: v3
patch_series:
- version: v3
  msgid: <unknown>
  date: 2026-08-04
  summary: sync wakeup 系列延续 08-03-004：多个子方向并行——(a) sync wakeup 选 waker 的 core 而非仅
    waker cpu；(b) 保留 wake-affine 语义；(c) 非 SMT reciprocal sync wakeup 优先 waker cpu。讨论焦点仍是『先定义统一
    sync wakeup policy』。
  review_outcome: 08-03-004 中 Venkatesh 要求先定义 policy；08-04 上各子补丁继续迭代，Chen Yu / Madadi
    等给出实测与微调和。无方向 NAK，但 policy 共识未定。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - sync wakeup 统一 policy 仍未定义（08-03-004 遗留）；多个子方向并行，需先收敛策略再定补丁定位
  next_action: 等待对 sync wakeup 整体策略（SMT/非SMT、idle core 优先、LLC 回退顺序）的共识；各子补丁暂处于『策略确定前的局部优化』状态。
contribution_opportunities:
- kind: discussion
  description: 可基于 08-03-004 提出的 policy 清单，结合本日 (a)(b)(c) 三个子方向，提出 sync wakeup 统一
    policy 草案，把分散的局部优化收敛到一个一致的语义下参与讨论。
generated_at: '2026-08-05T00:25:00'
source_email_count: 2
related_articles:
- sched-20260803-004-sched-fair-prefer-waker-cpu-for-non-smt-reciprocal-sync-wakeups
tags:
- cfs
- load_balance
- topology
- wake_affine
title: 'sched/fair: Let sync wakeups target the waker''s core'
layout: article
---

# sched/fair: sync wakeup 多子方向并行（policy 待定）

## TL;DR
sync wakeup 优化在 08-04 呈三个并行子方向：选 waker 的 core、保留 wake-affine、非 SMT reciprocal 优先 waker cpu。延续 08-03-004 的「先定义统一 policy」要求，目前仍 medium，需先收敛策略再定补丁定位。

## 背景与问题
sync wakeup（waker 与被唤醒者后续会同步通信）的放置策略涉及 SMT、idle core、LLC 边界，主线各处零散修补（详见 08-03-004）。08-04 出现多个相关 patch：(a) sync wakeup 选 waker 的整 core 而非仅 waker cpu；(b) 保留 wake-affine 语义避免回归；(c) 非 SMT reciprocal 场景优先 waker cpu。三者都是更大 policy 缺口上的局部优化。

## 技术方案
- (a) 把被唤醒任务放到 waker 所在 core（而非任意 waker cpu 兄弟），利用 core 级热缓存。
- (b) 在引入新放置逻辑时保留既有 wake-affine 行为，避免对 affine 负载的回归。
- (c) 非 SMT reciprocal sync wakeup 优先选 waker cpu（08-03-004 的延续）。

## 版本演进与当前进展
- 08-03：v3 基础 + Venkatesh 要求先定义 policy（08-03-004）。
- 08-04：三个子方向继续迭代，Chen Yu / Madadi Vineeth Reddy 等给出实测与微调。

## Maintainer 意见与讨论焦点
延续 08-03-004：核心障碍仍是「先定义 sync wakeup 统一 policy」。各子补丁无方向 NAK，但 maintainer 倾向在 policy 共识后再接收局部优化，避免未来冲突。

## 合入评估
合入可能性 medium。阻塞在 policy 共识；一旦定义清楚，(a)(b)(c) 都可较快落地。

## 效果评估
邮件含各子方向的实测（Chen Yu / Madadi 的微调和数据），属「有实证」的局部优化。但缺乏统一 policy 下的整体评估。

## 我可以参与的点
- 这是明确讨论参与点：基于 08-03-004 的 policy 清单 + 本日三个子方向，提出 sync wakeup 统一 policy 草案，收敛分散优化（无人已给出完整定义）。

## 参考链接
- 08-03 文章：sched-20260803-004-sched-fair-prefer-waker-cpu-for-non-smt-reciprocal-sync-wakeups
