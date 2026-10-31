# sched_ext: Avoid unnecessary IMMED reenqueues on idle CPUs

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261029-012：Andrea Righi 修 sched_ext 效率缺陷——两个 IMMED 任务在空闲 CPU 上被唤醒时，内核会不必要地把两个都踢回 BPF（`rq_is_open()` 看到 `next_class == ext` 就判 CPU 不可用，尽管仍 idle）。v2 改为「CPU idle 时即便 `next_class` 已被抬到 ext 也报告 rq 开放」，只把 head 之后的 IMMED 任务踢回 BPF。virtme-ng 4-vCPU 复现：10000 对唤醒里 9776 次不必要 head reenqueue，修复后归零。`Fixes: 98d709cba319`。
- sched-20261030-012（今天）：Tejun Heo 回帖 **「Applied to sched_ext/for-7.4-fixes. Thanks.」**——该修复已被收取到 sched_ext 的 7.4 修复分支，等待随合并窗口进 mainline。

## 背景与问题
（承接 20261029-012）两个 IMMED 任务在空闲 CPU 上被唤醒时，第一次插入把 `rq->next_class` 抬到 ext，第二次插入触发的 reenqueue scan 里 `rq_is_open()` 误判 CPU 不可用，把本可被下一次 pick 采用的 head 也一并踢回 BPF。今日无新背景，为合入确认。

## 技术方案
（承接 v2）v2 方案：CPU idle 时即便本地插入已把 `next_class` 抬到 ext，也报告 rq 开放；只 `+8` 行，保留 DSQ head、head 之后的 IMMED 任务仍回 BPF。Tejun 首轮要求的「core-sched cookie 检查拆出」与「skipped-head 记账修复拆出」均已从 v2 移除。今日无新代码，为收取确认。

## 版本演进与当前进展
*current_version: v2*（2026-10-28 发出）。今日被 Tejun 收取到 `sched_ext/for-7.4-fixes`。

## Maintainer 意见与讨论焦点
- **Tejun Heo（sched_ext maintainer）**：今日确认「Applied to sched_ext/for-7.4-fixes.」，此前 review 意见（拆出 core-sched 与 skipped-head 记账）已全部吸收。
- 无遗留分歧。

## 合入评估
*likelihood=merged*。已合入 `sched_ext/for-7.4-fixes`，等待随 sched_ext fixes pull 进 mainline。*blocking_issues*：无。*next_action*：随 sched_ext/for-7.4-fixes 合并窗口进入 mainline。

## 效果评估
作者 virtme-ng 4-vCPU 复现：10000 对唤醒里 9776 次不必要 head reenqueue，修复后归零（纯效率优化，无性能基准数字）。

## 我可以参与的点
当前阶段已合入，暂无明显参与空间；可持续观察 core-sched 相关的后续独立补丁（作者曾提到 IMMED 在 core sched 下的处理需单独成 patch）。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261028165258.3723153-1-arighi@nvidia.com/

---
id: sched-20261030-012
date: 2026-10-30
subject: "sched_ext: Avoid unnecessary IMMED reenqueues on idle CPUs"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<20261028165258.3723153-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20261028165258.3723153-1-arighi@nvidia.com/"
authors: [Andrea Righi]
maintainers_involved: [Tejun Heo]
current_version: v2
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.4-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "随 sched_ext/for-7.4-fixes 合并窗口进入 mainline"
contribution_opportunities: []
generated_at: "2026-10-31T09:00:00"
source_email_count: 1
related_articles: [sched-20261029-012]
tags: [sched_ext]
---