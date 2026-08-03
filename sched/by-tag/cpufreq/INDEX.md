# tag: cpufreq

共 1 篇

- [sched-20260801-009](../../2026/08/sched-20260801-009-cpufreq-intel-pstate-adjust-policy-cur-in-active-mode.md) `fix/low/under_review` — `intel_pstate` 在 performance policy 下把 CPU 钉到固定 pstate 后，却又把 `policy->cur` 覆写成 `policy->min`，导致 nohz_full 隔离 CPU 因为拿不到新的 APERF/MPERF 采样而**永远上报频率下限**。修复很直接：把 `policy->cur` 设为实际钉住的频率。Rafael 与 Srinivas 均
