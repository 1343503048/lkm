# sched: Handle split scheduling and execution contexts in task ticks

## TL;DR
本文为增量更新，完整背景见 related_articles（sched-20260910-003 为 v4 分析）。Hui Su 于 09-13 14:47 发出 v5（4 补丁）：按 Peter 意见把 FAIR tick 重排为「donor 块 + 执行上下文块」、砍掉 RT watchdog 补丁改为独立的生命周期回调设计、task_tick_scx() 显式 donor-gated、core slice baseline 保留跨同 donor reselect。同日 Kayra Cizmeci 质疑补丁 1「单独无用」、作者回应拆分是为可评审性。Peter 尚未对 v5 表态，系列维持 under_review 但 v5 已完整交付 v4 承诺的全部改动。

## 背景与问题
proxy execution 把调度上下文（rq->donor）与执行上下文（rq->curr）分离后，scheduler tick 的各消费者归属出现不一致：NUMA 扫描、cache-aware 记账的输入状态跟执行任务，而调度策略与 slice 判断跟 donor。v4（5 补丁）曾引入 RT watchdog 处理但被 Peter NAK（不接受在 __schedule() 中间散落 RT 代码），并要求重排 FAIR tick。本篇只覆盖 v5 带来的变化与 09-13 新讨论，历史背景见 [[sched-20260910-003]]、[[sched-20260909-001]]、[[sched-20260903-001]]。

## 技术方案
v5 四补丁（基线 cba2348ab114391f5b1a00fa65c5b739f13f0563）：

- **1/4 sched: Dispatch task ticks for donor and execution classes**（接口与分发器）：`sched_class::task_tick()` 去掉 task 参数，各类通过 rq 选择自己拥有的状态；core 新增公共分发器 `task_tick(rq, queued)`——先调 donor 类，`sched_proxy_exec()` 且 curr 类不同时再调执行类。本补丁刻意保持各类 tick 行为 donor-gated，只引入接口与分发机制；task_tick_scx() 显式 donor-gated（执行上下文属于 sched_ext 而 donor 是其他类时直接返回，不做 SCX 策略工作），与 Andrea 的 sched_ext/proxy-execution 工作的所有权方向对齐。
- **2/4 sched/numa: Drive NUMA task tick from execution context**（Fixes 7de9d4f94638）：task_tick_numa() 操作执行任务拥有的 mm/NUMA 状态，且用记账到 rq->curr 的任务运行时驱动周期扫描，改到 curr 是 FAIR 时执行；donor tick 先跑，保证执行运行时先记账后消费（Suggested-by K Prateek Nayak、Tim Chen、Peter Zijlstra）。
- **3/4 sched/cache: Drive cache task tick from execution context**（Fixes df0d98475954）：task_tick_cache() 与 account_mm_sched() 同属 rq->curr 的记账路径，移到执行上下文块，避免执行任务的 cache 状态与 epoch 变陈旧（Suggested-by Tim Chen）。
- **4/4 sched/core: Fix donor slice accounting under proxy execution**（Fixes aa4f74dfd42b）：core scheduling 的 `__entity_slice_used()` 判断对 rq->donor 做，但 proxy 下任务运行时记到 rq->curr，donor 的 `sum_exec_runtime - prev_sum_exec_runtime` 几乎不动，force-idle 重调度永不触发。改用 per-rq 的 task-clock 基线 `core_sched_start`（选 donor 时快照 `se->exec_start`），`rtime = se->exec_start - rq->core_sched_start`；同 donor 的 execution-owner handoff 会做合成 put_prev_task()/set_next_task()，此时保留 baseline 不重置，选新 donor 或显式 reactivation 才刷新。存 struct rq 而非 sched_entity，避免 32 位 + CONFIG_SCHED_CORE 构型下 entity 变大。

RT watchdog 不再在本系列内：作者 09-13 凌晨在 v4 4/5（sched/rt: Fix RT watchdog accounting for proxy execution）回帖说明，新 WIP 从调度核心暴露通用 proxy 生命周期事件（`enum sched_proxy_event { START, BLOCK, STOP }` + `sched_class::proxy_event()` 回调），RT 类消费这些事件维持 watchdog 区间语义——watchdog 记 rq->curr、RT service 跟 effective donor class；mutex handoff 不再直接调回调，等执行任务下次进 __schedule() 持 rq 锁时上报 STOP。该 WIP 需要先与 Zhidao Su 的 proxy-walk 环检测工作调和（新的 retained blocked_donor 遍历假设链无环），并与 Andrea 的 sched_ext/proxy 工作处理 task_tick() 所有权重叠，因此下一版将是含补丁 1、2、3 和 core-slice 补丁的 4 补丁系列，RT 独立推进。

## 版本演进与当前进展
current_version: v5（2026-09-13 发出）。Changes since v4（cover letter 自述）：

- FAIR task tick 重排为一个 donor 块 + 一个执行上下文块，NUMA 与 cache 工作进后者（落实 Peter 09-09 的重排要求）；
- task_tick_scx() 保持 donor-gated，等待 sched_ext/proxy 集成单独推进；
- 同 donor 合成 reselect 时保留 core-slice baseline，新 donor 或显式 set-next reactivation 才重置；
- RT watchdog 补丁移出系列、独立推进（回应 Peter 的 NAK，改走生命周期回调设计）。

09-13 讨论：Kayra Cizmeci 指出 1/4 单独达不到 commit message 宣称的效果——DL donor + FAIR curr 的 proxy 场景下，FAIR 类被当执行类调到但因 donor-gated 直接返回，什么都没做，建议把补丁 1 和用例合并、并改写混淆的 commit message。作者回应：1/4 是行为保持的接口转换 + 分发器，2/3 补丁才是执行上下文的使用者，拆分让接口转换与 NUMA/cache 语义修复各自可评审、各带各的 Fixes:；同意 1/4 开头段落有误导，将改写为明示「准备性补丁」；若社区偏好分发器与第一个使用者一起进，可以 fold patch 2 into patch 1。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（09-09，历史）：3/5 重排要求与 4/5 NAK 是 v5 结构的直接成因。v5 交付后 Peter 尚未表态——这是当前最大的未决点：1/4 动 `sched_class::task_tick()` 全类签名，必须经他收下；4/4 的 task-clock 谓词方案也需他复核。
- **Kayra Cizmeci**（09-13）：质疑补丁 1 粒度（单独无行为收益）与 commit message 准确性。这是评审节奏类意见而非技术反对，作者已给出合理解释并承诺改写，但「1/2 是否合并」实际会把决定权留给 Peter。
- **Tim Chen / K Prateek Nayak**：v5 补丁的 Suggested-by 归属，09-13 当天无新回帖确认。
- 未解决焦点：RT watchdog 的 proxy_event 生命周期设计还没有任何维护者意见；它与 Zhidao Su 环检测工作的调和是作者自认的前置条件。

## 合入评估
likelihood: medium（v4 分析的 medium 维持：作者对全部 blocking 意见交付了 v5，但 Peter 尚未复核，且 1/4 的签名改动是高侵入面改动）。blocking_issues：Peter 对 v5（尤其 1/4 签名改动与 4/4 谓词）未表态；补丁 1 与补丁 2 是否合并待定；RT watchdog 生命周期设计未成形且需与 proxy-walk 环检测调和；sched_ext/proxy 混合运行时矩阵仍未验证（当前 Kconfig 两者互斥）。next_action：作者改写 1/4 commit message 后等 Peter 复核；RT 工作与环检测调和后单独立系列。

## 效果评估
无 benchmark 数据。v5 cover 给出的验证（作者自述）：

- x86_64 vmlinux/modules/bzImage 在主配置与 CONFIG_SCHED_PROXY_EXEC=n、CONFIG_SCHED_CORE=n、CONFIG_SCHED_CACHE=n、CONFIG_FAIR_GROUP_SCHED=n、CONFIG_NUMA_BALANCING=y、CONFIG_SCHED_CLASS_EXT=y 变体下构建通过；sched_ext selftests 构建成功；
- x86_64 QEMU 启动 smoke 与 feature-off 启动测试 PASS；exact-head 双节点 NUMA/proxy smoke PASS；
- CORE-01 同 donor 焦点测试：服务分摊到两个 execution owner，各自低于 force-idle 阈值、累计超过阈值并触发重调度，全程单一 core_sched_start baseline；
- 局限自述：仅 x86_64 运行时验证，无 32 位或 ARM 运行时验证；无混合 sched_ext/proxy 运行（配置互斥）。

## 我可以参与的点
- 混合矩阵测试（testing）：在 CONFIG_SCHED_PROXY_EXEC + CONFIG_SCHED_CLASS_EXT 双开的树上验证 EXT→FAIR / FAIR→EXT / EXT→EXT / RT/DL→EXT 转换路径——这是作者连续两版自陈的验证缺口，也是 OLK 类下游分支上不了游验证的真实场景。
- 复核 4/4 baseline 逻辑（review）：`rtime = se->exec_start - rq->core_sched_start` 在「同 donor reselect 保留、新 donor 刷新」两条路径的边界（如 donor 在 handoff 间隔内被 dequeue/再 enqueue）是否有漏网情形，把结论带回列表。
- RT 生命周期 WIP（discussion）：作者明确请求对 proxy_event START/BLOCK/STOP 设计提意见，尤其「blocked_donor 链无环」假设与 Zhidao Su 环检测工作的调和方式。
- 1/2 合并取舍（discussion）：Kayra 的补丁粒度质疑尚无维护者裁决，若对接口转换与语义修复的拆分粒度有实践观点，现在是给出输入的窗口。

## 参考链接
- lore thread（v5 cover）: https://lore.kernel.org/all/20260913064722.1534766-1-sh_def@163.com/
- Kayra 对 1/4 的质疑: https://lore.kernel.org/all/20260913120814.1273086-1-kayracizmeci@gmail.com/
- 作者回应（拆分理由与 commit message 改写承诺）: https://lore.kernel.org/all/36503a3fb742ca20fa218ec190a50932.sh_def@163.com/
- RT watchdog 独立推进与 WIP 生命周期设计: https://lore.kernel.org/all/c8b457d91942d655cea763b6094c9df4.sh_def@163.com/
- 需调和的关联工作——Zhidao Su proxy-walk 环检测: https://lore.kernel.org/r/20260722120346.93000-1-soolaugust@gmail.com/ ；Andrea sched_ext/proxy-execution: https://lore.kernel.org/r/20260831134338.1531664-1-arighi@nvidia.com/
- 前作分析: [[sched-20260910-003]]（v4）、[[sched-20260909-001]]、[[sched-20260903-001]]

---
id: sched-20260913-002
date: 2026-09-13
subject: 'sched: Handle split scheduling and execution contexts in task ticks'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260913064722.1534766-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20260913064722.1534766-1-sh_def@163.com/'
upstream_commit: null
fixes_commit: 'aa4f74dfd42b'
merged_branch: null
current_version: v5
generated_at: '2026-09-14T10:24:00'
authors:
  - 'Hui Su'
maintainers_involved:
  - 'Peter Zijlstra'
patch_series:
  - version: v4
    msgid: '<20260909092901.2989564-1-sh_def@163.com>'
    date: 2026-09-09
    summary: '5 补丁：task_tick() 去 task 参数并引入 donor 先/curr 后公共分发器、NUMA/cache 移执行上下文、RT watchdog 跟 curr、core slicing 用 task-clock 域谓词（Fixes aa4f74dfd42b）。'
    review_outcome: 'Peter Zijlstra 要求重排 3/5 并 NAK 4/5；作者 09-10 逐条回应（重排布局、RT 改生命周期回调、task-clock 谓词），承诺 v5。详见 sched-20260910-003。'
  - version: v5
    msgid: '<20260913064722.1534766-1-sh_def@163.com>'
    date: 2026-09-13
    summary: '4 补丁：FAIR tick 重排为 donor 块+执行上下文块（NUMA/cache 进后者）；task_tick_scx() donor-gated；core slice baseline 保留跨同 donor reselect；RT watchdog 补丁移出系列独立推进（proxy_event 生命周期回调 WIP）。'
    review_outcome: 'Kayra Cizmeci 质疑 1/4 单独无用并建议与 2 合并；作者回应拆分系可评审性考虑、承诺改写 commit message、可按偏好 fold patch 2 into 1；Peter 尚未表态。'
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'Peter Zijlstra 对 v5 尚未表态（1/4 动 sched_class::task_tick() 全类签名必须经他收取）'
    - '补丁 1 与补丁 2 是否合并待定（Kayra 质疑后的取舍）'
    - 'RT watchdog 生命周期设计与 proxy-walk 环检测工作的调和未完成'
    - 'sched_ext/proxy 混合运行时矩阵未验证（Kconfig 当前互斥）'
  next_action: '作者改写 1/4 commit message；等 Peter 复核 v5 结构与 4/4 谓词；RT 工作调和后独立成系列'
contribution_opportunities:
  - kind: testing
    description: '在 PROXY_EXEC+CLASS_EXT 双开树上跑 EXT→FAIR/FAIR→EXT/EXT→EXT/RT、DL→EXT 混合转换矩阵，补作者连续两版自陈的运行时验证缺口'
  - kind: review
    description: '复核 4/4 的 core_sched_start baseline 在同 donor reselect 保留/新 donor 刷新边界（donor 在 handoff 间隔内 dequeue/enqueue 等）是否丢服务量'
  - kind: discussion
    description: '对 RT watchdog 的 proxy_event START/BLOCK/STOP 生命周期 WIP 提意见，特别是 blocked_donor 链无环假设与环检测工作的调和'
  - kind: discussion
    description: '就补丁 1/2 是否合并（接口转换与首个使用者的拆分粒度）给出输入'
source_email_count: 8
related_articles:
  - sched-20260910-003
  - sched-20260909-001
  - sched-20260903-001
tags:
  - proxy_execution
  - core_sched
  - numa_balancing
  - sched_ext
  - rt
---
