# sched: Handle split scheduling and execution contexts in task ticks

## TL;DR
本文为增量更新，完整背景见 related_articles 中的 sched-20260909-001。Hui Su 的 5 补丁 v4 系列在 09-09 收到 Peter Zijlstra 对 3/5 的重排要求和对 4/5 的明确 NAK 后，09-10 作者对全部四条意见给出了实质性回应：3/5 已按单 donor 块 + 单 curr 块重排、4/5 整个推翻原设计改为 sched_class 生命周期回调、5/5 改用 task-clock 域谓词，并确认 v5 将携带这些改动。同日 Andrea Righi 主动来对齐 proxy+sched_ext v13 系列与本系列的 task_tick_scx() 冲突。系列从「被 NAK」转为「v5 路线明确」，值得持续关注。

## 背景与问题
proxy execution 下调度上下文（rq->donor）与执行上下文（rq->curr）分离后，task_tick 的各消费者（NUMA、cache-aware、RT watchdog、core scheduling slice）该跟谁走出现不一致：v4 系列把 task_tick() 的 task 参数去掉、引入「donor 类先、curr 类后」的公共分发器（1/5），NUMA/cache 移到 FAIR 执行上下文（2/5、3/5），RT 类状态留 donor、watchdog 跟 curr（4/5），core slicing 用 task-clock 域度量 donor 已消耗 slice（5/5，Fixes aa4f74dfd42b）。

## 技术方案
09-10 邮件里披露的 v5 新设计（均为作者对 review 的回应）：

- **3/5 重排**（回应 Peter「合并成单个 donor_class 与单个 curr_class 块」）：task_tick_fair() 最终形态为——donor 是 FAIR 时执行 `entity_tick(); reweight_eevdf(); misfit/overutilized/core(donor);`，然后 `if (queued) return;`，curr 是 FAIR 时执行 `task_tick_numa(rq, curr); task_tick_cache(rq, curr);`。作者确认「不存在第二个 donor 块」，请 Peter 复核该布局，若认可则带进 v5。
- **4/5 推倒重来**（回应 Peter 的 NAK「不接受在 __schedule() 中间散落 rt 代码」）：从 __schedule() 移除全部 RT 特判，改为通过 sched_class 回调上报通用的 proxy 生命周期转换，RT 类消费这些事件以保持 RLIMIT_RTTIME 区间语义。所有权规则：「RT service applicability follows the effective donor scheduling class; watchdog state is charged to rq->curr」。回调不取锁不睡眠：core 调用方持 rq->lock，mutex handoff 路径不持 rq->lock 但关抢占。实现覆盖 proxy 链关系转换（旧 effective donor 先报 STOP 再装新关系；上游变化向嵌套链每个下游 owner 传播 STOP/START；teardown 先解析 effective root donor）。作者还放弃了最初的 per-task generation state 方案——它会让 task_struct 在 x86-64 与 i386 上都增加一个 64 字节分配单元。
- **5/5 改谓词**（跟进 Tim Chen/Chen Yu 的 task_tick_core() 讨论）：slice 检查仍关联 rq->donor（slice 属于调度上下文），但已消耗服务改在 task-clock 域度量：`rtime = se->exec_start - rq->core_sched_start`；proxy 执行期间 update_se() 用 rq_clock_task() 推进 donor 的 exec_start，使比较两侧同域。作者实测过 deadline/virtual-time 原型，不可靠：update_deadline() 可能在 task_tick_core() 求值前推进 deadline，使重构出的虚拟服务在 donor 已消耗服务后又变小。baseline 存 struct rq 而非每个 sched_entity（每 rq 只有一个活跃 donor；按 entity 存会在 i386 + CONFIG_SCHED_CORE=y 下把 sched_entity 从 224 字节撑到 256）。另一细节：execution-owner handoff 可能保留同一 donor，调度器会用合成的 put_prev_task()/set_next_task() 对处理 balance，该 reselect 不得重置 donor 的 core_sched_start，否则 handoff 前的服务量会被丢弃。
- **1/5 与 sched_ext 的协同**：Andrea Righi 主动提示其 v13 系列（见 sched-20260910-002）会让两系列「很快兼容」，建议本系列一并处理 SCX donor/execution context 所有权或双方协调改动。作者回应：本地草稿中 task_tick_scx() 显式 donor-gated，未复制 v13 的 donor 记账改动；分发器 donor 类先调、执行类不同时再调；SCX 仅作为非 EXT donor 的执行类被触达时，task_tick_scx() 直接返回不做 SCX 策略与 slice 工作。作者曾用 v13 + 早期 5 补丁系列建过集成树，唯一文本冲突就在 task_tick_scx() hunk；该树在 CONFIG_SCHED_CLASS_EXT=y + CONFIG_SCHED_PROXY_EXEC=y 下能构建并启动，但没有稳定的 EXT→FAIR、FAIR→EXT、EXT→EXT、RT/DL→EXT 全混合运行时矩阵，且早于本轮 P4 转换路径改动、未重新验证。

## 版本演进与当前进展
current_version: v4（2026-09-09 发出）。09-09：Peter 要求重排 3/5、NAK 4/5。09-10：作者逐条回应（3/5 已重排待复核、4/5 改生命周期回调设计、5/5 改 task-clock 谓词、1/5 与 Andrea 对齐 SCX 所有权边界），明确「若布局认可即携带进 v5 并发出更新系列」。1/5 改 sched_class::task_tick() 签名波及全部调度类，仍需 Peter 收下。

## Maintainer 意见与讨论焦点
- Peter Zijlstra（09-09，见前文）：3/5 重排要求与 4/5 NAK 是本日回应的直接对象；09-10 当天 Peter 尚未对作者的新设计表态。
- Andrea Righi（09-10）：不是对本系列的 review，而是跨系列协调——确认 v13 proxy+sched_ext 系列与本系列在 task_tick_scx() 上的冲突面，愿意协调所需改动。
- 未解决焦点：4/5 的 sched_class 回调设计是否满足 Peter「不把 RT 散落进 __schedule()」的底线（新设计把判断移进 RT 类自身消费回调，方向一致但未获确认）；5/5 的 task-clock 谓词是否说服 Tim Chen（作者称系「跟进与 Tim 和 Chen Yu 的讨论」，但本日无 Tim 回帖确认）。

## 合入评估
likelihood: medium（从 09-09 的 low 上调：作者对全部 blocking 意见给出了具体且方向正确的新设计，v5 路线清晰）。blocking_issues：Peter 对 4/5 新回调设计与 3/5 重排布局尚未点头；1/5 的 task_tick() 签名改动必须经 Peter 收取；与 Andrea v13 系列的 task_tick_scx() 冲突需在两系列合入顺序上协调；混合 EXT 运行时矩阵未验证。next_action：作者发 v5 携带 3/5 新布局、4/5 回调设计与 5/5 task-clock 谓词，并与 v13 系列约定合入顺序后做集成验证。

## 效果评估
无 benchmark 数据。有的量化信息是结构开销：per-task generation state 方案会使 task_struct 增加一个 64 字节分配单元（已放弃）；per-entity baseline 在 i386 + CONFIG_SCHED_CORE=y 下使 sched_entity 从 224 增至 256 字节（已改为存 struct rq）。集成树「能构建并启动」属作者自述，未见运行时测试数据。

## 我可以参与的点
- 在开启 CONFIG_SCHED_PROXY_EXEC + CONFIG_SCHED_CLASS_EXT 的树上按作者描述合入 v5 草稿与 Andrea v13，跑 EXT→FAIR / FAIR→EXT / EXT→EXT / RT/DL→EXT 混合矩阵——作者自陈没有稳定的全混合运行时验证，这是明确缺口（testing）。
- 复核 5/5 的 rtime = se->exec_start - rq->core_sched_start 谓词在 core scheduling + proxy 叠加场景（同 donor 的 execution-owner handoff）下是否会丢服务量，把结论带回列表（review）。
- 自家分支若依赖 cgroup/RT 计费口径，可评估 4/5 新回调设计中「watchdog 记 rq->curr、service 跟 effective donor class」规则对 RLIMIT_RTTIME 行为的影响（extend）。

## 参考链接
- lore thread（v4 封面）: https://lore.kernel.org/all/20260909092901.2989564-1-sh_def@163.com/
- 作者对 4/5 NAK 的新设计: https://lore.kernel.org/all/20260910105402.2784718-1-sh_def@163.com/
- 作者对 5/5 的 task-clock 谓词重做: https://lore.kernel.org/all/20260910105514.2788543-1-sh_def@163.com/
- 作者对 3/5 的重排布局: https://lore.kernel.org/all/20260910105300.2781275-1-sh_def@163.com/
- Andrea 的跨系列协调: https://lore.kernel.org/all/aqGa0J1_LM99oDkP@gpd4/ 与作者回应 https://lore.kernel.org/all/20260910104928.2771533-1-sh_def@163.com/

---
id: sched-20260910-003
date: 2026-09-10
subject: "sched: Handle split scheduling and execution contexts in task ticks"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260909092901.2989564-1-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/20260909092901.2989564-1-sh_def@163.com/"
upstream_commit: null
fixes_commit: "aa4f74dfd42b"
merged_branch: null
current_version: v4
generated_at: "2026-09-11T10:00:00"
authors:
  - "Hui Su"
maintainers_involved:
  - "Peter Zijlstra"
patch_series:
  - version: v4
    msgid: "<20260909092901.2989564-1-sh_def@163.com>"
    date: "2026-09-09"
    summary: "5 补丁：task_tick() 去 task 参数并引入 donor 先/curr 后的公共分发器（1/5），NUMA 与 cache 移到 FAIR 执行上下文（2/5、3/5），RT 状态留 donor、watchdog 跟 curr（4/5），core slicing 用 task-clock 域度量 donor slice（5/5，Fixes aa4f74dfd42b）。"
    review_outcome: "09-09 Peter 要求重排 3/5 并 NAK 4/5；09-10 作者逐条回应：3/5 重排为单 donor 块+单 curr 块待复核，4/5 改为 sched_class 生命周期回调+RT 类消费事件，5/5 改 rtime=se->exec_start-rq->core_sched_start 谓词，1/5 与 Andrea Righi 对齐 SCX 所有权边界，确认 v5 携带全部改动。"
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "Peter Zijlstra 尚未对 4/5 的 sched_class 回调新设计与 3/5 重排布局表态"
    - "1/5 修改 sched_class::task_tick() 签名波及全部调度类，必须由 Peter 收下"
    - "与 proxy+sched_ext v13 系列在 task_tick_scx() 上存在已知文本冲突，需协调合入顺序"
    - "EXT 混合类转换的运行时矩阵未验证（集成树仅构建+启动）"
  next_action: "作者发 v5 携带新设计与重排布局，并与 Andrea 的 v13 系列约定合入顺序后补集成验证"
contribution_opportunities:
  - kind: testing
    description: "在 PROXY_EXEC+SCHED_CLASS_EXT 双开的树上合入 v5 草稿与 v13，跑 EXT→FAIR/FAIR→EXT/EXT→EXT/RT、DL→EXT 混合运行时矩阵，补作者自陈的验证缺口"
  - kind: review
    description: "复核 5/5 task-clock 谓词在 core scheduling + 同 donor execution-owner handoff 叠加场景下是否丢服务量"
  - kind: extend
    description: "评估 4/5 「watchdog 记 rq->curr、service 跟 effective donor class」规则对自家分支 RLIMIT_RTTIME 行为的影响"
source_email_count: 5
related_articles:
  - "sched-20260909-001"
  - "sched-20260903-001"
tags:
  - rt
  - core_sched
  - sched_ext
  - proxy_execution
---
