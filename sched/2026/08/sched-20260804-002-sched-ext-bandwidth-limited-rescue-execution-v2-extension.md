# sched_ext: Fixes for v7.2-rc6

# sched_ext: rescue 执行 v2 扩展（与 proxy execution 联动）

## TL;DR
sched_ext 的 rescue 执行（v2，08-03 发出）在 08-04 追加了「通用 rejected DSQ 重入队」与「阻塞 proxy donor 处理」，与同日大型 proxy execution 系列（08-04-001）形成接口联动。这是 08-03-001 的后续进展。

## 背景与问题
rescue 执行解决子调度器持有 caps 不覆盖任务亲和、导致任务被 cap 反复拒绝/饿死的可用性短板（详见 08-03-001）。08-04 的新增内容：当任务被 DSQ 拒绝（rejected）时的通用重入队路径，以及当 donor 因 mutex/rt 阻塞而进入 proxy 状态时，rescue 升级为 protected 不应与该 donor 的 proxy 生命周期冲突。

## 技术方案
- 通用化 rejected DSQ 重入队：任何 DSQ 拒绝的入队统一走可重入的 rescue 候选路径，而非分散在各子调度器。
- 阻塞 proxy donor 处理：rescue 升级为 protected 时识别 donor 是否处于 proxy 阻塞，避免双重管理（与 08-04-001 的 `SCX_OPS_ENQ_BLOCKED` 语义对齐）。

## 版本演进与当前进展
- 08-03：v2 12 patch 基础（08-03-001）。
- 08-04：追加 rejected-DSQ 重入队 + proxy donor 处理，讨论其与 proxy execution 系列的接口一致性。

## Maintainer 意见与讨论焦点
Tejun 主导，焦点在与 proxy execution 系列（08-04-001）的 donor 准入边界对齐，尚无 NAK。

## 合入评估
合入可能性 high。与 08-04-001 同步推进，无独立障碍。

## 效果评估
邮件未附 benchmark；属机制扩展，效果以「rescue 不破坏 proxy 语义 + 无 stall」衡量。

## 我可以参与的点
- 在 caps + proxy 阻塞复合场景下压测 rescue→protected 升级，验证两者不冲突，回帖验证数据（作者未附 runs）。

## 参考链接
- 08-03 文章：sched-20260803-001-sched-ext-bandwidth-limited-rescue-execution-for-stranded-tasks
- lore (v2): https://lore.kernel.org/lkml/20260803055435.2697653-1-tj@kernel.org

---
subject: "sched_ext: Add bandwidth-limited rescue execution for stranded tasks"
id: sched-20260804-002
date: 2026-08-04
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260803055435.2697653-1-tj@kernel.org>"
lore_url: "https://lore.kernel.org/lkml/20260803055435.2697653-1-tj@kernel.org"
authors: [Tejun Heo]
maintainers_involved: [Tejun Heo]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20260803055435.2697653-1-tj@kernel.org>"
    date: 2026-08-03
    summary: "内核侧 rescue 执行（小带宽运行被 cap 拒绝任务，超时升级 protected）的基础 12 patch。08-04 上追加 (1) 通用化 rejected DSQ 重入队；(2) 阻塞 proxy donor 的处理，与 08-04-001 proxy execution 联动。"
    review_outcome: "v2 已发，08-04 讨论聚焦与 proxy execution 系列的接口一致性。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["需与 08-04-001 proxy execution 系列的 donor 准入语义对齐"]
  next_action: "等待 Tejun 把 rescue 与 proxy donor 处理统一后发后续版本。"
contribution_opportunities:
  - kind: testing
    description: "在子调度器持有 caps 且任务亲和与授予 cid 不重叠、并触发 proxy 阻塞的场景下压测，验证 rescue→protected 升级不破坏 proxy 语义，回帖验证数据。"
generated_at: "2026-08-05T00:25:00"
source_email_count: 2
related_articles: ["sched-20260803-001-sched-ext-bandwidth-limited-rescue-execution-for-stranded-tasks"]
tags: [sched_ext, affinity]
---
