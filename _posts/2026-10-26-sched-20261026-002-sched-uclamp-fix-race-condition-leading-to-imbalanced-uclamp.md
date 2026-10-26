---
id: sched-20261026-002
date: 2026-10-26
subject: 'sched/uclamp: Fix race condition leading to imbalanced uclamp_rq'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261024233945.74794-1-qyousef@layalina.io>
lore_url: https://lore.kernel.org/all/20261024233945.74794-1-qyousef@layalina.io/
authors:
- Qais Yousef
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v1
  msgid: <20261024233945.74794-1-qyousef@layalina.io>
  date: 2026-10-24
  summary: idle 入口做 uclamp_rq 失衡纠错，堵不住 static key 非原子竞态就事后修复
  review_outcome: lkp 报 init_uclamp_rq 在 !CONFIG_UCLAMP_TASK 下重复符号链接错误
- version: v2
  msgid: <20261025162612.360033-1-qyousef@layalina.io>
  date: 2026-10-26
  summary: 修 lkp 链接错误（!CONFIG_UCLAMP_TASK 补 static inline dummy），idle 检测加 WARN_ON
  review_outcome: Peter 建议折叠 uclamp_flags + 用 UCLAMP_FLAG_IDLE 判据取代 bucket 扫描
upstream_commit: null
fixes_commit: 46609ce227039
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 需按 Peter 意见以 flag 判据取代 bucket 扫描后重发 v3
  next_action: 作者改用 flag 判据后重发 v3，折叠 uclamp_flags 留待后续独立补丁
contribution_opportunities:
- kind: review
  description: 评估折叠 uclamp_flags 进 struct uclamp_rq hole 的可行性与 UCLAMP_FLAG_IDLE 判据等价性
- kind: testing
  description: 启用 uclamp 的构建上验证 idle 纠错逻辑、失衡只瞬时存在
generated_at: '2026-10-27T01:00:00'
source_email_count: 4
related_articles:
- sched-20261025-001
tags:
- uclamp
- cfs
title: 'sched/uclamp: Fix race condition leading to imbalanced uclamp_rq'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-001-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261025-001</a>：Qais Yousef 发单补丁修 uclamp 的 static key 非原子翻转导致的 runqueue 计数失衡竞态：`sched_uclamp_used` 使能瞬间部分 CPU 走 uclamp 快路径、部分不走，跨 CPU 的 enqueue/dequeue 不对称会使 `uclamp_rq` 计数永久错位。方案不试图堵住竞态，改为「视为既成事实 + idle 入口纠错」。kernel test robot 当日报出 arm/arc allnoconfig 下的 `init_uclamp_rq` 重复符号链接错误，需先修。
- <a class="article-ref" href="/lkm/2026/10/26/sched-20261026-002-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261026-002</a>（今天）：作者发 **v2**，修掉 lkp 报的 `init_uclamp_rq` 在 `!CONFIG_UCLAMP_TASK` 下缺 `static inline` 的 dummy 定义问题（链接错误根因），并把 idle 入口的失衡检测改为 `WARN_ON(uclamp_is_imbalanced(rq))`。Peter Zijlstra 首轮 review：指出一处 whitespace 问题，并建议「把 `uclamp_flags` 折进 `struct uclamp_rq` 的 hole、用 `UCLAMP_FLAG_IDLE` 判断是否真的需要扫 bucket」。Qais 回应：会改成「flag 未置位即视为 corruption、不扫 bucket」，并同意把 uclamp_flags 折进 bucket 的事放到**后续独立补丁**（因为本补丁要进 LTS，先保持最小化）。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-001-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261025-001</a>）static key 跨 CPU 并不保证原子使能，`sched_uclamp_used` 打开时，有些 CPU 的 `uclamp_is_used()` 已返回 true、有些还没，导致 `uclamp_rq_{inc,dec}_id` 不对称。减而无增是安全的（代码注释已说明），但**增而无减**会破坏 `uclamp_rq` 状态。这个增而无减的竞态含义是：某 CPU 看到 key 翻转后在 enqueue 任务时递增，而该任务在另一个尚未看到翻转的 CPU 上 dequeue——作者提醒「这可能是更深问题的症状，需警惕」。真正堵住竞态很难（作者引用了 [1] 的讨论）。`Fixes: 46609ce227039`（"sched/uclamp: Protect uclamp fast path code with static key"），`Reported-by: Wei Wang <wvw@google.com>`。

今日无新背景，为 v2 修复 + 维护者首轮 review。

## 技术方案
（承接 <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-001-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261025-001</a>）不堵竞态，而是把失衡当作既成事实，在**进入 idle 时做纠错动作**，保证该状态只在 `sched_uclamp_used` 使能后的很短时间内瞬时存在。核心新增 `uclamp_is_imbalanced(rq)` 扫描 `uclamp_rq` 各 clamp_id 的 bucket，idle 上若有 bucket.tasks 非零即视为失衡、调 `init_uclamp_rq(rq)` 重置。

今日方案演进：

- **v2 改动**：`init_uclamp_rq` 从 `static` 改为公开声明（`kernel/sched/sched.h` 里 `void init_uclamp_rq(struct rq *rq);`），并为 `!CONFIG_UCLAMP_TASK` 补 `static inline void init_uclamp_rq(struct rq *rq) {}` 与 `uclamp_is_imbalanced()` 返回 false 的 dummy——修掉 lkp 报的 arm/arc allnoconfig 下重复符号链接错误；同时 idle 入口的检测加 `WARN_ON`。
- **Peter Zijlstra 意见**：`struct uclamp_rq` 里有 hole，`uclamp_flags` 也是独立成员，建议把 `uclamp_flags` 折进 hole，并用 `UCLAMP_FLAG_IDLE` 判断「是否需要扫 bucket」（即 flag 未置位时直接判定 corruption，省掉 bucket 扫描）。
- **Qais Yousef 回应**：本来就觉得扫 bucket 不优雅、当时图「对 backport 更安全」才那么写；同意改成「flag 未置位即 corruption、不扫 bucket」并更新；同时确认「把 uclamp_flags 折进 bucket 不会增大结构体、且对未来去掉 uclamp_rq 有帮助」，但鉴于本补丁要进 LTS，倾向**保持最小化、折进 bucket 的事放后续独立补丁**。

## 版本演进与当前进展
*current_version: v2*（`<20261025162612.360033-1-qyousef@layalina.io>`，北京时间 10-26 00:26 进入缓存）。v1（`<20261024233945.74794-1-qyousef@layalina.io>`）→ v2 的关键改动：修 lkp 报的 `init_uclamp_rq` 在 `!CONFIG_UCLAMP_TASK` 下缺 static inline dummy 的链接错误。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（当日两封）：(1) 指出 v2 有一处 **whitespace fail**；(2) 建议折叠 `uclamp_flags` 进 `struct uclamp_rq` 的 hole、用 `UCLAMP_FLAG_IDLE` 判断是否真的需要 bucket 扫描。
- **Qais Yousef（作者）**：同意「flag 未置位即 corruption、不扫 bucket」的简化方向并会更新；确认折叠 uclamp_flags 不会让结构体变大、也有利于将来去掉 uclamp_rq，但「既然要进 LTS，先保持最小化，折叠的事放后续独立补丁」。

无分歧性 NAK；Peter 未反对方案本身，只要求判据更简洁、避免 bucket 扫描。

## 合入评估
*likelihood=medium*。方向已获 Peter 认可（无方向性异议），v2 修掉了 lkp 的链接错误；但还需按 Peter 意见把「扫 bucket」换成「flag 判据」再发 v3。*blocking_issues*：需按 Peter 意见以 flag 判据取代 bucket 扫描；whitespace 问题。*next_action*：作者改用 flag 判据后重发 v3（折叠 uclamp_flags 留待后续独立补丁）。

## 效果评估
无量化数据。作者定性描述：用 `sched_feat` 强制注入额外 inc 制造失衡时，可见 WARN 出现、cpufreq 频率 spike；关闭注入后 idle entry 的 reset 能把状态修复。属正确性修复。

## 我可以参与的点
- *kind: review*：评估「折叠 `uclamp_flags` 进 `struct uclamp_rq` hole」是否真的不增长结构体、以及 `UCLAMP_FLAG_IDLE` 作判据的等价性。
- *kind: testing*：在启用 uclamp（且混用 uclamp_max，如 schedqosd）的构建上验证 idle 纠错逻辑，确认失衡只瞬时存在、不累积。

## 参考链接
- v2 patch: https://lore.kernel.org/all/20261025162612.360033-1-qyousef@layalina.io/
- Peter 首评（whitespace + 折叠建议）: https://lore.kernel.org/all/20261026101254.GA2668200@noisy.programming.kicks-ass.net/
- 作者回应: https://lore.kernel.org/all/9054450c-f85f-402a-a2ff-fa5f314f92c5@layalina.io/
- 竞态讨论 [1]: https://lore.kernel.org/lkml/CANDhNCqyXsZ6G77z+9s=rTO6BZifRG9+hVxMTah+tAv6pB6h3w@mail.gmail.com/
- 前文: <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-001-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261025-001</a>
