# sched/cache: Keep nr_pref_llc_running in the runnable domain

## TL;DR
本文为增量更新（完整背景见 related_articles）。Kayra Cizmeci 的「把 nr_pref_llc_running 收进 runnable 域」4 补丁系列（patch 1/4）今日再获 Tim Chen 评审：认可改动方向（"This change looks good and make the code cleaner"），但要求把操作场景注释收紧——点明「CPU0/CPU1 都在 preferred LLC、任务在 CPU1 上被唤醒」的前提，并把某段代码块归到 CPU 0 下，认为现有注释过长、不够全面。

## 背景与问题
承 sched-20260828-004 与 sched-20260914-005：`nr_pref_llc_running` 计数口径（DELAY_DEQUEUE 下跟随 queued 语义 vs `cfs.h_nr_runnable` 扣除 delay-dequeued 任务）导致 `alb_break_llc()` 判断失效。Kayra 09-10 投出 4 补丁系列，把该计数收进 runnable 域，省掉独立判据与多处调用。09-14 Chen Yu 已实测 Kayra 方案并倾向维持较简版本、补注释；09-15 Tim Chen 接着评审。

## 技术方案
本日无新代码。Tim Chen 对 patch 1/4 的注释场景描述给出具体修改意见：注释应明确「假设 CPU0 与 CPU1 都在 preferred LLC、任务在 CPU1 上被唤醒」这一前提；「LB 把 delayed 任务从 preferred LLC 迁到 non-preferred LLC」时 `rq1->nr_pref_llc_running++` 所在代码块应标注归 CPU 0；并指出所列操作场景不够全面、注释偏长。

## 版本演进与当前进展
无新版本。本日是 patch 1/4 的第三位评审者（Chen Yu 之后）Tim Chen 的反馈，方向性认可 + 注释修改要求，尚未见作者新版本。

## Maintainer 意见与讨论焦点
- **Tim Chen (Intel)**：认可改动让代码更清晰（"This change looks good and make the code cleaner"），但要求收紧注释的场景前提与代码块归属，认为现有注释不全面且偏长。
- **Chen Yu**（09-14，见 related_articles）：实测 Kayra 方案后认为更复杂、角落案例更多，维持较简版本。
- 无 NAK；分歧点在「注释如何写才既准确又不冗长」，非方案方向之争。

## 合入评估
likelihood=medium。方向已获 Tim 与 Chen Yu 双重认可，但注释修改未落实、作者未回应，尚无 Ack。blocking_issues：注释的场景前提与代码块归属需按 Tim 意见修订；作者未回应。next_action：作者按 Tim 意见收紧 patch 1/4 注释并出新版，争取 Ack。

## 效果评估
无效果数据。本日讨论聚焦代码可读性与注释准确性，不涉及性能或行为变化验证。

## 我可以参与的点
- kind=review：核对 patch 1/4 中 `nr_pref_llc_running++` 的维护点与注释描述是否一致（set_delayed/clear_delayed/account_llc_enqueue/account_llc_dequeue 四处），帮助作者一次性把注释写准。
- kind=discussion：就「注释应覆盖哪些操作场景才算既全面又不过长」给出建议，加速收敛。

## 参考链接
- Tim Chen 评审回帖：https://lore.kernel.org/all/025bdcdef34170b1ffcc673c6b59cb51abc8fef5.camel@linux.intel.com/
- 线程根：https://lore.kernel.org/all/f3b70dd40e29b309ff3449a95a4af4513ad0ef70.camel@linux.intel.com/

---
id: sched-20260915-005
date: '2026-09-15'
subject: 'sched/cache: Keep nr_pref_llc_running in the runnable domain'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<f3b70dd40e29b309ff3449a95a4af4513ad0ef70.camel@linux.intel.com>'
lore_url: 'https://lore.kernel.org/all/025bdcdef34170b1ffcc673c6b59cb51abc8fef5.camel@linux.intel.com/'
authors:
  - 'Kayra Cizmeci'
maintainers_involved:
  - 'Tim Chen'
  - 'Chen Yu'
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '注释的场景前提与代码块归属需按 Tim 意见修订'
    - '作者尚未回应本轮反馈'
  next_action: '作者按 Tim 意见收紧 patch 1/4 注释并出新版'
contribution_opportunities:
  - kind: review
    description: '核对 nr_pref_llc_running++ 维护点与注释描述是否一致，帮作者一次写准注释'
  - kind: discussion
    description: '就注释应覆盖哪些操作场景给出建议，加速收敛'
generated_at: '2026-09-16T01:05:00'
source_email_count: 1
related_articles:
  - 'sched-20260914-005'
  - 'sched-20260828-004'
tags:
  - load_balance
  - cfs
---