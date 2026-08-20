# tag: rt

共 2 篇

- [sched-20260820-006](../../2026/08/sched-20260820-006.md) `fix/low/under_review` — `struct cpupri_vec` 的 `count` 字段删除从 08-19 的 v1 推进到 08-20 的 v2：RT 优先级队列死代码清理，讨论收敛，合入概率高。
- [sched-20260820-001](../../2026/08/sched-20260820-001.md) `fix/medium/under_review` — Zhe Liu 修一个 CFS 带宽配置顺序陷阱：先 `cpu.max.burst` 配大值、再设有限 `cpu.max` quota 时，因旧 burst 校验不通过导致 quota 写入直接 EINVAL。修复为「改 quota 不兼容则把 burst 清零」，附文档与 selftest。Michal Koutny 倾向改成 clamp 到 quota，分歧待解。