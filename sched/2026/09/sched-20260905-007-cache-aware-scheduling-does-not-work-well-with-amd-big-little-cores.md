# Cache-aware scheduling does not work well with amd big/little cores

## TL;DR

一封反馈邮件（Re: "Cache-aware scheduling does not work well with amd big/little cores"）引用 Tim Chen 与 Klaus Kusche 的对话：两补丁组合「看起来达到了预期效果」，长运行 CPU 密集进程会在快核空闲时迁移到快核，LTO 编译「明显更快完成」。目前讨论中；正面结论（快核迁移、编译加速）+ 待细化边界情形。

## 背景与问题

一封反馈邮件（Re: "Cache-aware scheduling does not work well with amd big/little cores"）引用 Tim Chen 与 Klaus Kusche 的对话：两补丁组合「看起来达到了预期效果」，长运行 CPU 密集进程会在快核空闲时迁移到快核，LTO 编译「明显更快完成」。即 cache-aware / 偏好 CPU 调度在 AMD big/little 上总体有效，但仍存在可调优点（主题中的 "does not work well" 指向具体边界情形）。

## 技术方案

- 无补丁，属社区反馈/调优讨论。

## 版本演进与当前进展

- 讨论中；正面结论（快核迁移、编译加速）+ 待细化边界情形。
- 与 09-04 006（tip 合入 cache-aware 均衡避免 misfit）协同，反映该工作在真实 AMD big/little 平台上的实测效果。

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
  - [[sched-20260904-006]] tip/sched/urgent 合入：cache-aware 均衡避免制造 misfit（f0d243a）。
- 相关代码/commit：
  - `kernel/sched/fair.c` cache-aware 均衡 / 偏好 CPU 选择

---
id: sched-20260905-007
date: '2026-09-05'
subject: Cache-aware scheduling does not work well with amd big/little cores
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=Cache-aware+scheduling+does+not+work+well+with+amd+big/little+cores
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Klaus Kusche
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 1
related_articles:
- sched-20260904-006
tags:
- sched/cache
- topology
---
