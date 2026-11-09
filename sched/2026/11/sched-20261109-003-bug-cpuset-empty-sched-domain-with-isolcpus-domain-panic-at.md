# cpuset: empty sched domain with isolcpus=domain, panic at CPU offline

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261108-001：Mathieu Desnoyers 报告一个可复现 panic——`isolcpus=domain` 启动时 cpuset 分区可把所有 housekeeping CPU 拿走，顶层 cpuset 只剩隔离 CPU、生成空调度域，随后 CPU offline 触发 `partition_sched_domains()` 越界读 `cpu_rq(NR_CPUS)->sd` 直接内核 panic。附根因分析与修复草案。
- sched-20261109-003（今天）：**Waiman Long（cpuset/cgroup 维护者）确认这是已知问题、正在 cpuset 代码里修**（保证顶层 cpuset 至少留一个 online housekeeping CPU），并指向 Guopeng Zhang 的系列；Mathieu 同意放弃自己的修复草案、改用 Guopeng 系列，可在其复现环境上测试 v3，并指出 `_cpu_down()` 草案覆盖了 cpuset 修不到的一个角例（最后一个 HK CPU 无分区可还）。

## 背景与问题

（承接 sched-20261108-001）`isolcpus=domain` 启动时部分 CPU 被隔离，cpuset 分区允许子分区把顶层 cpuset 的所有 housekeeping CPU 占走，顶层 cpuset 只剩隔离 CPU → `generate_sched_domains()` 生成空调度域 → 下次 CPU offline 时 `partition_sched_domains()` 在空 mask 上 `cpumask_first()` 返回 `NR_CPUS`、越界读 `cpu_rq(64)->sd` 触发 page fault panic。今日讨论聚焦归属与修法：这个 bug 应在 cpuset 代码里从源头修（保证顶层调度域至少留一个 HK CPU），而非在 `generate_sched_domains()` 里堵空调度域生成。

## 技术方案

今日确认的修法路径：

- **主方案（Waiman/Guopeng Zhang 系列）**：在 cpuset 分区创建/更新与 CPU hotplug 路径都要求「顶层 cpuset 的调度域保留至少一个 active boot domain housekeeping CPU」，从源头杜绝空顶层调度域。见 `https://lore.kernel.org/lkml/20261105130344.664336-1-guopeng.zhang@linux.dev/`。
- **Mathieu 的 `_cpu_down()` 草案（今日放弃，但保留角例价值）**：Waiman 表示「该补丁正确、不反对，但修好 cpuset 后可能不再必要」。Mathieu 指出该草案覆盖一个 cpuset 修不到的角例——无分区时最后一个 online housekeeping CPU 下线，没有任何分区能把它「还回来」。

## 版本演进与当前进展

*current_version: null（[BUG] 讨论线程，无版本化补丁）*。今日：Waiman 确认是已知问题、cpuset 侧正在修；Mathieu 决定放弃自己的 `_cpu_down()` 草案、改用 Guopeng 系列，并承诺在复现环境（5 vCPU + `isolcpus=domain,0,1`）上测试 Guopeng 系列 v3。

## Maintainer 意见与讨论焦点

- **Waiman Long（cpuset/cgroup 维护者）**：明确「已知问题，我们正在 cpuset 代码里修，保证顶层 cpuset 至少留一个 online housekeeping CPU」；对 Mathieu 的 `_cpu_down()` 草案「正确 AFAICS、不反对，但修好 cpuset 后可能不必要」。
- 无 NAK。唯一待跟进点：`_cpu_down()` 草案覆盖的「最后 HK CPU 无分区可还」角例，是否需要在 Guopeng 系列之外单独收。

## 合入评估

*likelihood=high*（对「问题会被修复」而言）。bug 根因清晰、复现可靠，修复已归口到 cpuset 维护者 Waiman 的系列（Guopeng Zhang v2/v3），Mathieu 愿意提供复现环境测试。*blocking_issues*：① Guopeng 系列 v3 尚未在 Mathieu 的复现环境实测；② `_cpu_down()` 草案的角例是否需单独收未定。*next_action*：Guopeng 出 v3，Mathieu 在其复现环境回归测试。

## 效果评估

panic 为作者一次性实测触发（「I hit it once」），今日无新增量化数据。修复正确性依赖 Guopeng 系列 v3 的回归验证（Mathieu 已承诺在其复现环境跑）。

## 我可以参与的点

- **testing**：在 `isolcpus=domain` 平台复跑「cpuset 分区抢占 housekeeping CPU + CPU offline」循环，验证 Guopeng 系列 v3 后无空调度域、不 panic。
- **review**：评估 `_cpu_down()` 草案覆盖的「最后一个 HK CPU 无分区可还」角例是否需要在 cpuset 系列之外单独补防御。

## 参考链接

- Waiman 的确认回帖: https://lore.kernel.org/all/12cb0bee-57aa-4609-bc2e-77806e0b6805@redhat.com/
- Mathieu 放弃草案、改用 Guopeng 系列: https://lore.kernel.org/all/20261108184620.1548615-1-mathieu.desnoyers@efficios.com/
- Guopeng Zhang 的 cpuset 系列: https://lore.kernel.org/lkml/20261105130344.664336-1-guopeng.zhang@linux.dev/

---
id: sched-20261109-003
date: '2026-11-09'
subject: "cpuset: empty sched domain with isolcpus=domain, panic at CPU offline"
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<12cb0bee-57aa-4609-bc2e-77806e0b6805@redhat.com>"
lore_url: "https://lore.kernel.org/all/12cb0bee-57aa-4609-bc2e-77806e0b6805@redhat.com/"
authors: [Mathieu Desnoyers]
maintainers_involved: [Waiman Long]
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "Guopeng 系列 v3 尚未在 Mathieu 的复现环境实测"
  next_action: "Guopeng 出 v3，Mathieu 在其复现环境回归测试"
contribution_opportunities:
  - kind: testing
    description: "在 isolcpus=domain 平台复跑 cpuset 分区抢占 HK CPU + offline 循环，验证 Guopeng v3 不 panic"
  - kind: review
    description: "评估 _cpu_down() 草案的「最后 HK CPU 无分区可还」角例是否需单独补防御"
generated_at: "2026-11-10T09:00:00+08:00"
source_email_count: 3
related_articles: [sched-20261108-001]
tags: [cgroup, topology, crash, affinity]
---
