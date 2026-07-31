# tag: eevdf

共 1 篇

- [sched-20260730-006](../../2026/07/sched-20260730-006-docs-scheduler-fix-eevdf-inaccuracies.md) `fix/low/under_review` — Zhan Xusheng 修复调度器文档中两处 EEVDF 相关的不准确描述：`sched-design-CFS.rst` 仍描述 fair class 为总是运行最小 vruntime 任务（实际自 Linux 6.6 起已实现 EEVDF），`sched-eevdf.rst` 中发布日期和 `sched_setattr()` 描述有误。纯文档修复，无代码改动。
