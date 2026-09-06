# tag: sched_clock

共 2 篇

- [sched-20260906-005](../../2026/09/sched-20260906-005.md) `discussion/none/stalled` — 本文为 09-03 第 015 篇（sched_clock 绝对时间选项）的增量更新：Thomas Gleixner 明确 NAK，称其是 firmware debug hack，维护者不关心这类 bug-chasing 故事。系列基本停滞，不建议继续跟进。
- [sched-20260903-015](../../2026/09/sched-20260903-015.md) `patch_series/medium/under_review` — 部分平台的硬件时钟会在复位/暂停后回绕或清零，使基于它的 `sched_clock()` 出现跳变，影响调度时间基准与 trace 一致性。本系列增加一个选项，使 `sched_clock` 在该硬件时钟复位时使用「绝对时间」语义，削弱复位造成的可见跳变。