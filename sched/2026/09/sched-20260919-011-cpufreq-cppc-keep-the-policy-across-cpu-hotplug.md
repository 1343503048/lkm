# cpufreq: CPPC: Keep the policy across CPU hotplug

## TL;DR
增量更新：Sumit Gupta 的 CPPC CPU hotplug 策略保留系列（v4）本日收到 Christian Loehle 的意见——他认为应在 hotplug 系列之前落地 ACPI 规范要求的"Minimum Performance ≤ Maximum Performance / Desired Performance 界内"顺序保证，并贴出一版草拟补丁（分批写入 control、快速切换只在变化时带 limits），请系列作者测 AUTOSEL 场景。

## 背景与问题
背景见 sched-20260917-016：CPPC（ACPI Collaborative Processor Performance Control）在 CPU hotplug 时策略被丢失，系列旨在跨 hotplug 保留 policy。本日讨论引向一个相关但更底层的规范符合性问题。

## 技术方案
本日无系列方案变更。Christian Loehle 提出配套补丁：`cppc_set_perf()` 目前按固定顺序写 Minimum/Desired/Maximum Performance 三个 control，在固件重置 controls 或策略边界跨过当前 desired 值时会暴露非法三元组。其草拟补丁改为：读实时 limits，分三阶段非原子更新（先放宽区间→更新 Desired→再收紧），使每次提交的 PCC control 都满足规范；保留"完整元组在同一 PCC 命令"时的单命令路径；拒绝非法请求并在首个失败访问后停止；让 `cppc_cpufreq` 的快速切换仅在 limits 与上次成功请求不同时才带上 limits，resume 与失败请求后失效缓存。作者希望把该逻辑接到 hotplug 系列上并测 AUTOSEL。

## 版本演进与当前进展
- v1（2026-08-06，`<20260806200857.601152-1-sumitg@nvidia.com>`）：原始 CPPC hotplug 策略保留系列（见 sched-20260917-016）。
- 本日 Christian Loehle（`<1be30b2b-e1e5-41ed-a0dc-0dd5ad3c47cd@arm.com>`）对 v4 1/4 提出规范顺序问题，并给出草拟补丁。

## Maintainer 意见与讨论焦点
- **Christian Loehle（Arm，cpufreq 活跃 contributor）**：不理解为何规范顺序保证不先于 hotplug 系列落地（"真该随 MIN/MAX_PERF 支持就落地，或至少为此后的 AUTOSEL 铺路"）；不反对 Jie 关于"健全平台应能容忍瞬时违规"的判断，但认为现在就能绝对遵守规范、避免未来维护一堆 quirk；给出"轻测、未见违规"的草拟补丁并请系列作者 wiring + 测 AUTOSEL。
- 分歧/未决：顺序保证补丁应先于 hotplug 系列与否、草拟补丁的 AUTOSEL 场景验证。

## 合入评估
likelihood=medium。系列本身推进中，但讨论引出了应先落地的规范顺序保证，范围可能扩大。blocking_issues：Christian 主张顺序保证应先于 hotplug 系列落地，需作者评估并测 AUTOSEL。next_action：系列作者把 Christian 的顺序保证补丁接入并测 AUTOSEL 场景，回复落地顺序。

## 效果评估
本日无新增 benchmark。Christian 的草拟补丁"轻测未见违规"，明确尚需热插拔 + AUTOSEL 测试。

## 我可以参与的点
- kind=testing：在 CPPC 平台（尤其支持 AUTOSEL/自主选择的固件）上验证 hotplug + 顺序保证补丁的违规情况。
- kind=review：评估规范顺序非原子三阶段更新对 cpufreq 快速切换路径的影响。

## 参考链接
- lore（Christian Loehle 回复）: https://lore.kernel.org/all/1be30b2b-e1e5-41ed-a0dc-0dd5ad3c47cd@arm.com/
- lore（v1 cover）: https://lore.kernel.org/all/20260806200857.601152-1-sumitg@nvidia.com/

---
id: sched-20260919-011
date: '2026-09-19'
subject: 'cpufreq: CPPC: Keep the policy across CPU hotplug'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260806200857.601152-1-sumitg@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20260806200857.601152-1-sumitg@nvidia.com/'
authors:
  - 'Sumit Gupta'
maintainers_involved: []
current_version: v4
patch_series:
  - version: v1
    msgid: '<20260806200857.601152-1-sumitg@nvidia.com>'
    date: '2026-08-06'
    summary: 'CPPC 跨 hotplug 保留 policy 系列'
    review_outcome: '见 sched-20260917-016'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'Christian 主张规范顺序保证应先于 hotplug 系列落地，需作者接草拟补丁并测 AUTOSEL'
  next_action: '系列作者接入顺序保证补丁并测 AUTOSEL 场景，回复落地顺序'
contribution_opportunities:
  - kind: testing
    description: '在支持 AUTOSEL 的 CPPC 平台验证 hotplug + 顺序保证补丁'
  - kind: review
    description: '评估三阶段非原子更新对快速切换路径的影响'
generated_at: '2026-09-20T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260917-016
tags:
  - cpufreq
---