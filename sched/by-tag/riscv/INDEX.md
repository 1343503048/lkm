# tag: riscv

共 7 篇

- [sched-20261109-014](../../2026/11/sched-20261109-014-sched-move-stack-canary-to-the-start-of-the-randomizable-reg.md) `fix/low/under_review` — 本文为增量更新，完整脉络见下。
- [sched-20261107-010](../../2026/11/sched-20261107-010-sched-move-stack-canary-to-the-start-of-the-randomizable-reg.md) `fix/medium/under_review` — 本文为增量更新，完整脉络见下。
- [sched-20261106-014](../../2026/11/sched-20261106-014-sched-move-stack-canary-to-the-start-of-the-randomizable-reg.md) `fix/medium/under_review` — RISC-V 的 task_struct 增长导致 per-task stack canary 偏移超界、构建失败的修复（把 `stack_canary` 挪到「可随机化区域」的起始处），今天被 Valentin Schneider 再次推动：他替社区「ping」Peter 与 Ingo，请他们收取该补丁，并评估了唯一替代方案（加一条 LUI 指令拉伸 RISC-V 立即数），认为「有点浪费但当下
- [sched-20261102-027](../../2026/11/sched-20261102-027-sched-convert-paravirt-steal-to-new-static-key-apis.md) `fix/merged_tip` — Hongyan Xia 的 paravirt_steal 静态 key API 迁移补丁（RESEND 单补丁，亦为「Remove deprecated static key API in scheduler code」0/3 系列的 2/3）已被 Peter Zijlstra 收取，commit `a5576ebce920` 进 riscv/linux.git（fixes）。这是跨月的静态 ke
- [sched-20260907-015](../../2026/09/sched-20260907-015-sched-update-the-thread-info-in-task-description.md) `fix/stalled` — 本文为增量更新，完整背景见 sched-20260726-006（Huacai Chen 的 `THREAD_INFO_IN_TASK` Kconfig 描述修正，V2 于 06-09 发出）。本日唯一一封邮件是**作者自己第二次 ping**：Huacai Chen 直接点名 `Hi, Ingo, Peter, Could you please spend some time reviewing
- [sched-20260807-022-riscv-vector-preserve-state-scheduling.md](../../2026/08/sched-20260807-022-riscv-vector-preserve-state-scheduling.md) `in-review`
- [sched-20260726-006](../../2026/07/sched-20260726-006-sched-update-the-thread-info-in-task-description.md) `fix/low/stalled` — Huacai Chen 更新 `THREAD_INFO_IN_TASK` 的 Kconfig 描述，纠正一处过时且误导的说明（并非要删除除 flags 外的所有字段，实际只需移除 task_struct 指针字段）。补丁自 6/9 发出后一直无人 review，7/26 作者发出 "Gentle ping?" 催促，目前停滞。
