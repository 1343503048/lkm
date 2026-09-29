# sched/eevdf: Add min slice check when selecting CPU

> **subject**：`sched/eevdf: Add min slice check when selecting CPU`

## TL;DR

本文为增量更新，完整脉络见 related_articles（Vincent Guittot 的 8 补丁「Improving latency of short slice tasks」系列中的 patch 8/8）。

- sched-20260922-011：Peter Zijlstra 认为 8/8 与 `select_idle_sibling()` 重复，建议复用初次扫描记录的最小 slice CPU，避免重复扫描。
- sched-20260927-007：Kayra Cizmeci 质疑 `select_slice_cpu()` 里的 `nr_idle_scan` 语义与「idle CPU 扫描」注释不符。
- sched-20260929-018（今天）：Vincent Guittot 回复承认注释需更新（现在不是找 idle CPU、只是沿用循环次数限制），并明确「顺便我会把它与 idle CPU 搜索合并」——即同时回应了 Kayra 的注释疑问与 Peter 的重复扫描意见。

## 背景与问题

（承接 sched-20260927-007）EEVDF 下短 slice 任务在 `select_task_rq_fair()` 找不到空闲 CPU 时，可能被放到已运行同长或更短 slice 任务的 CPU 上导致显著等待，patch 8/8 在选 CPU 最后阶段加入 min slice 检查。今天无新背景，进展是作者确认注释问题并宣告合并方向。

## 技术方案

（承接）patch 8/8 新增 `select_slice_cpu()` 比较候选 CPU 的 slice。Vincent 今日的回应：注释需要更新（因为已不是在找 idle CPU，但循环次数的限制仍然保留）；并宣布「I'm going to merge this with searching idle CPU」，即把 `select_slice_cpu()` 与 idle CPU 搜索路径合并——这同时回应了 Kayra 的 `nr_idle_scan` 语义/注释疑问，也落实了 Peter「与 `select_idle_sibling()` 重复、建议复用」的意见。

## 版本演进与当前进展

- v1（2026-09-21，patch 8/8 `<20260921152238.3804392-9-vincent.guittot@linaro.org>`）。
- 09-22：Peter review——与 `select_idle_sibling()` 重复，建议复用（对应 sched-20260922-011）。
- 09-27：Kayra 质疑 `nr_idle_scan` 语义。
- 09-29：Vincent 回复（`<CAKfTPtCyZRjjDWQxoHjG-SdJueTXBCZ4HesjPT0sPikb_dQtEw@mail.gmail.com>`），确认注释需更新并宣布将与该 idle CPU 搜索合并。

## Maintainer 意见与讨论焦点

- **Vincent Guittot**（作者/维护者）：承认注释需更新（不再找 idle CPU、仅沿用循环次数限制），并宣布与 idle CPU 搜索合并。
- **Kayra Cizmeci**（前一日）：质疑 `nr_idle_scan` 语义与注释脱节。该疑问被 Vincent 接受（注释要改）。
- **Peter Zijlstra**（前一日）：8/8 与 `select_idle_sibling()` 重复。该意见被 Vincent 以「合并」回应。
- 两条针对性意见均获作者正面回应，实现将在后续版本调整。

## 合入评估

*likelihood=medium*。方向（CPU 选择考虑 min slice）与系列一脉相承，两条 review 意见（注释语义、重复扫描）均已获作者回应并将合并落实，但调整后的新版本尚未发出。*blocking_issues*：`select_slice_cpu()` 与 idle CPU 搜索的合并尚未落地。*next_action*：Vincent 在下一版本落实「与 idle CPU 搜索合并 + 更新注释」后重发该 patch。

## 效果评估

本 patch 无单独效果数据；系列整体 benchmark 见 sched-20260921-001。

## 我可以参与的点

- `review`：在 Vincent 落地「与 idle CPU 搜索合并」后，核对合并是否消除与 `select_idle_sibling()` 的重复扫描、`nr_idle_scan` 语义是否与新注释一致。

## 参考链接

- lore（patch 8/8）: https://lore.kernel.org/all/20260921152238.3804392-9-vincent.guittot@linaro.org/
- lore（Vincent 回复）: https://lore.kernel.org/all/CAKfTPtCyZRjjDWQxoHjG-SdJueTXBCZ4HesjPT0sPikb_dQtEw@mail.gmail.com/

---
id: sched-20260929-018
date: 2026-09-29
subject: "sched/eevdf: Add min slice check when selecting CPU"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260921152238.3804392-9-vincent.guittot@linaro.org>"
lore_url: "https://lore.kernel.org/all/CAKfTPtCyZRjjDWQxoHjG-SdJueTXBCZ4HesjPT0sPikb_dQtEw@mail.gmail.com/"
authors:
  - "Vincent Guittot"
maintainers_involved:
  - "Vincent Guittot"
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260921152238.3804392-9-vincent.guittot@linaro.org>"
    date: 2026-09-21
    summary: "select_task_rq_fair 找不到空闲 CPU 时新增 select_slice_cpu() 比较 slice 选 CPU"
    review_outcome: "Peter 09-22 建议复用初次扫描；Kayra 09-27 质疑 nr_idle_scan 语义；Vincent 09-29 确认注释需更新并宣布与 idle CPU 搜索合并"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "select_slice_cpu 与 idle CPU 搜索的合并尚未落地"
  next_action: "Vincent 在下一版本落实合并 + 注释更新后重发"
contribution_opportunities:
  - kind: review
    description: "核对合并后的实现是否消除与 select_idle_sibling 的重复扫描、nr_idle_scan 语义与新注释一致"
generated_at: "2026-09-30T01:15:00"
source_email_count: 1
related_articles:
  - sched-20260927-007
tags:
  - eevdf
  - load_balance
---