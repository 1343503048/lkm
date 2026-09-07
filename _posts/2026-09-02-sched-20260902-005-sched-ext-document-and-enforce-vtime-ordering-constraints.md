---
id: sched-20260902-005
date: '2026-09-02'
subject: 'sched_ext: document and enforce vtime ordering constraints'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20260902024812.794879-1-cui.tao@linux.dev>
lore_url: https://lore.kernel.org/all/20260902024812.794879-1-cui.tao@linux.dev/
upstream_commit: null
fixes_commit: a4103eacc2ab
merged_branch: sched_ext/for-7.4
current_version: v3
generated_at: '2026-09-07'
authors:
- Tao Cui
maintainers_involved:
- Tejun Heo
- Andrea Righi
patch_series:
- 'sched_ext: document the rolling-cursor requirement for dsq_vtime'
- 'sched_ext/scx_flatcg: make cgv_node_less() wraparound-safe'
merge_assessment:
  likelihood: merged
  blocking_issues:
  - 无：Tejun Heo 9/2 14:42 已 "Applied 1-2 to sched_ext/for-7.4 with the subjects capitalized"
  - v1 里「内核 priq 比较器也改成回绕比较」那一刀被 Andrea/Tejun 否决，内核侧目前仅靠文档约束，缺 lag/lead 界的使用者仍有隐患
  next_action: 关注是否有调度器在内核 priq 上需要强制回绕界；把该契约用于自研 sched_ext 比较器体检
contribution_opportunities:
- 审计自研 sched_ext 调度器中所有 vtime/cvtime 的裸 < 比较，按新增 kdoc 契约整改
- 把 scx_flatcg 的 lag/lead 界形式化成可复用说明或 helper，供其它 time_before64() 排序的 DSQ 自检
- 跟踪 sashiko-bot 在 sched_ext 的其余报告（与 004 的 NMI 审计同源）
- 按「每 CPU 每次 pick 记一整个 slice」估算长稳容器场景下 scx_flatcg 的回绕点并做验证
source_email_count: 7
related_articles: []
tags:
- sched_ext
- documentation
title: 'sched_ext: document and enforce vtime ordering constraints'
layout: article
---

## TL;DR

`sched_ext` 的 vtime 排序用的是 **回绕语义的 `time_before64()`**，而不是普通无符号比较：只要同一个
DSQ 里的两个值相差不到 `2^63` 就成立，否则顺序会翻。Tao Cui 把这条隐含契约写进 kdoc（1/2），
并修掉 `scx_flatcg` 里唯一违反它的比较器（2/2，`cgv_node_less()` 的 `plain <` → `time_before()`）。
**上一轮本文写的「缓存里看不到 v3 的结论性意见」是错的：Tejun Heo 当日 14:42 就回复
"Applied 1-2 to sched_ext/for-7.4 with the subjects capitalized."** 从 v1 到进树不到 16 小时，
是观察「sched_ext 小修复如何被 maintainer 当场塑形」的干净样本。

## 背景与问题

`scx_bpf_dsq_insert_vtime()` 的排序按 `time_before64()`，"which considers wrapping. A numerically
larger vtime may indicate an earlier position in the ordering and vice-versa."——这是 vtime 型调度器的
天然写法，但**约束「同一 DSQ 内的值必须彼此相差小于 `2^63`」在代码和文档里都没写出来**。
`scx_flatcg` 的 BPF 红黑树比较器 `cgv_node_less()` 恰好用了朴素 `<`：一旦 `cvtime` 回绕，
回绕节点会被排到树最前，未回绕的全体卡在它后面。

## 技术方案

- **1/2 `sched_ext: document the rolling-cursor requirement for dsq_vtime`**
  （`kernel/sched/ext/ext.c`，+3/-1）在 kdoc 里补：
  "vtime is a rolling cursor and values used for ordering within a given DSQ should stay less than
  `2^63` apart for `time_before64()` ordering to remain well-defined."
- **2/2 `sched_ext/scx_flatcg: make cgv_node_less() wraparound-safe`**
  （`tools/sched_ext/scx_flatcg.bpf.c`，1 行）：
  `return cgc_a->cvtime < cgc_b->cvtime;` → `return time_before(cgc_a->cvtime, cgc_b->cvtime);`
  并给出为什么这里可以安全使用回绕比较：`cgrp_cap_budget()` 约束住 `cvtime_now` 之后的 **lag**，
  而 **lead** 由「每次 pick 给 cgroup 记一整个 slice」的 slice charge 加上重新入队时 pending 的
  `cvtime_delta` 约束，两者都远小于 `2^63`。

标签：`Fixes: a4103eacc2ab ("sched_ext: Add a cgroup scheduler which uses flattened hierarchy")`、
`Reported-by: Sashiko <sashiko-bot@kernel.org>`。

## 版本演进与当前进展

v1（9/1，含 3 个补丁）→ Tejun 逐条评审 v2（9/1 22:03）→ 作者 9/2 09:21 汇总接受 →
**v3 9/2 10:48 → Tejun 14:42 applied**。

v1→v2 的实质变化最有信息量：**删掉「把内核 priq 比较器也改成回绕比较」那一刀**。作者在封面 changelog
里写的原因："the cyclic ordering is the documented contract; a plain comparison causes unbounded
starvation at the natural wrap (Andrea, Tejun)"——即内核侧的 priq 不能改成回绕比较，
因为内核没有像 `cgrp_cap_budget()` 那样的 lag/lead 界；改法只能是「把契约写下来」而不是「全面强制」。

v2→v3 全部是 Tejun 的修正（封面逐条列出）：
1. 界要写成 **"less than `2^63` apart"** 而不是 "within"——"Two values exactly 2^63 apart are before
   each other in both directions"；
2. 回绕后果方向写反了：不是未回绕的卡在前面，而是 "Plain < puts the wrapped node at the front.
   The unwrapped ones get stuck behind it."；
3. 回绕时间尺度比想象近得多："each CPU picking a cgroup charges it a full slice, so the wrap is
   closer than weeks."；
4. 只讲 lag 不够，**lead 也要有界**："cgrp_cap_budget() only bounds the lag. The lead is bounded by
   the slice charge plus pending cvtime_delta on re-insertion."；
5. `Fixes:` 指向的 commit 不在主线，正确上游 hash 是 `a4103eacc2ab`；
6. 比较器直接用 `time_before()`，把那行注释删掉。

## Maintainer 意见与讨论焦点

- **Tejun Heo** 是唯一评审者，也是 committer；六条意见全是「正确性表述」而非风格，且当天就 applied
  （只把 subject 首字母大写）。这说明 sched_ext 小修的门槛在于**技术表述必须精确**，而不是在于要多少
  Acked-by。
- **Andrea Righi** 参与的是 v1 那一刀被撤的决定（changelog 记名 "Andrea, Tejun"）。
- 报告者是 **sashiko-bot**（`Reported-by: Sashiko <sashiko-bot@kernel.org>`），
  原始发现贴 `3f1ce004-e259-4e72-a5f7-14a5050053bd@linux.dev` 已作为 `Link:` 写进补丁。
  也就是说，这次是自动审查机器人发现 → 人写补丁 → 人纠正表述 → 进树。
- 作者身份细节值得注意：邮件从 `Tao Cui <cui.tao@linux.dev>` 发出，`From:`/`Signed-off-by:`
  是 `Tao Cui <cuitao@kylinos.cn>`。

## 合入评估

**likelihood: likely（事实已完成）**——两个补丁 9/2 即进 `sched_ext/for-7.4`，无遗留卡点。
唯一「没做」的是内核侧 priq 比较器，被明确判定为不该做（缺 lag/lead 界），后续若要强制，
需要为内核 priq 的使用者补上同样的界。

## 效果评估

1 行比较器修复，无性能影响，属正确性。严重性完全由「界有多近」决定，而这正是 Tejun 纠正的地方：
每个 CPU 每次 pick 一个 cgroup 就记一整个 slice，因此回绕不是「几周」量级，而是随 CPU 数与调度频率
线性逼近；一旦回绕，未回绕的 cgroup 全体排在回绕节点之后 → 对 `scx_flatcg` 是**无界饥饿**，
不是误差。这也解释了为什么 v1 想改内核 priq 会被拦下：同样的改动在没有 lag/lead 界的地方会把
「不常见但有限」的误差换成「不可控的饥饿」。

## 我可以参与的点

- 给自家 sched_ext 调度器做同类体检：所有自定义比较器里 `vtime`/`cvtime`/`dsq_vtime` 的裸 `<`
  都是同一类 bug；这条契约现在写进了内核 kdoc，可以直接引用作为依据。
- 顺着「界从哪来」做一件更值钱的事：把 `scx_flatcg` 的 lag/lead 界形式化成一份可复用的说明或
  helper，供其它使用 `time_before64()` 排序的 DSQ 检查自己是否满足前提。
- 关注 sashiko-bot 的其余报告：`scx_bpf_task_set_slice()` 的竞争正是同一批审计的产物
  （见 [[sched-20260902-004]]）。
- cgroup 视角：`scx_flatcg` 是扁平层级 cgroup 调度器，这条回绕修复影响长时间运行的容器场景，
  做 cgroup CPU 公平性测试时可以按「每 CPU 每次 pick 记一整个 slice」来估算回绕点。

## 参考链接

- https://lore.kernel.org/all/20260902024812.794879-1-cui.tao@linux.dev/ （v3 0/2 封面，含完整 changelog）
- https://lore.kernel.org/all/20260902024812.794879-2-cui.tao@linux.dev/ （v3 1/2 kdoc）
- https://lore.kernel.org/all/20260902024812.794879-3-cui.tao@linux.dev/ （v3 2/2 flatcg）
- Tejun 的 v2 评审：https://lore.kernel.org/all/0cbe2f233f77f013361d4593a88bac38@kernel.org/ 、
  https://lore.kernel.org/all/beadefcfd5ae112a703b2514f6eebf34@kernel.org/ ；
  applied：https://lore.kernel.org/all/752cd2e42b6161465a7644c3085ce924@kernel.org/
- sashiko 原始报告（补丁 `Link:`）：https://lore.kernel.org/all/3f1ce004-e259-4e72-a5f7-14a5050053bd@linux.dev/
- 相关：[[sched-20260902-004]]、[[sched-20260902-006]]
