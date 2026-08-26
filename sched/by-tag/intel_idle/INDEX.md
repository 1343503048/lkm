# tag: intel_idle

共 1 篇

- [sched-20260804-022](../../2026/08/sched-20260804-022-intel_idle-avoid-deep-idle-during-init.md) `fix/low/under_review` — intel_idle 在初始化/early 阶段若进入 deep idle 状态，可能在某些平台引起唤醒延迟异常或初始化时序问题。Zhang Rui 改为初始化期间避免 deep idle，完成后再允许。低严重度修复，合入可能性 medium，待平台确认。
