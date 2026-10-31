---
id: sched-20261031-010
date: 2026-10-31
subject: 'sched/core: Pause KCOV in __schedule()'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261005185803.39170-1-kmehltretter@gmail.com>
lore_url: https://lore.kernel.org/all/20261005185803.39170-1-kmehltretter@gmail.com/
authors:
- Karl Mehltretter
maintainers_involved:
- Andrew Morton
current_version: v4
patch_series:
- version: v4
  msgid: <20261005185803.39170-1-kmehltretter@gmail.com>
  date: 2026-10-05
  summary: 6 片：在 __schedule()/hrtimer 等热点插入 kcov_pause()/kcov_resume() guard 抑制插桩
    callee
  review_outcome: Andrew Morton 要求 CONFIG_KCOV=n 零代码变化；作者承诺 v5 修复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 'v5 需把 guard 收敛进 #ifdef CONFIG_KCOV，保证 non-KCOV 零代码变化'
  - 调度侧（Peter Zijlstra）对 open-code guard 进 kernel/sched/core.c 仍未认账
  next_action: 作者发 v5（non-KCOV 零代码变化 + hrtimer wrapper 修正）
contribution_opportunities:
- kind: review
  description: 验证 v5 后 CONFIG_KCOV=n 下 __schedule() 等热点 objdump 零差异
- kind: testing
  description: CONFIG_KCOV=y 下量化 guard 对 __schedule() 热路径的实际开销
generated_at: '2026-11-01T09:00:00'
source_email_count: 2
related_articles: []
tags: []
title: 'sched/core: Pause KCOV in __schedule()'
layout: article
---

## TL;DR
Karl Mehltretter 的 KCOV 系列（v4，`sched/core: Pause KCOV in __schedule()` 为 4/6）今日被 Andrew Morton 审出关键问题：`kcov_pause` guard 在 `CONFIG_KCOV=n` 时**并未被编译掉**，会把 `class_kcov_pause_t` + `__cleanup__` 析构那一堆宏展开留在核心调度函数里，non-KCOV 内核也吃这套「goop」。Morton 要求用宏魔法让 non-KCOV 构建零代码变化；作者回帖承认「v2 里把 guard 放在 `#ifdef CONFIG_KCOV` 之外是疏忽」，承诺在 v5 连同 hrtimer wrapper 一起修。

## 背景与问题
KCOV 约定「排除中断与调度器自身覆盖」以保持 syscall 覆盖率与输入相关，但 `kernel/sched/` 未插桩、它调用的函数（如 `sched_clock()`、架构 helper 等）却插桩，会导致非确定性的覆盖污染。该系列（v4 6 片）在 `__schedule()`/`hrtimer` 等热点插入 `kcov_pause()/kcov_resume()` guard 来抑制这些插桩 callee。今日焦点是**代价控制**：Morton 检查 `kernel/sched/core.i` 后指出该 guard 展开体（含 `no_instrument_function`、`always_inline` 的构造/析构函数）在 `CONFIG_KCOV=n` 时仍残留。

## 技术方案
（承接 v4，今日为 review）当前 guard 用 `__cleanup__` 作用域对象实现暂停/恢复。Morton 的诉求：用宏让 `CONFIG_KCOV=n` 时这些对象/调用**完全消失**（不产生任何生成代码差异）；`CONFIG_KCOV=y` 时开销可接受（该配置下仅 debug/研究/fuzz 内核用）。作者确认修法：把 guard 移进 `#ifdef CONFIG_KCOV` 之内，并同步处理 hrtimer 侧的 wrapper。

## 版本演进与当前进展
*current_version: v4*（cover `<20261005185803.39170-1-kmehltretter@gmail.com>`，当日仅 4/6 与两封 review 入缓存）。进展：v4 进入实审阶段——Andrew Morton 给出首个实质性技术意见（non-KCOV 代码膨胀）。

## Maintainer 意见与讨论焦点
- **Andrew Morton（mm/维护者，走读 sched 侧）**：「Adding all this goop to core scheduler functions on non-KCOV kernels won't be terribly popular!」要求 CONFIG_KCOV=n 零代码变化；并点评「The overhead is probably acceptable with CONFIG_KCOV=y」。
- **Karl Mehltretter（作者）**：承认 v2 起把 guard 留在 `#ifdef` 外是疏忽，承诺 v5 修复（含 hrtimer wrapper）。
- 无 NAK；分歧集中在「non-KCOV 构建零膨胀」这一可执行的具体要求上，方向已明确。

## 合入评估
*likelihood=medium*。方向获得 Morton 认可（只要求控制 non-KCOV 膨胀），修法明确、改动小；但该系列整体仍缺 Peter Zijlstra 对「open-code guard 进 `kernel/sched/core.c`」的调度侧认账（此为该系列长期卡点，见 <a class="article-ref" href="/lkm/2026/09/02/sched-20260902-016-kcov-suppress-timer-and-scheduler-coverage-leaks.html">sched-20260902-016</a>）。*blocking_issues*：v5 需把 guard 收敛进 `#ifdef CONFIG_KCOV`；调度侧未认账。*next_action*：作者发 v5（零 non-KCOV 代码变化 + hrtimer wrapper 修正）。

## 效果评估
今日无新增覆盖率数据；Morton 的反馈是关于**生成的代码规模**（non-KCOV 内核的「goop」），非运行时性能数字。此前系列（v2）的 syzkaller 覆盖收益数据见 <a class="article-ref" href="/lkm/2026/09/02/sched-20260902-016-kcov-suppress-timer-and-scheduler-coverage-leaks.html">sched-20260902-016</a>。

## 我可以参与的点
- **review**：验证 v5 的宏收敛后 `CONFIG_KCOV=n` 下 `__schedule()` 等热点 objdump 确实零差异（作者宣称可做到，值得独立复核）。
- **testing**：在 `CONFIG_KCOV=y` 下量化 guard 对 `__schedule()` 热路径的实际开销，补系列一直缺失的运行时性能数据。

## 参考链接
- v4 4/6 的 Morton review: https://lore.kernel.org/all/20261030142354.bbc5e7f26fbfb6a8eee21290@linux-foundation.org/
- 作者回应: https://lore.kernel.org/all/auXoWFzEuirP2IuC@gmail.com/
- 同系列早期脉络: <a class="article-ref" href="/lkm/2026/09/02/sched-20260902-016-kcov-suppress-timer-and-scheduler-coverage-leaks.html">sched-20260902-016</a>
