---
id: sched-20261105-014
date: 2026-11-05
subject: 'sched/psi: don''t drop the last byte of a trigger write'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261104-work-procfs-bugfixes-v2-13-bbf7d5546809@kernel.org>
lore_url: https://lore.kernel.org/all/20261104-work-procfs-bugfixes-v2-13-bbf7d5546809@kernel.org/
authors:
- Christian Brauner
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <20261104-work-procfs-bugfixes-v2-13-bbf7d5546809@kernel.org>
  date: 2026-11-04
  summary: psi_write 最多拷贝 31 字节并补终止符，不再吞掉短写入的末位数字。
  review_outcome: 暂无 review。
upstream_commit: null
fixes_commit: 0e94682b73bf
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等 psi 维护者收取，并随 stable 回合（Cc stable）
contribution_opportunities:
- kind: testing
  description: 无换行短写入 /proc/pressure/* 验证不再丢末位
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 2
related_articles: []
tags:
- psi
title: 'sched/psi: don''t drop the last byte of a trigger write'
layout: article
---

## TL;DR

Christian Brauner 修 `psi_write()` 的缓冲区结尾处理：当前最多拷贝 32 字节并「覆盖最后一字节」作为终止符，导致短于 32 字节、无换行结尾的 trigger 写入丢掉最后一位数字（`"some 150000 1000000"` 变成 `"some 150000 100000"`，`"some 150 10000"` 直接 -EINVAL）。补丁改为最多拷贝 31 字节并在其后补终止符，`Fixes: 0e94682b73bf` 且 `Cc: stable`，属低风险正确性修复，合入概率高。

## 背景与问题

psi 的 trigger 文件（`/proc/pressure/*`）写入走 `psi_write()`：它最多拷贝 32 字节，并通过「覆盖缓冲区最后一字节」来保证字符串终止。写满 32 字节时没问题，但如果写入更短且没有换行结尾，覆盖掉的恰好是用户写入的最后一个有效数字，造成静默截尾或解析失败。只有以换行结尾的写入才能正确解析。

## 技术方案

把「最多拷贝 32 字节 + 覆盖最后一字节」改为「最多拷贝 31 字节 + 在其后补 `\0`」，这样无论写入多短都不会吃掉用户数据。改动仅 `kernel/sched/psi.c` 一处 2 行量级。

## 版本演进与当前进展

*current_version: v2（今日另有 RESEND v2 同内容）*。该补丁是 Brauner 大型 procfs 重构系列（`work-procfs-bugfixes`，51 补丁）中与 psi 直接相关的独立 bugfix 抽出。今日无讨论回复。

## Maintainer 意见与讨论焦点

暂无回复。补丁带 `Fixes:`（0e94682b73bf，psi monitor 引入时）与 `Cc: stable`，作者是 fs 维护者 Christian Brauner。

## 合入评估

*likelihood=high*。两点式、带 Fixes 与 stable 标注的正确性修复，无设计争议。*blocking_issues*：暂无。*next_action*：等 psi 相关维护者收取；因 Cc stable，预计会随稳定分支回合。

## 效果评估

作者以两个具体输入示例说明修复效果（短写入不再丢末位数字、短窗口串不再误报 -EINVAL）；未附量化测试数据。

## 我可以参与的点

- testing：验证 `echo -n "some 150000 1000000" > /proc/pressure/cpu`（无换行）在补丁后能被正确触发与解析。
- 当前阶段暂无其它明显参与点。

## 参考链接

- lore thread（v2 13/51）: https://lore.kernel.org/all/20261104-work-procfs-bugfixes-v2-13-bbf7d5546809@kernel.org/
