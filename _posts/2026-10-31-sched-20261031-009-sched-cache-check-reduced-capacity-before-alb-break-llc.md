---
id: sched-20261031-009
date: 2026-10-31
subject: 'sched/cache: Check reduced capacity before alb_break_llc()'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261029023650.3404429-1-zhanxusheng1024@gmail.com>
lore_url: https://lore.kernel.org/all/20261029023650.3404429-1-zhanxusheng1024@gmail.com/
authors:
- Zhan Xusheng
maintainers_involved: []
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v2 未发出，需按双条件（同 LLC idle CPU 优先 + 抑制回迁）改版
  next_action: 作者按双条件改出 v2，并附 nr_migrations 前后对比
contribution_opportunities:
- kind: testing
  description: 复跑 20%~60% IRQ + cache-aware 的 ping-pong 场景，验证 v2 后 nr_migrations 回落且吞吐不回退
- kind: review
  description: 评估同 LLC idle CPU 优先与减少回迁两条件的判定顺序是否会引入新的放置偏差
generated_at: '2026-11-01T09:00:00'
source_email_count: 2
related_articles:
- sched-20261030-006
tags:
- load_balance
title: 'sched/cache: Check reduced capacity before alb_break_llc()'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/29/sched-20261029-007-sched-cache-check-reduced-capacity-before-alb-break-llc.html">sched-20261029-007</a>：Zhan Xusheng 发单补丁修 cache-aware 调度放置缺陷——把 reduced-capacity 检查挪到 `alb_break_llc()` 之前，避免任务被钉在低容量 CPU。
- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-006-sched-cache-check-reduced-capacity-before-alb-break-llc.html">sched-20261030-006</a>：Chen Yu 走读 `can_migrate_llc()` 后给出阈值量化（仅 IRQ 压力 >66.7% 才放行迁移），并表态会亲自跑 hackbench/netperf 验证。
- <a class="article-ref" href="/lkm/2026/10/31/sched-20261031-009-sched-cache-check-reduced-capacity-before-alb-break-llc.html">sched-20261031-009</a>（今天）：Tim Chen 给出两处保留意见（① 应优先迁到 preferred LLC 内其它 idle CPU；② 存在 ping-pong 迁移风险），并请作者测 `nr_migrations`。Zhan Xusheng 实测确认 ping-pong 确实发生（IRQ 负载越高越严重），将按「两条件」改出 v2。

## 背景与问题
（承接）源 CPU 容量被 IRQ/hrtimer 压减后，LLC 优先策略仍把任务钉在低容量 CPU。今日 Tim Chen 补充两个此前未覆盖的边界：即便源 CPU 容量不足，**preferred LLC 内可能还有 idle CPU**，任务迁到非 preferred LLC 之前应先尝试同 LLC 内的 idle CPU；且 cache-aware 调度可能因「只带 IRQ 负载的 CPU 被当作 idle」而把任务拉回，形成 ping-pong。

## 技术方案
（方案方向不变：reduced-capacity 检查提前）今日为走读与实测，无新补丁。Tim Chen 主张 LLC override 只应在「preferred LLC 内无足够容量的 idle CPU」时生效；Zhan Xusheng 实测认同，计划 v2 同时满足「preferred LLC 无 idle CPU 且容量不足」与「不被拉回（容量已压减）」两个条件。

## 版本演进与当前进展
*current_version: v1*（2026-10-29 发出；今日为第二轮 review + 数据）。无新版本；Zhan Xusheng 明确「I'll work on a v2 along those lines」。

## Maintainer 意见与讨论焦点
- **Tim Chen（Intel）**：两处保留——优先迁 preferred LLC 内 idle CPU、防 ping-pong 回迁，并要求作者测 `nr_migrations`/`sched_migrate_task`（20s，20%~40% IRQ 负载）。
- **Zhan Xusheng（作者）**：实测确认 ping-pong（20%/40%/60% IRQ 下 `nr_migrations` 均显著上升，60% 时成对 0→2/2→0 抖动、kprobe 显示回迁来自 `LBF_ACTIVE_LB_LLC`），采纳 Tim 的双条件建议。
- 无 NAK；方向已收敛到「双条件 v2」，等待改版。

## 合入评估
*likelihood=medium*。作者已有 Kayra Reviewed-by、Chen Yu 倾向认可、Tim Chen 的意见有数据支撑且作者已采纳；v2 落地后可望上升。*blocking_issues*：v2 未发出；需解决 ping-pong 回迁与「同 LLC idle CPU 优先」的取舍。*next_action*：作者按双条件改出 v2，并附 `nr_migrations` 前后对比。

## 效果评估
今日新增量化数据（Zhan Xusheng 实测）：IRQ 负载 20%/40%/60% 下，补丁的 `nr_migrations` 均高于 mainline（60% 时出现了 327 的离群值），但吞吐迭代次数从 1.9e7 提升到 5.0e7（60% 场景）；即当前 v1 用「更多迁移」换「吞吐提升」，需 v2 抑制无谓迁移。

## 我可以参与的点
- **testing**：复跑 Zhan 的 ping-pong 场景（20%~60% IRQ + cache-aware），验证 v2 双条件后 `nr_migrations` 回落、吞吐不回退。
- **review**：评估「先找 preferred LLC 内 idle CPU」与「减少回迁」两个条件的判定顺序是否会引入新的放置偏差。

## 参考链接
- lore thread（v1）: https://lore.kernel.org/all/20261029023650.3404429-1-zhanxusheng1024@gmail.com/
- Tim Chen 的保留意见: https://lore.kernel.org/all/93e3e1388b3d4512818e7f1e19003e0feb4890dd.camel@linux.intel.com/
