# sched/eevdf: Move to a single runqueue

## TL;DR
ARM 的 Aishwarya Rambhadran 报告 v7.2 → v7.3 周期在 AWS Graviton3 上的 schbench p99 请求延迟回归，用 Fastpath 自动化 bisect 定位到「sched/eevdf: Move to a single runqueue」这一 commit。整体 schbench 结果为中性（部分配置改善、部分回退），但个别线程配置出现 ~30% 的 p99 延迟回退。作者正待 Peter Zijlstra 回应这是否是单运行队列改动的预期取舍。

## 背景与问题
报告人用 Fastpath（Linux 内核性能基准工具）对比 v7.2 与 v7.3 周期，在 AWS Graviton3（m7g.metal）上跑 schbench。整套 schbench 无显著回退，结果随线程配置呈现改善与回退混合；但少数配置出现较大的 p99 请求延迟回退。典型数据（v7.2 → v7.3-rc4）：

- message-thread:16, worker-thread:16：662869 us → 969557 us（**-31.63%**）
- message-thread:64, worker-thread:4：730453 us → 942251 us（**-22.48%**）
- message-thread:32, worker-thread:4：74251 us → 56725 us（**+30.90%**，改善）

对 m16/t16 的 p99 回退做 Fastpath 自动 git bisect，把「sched/eevdf: Move to a single runqueue」判为 first bad commit：原始回退约 30.9%，可复现性校验（20 次重复、2 次开机会话）显示约 27.8% 回退。报告人指出该 commit 改变了 EEVDF 运行队列组织、本意部分是为了解决层级公平/ cgroup 调度的延迟问题，且其之上已有后续修复，如 `68e37487810a`（"sched/fair: Fix flat hierarchy"，`Fixes: 85570f10a4c6`）。

## 技术方案
本文为回归报告，不含补丁方案。核心疑点是单运行队列（single runqueue）把 EEVDF 的层级结构拍平后，在某些公平/ cgroup 调度配置下 p99 尾部延迟是否产生了与收益不对称的回退——报告人希望确认这是否是单运行队列改动的预期权衡，还是值得进一步排查的回归。

## 版本演进与当前进展
- 报告（v7.3 周期，09-23 22:21 入缓存，`<bd81bbec-ee59-401a-bec6-116196ad3a34@arm.com>`）当日发出，尚未见维护者回应。

## Maintainer 意见与讨论焦点
当日无维护者回复（报告直指 Peter Zijlstra 为收件人）。报告人主动提出可补充更多测试或完整 bisect 数据，态度是「求证而非断言」，无争议。

## 合入评估
likelihood=unknown。这是对已合入主线（v7.3）的调度改动提出的性能回退质疑，需先确认是否为预期权衡。blocking_issues：回退是否属「预期取舍」尚无定论；单运行队列改动本身无 Fixes 可回退（改的是架构层面），若有问题需进一步针对性修复。next_action：Peter 及 EEVDF 相关维护者回应定性，作者补充完整 bisect/测试数据。

## 效果评估
报告给出的为 schbench p99 实测数字（上文已列），为定量数据；但整体 schbench 结果为混合（无全局回退），作者明确「这不像是普遍的延迟劣化」。定性判断：特定 cgroup/层级调度配置的 p99 尾部回退。

## 我可以参与的点
- kind=testing：在其他 arm64（或 x86）机型上复现 m16/t16、m64/t4 的 schbench p99 配置，确认回退是否平台无关；若能给出开启/关闭单运行队列（或对应修复）的对比数据价值最高。
- kind=discussion：从 EEVDF 层级公平调度的角度分析单运行队列对 cgroup 场景 p99 尾部的影响机制，帮助判断这是否为可接受的权衡。

## 参考链接
- lore（回归报告）: https://lore.kernel.org/all/bd81bbec-ee59-401a-bec6-116196ad3a34@arm.com/
- 被 bisect 的原始 commit（June，单运行队列 v3 7/7）: https://lore.kernel.org/all/20260605124052.227463677@infradead.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260923-001
subject: 'sched/eevdf: Move to a single runqueue'
date: '2026-09-23'
subsystem: sched
type: regression
status: under_review
severity: medium
thread_root_msgid: '<bd81bbec-ee59-401a-bec6-116196ad3a34@arm.com>'
lore_url: 'https://lore.kernel.org/all/bd81bbec-ee59-401a-bec6-116196ad3a34@arm.com/'
authors:
  - 'Aishwarya Rambhadran'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<bd81bbec-ee59-401a-bec6-116196ad3a34@arm.com>'
    date: '2026-09-23'
    summary: 'Graviton3 上 schbench p99 延迟回归报告，bisect 指向 single runqueue commit'
    review_outcome: '当日无维护者回应'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '回退是否属单运行队列改动的预期权衡尚无定论'
  next_action: '维护者定性是否为预期取舍，作者补充完整 bisect/测试数据'
contribution_opportunities:
  - kind: testing
    description: '跨机型复现 m16/t16、m64/t4 的 schbench p99 回退并给出对比数据'
  - kind: discussion
    description: '分析单运行队列对 cgroup 场景 p99 尾部延迟的影响机制'
generated_at: '2026-09-24T09:00:00'
source_email_count: 1
related_articles: []
tags:
  - eevdf
  - regression
---
