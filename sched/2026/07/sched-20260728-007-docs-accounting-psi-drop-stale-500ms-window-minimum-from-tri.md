# docs: accounting/psi: drop stale 500ms window minimum from trigger docs

## TL;DR

PSI 文档修复补丁的讨论：作者 Tao 计划发 v2，保留 window-range 修复但恢复 system-wide 和 cgroup 文件的统一措辞。此前 commit 8b39d20eceed 已 revert 了 cgroup-specific gating，所以 2s-multiple 规则对两者统一适用。

## 背景与问题

PSI trigger 文档中残留了"500ms window minimum"的过时描述。实际上 commit 519fabc7aaba 添加的 cgroup-specific gating 已被 8b39d20eceed revert，当前 system-wide 和 cgroup 文件使用相同的 window 规则。

## 技术方案

- v1：移除文档中的 500ms minimum 描述，但措辞上区分了 system-wide 和 cgroup
- v2（计划中）：保留 window-range 修复，但恢复统一措辞（不再区分 system-wide/cgroup）

## 版本演进与当前进展

- v1（2026-07-27）：发出文档修复
- Suren Baghdasaryan 回帖指出历史上下文（8b39d20eceed revert 了 cgroup-specific gating）
- 作者 Tao 确认将发 v2

## Maintainer 意见与讨论焦点

- **Suren Baghdasaryan**：指出 8b39d20eceed 已 revert cgroup-specific gating，2s-multiple 规则统一适用
- 无争议，纯文档修正

## 合入评估

可能性高。纯文档修复，方向已确认，v2 发出后预计很快合入。

## 效果评估

暂无效果数据（文档修改，不涉及代码行为变化）。

## 我可以参与的点

当前阶段暂无明显参与空间。纯文档修复，v2 即将发出。

## 参考链接

- lore thread: https://lore.kernel.org/r/CAJuCfpGhijcg1N2AxbRbTHf7FvtaTG_xYL1fPVUA=k7snPYtzA@mail.gmail.com
- tip-bot commit: 未获取到

---
subject: "docs: accounting/psi: drop stale 500ms window minimum from trigger docs"
id: sched-20260728-007
date: 2026-07-28
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: "<CAJuCfpGhijcg1N2AxbRbTHf7FvtaTG_xYL1fPVUA=k7snPYtzA@mail.gmail.com>"
lore_url: "https://lore.kernel.org/r/CAJuCfpGhijcg1N2AxbRbTHf7FvtaTG_xYL1fPVUA=k7snPYtzA@mail.gmail.com"
authors: [Tao]
maintainers_involved: [Suren Baghdasaryan]
current_version: v1
patch_series:
  - version: v1
    msgid: "<CAJuCfpGhijcg1N2AxbRbTHf7FvtaTG_xYL1fPVUA=k7snPYtzA@mail.gmail.com>"
    date: 2026-07-27
    summary: "Drop stale 500ms window minimum from PSI trigger docs"
    review_outcome: "Suren 指出历史上下文；作者计划发 v2 恢复统一措辞"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "作者发 v2 保留 window-range fix 但恢复统一措辞"
contribution_opportunities: []
generated_at: "2026-07-30T10:00:00"
source_email_count: 1
related_articles: []
tags: [psi]
---
