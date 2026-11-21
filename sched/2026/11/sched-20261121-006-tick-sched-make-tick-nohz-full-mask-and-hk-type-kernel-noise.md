# tick/sched: Make tick_nohz_full_mask and HK_TYPE_KERNEL_NOISE cpumask consistent

## TL;DR

Waiman Long 的 3 补丁系列（PATCH-next）之一：修 `tick_nohz_full_mask` 与 `HK_TYPE_KERNEL_NOISE` 两个 cpumask 长期不一致的问题，属于其修复「boot CPU 被域隔离导致启动 BUG()」的前置一致化。当日 kernel test robot 报出构建警告：`EXPORT_SYMBOL used for init symbol 'housekeeping_set_cpu'`（powerpc W=1），需小改后重发。

## 背景与问题

`nohz_full` 启动参数先被传给 `tick_nohz_full_setup()` 建立 `tick_nohz_full_mask`，随后 `HK_TYPE_KERNEL_NOISE` cpumask 被设为给定 CPU 列表的补集。timer 与 RCU 的一部分代码直接用 `tick_nohz_full_mask`，另一部分 timer、调度器与其它子系统用 `HK_TYPE_KERNEL_NOISE`。两处不一致的根源有二：① 命令行出现多个 `nohz_full=` 时，只有第一个传给 `tick_nohz_full_setup()`，而 `HK_TYPE_KERNEL_NOISE` 由最后一个 `nohz_full` 参数控制；② `CONFIG_PM_SLEEP_SMP && !CONFIG_PM_SLEEP_SMP_NONZERO_CPU`（PC 上 PowerPC 之外常见默认）下 boot CPU 会被从 `tick_nohz_full_mask` 清除（维护 timekeeping），但对应的 `HK_TYPE_KERNEL_NOISE` 不动。这与 Waiman 在 [BUG] select_fallback_rq 线程里的观察一致（CPU 0 在 `tick_nohz_init()` 被自动清出 nohz_full）。

## 技术方案

对第一个不一致：每次出现 `nohz_full` 参数都调用 `tick_nohz_full_setup()`（而非仅第一次）；并同步维护 boot CPU 清除后的 `HK_TYPE_KERNEL_NOISE`（第二处不一致）。补丁顺带 `EXPORT_SYMBOL` 导出 `housekeeping_set_cpu`（该符号被声明为 `__init`，触发下述构建警告）。

## 版本演进与当前进展

*current_version: v1（2026-11-21，`<20261121031329.240177-2-longman@redhat.com>`，PATCH-next 1/3）*。首版，当日收到 kernel test robot 构建警告。

## Maintainer 意见与讨论焦点

- **kernel test robot（0-day CI，非维护者）**：`powerpc-akebono_defconfig`、W=1、clang 下报 `modpost: vmlinux: EXPORT_SYMBOL used for init symbol 'housekeeping_set_cpu'. Remove __init or EXPORT_SYMBOL.`
- 无 NAK；属机械的符号导出/__init 冲突，需去掉 `__init` 或 `EXPORT_SYMBOL` 其一。

## 合入评估

*likelihood=medium*。方向清晰、直接支撑 boot CPU 隔离修复，但当前有构建警告需先清。*blocking_issues*：`EXPORT_SYMBOL` 与 `__init` 冲突的 modpost 警告。*next_action*：作者去掉 `housekeeping_set_cpu` 的 `__init`（或改为不导出）后重发，并与同系列 2/3、3/3 一起评审。

## 效果评估

无性能数据；属正确性/一致化修复，收益体现为 boot CPU 隔离语义一致（承接同系列 2/3 对启动 BUG() 的修复）。

## 我可以参与的点

- **review**：核对多个 `nohz_full=` 参数与 PM_SLEEP 路径下两个 cpumask 的最终一致性、`housekeeping_set_cpu` 导出后有无并发风险。
- **testing**：在带多个 nohz_full 参数、及 CONFIG_PM_SLEEP_SMP 的 PPC/非 PPC 内核上验证两 mask 一致。

## 参考链接

- lore thread（1/3）: https://lore.kernel.org/all/20261121031329.240177-2-longman@redhat.com/
- lkp 构建警告: https://lore.kernel.org/all/202611211717.qIDq0wIX-lkp@intel.com/

---
id: sched-20261121-006
date: '2026-11-21'
subject: "tick/sched: Make tick_nohz_full_mask and HK_TYPE_KERNEL_NOISE cpumask consistent"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261121031329.240177-2-longman@redhat.com>"
lore_url: "https://lore.kernel.org/all/20261121031329.240177-2-longman@redhat.com/"
authors: [Waiman Long]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261121031329.240177-2-longman@redhat.com>"
    date: '2026-11-21'
    summary: "PATCH-next 1/3：统一 tick_nohz_full_mask 与 HK_TYPE_KERNEL_NOISE，多次 nohz_full 参数与 boot CPU 清除均同步"
    review_outcome: "lkp 报 EXPORT_SYMBOL/__init 冲突"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["EXPORT_SYMBOL 与 __init 冲突的 modpost 警告"]
  next_action: "去掉 housekeeping_set_cpu 的 __init 或 EXPORT_SYMBOL 后重发"
contribution_opportunities:
  - kind: review
    description: "核对多 nohz_full 参数与 PM_SLEEP 路径下两 mask 一致性、housekeeping_set_cpu 导出并发安全"
  - kind: testing
    description: "多 nohz_full 参数及 CONFIG_PM_SLEEP_SMP 的 PPC/非 PPC 内核验证两 mask 一致"
generated_at: "2026-11-22T01:00:00+08:00"
source_email_count: 91
related_articles: []
tags: [nohz, affinity]
---