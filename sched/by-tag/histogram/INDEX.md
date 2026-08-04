# tag: histogram

共 2 篇

- [sched-20260804-019](../../2026/08/sched-20260804-019-perf-sched-latency-v7-median-fix.md) `feature/under_review` — `perf sched latency` v7（08-03-010）在 08-04 收到 review：global 直方图排除 swapper 线程的方式（比较 comm 字符串）被建议改为检查 `tid==0`；另讨论 `--histogram/--time/--CPU` 输出细节。已 7 版，合入可能性 high，待小修订。
- [sched-20260803-010](../../2026/08/sched-20260803-010-perf-sched-latency-refine-outputs-unit-scaling-histogram-v7.md) `feature/under_review` — `perf sched latency` 在 v6（08-02）基础上发 v7，仅修正直方图中位数计算的零点偏差。属工具侧打磨，已迭代 7 版，合入可能性高。这是 08-02 系列 003 的后续版本。
