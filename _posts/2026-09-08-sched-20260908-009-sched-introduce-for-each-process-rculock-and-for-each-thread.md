---
id: sched-20260908-009
date: '2026-09-08'
subject: 'sched: introduce for_each_process_rculock and for_each_thread_rculock'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260907081334.1152889-1-ye.liu@linux.dev>
lore_url: https://lore.kernel.org/all/20260907212054.88063-1-sj@kernel.org/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-08'
authors:
- Ye Liu
maintainers_involved:
- SJ Park
patch_series:
- version: v2
  msgid: <20260907081334.1152889-1-ye.liu@linux.dev>
  date: '2026-09-07'
  summary: 8 补丁：include/linux/sched/signal.h 新增 for_each_process_rculock()/for_each_thread_rculock()/for_each_process_thread_rculock()（scoped_guard(rcu)
    把 RCU 读锁作用域绑定到循环），其余 7 个补丁机械替换 mm/ kernel/ fs/ lib/ security/ 调用点；17 files changed,
    54 insertions(+), 81 deletions(-)。本日无新版本、无代码变化。
  review_outcome: SJ Park 09-08 给 patch 1/8 有条件 Reviewed-by（前提是采纳 Lorenzo 的缩进要求）。1/8
    现累计 Acked-by Michal Hocko 与三份 Reviewed-by（Lorenzo 条件式、Oleg Nesterov 无条件、SJ Park
    条件式）。
merge_assessment:
  likelihood: high
  blocking_issues:
  - 等 v3 落实 for 循环体缩进与 commit message 精简，两份条件式 Reviewed-by 以此为前提
  - 收树路径未定，暗示走 mm 树但 signal.h 与 kernel/sched 改动需 sched 侧配合
  - fs/ lib/ security/landlock kernel/trace kernel/locking 各站点仍缺各自维护者 ack
  next_action: 跟进 v3 是否发出以及由哪棵树收取；本向日无新增技术阻塞
contribution_opportunities:
- kind: review
  description: 核对 kernel/sched/debug.c print_rq() 与 kernel/sched/core.c show_state_filter()
    替换后 RCU 临界区是否与原 rcu_read_unlock() 位置严格等价、有无循环外继续使用 p/t 的写法
- kind: extend
  description: 主线 for_each_process_thread() 仍有约 40 处未覆盖站点，但建议等 v3 定型与收树路径明确后再铺新补丁
- kind: testing
  description: 对机械替换跑 objdiff 与 PREEMPT_NONE/PREEMPT_RCU 两种配置的编译验证，补上目前缺失的等价性证据
source_email_count: 1
related_articles:
- sched-20260907-004
tags:
- sched_debug
title: 'sched: introduce for_each_process_rculock and for_each_thread_rculock'
layout: article
---

## TL;DR

本文为增量更新，完整背景与 v1→v2 的差异见 [[sched-20260907-004]]。09-08 本线程只有一封新邮件：SJ Park 在 05:20 给 patch 1/8 打上 `Reviewed-by`，条件是 Lorenzo Stoakes 提的缩进要求被采纳（「Assuming Lorenzo's indentation change requests are accepted」）。至此 1/8 已握有 `Acked-by: Michal Hocko` + 三份 `Reviewed-by`（Lorenzo 有条件、Oleg Nesterov 无条件、SJ Park 有条件），阻塞项依旧只剩「发一版落实缩进与 commit message 精简的 v3」以及收树路径未定。这类全树机械替换系列，review 侧已基本放行。

## 背景与问题

摘要（详见 [[sched-20260907-004]]）：全树大量位置在为「遍历进程/线程」手工配对 RCU 读锁，循环里出现 `break`/`goto`/提前 `return` 时解锁点要靠人脑穷举；`guard(rcu)()` 的写法又把临界区撑得比循环大。Ye Liu 的 v2 在 `include/linux/sched/signal.h` 新增 `for_each_process_rculock()` / `for_each_thread_rculock()` / `for_each_process_thread_rculock()`，用 `scoped_guard(rcu)` 把锁作用域绑到循环本身，另外 7 个补丁机械替换 mm/、kernel/、fs/、lib/、security/ 的调用点（17 files changed, 54 insertions(+), 81 deletions(-)）。命名从 `*_rcu` 改成 `*_rculock` 是为了不与「假定调用者已持锁」的既有约定混淆。

## 技术方案

本日无方案变化、无新代码。

## 版本演进与当前进展

- 09-08 05:20:53（北京时间，UTC 为 09-07 21:20）SJ Park 回复 patch 1/8（`<20260907212054.88063-1-sj@kernel.org>`），原文：「Looks good to me. Assuming Lorenzo's indentation change requests are accepted, Reviewed-by: SJ Park <sj@kernel.org>」。
- 版本号仍停在 v2，本日作者未重投，其余 7 个补丁本日无人回帖。

## Maintainer 意见与讨论焦点

- **SJ Park**：认可宏的实现，但把 `Reviewed-by` 挂在一个前置条件上——Lorenzo 的缩进意见要被采纳。这与 Lorenzo 自己在 09-07 给出的条件式 `Reviewed-by` 口径一致，等于两人用同一个条件卡住 v3。
- 无新增反对意见，也无新增分歧。09-07 遗留的三点本日仍未推进：（1）缩进风格（`for` 循环体多缩进一个 tab，Lorenzo 要求，Oleg 表示无所谓）；（2）cover 里那段关于 checkpatch 误报的说明要从 commit message 删掉；（3）mm 之外各站点（fs/、lib/、security/landlock、kernel/trace、kernel/locking）仍缺各自维护者 ack，`include/linux/sched/signal.h` 与 `kernel/sched/` 两处还需要 sched 侧点头。

## 合入评估

`likelihood=high`，与 09-07 判断一致且依据更强了一分：patch 1 现在有条件式与无条件式共三份 `Reviewed-by` 加一份 `Acked-by`。`blocking_issues`：

1. 等 v3 落实缩进与 commit message 精简——两份有条件 `Reviewed-by` 都以它为前提。
2. 收树路径仍未定：Lorenzo 回 cover 时称呼 Andrew，暗示走 mm 树，但 `include/linux/sched/signal.h` 与 `kernel/sched/*` 的改动需要 sched 侧配合，跨树依赖最容易停滞。
3. mm 之外子系统的 ack 仍缺。

`next_action`：跟进是否发 v3 以及由哪棵树收取；本向日没有需要作者解决的新技术问题。

## 效果评估

暂无效果数据——本日是纯机械替换类清理，邮件里没有也不需要 benchmark；作者与 review 者讨论的是可读性与锁作用域正确性，没有量化指标。

## 我可以参与的点

- **补齐 sched 侧等价性核对（review）**：这是 sched 维护者最可能问而目前没人回答的点——`kernel/sched/debug.c` 的 `print_rq()` 与 `kernel/sched/core.c` 的 `show_state_filter()` 替换后，RCU 临界区范围要与原 `rcu_read_unlock()` 位置严格等价，特别要确认没有循环外继续使用 `p`/`t` 的写法。我可以直接把这两处的替换前后对比贴出来。
- **把剩余站点做完（extend）**：主线 `for_each_process_thread()` 仍有约 40 处调用未被本系列覆盖（`kernel/tracepoint.c`、`kernel/sys.c`、`kernel/power/process.c`、`kernel/events/core.c`、`kernel/livepatch/transition.c`、`drivers/tty/tty_io.c`、`fs/fs_struct.c`、`mm/kmemleak.c` 等）。不过考虑到 v3 尚未出现、收树路径未定，现在铺新站点更可能增加作者与维护者的负担，建议等 v3 定型后再动。
- **验证脚本（testing）**：作者的「机械替换」目前没有 objdiff 或编译矩阵证据。跑一遍 objdiff 加 `PREEMPT_NONE`/`PREEMPT_RCU` 两种配置，是有明确判据、能直接回帖的增量。

## 参考链接

- 本日回帖（SJ Park 的 Reviewed-by）: https://lore.kernel.org/all/20260907212054.88063-1-sj@kernel.org/
- v2 cover: https://lore.kernel.org/all/20260907081334.1152889-1-ye.liu@linux.dev/
- v2 1/8: https://lore.kernel.org/all/20260907081334.1152889-2-ye.liu@linux.dev/
- tip-bot commit: 未获取到
- stable backport: 未获取到
