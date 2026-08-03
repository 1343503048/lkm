---
id: sched-20260801-001
date: 2026-08-01
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<uid-14362@qq-imap>"
lore_url: unknown
authors: [Tejun Heo]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<uid-14362@qq-imap>"
    date: 2026-08-01
    summary: "12 个 patch 的 PATCHSET，为 sched_ext 子调度器引入内核侧「带宽受限救援执行」（rescue execution）：子调度器插入可能被 cap 拒绝的任务时打 SCX_ENQ_RESCUE 标记，内核不再回弹而是以受限带宽在目标 CPU 上直接运行该任务；救援长期得不到服务时升级为 protected execution；某 CPU 救援队列持续过载时驱逐该 CPU 上救援消耗最高的子调度器。"
    review_outcome: "当日刚发出，尚无 review 回复"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待社区对 rescue 语义、带宽参数与过载驱逐启发式的 review 意见"
contribution_opportunities:
  - kind: testing
    description: "构造「子调度器持有的 cid 集合无法覆盖任务亲和性」的场景（如 cpuset 与 cid 授权不一致），验证 rescue 路径是否真的避免了 watchdog stall，并把复现脚本与结果回帖"
  - kind: review
    description: "审阅 0008/0009 的过载驱逐启发式：以「该 CPU 上近期救援消耗最高的子调度器」作为驱逐对象，在多个子调度器负载相近时是否会误伤"
generated_at: "2026-08-02T00:55:00"
source_email_count: 13
related_articles: []
tags: [sched_ext, cgroup, affinity]
---

## TL;DR

Tejun Heo 发出 12 个 patch 的系列，为 sched_ext 层级调度（子调度器）补上一条内核兜底路径：当子调度器持有的 cid 无法覆盖某个任务的亲和性时，内核以受限带宽直接把该任务跑起来，而不是让它在 cap 拒绝与重新入队之间反复直到调度器被驱逐或任务 stall。这是 sched_ext 层级化能力的关键补齐，由子系统 maintainer 本人提出，值得关注。

## 背景与问题

sched_ext 的层级调度中，一个子调度器只持有父调度器授予的 cid 集合，而内核不保证这个集合能覆盖其名下所有任务的 CPU 亲和性。当出现一个任务的 affinity 与子调度器所有 cid 都不相交时，当前实现没有任何合理收敛路径：

- 子调度器的 insert 被 cap 拒绝，任务被重新入队；
- 反复重试直到触发 repeat limit，子调度器整体被驱逐；
- 或者任务一直排不上队，最终撞到 watchdog stall。

两种结局都是失败：要么惩罚了整个子调度器，要么直接把任务饿死。问题的根源在于「授权范围」与「任务亲和性」是两个独立演化的约束，而内核没有为二者冲突提供出口。

## 技术方案

核心是引入 **rescue execution**：调度器把一个可能被 cap 拒绝的 insert 标记为 `SCX_ENQ_RESCUE`，内核收到后不再回弹，而是在目标 CPU 上以一个较小的配置带宽运行该任务。

关键的设计取舍在于「救援不能变成一个绕过 cap 体系的后门」，因此：

1. **救援起步是非侵入式的**。持有该 cid 上 cap 的调度器基本保持对 CPU 的控制权——例如持有抢占 cap 的一方仍然可以抢占被救援的任务。也就是说救援任务在正常情况下只是「见缝插针」。
2. **长期不被服务才升级**。当一次救援长时间得不到服务，才升级为 protected execution，此时内核授予的 slice 需要能抵御调度器侧的写入，这正是 0006（在插入提交点同步 slice 与 dsq_vtime 写入）与 0007（`SCX_TASK_PROTECTED`）所做的铺垫。
3. **过载归因到真正的消费者**。当某 CPU 的救援队列越过过载阈值持续饱和，内核驱逐的是「该 CPU 上近期救援消耗最高的子调度器」，而不是简单地怪罪等待者所属的调度器——这一点是明确的设计声明，说明作者已经预见到朴素归因会误伤受害者。

系列结构清晰分层：0001–0005 为准备工作（重命名、helper 可见性、dsq-move flag 校验、`SCX_ENQ_IGNORE_CAPS` 一并豁免抢占 cap）；0006–0007 是 protected execution 的地基；0008–0009 是救援机制与过载驱逐本体；0010 同步 tools 侧 autogen enum 头文件；0011–0012 修复 scx_qmap 的 pinned task 直接派发并让它作为示范消费者接入 rescue。

## 版本演进与当前进展

v1 于 2026-08-01 16:51 发出，基于 `sched_ext/for-7.3`（ee7aece60817），目标分支为 for-7.3。当日尚无 review 回复。

## Maintainer 意见与讨论焦点

Tejun Heo 本人即 sched_ext maintainer，该系列由他自己提出，因此不存在通常意义上的「维护者是否接受」问题。截至 2026-08-01 当日无第三方回复，暂无公开争议点。

需要留意但尚未被讨论的潜在焦点：救援带宽的取值与可配置粒度、protected execution 的升级时机判定、以及过载驱逐启发式在多子调度器竞争下的公平性。这些目前都只有作者的单方面设计陈述，还没有经过社区检验。

## 合入评估

合入可能性 **high**：由子系统 maintainer 自己发出、直接基于 `sched_ext/for-7.3` 且已提供 git tree，走的是常规的 for-next 流程。当前没有已知阻塞项，主要变数是社区对 rescue 语义与驱逐启发式是否提出结构性意见。

## 效果评估

暂无效果数据。封面信中没有给出任何 benchmark 或 stall 复现前后的对比数字，只有机制层面的描述。

## 我可以参与的点

- **测试**：构造子调度器 cid 授权与任务 affinity 不相交的场景（例如通过 cpuset 变更让任务落到未授权 cid 上），验证 rescue 路径确实避免了 watchdog stall，并测量救援带宽对整体吞吐的影响，把复现脚本与数据回帖。
- **Review**：0009 的过载驱逐启发式值得细看——「近期救援消耗最高」在多个子调度器负载相近、或某调度器短时突发时是否会造成误驱逐，这是可以提出具体质疑的点。

## 参考链接

- lore thread: 未获取到
- git tree: `git://git.kernel.org/pub/scm/linux/kernel/git/tj/sched_ext.git`（封面信中给出，分支名在正文截断处）
- tip-bot commit: 未获取到
- stable backport: 未获取到
