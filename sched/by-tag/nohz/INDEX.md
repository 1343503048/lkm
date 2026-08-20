# tag: nohz

共 1 篇

- [sched-20260820-009](../../2026/08/sched-20260820-009.md) `fix/low/under_review` — Andrea Righi 的 NOHZ idle 平衡系列推进到 v4：优先把任务搬到「完全空闲核心」而非「仅部分兄弟线程空闲的核心」，以保留空闲 SMT 兄弟供单线程突发。属 08-09 009 线的延续。