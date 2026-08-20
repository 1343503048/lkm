# tag: load_balance

共 2 篇

- [sched-20260820-011](../../2026/08/sched-20260820-011.md) `discussion/medium/under_review` — `Remove sched_class::balance()` 系列与 core_sched pick_task 竞态在 08-20 继续交织：Peter 给出 core_seq 跟踪多 pick 的 sketch、Tejun 确认 SCX 下锁丢弃可前进、idle pick 传 NULL rf。forward-progress（活锁）保证仍未敲定，原始 cover 仍缺。属 08-19 011/002 延续。
- [sched-20260820-009](../../2026/08/sched-20260820-009.md) `fix/low/under_review` — Andrea Righi 的 NOHZ idle 平衡系列推进到 v4：优先把任务搬到「完全空闲核心」而非「仅部分兄弟线程空闲的核心」，以保留空闲 SMT 兄弟供单线程突发。属 08-09 009 线的延续。