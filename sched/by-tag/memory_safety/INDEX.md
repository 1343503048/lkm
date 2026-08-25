# tag: memory_safety

共 1 篇

- [sched-20260821-011](../../2026/08/sched-20260821-011-cpuidle-dt-idle-genpd-kfree-the-original-name-allocation.md) `fix/medium/under_review` — `dt_idle_pd_alloc()` 中 `pd->name` 指向 `kasprintf()` 分配内存的中间位置（`kbasename()` 偏移），`kfree()` 时触发内存错误。Linkai Gong 的修复改为直接 `kstrdup(kbasename(...))` 复制基名字符串。
