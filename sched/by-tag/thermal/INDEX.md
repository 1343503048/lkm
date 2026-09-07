# tag: thermal

共 1 篇

- [sched-20260831-013](../../2026/08/sched-20260831-013-cpufreq-amd-pstate-add-epp-tunings-for-zen6-client-platforms.md) `feature/under_review` — Mario Limonciello（AMD）8/31 13:46 发 2 补丁：1/2 给 amd-pstate 建立 **per-SoC / per-core-type 的 EPP 表**（`x86_cpu_id` 匹配，缺 SoC 则回落 legacy 常量），2/2 用它给 Zen6 客户端写入第一组调优值。核心手法是把 `power` 档从"所有核一个 0xFF"改成"大核 64、小核/低
