# sched_ext: Fix scx_bpf_dsq_reenq___compat kfunc extern prototype

## TL;DR
Tejun Heo 修复 `scx_bpf_dsq_reenq()` 的 `___compat` 变体 kfunc extern 原型暴露问题：旧 BPF 调度器因 extern 原型缺失/错误而无法解析该 kfunc。已 apply 到 `sched_ext/for-7.2-fixes`（stable 候选）。

## 背景与问题
sched_ext 为旧 BPF 程序保留 `___compat` 兼容 kfunc。但 `scx_bpf_dsq_reenq()` 的 compat 变体外联原型在 BPF 端未正确暴露，导致依赖它的旧调度器编译或加载时报 `unresolved symbol / kfunc` 错误，破坏向后兼容。

## 技术方案
修正 autogen 的 kfunc extern 原型生成，使 `scx_bpf_dsq_reenq___compat`（或对应兼容名）在 BPF 程序侧可见且签名正确。属于 ABI/兼容性修复，无运行时逻辑改动。

## 版本演进与当前进展
- v1（40951）讨论于 40959。
- v2 同日修订并 apply 到 `sched_ext/for-7.2-fixes`（stable 候选）。

## Maintainer 意见与讨论焦点
Tejun 自审自收，作为 7.2 修复稳定回传候选。

## 合入评估
已合入 for-7.2-fixes。关注 stable 回传状态。

## 效果评估
恢复旧 BPF 调度器对 reenq compat kfunc 的可用性；无性能影响。

## 我可以参与的点
- 用旧调度器验证加载不再报 unresolved kfunc。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched_ext: Fix scx_bpf_dsq_reenq___compat kfunc extern prototype"
id: sched-20260815-010
date: 2026-08-15
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<uid-40951@qq-imap>"
lore_url: "未获取到"
authors: [Tejun Heo]
maintainers_involved: [Tejun Heo]
current_version: v2
patch_series:
  - version: v2
    msgid: "<uid-40951@qq-imap>"
    date: 2026-08-15
    summary: "正确暴露 scx_bpf_dsq_reenq() 的 ___compat 变体 kfunc extern 原型，使旧 BPF 程序能编译/加载。"
    review_outcome: "已 apply 到 sched_ext/for-7.2-fixes（stable 候选）。"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.2-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已进入 for-7.2-fixes，关注是否走 stable 回传。"
contribution_opportunities:
  - kind: testing
    description: "用旧版本 BPF 调度器（依赖 reenq compat）验证加载不再报 unresolved kfunc。"
generated_at: "2026-08-16T00:10:00"
source_email_count: 2
related_articles: []
tags: [sched_ext]
---
