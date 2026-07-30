# tag: x86

共 1 篇

- [sched-20260726-006](../../2026/07/sched-20260726-006-sched-update-the-thread-info-in-task-description.md) `fix/low/stalled` — Huacai Chen 更新 `THREAD_INFO_IN_TASK` 的 Kconfig 描述，纠正一处过时且误导的说明（并非要删除除 flags 外的所有字段，实际只需移除 task_struct 指针字段）。补丁自 6/9 发出后一直无人 review，7/26 作者发出 "Gentle ping?" 催促，目前停滞。
