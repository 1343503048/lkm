# tag: memory_safety

共 2 篇

- [sched-20260824-007](../../2026/08/sched-20260824-007-sched-core-stale-rq-curr-arm64.md) `bug/critical/under_review` — 超过十台 HiSilicon Kunpeng 920 ARM64 生产服务器报告了偶发内核崩溃，共同特征：`rq->curr != current`——CPU 已切换到 idle 但 `rq->curr` 仍指向旧任务。怀疑 `__schedule()` 中的 `rq->curr = next` 更新未生效或被回退。运行 23-300 天后触发。
- [sched-20260821-011](../../2026/08/sched-20260821-011-cpuidle-dt-idle-genpd-kfree-the-original-name-allocation.md) `fix/medium/under_review` — `dt_idle_pd_alloc()` 中 `pd->name` 指向 `kasprintf()` 分配内存的中间位置（`kbasename()` 偏移），`kfree()` 时触发内存错误。Linkai Gong 的修复改为直接 `kstrdup(kbasename(...))` 复制基名字符串。
