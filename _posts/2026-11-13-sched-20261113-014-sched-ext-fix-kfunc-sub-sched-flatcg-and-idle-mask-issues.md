---
id: sched-20261113-014
subject: 'sched_ext: fix kfunc, sub-sched, flatcg and idle-mask issues'
date: 2026-11-13
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261112130934.563321-1-cui.tao@linux.dev>
lore_url: https://lore.kernel.org/all/20261112130934.563321-1-cui.tao@linux.dev/
authors:
- Tao Cui
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261112130934.563321-1-cui.tao@linux.dev>
  date: 2026-11-12
  summary: 六补丁修 sched_ext core / scx_flatcg / CID helper 六个问题
  review_outcome: Tejun 逐封评审：1/6 Applied to for-7.4-fixes，2-6 被退回重想
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4-fixes
merge_assessment:
  likelihood: low
  blocking_issues:
  - 2-6 未通过 Tejun 评审（5/6 race 未修好、6/6 未解决所描述问题、其余需返工）
  next_action: 作者按 Tejun 意见重想 2-6 的实际用法语义后再发
contribution_opportunities:
- kind: review
  description: 帮助审视 2-6 各补丁在实际 sched_ext 用法下是否成立
- kind: testing
  description: 验证 1/6 后 tracing 程序调用 DSQ 迭代 kfunc 不再锁死
generated_at: '2026-11-14T01:30:00'
source_email_count: 8
related_articles:
- sched-20261112-002
tags:
- sched_ext
- bpf
title: 'sched_ext: fix kfunc, sub-sched, flatcg and idle-mask issues'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-002-sched-ext-fix-kfunc-sub-sched-flatcg-and-idle-mask-issues.html">sched-20261112-002</a>：Tao Cui 发六补丁修 sched_ext core、scx_flatcg 与 CID helper 的六个问题（最严重：两个 DSQ 迭代 kfunc 可被 tracing 程序调用、持锁时递归自旋锁死整机）。刚发出时无维护者回复。
- <a class="article-ref" href="/lkm/2026/11/13/sched-20261113-014-sched-ext-fix-kfunc-sub-sched-flatcg-and-idle-mask-issues.html">sched-20261113-014</a>（今天）：**Tejun Heo 逐封评审全部六封**——1/6「Reject DSQ iterator kfuncs in tracing programs」被 **Applied to sched_ext/for-7.4-fixes**；2/6 认为该改的是 kerneldoc 而非行为；3/6 问「Why is this useful?」；4/6 指出调度器 root/sub 角色取决于加载方式、不该拆分 op 表；5/6「实际上没修好 race」建议只加注释；6/6「failure mode 无害、补丁连自己描述的都没解决」。**作者 Tao 承认用 LLM 辅助、承认过度聚焦问题而忽略实际用法**，承诺后续改进。

## 背景与问题
（承接 20261112-002）作者在 `sched_ext/for-next` 上逐个修复六个独立缺陷（DSQ 迭代 kfunc 可被 tracing 递归调用锁死、`scx_bpf_cid_node()` 对非法 cid abort、sub-scheduler 在 `ops.init_cids()` 读 caps 被杀、`cid_online/cid_offline` 回调不触发、scx_flatcg ENQ_RACE 甩出 cgroup、hotplug 不清内置 idle mask）。今日 Tejun 评审指出六个里只有一个真正该合。

## 技术方案
今日为逐封评审，无新代码：
- **1/6** `sched_ext: Reject DSQ iterator kfuncs in tracing programs`：**Applied**（唯一实质修复）。
- **2/6** `Make scx_bpf_cid_node() a benign lookup for invalid cids`：Tejun 认为该改的是 kerneldoc（说明非法 cid 触发错误），其它 cid kfunc 对非法 cid 报错、这一个应保持一致。
- **3/6** `Return -EBUSY from a pre-init scx_bpf_sub_caps() read`：Tejun 问「这有什么用」——`ops.init_cids()` 文档写明在 caps/shards 定型前运行，调度器此时无从查询或重试。
- **4/6** `Reject cid_online/cid_offline on sub-schedulers`：调度器 root/sub 取决于加载方式，不该要求按加载方式拆 op 表。
- **5/6** `scx_flatcg: Don't strand a cgroup on the ENQ_RACE path`：Tejun 实测该补丁没修好 race（仍可复现 stall），建议只加注释；scx_flatcg 本就不面向生产、用 arena 结构能做得更好。
- **6/6** `Clear the built-in idle masks on CPU hotplug transitions`：failure mode 无害，且补丁「连自己描述的都没解决」（实现了 hotplug ops、只读 idle mask 的调度器在 offline 窗口仍会看到 CPU 留在 mask）。

## 版本演进与当前进展
v1（20261112）→ 今日 1/6 进 for-7.4-fixes，2-6 被退回重想。作者 Tao 回应：承认用 LLM 辅助、部分补丁源自其扫出的问题，认同过度聚焦问题本身而忽略「修复在实际用法下是否成立」，承诺后续改进。

## Maintainer 意见与讨论焦点
- **Tejun Heo（sched_ext 维护者）**：明确「这里只有一个真正的修复（1/6），其余相当空洞」，请作者「更仔细思考每个改动在实际用法语境下是否成立」，并直接点出 LLM 扫描补丁的问题。
- 无 NAK 但 5/6 基本被否决（race 未修好），2-4/6 被要求返工。

## 合入评估
1/6 已合入 for-7.4-fixes（merged）；其余 2-6 合入可能性低（需按 Tejun 意见返工或放弃）。整体系列 likelihood 评估为 low。

## 效果评估
无 benchmark；1/6 的锁死修复（DSQ 迭代 kfunc 被 tracing 递归调用）是实质正确性修复。

## 我可以参与的点
- **review**：帮助作者重新审视 2-6 各补丁在实际 sched_ext 用法下是否成立（尤其 5/6 的 ENQ_RACE race 是否能用 arena 结构根治）。
- **testing**：验证 1/6 修复后 tracing 程序调用 DSQ 迭代 kfunc 不再锁死。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261112130934.563321-1-cui.tao@linux.dev/
- 1/6 Applied: https://lore.kernel.org/all/32f1ba66f4cc42e77e88130565f1fac8@kernel.org/
