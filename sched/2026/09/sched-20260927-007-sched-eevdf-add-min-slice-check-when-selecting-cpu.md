# sched/eevdf: Add min slice check when selecting CPU

## TL;DR

本文为增量更新，完整脉络见 related_articles（Vincent Guittot 的 8 补丁「Improving latency of short slice tasks」系列中的 patch 8/8）。

- sched-20260921-001：系列 v1 发出，patch 8/8 在 `select_task_rq_fair()` 找不到空闲 CPU 时新增最后一层 `select_slice_cpu()`，比较 slice 选「任务能最先运行」的 CPU。
- sched-20260922-011：Peter Zijlstra 认为 8/8 与 `select_idle_sibling()` 重复，建议复用初次扫描记录的最小 slice CPU，避免重复扫描。
- sched-20260927-007（今天）：Kayra Cizmeci 对 8/8 提出疑问——`select_slice_cpu()` 里的 `nr_idle_scan` 语义与顶部「idle CPU 扫描」注释不符，当前场景并非找 idle CPU；请 Vincent 指正。

## 背景与问题

（承接 sched-20260921-001）EEVDF 下短 slice 任务在 `select_task_rq_fair()` 找不到空闲 CPU 时，可能被放到已运行同长或更短 slice 任务的 CPU 上、导致显著等待。patch 8/8 为此在选 CPU 的最后阶段加入 min slice 检查。

## 技术方案

（承接 sched-20260921-001）patch 8/8 新增 `select_slice_cpu()`：比较候选 CPU 的 slice，选择「任务能最先运行」的 CPU。今日 Kayra 的疑问落在实现细节——`select_slice_cpu()` 复用了 `nr_idle_scan` 变量/计数（其注释与 `select_idle_cpu` 系列谈的是「idle CPU 扫描」），但当前场景是「比较 slice 选 CPU」而非找 idle CPU，怀疑变量语义被误用。

## 版本演进与当前进展

- v1（2026-09-21，patch 8/8 `<20260921152238.3804392-9-vincent.guittot@linaro.org>`）。
- 09-22：Peter review——8/8 与 `select_idle_siblings()` 重复，建议复用初次扫描（对应 sched-20260922-011）。
- 09-27：Kayra 对 `nr_idle_scan` 语义提出疑问，本日 Vincent 未回复。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci**（今日，`<20260927074523.14558-1-kayracizmeci@gmail.com>`）：质疑「Ain't nr_idle_scan shows load of the system? Even the comment at top talks about idle CPU's, but we're not looking for an idle CPU right now.」，即变量语义/注释与当前用途脱节，请 Vincent 指正。
- **Peter Zijlstra**（前一日，已记录在 sched-20260922-011）：8/8 与 `select_idle_sibling()` 重复，建议复用。
- Vincent Guittot 本日未回复，两条针对性意见（Peter 的重复扫描、Kayra 的 `nr_idle_scan` 语义）均待处理。

## 合入评估

*likelihood=unknown*（就本 patch 而言）。patch 8/8 方向（CPU 选择考虑 min slice）与系列一脉相承，但实现上已有 Peter 的「重复扫描」意见，今日又叠加 Kayra 的 `nr_idle_scan` 语义疑问，实现尚未收敛。*blocking_issues*：`nr_idle_scan` 语义疑问待澄清；与 `select_idle_sibling` 的重复扫描待调整。*next_action*：Vincent 回复 Kayra，并落实 Peter 的「复用初次扫描」意见后重发该 patch。

## 效果评估

本 patch 无单独效果数据；系列整体 benchmark 见 sched-20260921-001。

## 我可以参与的点

- `discussion`：回应 `nr_idle_scan` 语义疑问——该变量在 `select_slice_cpu()` 场景中的实际含义与顶部注释是否脱节，澄清或提出注释修正。
- `review`：核对 `select_slice_cpu()` 与 `select_idle_sibling()` 的扫描逻辑重叠程度，判断是否可复用初次扫描、消除重复。

## 参考链接

- patch 8/8: https://lore.kernel.org/all/20260921152238.3804392-9-vincent.guittot@linaro.org/
- Kayra 回复: https://lore.kernel.org/all/20260927074523.14558-1-kayracizmeci@gmail.com/
- 系列 cover: https://lore.kernel.org/all/20260921152238.3804392-1-vincent.guittot@linaro.org/

---
id: sched-20260927-007
date: 2026-09-27
subject: "sched/eevdf: Add min slice check when selecting CPU"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260921152238.3804392-9-vincent.guittot@linaro.org>"
lore_url: "https://lore.kernel.org/all/20260927074523.14558-1-kayracizmeci@gmail.com/"
authors:
  - "Vincent Guittot"
maintainers_involved:
  - "Peter Zijlstra"
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260921152238.3804392-9-vincent.guittot@linaro.org>"
    date: 2026-09-21
    summary: "select_task_rq_fair 找不到空闲 CPU 时新增 select_slice_cpu()，比较 slice 选最先能运行的 CPU。"
    review_outcome: "Peter 09-22 认为与 select_idle_sibling 重复；Kayra 09-27 质疑 nr_idle_scan 语义，Vincent 未回复。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "nr_idle_scan 语义疑问待澄清"
    - "与 select_idle_sibling 的重复扫描待调整"
  next_action: "Vincent 回复 Kayra，并落实 Peter 的复用初次扫描意见后重发"
contribution_opportunities:
  - kind: discussion
    description: "回应 nr_idle_scan 语义疑问，澄清或提出注释修正"
  - kind: review
    description: "核对 select_slice_cpu 与 select_idle_sibling 扫描重叠，判断能否复用消除重复"
generated_at: "2026-09-28T09:00:00"
source_email_count: 1
related_articles:
  - sched-20260921-001
  - sched-20260922-011
tags:
  - eevdf
  - load_balance
---