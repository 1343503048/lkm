# tag: proxy_execution


- [sched-20260806-010](../../2026/08/sched-20260806-010-sched-ext-proxy-execution-conservative-terminate.md) `feature/under_review` — proxy execution 07/15 转向保守 terminate：在 sched_change_begin 边界结束代理，而非跨类保留 donor。延续 08-05-001。

- [sched-20260805-001](../../2026/08/sched-20260805-001-sched-ext-proxy-exec-reject-dsq-class-transition.md) `feature/under_review` — Andrea Righi 的 sched_ext proxy execution 系列 08-05 review 收尾：跨类切换不能无条件阻断 proxy donor（RT/DL PI 需跨类保留），reject DSQ 路径需拆分并直接写 reason 到 p->scx.flags。延续 08-04-001。
- [sched-20260804-001](../../2026/08/sched-20260804-001-sched-ext-enable-proxy-execution-with-sched_ext.md) `feature/under_review` — Andrea Righi 的 15-patch 系列把内核主流的 SCHED_PROXY_EXEC（代理执行）机制带到 sched_ext：互斥锁/RT 阻塞的任务可被同调度类或更早调度类的高优先级任务「代理执行」，从而缓解优先级反转。Tejun 评价「Nice.」并指出两处需澄清的语义。属大型 feature，合入可能性高，仍处 review。

## 文章
- [Proxy Execution: Sleeping Owner Handling (v31, resend)](../../2026/08/sched-20260807-001-proxy-execution-sleeping-owner-v31.md)

共 1 篇
