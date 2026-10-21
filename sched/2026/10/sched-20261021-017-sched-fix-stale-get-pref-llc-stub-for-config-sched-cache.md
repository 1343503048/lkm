# sched: fix stale get_pref_llc() stub for !CONFIG_SCHED_CACHE

## TL;DR
Yafang Shao 的 bpf-next RFC v3 系列（per-cgroup NUMA balancing 模式选择）中的 1/5 补丁：修正 `!CONFIG_SCHED_CACHE` 构建下 `get_pref_llc()` 桩函数已过期（与实际签名不符）的问题。当日获 Gregory Price 与 Chen Yu 双 Reviewed-by，两人均建议这类修复应**从系列中拆出单独提交**；作者已回应会单独发送。

## 背景与问题
`get_pref_llc()` 的 `!CONFIG_SCHED_CACHE` 桩实现与其新签名失配（stale），在关闭 SCHED_CACHE 的构建下会编译/语义异常。该修复混在 Yafang 的 bpf-next RFC 系列里，评审者一致认为应作为独立修复提交、不要裹进大系列。

## 技术方案
单补丁：把 `!CONFIG_SCHED_CACHE` 下过期的 `get_pref_llc()` 桩更新到与实际函数签名一致。具体 diff 未完整进入当日缓存。

## 版本演进与当前进展
*current_version: v3*（所在 bpf-next 系列为 RFC v3；本补丁 `<20261019064157.29885-2-laoar.shao@gmail.com>`）。

## Maintainer 意见与讨论焦点
- Gregory Price（Meta）：*Reviewed-by*，并要求「这类修复请从系列中拆出单独提交」。
- Chen Yu（Intel）：*Reviewed-by*（"Ah, right"）。
- 作者 Yafang Shao：回应「谢谢 review，我会单独发送」。无分歧。

## 合入评估
*likelihood=high*。双 Reviewed-by、无争议，作者已承诺拆分单独发送。*blocking_issues*：需从 bpf-next 系列中拆出、走独立提交。*next_action*：作者单独发出该修复补丁。

## 效果评估
无 benchmark。属编译正确性修复（stub 签名对齐）。

## 我可以参与的点
- `review`：作者单独发出后核对 stub 与真实签名是否完全一致、覆盖所有构建配置。

## 参考链接
- 补丁 1/5：https://lore.kernel.org/all/20261019064157.29885-2-laoar.shao@gmail.com/
- Gregory Price Reviewed-by：https://lore.kernel.org/all/179254940965.1919196.7604748267690139512.b4-reply@b4/

---
id: sched-20261021-017
date: 2026-10-21
subject: "sched: fix stale get_pref_llc() stub for !CONFIG_SCHED_CACHE"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261019064157.29885-2-laoar.shao@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261019064157.29885-2-laoar.shao@gmail.com/"
authors: ["Yafang Shao"]
maintainers_involved: []
current_version: v3
patch_series:
  - version: v3
    msgid: "<20261019064157.29885-2-laoar.shao@gmail.com>"
    date: 2026-10-19
    summary: "修正 !CONFIG_SCHED_CACHE 下 get_pref_llc() 桩签名"
    review_outcome: "Gregory Price + Chen Yu Reviewed-by，要求拆分单独提交"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["需从 bpf-next 系列拆出单独提交"]
  next_action: "作者单独发出该修复"
contribution_opportunities:
  - kind: review
    description: "单独提交后核对 stub 与真实签名一致"
generated_at: "2026-10-22T01:30:00"
source_email_count: 3
related_articles: ["sched-20261019-008"]
tags: [cfs]
---