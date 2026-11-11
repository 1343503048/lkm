---
id: sched-20261111-018
date: '2026-11-11'
subject: 'tools/sched_ext: robustness fixes from cold review'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20261110125001.4167503-1-cui.tao@linux.dev>
lore_url: https://lore.kernel.org/all/20261110125001.4167503-1-cui.tao@linux.dev/
authors:
- Tao Cui
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261110125001.4167503-1-cui.tao@linux.dev>
  date: '2026-11-10'
  summary: 9 补丁修示例调度器健壮性问题
  review_outcome: Tejun 应用 1/5/6/7/8，跳过 2/3/4/9
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.5
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 7.5 窗口进入 mainline
contribution_opportunities: []
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261110-004
tags:
- sched_ext
title: 'tools/sched_ext: robustness fixes from cold review'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-004-tools-sched-ext-robustness-fixes-from-cold-review.html">sched-20261110-004</a>：Tao Cui（麒麟）发 9 补丁系列，修复 sched_ext 四个示例调度器（scx_flatcg / scx_pair / scx_qmap / scx_userland）在 cold review 中发现的一批健壮性问题：非法 stats interval 导致 100% CPU 忙旋、usage synopsis 漏选项、restart 后 pair_id/hier stats baseline 未复位、batch size 0 被静默接受导致任务堆积等。均为工具层小修，多数带 `Fixes:`，无内核改动。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-018-tools-sched-ext-robustness-fixes-from-cold-review.html">sched-20261111-018</a>（今天）：**Tejun Heo 部分应用**——「Applied 1, 5, 6, 7 and 8 to sched_ext/for-7.5（修正了 8 描述里一句乱码）；2/3/4/9 跳过，因为它们没有实质区别」。作者也向 David Carlier 澄清：cover 里「busy-check 清理」一句是遗留下来的（该清理已在发版前被砍掉，因为被 hijack 的更新总是以 -EBUSY 失败、无可观测差异），patch 8/9 的交换也只是同一段晚改动的编辑失误。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-004-tools-sched-ext-robustness-fixes-from-cold-review.html">sched-20261110-004</a>）示例调度器是 sched_ext 的参考实现与测试载体，工具层参数校验缺陷会误导使用者或让调度器进入异常状态。典型两例：`scx_flatcg` 的 `-i` interval 经 `strtod()`+`(float)` 转型切 timespec，负值/无法往返的值会产生负 tv_sec 或 `tv_nsec >= 1e9`，`nanosleep()` 返回 EINVAL 却从不检查，stats 循环 100% CPU 忙旋；`scx_userland` 的 `-b 0` 被静默接受、batch_size 保持 0，任务不断堆积。

## 技术方案

（承接 v1，无变化）逐调度器修：`scx_flatcg` 复位并校验 stats interval；`scx_pair` 处理 dispatching cgroup 消失时不再 abort、重启时 reset pair_id；`scx_qmap` 补 usage synopsis 选项并复位 hier stats baseline；`scx_userland` 检查 dispatch buffer 槽位、拒绝 batch size 0。8 个补丁带 `Fixes:`。

## 版本演进与当前进展

*current_version: v1（2026-11-10，`<20261110125001.4167503-1-cui.tao@linux.dev>`）*。今日 Tejun 应用 patch 1/5/6/7/8（进 `sched_ext/for-7.5`），跳过 2/3/4/9（判定无实质区别）；作者回应了 David Carlier 对 cover 与 patch 顺序的两处疑问，无新版本。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext 维护者）**：应用 5 个补丁，跳过 2/3/4/9——「它们没有实质区别」。
- **David Carlier（评审者）**：指出 cover 里「busy-check」句与 patch 8/9 顺序问题；作者澄清均为发版前编辑遗留，非代码问题。
- 无 NAK。

## 合入评估

*likelihood=merged*。有效子集（5/9）已进 `sched_ext/for-7.5`，其余 4 个被维护者明确放弃。*blocking_issues*：无。*next_action*：随 7.5 窗口进入 mainline；被跳过的 2/3/4/9 无需跟进。

## 效果评估

无量化数据。均为工具层健壮性修复（消除忙旋、误入异常状态）。

## 我可以参与的点

当前阶段已由维护者处理完毕，暂无明显参与空间。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110125001.4167503-1-cui.tao@linux.dev/
- Tejun 的应用确认: https://lore.kernel.org/all/a7610cb55d3f6172fc3f717116ee44cc@kernel.org/
- 作者对 David Carlier 的澄清: https://lore.kernel.org/all/d7846fef-ba62-4c3e-9498-d3d685536df1@linux.dev/
