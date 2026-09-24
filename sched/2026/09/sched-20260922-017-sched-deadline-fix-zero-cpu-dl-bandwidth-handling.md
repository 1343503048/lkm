# sched/deadline: Fix zero-CPU DL bandwidth handling

## TL;DR
本文为增量更新，完整背景见 sched-20260919-001。Hui Su 的 v2 系列（修复零 CPU 的 DL 带宽除零 + 拒绝向 inactive CPU 写 debugfs dl_server）当天获 Juri Lelli 两封 Acked。Juri 对 2/2 提出一个修正意见：`Fixes:` 标签应指向 `4043f5498416`（"sched/deadline: Reject debugfs dl_server writes for offline CPUs"）更贴切。两补丁基本可合，只差修 Fixes 标签。

## 背景与问题
背景见 sched-20260919-001：DL bandwidth 记账在 CPU 全 inactive（dl_rq->dl_bw 为 0）时除零；debugfs dl_server 写操作未拒绝 inactive CPU。

## 技术方案
方案见 sched-20260919-001：1/2 修复除零（用激活的 CPU 集合做分母），2/2 拒绝向 inactive CPU 写 dl_server。

## 版本演进与当前进展
v2（cover `<20260919153150.2618403-1-sh_def@163.com>`）发出后，当天 Juri 分别对 1/2、2/2 回复 Acked。

## Maintainer 意见与讨论焦点
- **Juri Lelli**（SCHED_DEADLINE 维护者）：1/2「Looks good to me. Acked-by」；2/2 提出「Isn't 4043f5498416 ("sched/deadline: Reject debugfs dl_server writes for offline CPUs") more appropriate?」——建议 2/2 的 `Fixes:` 指向更贴切的 commit，其余认可并 Acked。
- 无反对意见。

## 合入评估
*likelihood=high*。两补丁均获 deadline 维护者 Acked，仅需修正 2/2 的 Fixes 标签。*blocking_issues*：2/2 的 Fixes 标签待改。*next_action*：作者按 Juri 意见更新 2/2 的 Fixes 标签后重发或由维护者直接调整。

## 效果评估
无本日新增数据；正确性修复（除零 crash 风险、debugfs 非法写）。

## 我可以参与的点
- **review**：核对 2/2 的 Fixes 标签（4043f5498416 vs 当前标签）与修复范围的匹配。
- **testing**：在 all-inactive CPU 的 cpuset 配置下验证 DL 带宽记账与 debugfs dl_server 写。

## 参考链接
- lore（v2 cover）: https://lore.kernel.org/all/20260919153150.2618403-1-sh_def@163.com/
- Juri 对 1/2: https://lore.kernel.org/all/arJ0q2YDoJdPVLTz@jlelli-thinkpadt14gen4.remote.csb/
- Juri 对 2/2: https://lore.kernel.org/all/arJ06kuNFepnpG2g@jlelli-thinkpadt14gen4.remote.csb/

---
id: sched-20260922-017
date: '2026-09-22'
subject: 'sched/deadline: Fix zero-CPU DL bandwidth handling'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260919153150.2618403-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20260919153150.2618403-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved:
  - 'Juri Lelli'
current_version: v2
patch_series:
  - version: v1
    msgid: null
    date: '2026-09-18'
    summary: '初版（见 sched-20260919-001 前的讨论）'
    review_outcome: '未获取到 v1 细节'
  - version: v2
    msgid: '<20260919153150.2618403-1-sh_def@163.com>'
    date: '2026-09-19'
    summary: '1/2 修除零，2/2 拒绝 inactive CPU dl_server 写'
    review_outcome: 'Juri 两封 Acked，2/2 Fixes 标签待改'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - '2/2 的 Fixes 标签待改为 4043f5498416'
  next_action: '更新 2/2 Fixes 标签后合入'
contribution_opportunities:
  - kind: review
    description: '核对 2/2 Fixes 标签与修复范围的匹配'
  - kind: testing
    description: '在 all-inactive CPU 的 cpuset 配置下验证 DL 带宽记账与 debugfs 写'
generated_at: '2026-09-23T00:00:00'
source_email_count: 2
related_articles:
  - sched-20260919-001
tags:
  - deadline
  - cgroup
---