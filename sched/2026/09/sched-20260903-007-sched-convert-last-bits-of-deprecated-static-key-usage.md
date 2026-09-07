# sched: Convert last bits of deprecated static key usage

## TL;DR

原始 static key 没有类型信息，无法防止误配（如在默认 TRUE 的 key 上用 static_key_false()），且 static_key_{true/false}() 命名易混淆，故已被废弃。目前v2，纯清理性质。- 与 sched-20260902-002 的 PREEMPT_DYNAMIC 简化同源目标（去除 deprecated API）。

## 背景与问题

原始 static key 没有类型信息，无法防止误配（如在默认 TRUE 的 key 上用 `static_key_false()`），且 `static_key_{true/false}()` 命名易混淆，故已被废弃。此前已转换多数站点，本系列转换调度器内最后一批废弃 static key API，完成后调度器代码零废弃 static key 用法。

## 技术方案

- 将剩余站点从 `static_key_{true/false}()` 迁移到 `static_branch_*`。
- `sk_dynamic_*` 原本使用未废弃的 `static_key_{enable/disable}()`，也顺带迁移到新的 `static_branch_*` API，统一风格。

## 版本演进与当前进展

- v2，纯清理性质。
- 与 `sched-20260902-002` 的 PREEMPT_DYNAMIC 简化同源目标（去除 deprecated API）。

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
  - [[sched-20260902-002]] PREEMPT_DYNAMIC 简化 + static key 迁移（合入）。
- 相关代码/commit：
  - `kernel/sched/` 内各 `static_key_*` 使用点

---
id: sched-20260903-007
date: '2026-09-03'
subject: 'sched: Convert last bits of deprecated static key usage'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched+Convert+last+bits+of+deprecated+static+key+usage
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: null
authors:
- Hongyan Xia
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 1
related_articles:
- sched-20260902-002
tags:
- sched/core
---
