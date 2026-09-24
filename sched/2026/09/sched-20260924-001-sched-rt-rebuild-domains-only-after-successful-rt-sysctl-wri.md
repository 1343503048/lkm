# sched/rt: Rebuild domains only after successful RT sysctl writes

## TL;DR
Joseph Salisbury 的修复补丁：把 `rebuild_sched_domains()` 从「每次 RT sysctl 写入前无条件执行」改为「仅当写入成功且值真实变化时」才执行，消除 RT 周期/运行时间参数每次读取都触发全量调度域重建的开销。本日 Chengfeng Lin 给出独立实测：在 v7.2 上该补丁把 RT sysctl 读延迟从约 8.57us 降到 0.264us（-96.9%），并确认写入语义不变。属副作用可控的纯优化修复，离合入只差一轮维护者收尾。

## 背景与问题
RT sysctl 读写路径上，`sched_rt_period_us`/`sched_rt_runtime_us` 等参数在每次 sysctl 处理时都会走 `rebuild_sched_domains()` 与 deadline 带宽重算，即便本次只是**读取**或**同值写入**也照做。这带来两类问题：

1. 高频监控/调优工具反复 read 这些 sysctl 时，每次都触发代价高昂的调度域重建（涉及 CPU 拓扑扫描、持全局锁），读延迟被无谓放大。
2. `rebuild_sched_domains()` 有全局副作用（重建所有 CPU 的调度域、invalid 缓存），同值写入或无效写入本不该触发。

本补丁把重建动作收窄到「写入成功且参数真正变化」的路径上。

## 技术方案
补丁调整 RT sysctl 处理逻辑：仅在 sysctl 写处理成功、且参数确实发生变化的条件下才调用 `rebuild_sched_domains()` 与相关的 deadline 带宽重新记账。失败的写入（非法文本、越界值、非法 period/runtime 组合）保持旧值不变，也跳过重建。补丁代码目前以独立验证者复现的形态存在（v1，thread root `<20260313183716.990792-1-joseph.salisbury@oracle.com>`），本日邮件未附完整 diff。

## 版本演进与当前进展
- v1（2026-03-13，thread root `<20260313183716.990792-1-joseph.salisbury@oracle.com>`）发出后暂无本日报内的跟进；本日（09-24）Chengfeng Lin 独立在 v7.2 上验证并提供量化数据。

## Maintainer 意见与讨论焦点
- **Chengfeng Lin（测试者，非补丁作者）**：给出完整 microbenchmark——「original A → patched → original B」三段式、每轮重启、4096 次 pread、3 次热身 + 9 次采样。两个 RT 读参数降幅均为 96.91%/96.92%，RR 控制项变化仅 0.83%（在噪声范围内），确认补丁只改善了 RT 读路径、不改变其它行为；另用独立探针确认补丁后的 RT 读跳过了 `rebuild_sched_domains()` 与 deadline 带宽重算，写入（含同值写入）仍正确触发全局更新。
- 本日无维护者（Peter Zijlstra / RT 相关）置评。

## 合入评估
*likelihood=high*。方向明确（消除读取路径上的无谓重构）、优化动机充分、已有独立的可复现量化背书（-96.9%）。但本日只见到测试背书、未见补丁作者的响应或维护者正式 ACK，且补丁源自较早（03-13）的 thread root，需确认其在当前开发分支上的适用性。*blocking_issues*：无明确反对项，主要待维护者收取，并确认补丁在当前开发分支上的适配（本次测试基于 v7.2，测试者已做 context 适配）。*next_action*：作者/维护者确认补丁适用于当前主线后正式收取。

## 效果评估
Chengfeng Lin 实测（bare-metal i7-12700KF，20 逻辑 CPU，全速性能 governor、无 Turbo、`CONFIG_RT_GROUP_SCHED=n`）：

- `sched_rt_period_us`：8547.294 → 264.575 ns/read（-96.91%）
- `sched_rt_runtime_us`：8574.240 → 263.690 ns/read（-96.92%）
- `sched_rr_timeslice_ms`（对照）：253.4 → 250.3 → 251.3（仅 0.83% 波动，无意义变化）

属可复现的 read-loop microbenchmark；测试者本人也注明这些是读循环微基准而非应用级计时，且未覆盖并发写、CPU hotplug、DL admission 失败等路径。

## 我可以参与的点
- kind=testing：补上测试者明确没覆盖的场景——并发写、CPU hotplug 期间的 RT sysctl 写入、带活跃 SCHED_DEADLINE 任务时的 DL admission 失败路径，确认收窄重建条件后这些场景无回归。
- kind=review：核对「成功写入且值变化」的判定条件是否精确覆盖所有合法/非法输入分支（含同值写入）。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260313183716.990792-1-joseph.salisbury@oracle.com/
- 测试回复: https://lore.kernel.org/all/179018297078.3.9126136955304841169@gmail.com/

---
id: sched-20260924-001
date: '2026-09-24'
subject: 'sched/rt: Rebuild domains only after successful RT sysctl writes'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260313183716.990792-1-joseph.salisbury@oracle.com>'
lore_url: 'https://lore.kernel.org/all/20260313183716.990792-1-joseph.salisbury@oracle.com/'
authors:
  - 'Joseph Salisbury'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260313183716.990792-1-joseph.salisbury@oracle.com>'
    date: '2026-03-13'
    summary: '仅当 RT sysctl 写入成功且值变化时才 rebuild_sched_domains()'
    review_outcome: 'Chengfeng Lin 独立实测 -96.9% 读延迟，无维护者正式置评'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '作者/维护者 rebase 到当前主线并附实测数据后收取'
contribution_opportunities:
  - kind: testing
    description: '补测并发写、CPU hotplug 期写入、活跃 DL 任务 admission 失败路径'
  - kind: review
    description: '核对重建条件是否精确覆盖所有合法/非法输入分支'
generated_at: '2026-09-25T09:00:00'
source_email_count: 1
related_articles: []
tags:
  - rt
  - rt_bandwidth
---