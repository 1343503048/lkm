# sched_ext: Reset cpuperf_target when a sub loses SCX_CAP_PERF or dies

> **subject**：`sched_ext: Reset cpuperf_target when a sub loses SCX_CAP_PERF or dies`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261004-004：Tao Cui 报告并修复 sched_ext 子调度器生命周期漏洞——持有 `SCX_CAP_PERF` 的子调度器把 cpuperf target 写低后消失（cap 回收/kill/detach/cgroup 移除），target 残留：`scx_bpf_sub_revoke()` 只清 caps 位图、`scx_sub_disable()` 重定任务但都不碰 `rq->scx.cpuperf_target`；读侧门 `scx_cpuperf_target()` 只测全局 `scx_enabled()`，root 调度器运行期间 schedutil 持续消费陈旧 target，switched-all 模式下 CPU 被钉死在低频（scx_simple 从不写 cpuperf，钉死无界）。v1 以 irq_work + disable 扫描双路复位。
- sched-20261006-006（今天）：**v2 发出**，修复面显著扩大——(1) disable 路径扫描改持 `scx_enable_mutex + cpus_read_lock()`（防与 root disable 的 `scx_cid_retire_tables()` 竞争、防 hotplug 击穿 cpu_online 测试）并补 RCU 读侧（表是 `__rcu` 注解、sweeper 可抢占）；(2) `scx_online_ecaps()` 在 CPU 回线时恢复中性基（此前离线时错过复位的 CPU 回线即恢复钉死）；(3) revoke 的写门关闭点（dispatch_one 折叠 ecaps 的 rq 锁临界区）同步折叠回中性基，封掉「仍在跑的子调度器把 IPI 复位后的值再污染回去」的窗口；(4) `scx_bpf_cidperf_set()` 拒绝垂死调度器的写入。changelog 注明多项改动吸收 Sashiko 的 review（该 review 未进当日缓存）。实测：kill 子调度器后 target 立即回 `SCX_CPUPERF_ONE`；离线期间 kill 的 CPU 回线时恢复中性基；十轮加载/卸载 + hotplug 交织 lockdep/KASAN 干净。

## 背景与问题

（承接 sched-20261004-004）sched_ext 子调度器持有 `SCX_CAP_PERF` 时可通过 `scx_bpf_cidperf_set()` 写 cpuperf target；调度器消失（revoke/kill/detach/cgroup removal）后写门关闭但**旧值永不清除**——schedutil 在 switched-all 模式下不加 CFS 利用率，CPU 被陈旧低频 target 钉死，直到 sched_ext 整体 disable/enable。v1 的双路复位（revoke 路 irq_work + disable 路扫描）有四个窗口：扫描与 root disable 的表退休竞争、hotplug 击穿 cpu_online 测试、RCU 注解违规、IPI 复位后仍存活的写者再污染。

## 技术方案

v2（`<20261006142834.2815197-1-cui.tao@linux.dev>`，`Fixes: 3a21e34eb258`）四个复位锚点 + 中性基原则：

- **revoke 路双保险**：`scx_bpf_sub_revoke()` 对被回收 cid 的 CPU 排队复位（per-CPU irq_work，因调用点持 pshard 锁禁 IRQ、可能已持别的 rq 锁，不能跨 CPU 取 rq 锁）；**折叠点复位**——revoke 的写门在目标 CPU dispatch_one 折叠 ecaps sync 时才关闭，故折叠的同一 rq 锁临界区里同步恢复中性基，与竞态写入及幸存共持有者的写入有序。两路分工：IPI 立即复位（fold 被高类 hog 无限推迟或不再 dispatch 的 CPU）；fold 点关门（持续远程写者反复污染后最终纠正）。
- **disable 路扫描加固**：`scx_sub_disable()` 在 unlink+drain 后扫该调度器 pshard 的 `SCX_CAP_PERF` cmask、对每个持 cap 的 CPU 排队复位；扫描持 `scx_enable_mutex`（防并发 root disable 跑到 `scx_cid_retire_tables()`——`drain_descendants()` 只等后代 unlink）+ `cpus_read_lock()`（防 CPU 在 cpu_online() 测试后离线）+ RCU 读侧（表 `__rcu`、sweeper 可抢占）。
- **回线恢复**：`scx_online_ecaps()` 在 CPU 重新上线时恢复中性基（先刷 rq clock 保证 `cpufreq_update_util()` 的断言）——离线时错过复位的 CPU 不再带着陈旧 target 回线。
- **垂死写者拒绝**：`scx_bpf_cidperf_set()` 拒绝 dying 调度器（扫描与 `ops.exit()` 之间、及其后 timer/tracer 窗口仍可能执行，写入会落在最终复位之后无人清理）。
- **hotplug 边界**：revoke 路不能钉住 hotplug——CPU 在测试与排队间标离线会触发 `irq_work_queue_on()` 的 WARN_ON_ONCE 一次，但排队的工作仍会被 dying-cpu/re-online flush 或 RT 的 per-CPU irq_work kthread 投递，两种顺序都终结于中性基。**过度复位是有意的**：仍共享 cap 的调度器下次更新会重写自己的 target。

## 版本演进与当前进展

- v1（10-04，`<20261004012721.615419-1-cui.tao@linux.dev>`，见 sched-20261004-004）：双路复位首发。
- v2（10-06 22:28 北京，`<20261006142834.2815197-1-cui.tao@linux.dev>`）：四处加固（mutex+cpus_read_lock+RCU、online 恢复、fold 点复位、垂死写入拒绝）。changelog 标注两项吸收 Sashiko 意见。当日无维护者回帖。

## Maintainer 意见与讨论焦点

- **Tao Cui**（麒麟，作者）：v2 对锁序/生命周期窗口的推演极为细致（每条路径的竞态都有对应排序论证）。
- **Tejun Heo**（sched_ext 维护者）：当日未回帖。v1/v2 期间未见其表态——而 cap 生命周期归属正是其在后续 sub_child_ecaps_updated 系列里主张「last-writer-wins、恢复责任归 grant 方」的领域，作者的内核侧复位方案与该主张存在方向张力（后续演进见 sched-20261008-004）。
- 焦点：内核侧主动复位 vs 「谁 grant 谁恢复」的契约划分——v2 仍是内核侧全兜底方案。

## 合入评估

*likelihood=medium*。修复真实（lockdep+KASAN+行为测试背书）、竞态论证完整；但 Tejun 未表态，且其后续系列显示其更倾向把恢复责任放到 BPF 侧父调度器（ops.sub_detach/sub_child_ecaps_updated）——本补丁与该方向竞争。*blocking_issues*：Tejun 的方向裁决未落地（内核复位 vs BPF 侧恢复）。*next_action*：等 Tejun 对 v2 的态度（合入或以其 sub_child_ecaps_updated 系列取代）。

## 效果评估

作者实测（lockdep 内核 VM）：

- 子调度器写 target=1 后被 kill：基线下满载 CPU 的 `rq->scx.cpuperf_target` 残留 1；v2 立即回 `SCX_CPUPERF_ONE`。
- kill 前 CPU 已离线：基线回线后恢复钉死；v2 回线即恢复中性基。
- 对存活子调度器 revoke `SCX_CAP_PERF`：门关闭时复位、其后 cap 门保持中性基。
- 持 cap 时热插拔循环：回线恢复基、直到子调度器重写。
- 十轮子调度器加载/卸载 + 交织 hotplug：lockdep 与 KASAN 全干净。

## 我可以参与的点

- `review`：核对 fold 点复位与 IPI 复位的重叠场景——「IPI 已复位、fold 又复位一次」的幂等性（都写 SCX_CPUPERF_ONE 应无害，但可确认无 A-B-A 写入次序问题）。
- `discussion`：在 Tejun 的 sub_child_ecaps_updated 讨论中对比两方案的残余差距——内核复位覆盖「父调度器忘记恢复」（scx_simple 类）场景，BPF 侧恢复覆盖「父级知道委派」场景；两者是否需要共存可作为设计输入。

## 参考链接

- v2 补丁: https://lore.kernel.org/all/20261006142834.2815197-1-cui.tao@linux.dev/
- v1（10-04）: https://lore.kernel.org/all/20261004012721.615419-1-cui.tao@linux.dev/

---
id: sched-20261006-006
date: '2026-10-06'
subject: 'sched_ext: Reset cpuperf_target when a sub loses SCX_CAP_PERF or dies'
subsystem: sched_ext
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20261006142834.2815197-1-cui.tao@linux.dev>'
lore_url: 'https://lore.kernel.org/all/20261006142834.2815197-1-cui.tao@linux.dev/'
authors:
  - 'Tao Cui'
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: '<20261004012721.615419-1-cui.tao@linux.dev>'
    date: '2026-10-04'
    summary: 'irq_work + disable 扫描双路复位 cpuperf_target'
    review_outcome: '无维护者回帖'
  - version: v2
    msgid: '<20261006142834.2815197-1-cui.tao@linux.dev>'
    date: '2026-10-06'
    summary: '扫描加固（mutex+cpus_read_lock+RCU）、回线恢复、fold 点复位、垂死写入拒绝'
    review_outcome: '发布当日无回帖；吸收 Sashiko 意见（未进缓存）'
related_articles:
  - sched-20261004-004
upstream_commit: null
fixes_commit: '3a21e34eb258'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: 'Tejun 未表态；与「谁 grant 谁恢复」契约的方向竞争'
  next_action: '等 Tejun 对 v2 的方向裁决'
generated_at: '2026-10-07T01:00:00'
---
