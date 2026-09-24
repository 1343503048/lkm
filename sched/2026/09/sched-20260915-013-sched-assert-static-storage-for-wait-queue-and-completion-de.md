# sched: assert static storage for wait queue and completion declarations

## TL;DR
Yury Norov 09-15 发 17 补丁系列的 patch 06/17：给 `DECLARE_WAIT_QUEUE_HEAD()`/`DECLARE_SWAIT_QUEUE_HEAD()`/`DECLARE_COMPLETION()` 加 `ASSERT_STATIC_STORAGE()`，确保 wait queue/completion 的嵌入锁静态初始化（lockdep 拿持久 class key），并把 AMS PMU 驱动里两个自动 completion 换成 `DECLARE_COMPLETION_ONSTACK()`。sashiko-bot 已审无问题（"found no issues"）。合入判断 unknown，尚未见维护者表态。

## 背景与问题
普通 wait queue 与 completion 声明会静态初始化其内嵌锁；自动（栈上）对象需要运行时初始化，lockdep 才能拿到持久的 class key。混用静态/栈上声明时，lockdep 的 class key 归属可能错乱，导致误报或漏报锁依赖。补丁通过编译期断言把「必须在静态存储里声明」固化下来，防止误用。

## 技术方案
- 给三个声明宏加 `ASSERT_STATIC_STORAGE()`（借助 `include/linux/compiler.h`）。
- `_ONSTACK` 变体在无 `CONFIG_LOCKDEP` 时展开为底层初始化器而非断言声明，保持可用。
- 把 AMS PMU 驱动里两个自动 completion（`ams_pmu_set_register()`/`ams_pmu_get_register()`）改为 `DECLARE_COMPLETION_ONSTACK()`。

改动共 4 文件 18 行（include/linux/completion.h、swait.h、wait.h、drivers/macintosh/ams/ams-pmu.c）。虽然以 `sched:` 为前缀（wait_queue/completion 属 kernel/sched 原语），实际改动都在头文件与一个驱动里。

## 版本演进与当前进展
本日为系列 patch 06/17（`<20260915031334.1194975-1-ynorov@nvidia.com>`，系列 cover `<20260915030336.1192299-1-ynorov@nvidia.com>`）首发；sashiko-bot 当日审无问题。无维护者回帖。

## Maintainer 意见与讨论焦点
- **sashiko-bot**（自动化审查）："Sashiko has reviewed this patch and found no issues. It looks great!"
- 无真人维护者表态；该补丁属 17 补丁跨子系统系列中的 sched 相关单发，评审口径仍在系列层面。

## 合入评估
*likelihood=unknown*。自动化审查通过但无维护者 A/N/T；作为跨子系统系列的 06/17，其合入依赖整个系列的推进节奏。*blocking_issues*：无维护者表态；系列其余 16 补丁的进度未在本日可见。*next_action*：等系列维护者（wait/completion 相关）整体评审，或作者说明该补丁是否可独立提前合入。

## 效果评估
无效果数据。这是编译期断言 + 静态存储正确性的改动，无运行时性能影响；价值在于把 lockdep class key 的持久性约束固化、防误用。

## 我可以参与的点
- kind=review：核对 `ASSERT_STATIC_STORAGE()` 在非 `CONFIG_LOCKDEP`、以及 `_ONSTACK` 变体展开后是否仍能通过编译与静态断言。
- kind=testing：在开启 `CONFIG_LOCKDEP` + `CONFIG_DEBUG_LOCK_ALLOC` 的内核上跑 ams-pmu 相关路径，确认 completion 栈上声明转换无锁依赖误报。

## 参考链接
- patch 06/17：https://lore.kernel.org/all/20260915031334.1194975-1-ynorov@nvidia.com/
- sashiko-bot 回帖：https://lore.kernel.org/all/20260915032557.D00B51F0089B@smtp.kernel.org/

---
id: sched-20260915-013
date: '2026-09-15'
subject: 'sched: assert static storage for wait queue and completion declarations'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260915030336.1192299-1-ynorov@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20260915031334.1194975-1-ynorov@nvidia.com/'
authors:
  - 'Yury Norov'
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '无维护者表态，合入依赖 17 补丁系列整体节奏'
  next_action: '等系列维护者整体评审，或作者说明该补丁可否独立提前合入'
contribution_opportunities:
  - kind: review
    description: '核对 ASSERT_STATIC_STORAGE 在非 CONFIG_LOCKDEP 及 _ONSTACK 展开后的编译与静态断言'
  - kind: testing
    description: '在 CONFIG_LOCKDEP 内核上跑 ams-pmu 路径，确认栈上 completion 转换无误报'
generated_at: '2026-09-16T01:05:00'
source_email_count: 2
related_articles: []
tags:
  - sched_debug
---