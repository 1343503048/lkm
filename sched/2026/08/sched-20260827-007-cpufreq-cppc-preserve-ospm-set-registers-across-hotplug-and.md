# cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload

## TL;DR
本文为增量更新（完整背景见 related_articles）。v4 收尾出现变数：作者 Sumit Gupta 08-27 承认**一直没看到 Sashiko（AI 审查代理）对该系列的 review 邮件**，刚补读网页版结论，承诺两条发现都会在 v5 处理。合入节奏因此再加一个版本周期。

## 背景与问题
CPPC cpufreq 驱动在 CPU hotplug 与驱动卸载时丢失 OSPM 设置的寄存器值（EPP、Autonomous Activity Window、Autonomous Selection）的问题，由 4 补丁系列解决（online()/offline() 回调保持 policy 存活 + 表驱动 save/restore）。背景与方案细节见 sched-20260826-005，此处不重复。

## 技术方案
当日无方案变化。唯一新信息是 v5 的触发源：Sashiko 对该系列产出了 2 条 review 发现（邮件作者未收到、仅网页可见），作者将逐条回应。**两条发现的具体内容在当日邮件中未展开，未获取到。**

## 版本演进与当前进展
- v1–v4：见 related 文章；v4 期间 Rafael J. Wysocki、Christian Loehle 参与 review（sched-20260826-005）。
- 08-26：Rafael 的邮件（本封回复的对象 `<CAJZ5v0hMRNTZbhb1tR7rf5+65Oes-7K__b1dLg5kGkm7NqKvWw@mail.gmail.com>`）提示作者去看 Sashiko 结论。
- 08-27：作者确认将出 v5。系列停留在 v4。

## Maintainer 意见与讨论焦点
无新的技术性分歧；焦点变成流程性的：AI review（Sashiko）发现是否成立、v5 如何回应。当日无人进一步表态。

## 合入评估
**possible**（维持原判但右移）。此前 review 面向合入推进正常，当前唯一已知阻塞是 Sashiko 的 2 条发现待回应；若 v5 处理干净，进入 Rafael 的队列概率不低。`next_action`：等 v5。

## 效果评估
当日无效果数据（该系列为功能正确性修复，非性能）。

## 我可以参与的点
- v5 发出后如有兴趣，可关注 Sashiko 两条发现是否与 ACPI/CPPC 寄存器保存路径相关——这是 ARM64 服务器（含华为平台）直接相关驱动；
- 目前阶段无明确缺口可补，观察 v5 即可。

## 参考链接
- 作者承诺 v5 的本封: https://lore.kernel.org/all/067ccb72-5324-4f4a-b21f-d1ce87f78ad0@nvidia.com/
- 所回复的 Rafael 侧提示邮件: https://lore.kernel.org/all/CAJZ5v0hMRNTZbhb1tR7rf5+65Oes-7K__b1dLg5kGkm7NqKvWw@mail.gmail.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260827-007
date: '2026-08-27'
subject: "cpufreq: CPPC: Preserve OSPM-set registers across hotplug and unload"
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<20260806200857.601152-1-sumitg@nvidia.com>"
lore_url: "https://lore.kernel.org/all/067ccb72-5324-4f4a-b21f-d1ce87f78ad0@nvidia.com/"
authors: [Sumit Gupta]
maintainers_involved: [Rafael J. Wysocki]
current_version: v4
patch_series:
  - version: v4
    msgid: "<20260806200857.601152-1-sumitg@nvidia.com>"
    date: 2026-08-06
    summary: "online/offline 回调保持 policy + 表驱动 save/restore OSPM 寄存器"
    review_outcome: "Rafael/Loehle 参与；Sashiko 产出 2 条发现，作者承诺 v5 处理"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "Sashiko review 的 2 条发现未回应（内容未获取到），作者计划 v5 处理"
  next_action: "等待 v5 及其对两条发现的回应"
contribution_opportunities: []
generated_at: "2026-09-07T22:05:00"
source_email_count: 1
related_articles: [sched-20260826-005]
tags: [cpufreq, arm64]
---
