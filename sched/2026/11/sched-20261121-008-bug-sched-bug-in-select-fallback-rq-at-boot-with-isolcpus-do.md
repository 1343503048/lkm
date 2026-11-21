# [BUG] sched: BUG() in select_fallback_rq() at boot with isolcpus=domain on the boot CPU and CONFIG_CPUSETS=n

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261118-004：Waiman Long 报告 `isolcpus=domain` + boot CPU + `CONFIG_CPUSETS=n` 下 `select_fallback_rq()` 触发 BUG()；Frederic Weisbecker 与 Waiman 讨论 boot CPU 能否被隔离。
- sched-20261119-012：Mathieu Desnoyers 定性为回归（`bf5b0c27fad2`），支持 Waiman「拒绝把 boot CPU 域隔离」的修法，愿提供测试资源。
- sched-20261120-020：Frederic 表态「We should forbid that on all archs.」并堵上 ABI 顾虑——该配置已受支持、不能直接移除。
- sched-20261121-008（今天）：**修复落地**——Waiman 补充观察「CPU 0 在 `tick_nohz_init()` 会被自动清出 nohz_full（`CONFIG_PM_SLEEP_SMP && !CONFIG_PM_SLEEP_SMP_NONZERO_CPU` 下）」，并发出 PATCH-next 系列（1/3 统一 `tick_nohz_full_mask` 与 `HK_TYPE_KERNEL_NOISE`，2/3 禁止 boot CPU 被域隔离，见 sched-20261121-006/007）。

## 背景与问题

（承接 sched-20261118-004 … 20261120-020）`isolcpus=domain` 把指定 CPU 剥离成隔离域；boot CPU 被指定且 `CONFIG_CPUSETS=n` 时，启动早期 `select_fallback_rq()` 找不到合法 fallback CPU 触发 BUG()。回归责任在 `bf5b0c27fad2`（切到 `HK_TYPE_DOMAIN`）。

## 技术方案

今日推进：Waiman 指出大多数内核（`CONFIG_PM_SLEEP_SMP && !CONFIG_PM_SLEEP_SMP_NONZERO_CPU`，PPC 之外默认）下 CPU 0 本就会被 `tick_nohz_init()` 从 nohz_full 清出——这为其「boot CPU 也不该进 isolcpus」的修法提供了对称性依据。随后他发出 PATCH-next 修复系列：2/3 直接把 boot CPU 从 isolcpus 范围清除并打警告（+ 更新文档），1/3 先统一两个 cpumask。这与前日「拒绝 + 打印 + 继续启动」的一致结论吻合。

## 版本演进与当前进展

*current_version: 无补丁 → 修复系列已发（2026-11-21）*。今日无对 bug 报告的进一步定性讨论，进展为修复补丁发出（sched-20261121-006/007）。

## Maintainer 意见与讨论焦点

- **Waiman Long**：补充 CPU 0 nohz_full 自动清除的对称性观察，并作为作者发出修复系列。
- **Frederic Weisbecker**（前情）：同意所有架构上拒绝 boot CPU 域隔离，提示隔离支持不能移除（ABI）。
- **Mathieu Desnoyers**（前情）：定性回归、支持拒绝 + 打印 + 继续启动。
- 无 NAK；方向一致，修复已由 Waiman 发出。

## 合入评估

*likelihood=high*。修复补丁已落地、方向获涉及方一致同意，进入补丁评审阶段。*blocking_issues*：修复系列 1/3 有 lkp 构建警告（`EXPORT_SYMBOL`/`__init` 冲突）；行为变更需维护者确认。*next_action*：清掉 1/3 构建警告后由维护者评审收取。

## 效果评估

无数据；问题表现为启动期 BUG()/panic，修复后应能正常启动并给出警告提示。

## 我可以参与的点

- **testing**：在含/不含 CONFIG_CPUSETS、PPC 与非 PPC 上验证修复系列后 `isolcpus=domain,0` 可启动、无 suspend 回归（承接 sched-20261121-007）。
- **review**：核对修复系列 1/3 的 mask 一致化与 2/3 的 boot CPU 清除是否彻底覆盖回归点。

## 参考链接

- lore thread（Waiman 今日回复）: https://lore.kernel.org/all/5a16dda3-f128-4109-a52b-f51e01309b35@redhat.com/
- 修复系列 2/3: https://lore.kernel.org/all/20261121031329.240177-3-longman@redhat.com/

---
id: sched-20261121-008
date: '2026-11-21'
subject: "[BUG] sched: BUG() in select_fallback_rq() at boot with isolcpus=domain on the boot CPU and CONFIG_CPUSETS=n"
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<dd335ee6-c879-4bee-9ea8-6d9e9216fb0e@redhat.com>"
lore_url: "https://lore.kernel.org/all/5a16dda3-f128-4109-a52b-f51e01309b35@redhat.com/"
authors: [Waiman Long]
maintainers_involved: [Frederic Weisbecker]
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["修复系列 1/3 有 lkp 构建警告", "行为变更需维护者确认"]
  next_action: "清掉 1/3 构建警告后由维护者评审收取修复系列"
contribution_opportunities:
  - kind: testing
    description: "验证修复系列后 isolcpus=domain,0 可启动、无 suspend 回归"
  - kind: review
    description: "核对 1/3 mask 一致化与 2/3 boot CPU 清除是否彻底覆盖回归点"
generated_at: "2026-11-22T01:00:00+08:00"
source_email_count: 91
related_articles: [sched-20261118-004, sched-20261119-012, sched-20261120-020]
tags: [cgroup, topology, crash]
---