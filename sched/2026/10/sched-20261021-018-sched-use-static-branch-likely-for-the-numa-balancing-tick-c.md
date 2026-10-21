# sched: use static_branch_likely() for the NUMA balancing tick check

## TL;DR
Yafang Shao 的 bpf-next RFC v3 系列中的 2/5 补丁：把 NUMA balancing tick 检查改用 `static_branch_likely()` 微优化。当日 Gregory Price 给出 *Acked-by*，并同样要求「这对你的系列有用，请单独提交」。

## 背景与问题
NUMA balancing 的 tick 检查当前用 `static_branch_unlikely()` 或普通分支，改用 `static_branch_likely()` 以符合其绝大多数情况下的走向，属微型性能/语义优化。该改动同样混在 bpf-next RFC 系列里，评审者要求拆分单独提交。

## 技术方案
单补丁：NUMA balancing tick 检查改用 `static_branch_likely()`。具体 diff 未完整进入当日缓存。

## 版本演进与当前进展
*current_version: v3*（所在 bpf-next 系列为 RFC v3；本补丁 `<20261019064157.29885-3-laoar.shao@gmail.com>`）。

## Maintainer 意见与讨论焦点
Gregory Price（Meta）：*Acked-by*，并明确「这跟 1/5 一样，对你的系列有用，请单独提交」。作者已承诺拆分。无分歧。

## 合入评估
*likelihood=high*。已获 Acked-by、无争议，作者承诺拆分。*blocking_issues*：需从 bpf-next 系列拆出单独提交。*next_action*：作者单独发出该补丁。

## 效果评估
无 benchmark。属分支预测/静态 key 语义微优化。

## 我可以参与的点
- `review`：单独提交后核对 NUMA balancing tick 路径的 static_branch 语义是否与注释/预期一致。

## 参考链接
- 补丁 2/5：https://lore.kernel.org/all/20261019064157.29885-3-laoar.shao@gmail.com/
- Gregory Price Acked-by：https://lore.kernel.org/all/179254956989.1919196.954997201143423051.b4-reply@b4/

---
id: sched-20261021-018
date: 2026-10-21
subject: "sched: use static_branch_likely() for the NUMA balancing tick check"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261019064157.29885-3-laoar.shao@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261019064157.29885-3-laoar.shao@gmail.com/"
authors: ["Yafang Shao"]
maintainers_involved: []
current_version: v3
patch_series:
  - version: v3
    msgid: "<20261019064157.29885-3-laoar.shao@gmail.com>"
    date: 2026-10-19
    summary: "NUMA balancing tick 检查改用 static_branch_likely()"
    review_outcome: "Gregory Price Acked-by，要求拆分单独提交"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["需从 bpf-next 系列拆出单独提交"]
  next_action: "作者单独发出该补丁"
contribution_opportunities:
  - kind: review
    description: "核对 static_branch 语义与注释一致"
generated_at: "2026-10-22T01:30:00"
source_email_count: 1
related_articles: ["sched-20261019-008"]
tags: [numa_balancing, cfs]
---