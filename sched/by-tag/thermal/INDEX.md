# tag: thermal

共 2 篇

- [sched-20260926-011](../../2026/09/sched-20260926-011-thermal-cpufreq-cooling-simplify-cpufreq-set-cur-state.md) `fix/merged_tip` — Thorsten Blum 提交的 cpufreq_cooling 清理补丁——`cpufreq_set_cur_state()` 直接返回 `freq_qos_update_request()` 的错误，去掉 `ret >= 0` 分支的冗余包裹。获 Rafael Wysocki 应用为 7.4 material。
- [sched-20260831-013](../../2026/08/sched-20260831-013-cpufreq-amd-pstate-add-epp-tunings-for-zen6-client-platforms.md) `feature/under_review` — Mario Limonciello（AMD）8/31 13:46 发 2 补丁：1/2 给 amd-pstate 建立 **per-SoC / per-core-type 的 EPP 表**（`x86_cpu_id` 匹配，缺 SoC 则回落 legacy 常量），2/2 用它给 Zen6 客户端写入第一组调优值。核心手法是把 `power` 档从"所有核一个 0xFF"改成"大核 64、小核/低
