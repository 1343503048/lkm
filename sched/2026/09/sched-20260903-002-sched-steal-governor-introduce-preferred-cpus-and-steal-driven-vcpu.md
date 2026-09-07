# sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff

## TL;DR

steal_governor 让过载 CPU 从空闲/轻载 CPU「窃取」任务，以缓解大机/SMT 拓扑下的核间负载不均。目前v12，目标合并窗口 7.4。- 本日多封 Re 讨论 PowerPC 实测与虚拟化场景下的收益/回归，整体处于复审收尾。

## 背景与问题

steal_governor 让过载 CPU 从空闲/轻载 CPU「窃取」任务，以缓解大机/SMT 拓扑下的核间负载不均。v12 相较 09-02 覆盖的 v11 主要做复审吸收与 rebase，并新增对虚拟化场景（paravirt / steal time 记账）的处理：对 vCPU 的 steal time 设上限，使宿主内核在 vCPU 被宿主机偷走时仍能判断「更空闲的 CPU」并迁移任务；同时引入 preferred CPU（结合 misfit / forced idle）以减少跨 LLC 抖动。

## 技术方案

- 延续 NUMA 细粒度 + `sched/cache` 辅助的决策框架（见 `sched-20260902-014`）。
- 新增 `sched/debug: Add migration stats due to non preferred CPUs`（v12 09/13），观测因非偏好 CPU 触发的迁移。
- 虚拟化路径：对 vCPU steal time 做上限 + 偏好 CPU 回退，避免宿主机抢占导致任务被错误「粘」在偷走时间的 vCPU 上。

## 版本演进与当前进展

- v12，目标合并窗口 7.4。
- 本日多封 Re 讨论 PowerPC 实测与虚拟化场景下的收益/回归，整体处于复审收尾。

## Maintainer 意见与讨论焦点

邮件清单中该系列以补丁往返为主，未捕获到维护者明确表态（缓存未含正文，无法给出具体意见）。

## 合入评估

证据不足：邮件缓存未保留正文，无法判断维护者态度与卡点，暂不给合入结论。

## 效果评估

邮件中未提及效果数据（缓存未保留正文，无法确认）。

## 我可以参与的点

证据不足：需结合完整邮件正文再判断参与空间；如该系列进入 review 中后期，可先跑一轮 benchmark 并回帖。

## 参考链接

- 相关文章/系列：
  - [[sched-20260902-014]] steal_governor v11 preferred（讨论版）。
- 相关代码/commit：
  - `kernel/sched/core.c` / `kernel/sched/fair.c` 的 steal / 偏好 CPU 选择逻辑
  - `sched/debug` 迁移统计

---
id: sched-20260903-002
date: '2026-09-03'
subject: 'sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff'
subsystem: sched
type: feature
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=steal_governor+v12+preferred+CPU
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v12
generated_at: null
authors:
- Shrikanth Hegde
- Yury Norov
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 5
related_articles:
- sched-20260902-014
tags:
- sched/core
- sched/fair
- sched/cache
- topology
---
