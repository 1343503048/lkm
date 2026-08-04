# tag: proxy_execution

共 1 篇

- [sched-20260804-001](../../2026/08/sched-20260804-001-sched-ext-enable-proxy-execution-with-sched_ext.md) `feature/under_review` — Andrea Righi 的 15-patch 系列把内核主流的 SCHED_PROXY_EXEC（代理执行）机制带到 sched_ext：互斥锁/RT 阻塞的任务可被同调度类或更早调度类的高优先级任务「代理执行」，从而缓解优先级反转。Tejun 评价「Nice.」并指出两处需澄清的语义。属大型 feature，合入可能性高，仍处 review。
