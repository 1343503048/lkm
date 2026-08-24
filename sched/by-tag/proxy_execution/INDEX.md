# tag: proxy_execution

共 2 篇

- [sched-20260823-011](../../2026/08/sched-20260823-011.md) `discussion/medium/under_review` — `sched: Flatten the pick` (v3 0/7) 后续讨论：Peter 让报告者确认 flat_cg 数是基于 flat-hierarchy fix (68e3748781) 还是 single-runqueue (85570f10a4c6)；并提醒 0day 曾 pin 该系列 patch 6/7 导致网络吞吐回退（ksoftirqd 更少运行）。报告者用 0day 复现脚本成功复现回退，分析 `wake_affine_weight()` 在 concur 模式下因 wakee 权重增大而更少选 this_cpu。属 core_sched/proxy_exec 线延续。
- [sched-20260820-011](../../2026/08/sched-20260820-011.md) `discussion/medium/under_review` — `Remove sched_class::balance()` 系列与 core_sched pick_task 竞态在 08-20 继续交织：Peter 给出 core_seq 跟踪多 pick 的 sketch、Tejun 确认 SCX 下锁丢弃可前进、idle pick 传 NULL rf。forward-progress（活锁）保证仍未敲定，原始 cover 仍缺。属 08-19 011/002 延续。