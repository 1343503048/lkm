# thermal/cpufreq_cooling: Simplify cpufreq_set_cur_state()

## TL;DR

Thorsten Blum 提交的 cpufreq_cooling 清理补丁——`cpufreq_set_cur_state()` 直接返回 `freq_qos_update_request()` 的错误，去掉 `ret >= 0` 分支的冗余包裹。获 Rafael Wysocki 应用为 7.4 material。

## 背景与问题

`drivers/thermal/cpufreq_cooling.c` 的 `cpufreq_set_cur_state()` 在 `freq_qos_update_request()` 成功后还要走一段 `if (ret >= 0) { cpufreq_cdev->cpufreq_state = state; ret = 0; }` 再统一 `return ret`，逻辑等价但写法冗余。

## 技术方案

改为错误直接返回、成功分支直落：`if (ret < 0) return ret;` 后接 `cpufreq_cdev->cpufreq_state = state; return 0;`。等价重构，无行为变化。规模 1 file changed, 5 insertions(+), 5 deletions(-)。

## 版本演进与当前进展

v1（2026-09-23，`<20260923202911.90464-3-blum@kernel.org>`，系列 3/3）提交后，09-26 Rafael Wysocki（`<CAJZ5v0ix=uLVTHzVO3t5HdPKrm-ybFU-HeVuYyXdbcDyNxCAUQ@mail.gmail.com>`）回复 "Applied as 7.4 material, thanks!"。

## Maintainer 意见与讨论焦点

- **Rafael Wysocki**（电源管理维护者）：无异议，直接应用为 7.4 材料。无分歧。

## 合入评估

已应用（*likelihood=merged*），目标 7.4。*blocking_issues*：无。*next_action*：无，等待 7.4 窗口随分支进入主线。

## 效果评估

纯代码清理，无性能数据；等价重构，降低可读性负担。

## 我可以参与的点

已应用，当前阶段暂无明显参与空间。

## 参考链接

- Rafael 应用回帖: https://lore.kernel.org/all/CAJZ5v0ix=uLVTHzVO3t5HdPKrm-ybFU-HeVuYyXdbcDyNxCAUQ@mail.gmail.com/
- 原补丁: https://lore.kernel.org/all/20260923202911.90464-3-blum@kernel.org/

---
id: sched-20260926-011
date: 2026-09-26
subject: "thermal/cpufreq_cooling: Simplify cpufreq_set_cur_state()"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<20260923202911.90464-3-blum@kernel.org>"
lore_url: "https://lore.kernel.org/all/CAJZ5v0ix=uLVTHzVO3t5HdPKrm-ybFU-HeVuYyXdbcDyNxCAUQ@mail.gmail.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: "2026-09-27T01:20:00"
authors:
  - "Thorsten Blum"
maintainers_involved:
  - "Rafael Wysocki"
patch_series:
  - version: v1
    msgid: "<20260923202911.90464-3-blum@kernel.org>"
    date: 2026-09-23
    summary: "cpufreq_set_cur_state() 直接返回 freq_qos_update_request() 错误，去掉 ret>=0 冗余分支"
    review_outcome: "09-26 Rafael 应用为 7.4 material"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "等待 7.4 窗口随分支进入主线"
contribution_opportunities: []
source_email_count: 1
related_articles: []
tags:
  - thermal
  - cpufreq
---