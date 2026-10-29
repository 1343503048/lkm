# sched/uclamp: Fix race condition leading to imbalanced uclamp_rq

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261025-001：Qais Yousef 发单补丁修 uclamp 的 static key 非原子翻转导致的 runqueue 计数失衡竞态：`sched_uclamp_used` 使能瞬间部分 CPU 走 uclamp 快路径、部分不走，跨 CPU 的 enqueue/dequeue 不对称会使 `uclamp_rq` 计数永久错位；方案不堵竞态，改为「视为既成事实 + idle 入口纠错」。
- sched-20261026-002（v2）：修掉 lkp 报的 `init_uclamp_rq` 在 `!CONFIG_UCLAMP_TASK` 下缺 `static inline` 的链接错误，idle 检测改 `WARN_ON(uclamp_is_imbalanced(rq))`；Peter Zijlstra 建议把 `uclamp_flags` 折进 hole、用 `UCLAMP_FLAG_IDLE` 判断是否需扫 bucket。
- sched-20261029-001（今天）：作者发 **v4**，拆成 2 补丁（1/2 修竞态 + 2/2 用 wrapper 替换 open-coding 的 `UCLAMP_FLAG_IDLE`，增强可读）；Christian Loehle 对 1/2 再提一条：仅检查 `nr_running` 不够，因为 CFS 带宽节流会经 `dequeue_task_fair()` 递减 `nr_running` 却不调用 `uclamp_rq_dec()`，clamp 状态必须保持有效。

## 背景与问题
（承接 20261025-001 / 20261026-002）static key 跨 CPU 并不保证原子使能，`sched_uclamp_used` 打开时，有些 CPU 的 `uclamp_is_used()` 已返回 true、有些还没，导致 `uclamp_rq_{inc,dec}_id` 不对称。减而无增是安全的（代码注释已说明），但**增而无减**会破坏 `uclamp_rq` 状态（某 CPU 看到 key 翻转后 enqueue 时递增，任务却在尚未看到翻转的另一 CPU 上 dequeue）。真正堵住竞态很难（作者引用了 [1] 的讨论）。`Fixes: 46609ce227039`（"sched/uclamp: Protect uclamp fast path code with static key"），`Reported-by: Wei Wang <wvw@google.com>`。

今日无新背景；v4 主要是对既有方案做可读性拆分 + 吸收 review 意见。

## 技术方案
（承接 20261025-001）不堵竞态，把失衡当作既成事实，在**进入 idle 时做纠错动作**（`uclamp_is_imbalanced(rq)` 检测 + 重置），保证该状态只在 `sched_uclamp_used` 使能后很短时间内瞬时存在。

今日方案演进：

- **v4 拆分为 2 补丁**：1/2 保持竞态修复本体（`kernel/sched/core.c` + `idle.c` + `sched.h`，+23/-1）；2/2 是纯可读性改动——用已有的 `uclamp_rq_is_idle()` 与新增的 set/clear wrapper 替换 open-coding 的 `UCLAMP_FLAG_IDLE`（`kernel/sched/core.c` + `sched.h`，+17/-7），不改变行为。
- **Christian Loehle 对 1/2 的质疑**：认为仅检查 `nr_running` 不足以判定「clamp 状态可安全丢弃/重置」，因为 **CFS 带宽节流（throttling）** 会通过 `dequeue_task_fair()` 递减 `nr_running`，但不调用 `uclamp_rq_dec()`——即此时 rq 的 clamp 计数仍有效、不能因为 `nr_running` 归零就当作空闲去纠错。这是对 idle-entry 纠错触发条件正确性的实质挑战。

## 版本演进与当前进展
*current_version: v4*（2026-10-29，cover `<20261029131354.11030-1-qyousef@layalina.io>`）。

- **v1**（`<20261024233945.74794-1-qyousef@layalina.io>`，2026-10-24）：单补丁，idle 入口纠错思路首版。
- **v2**（`<20261025162612.360033-1-qyousef@layalina.io>`，2026-10-25）：修 `init_uclamp_rq` 链接错误（补 `static inline` dummy），idle 检测加 `WARN_ON`；回应 Peter Zijlstra 的 whitespace 与「uclamp_flags 折进 hole」建议（后者作者决定放后续独立补丁，本补丁保持最小化以进 LTS）。
- **v3**（2026-10-28，缓存未取到 msgid）：据作者回帖，v3 按 John Stultz 对 v2 的 review 更新了 commit 文案，并针对 force_idle 路径给 `rq->nr_running` 加了 guard。
- **v4 今日**：拆 2 补丁 + wrapper 化；新增 Christian Loehle 的 `nr_running` 判定挑战，尚未见 v5 或作者回应。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（维护者，v2 阶段）**：指出 whitespace 问题；建议把 `uclamp_flags` 折进 `struct uclamp_rq` 的 hole、用 `UCLAMP_FLAG_IDLE` 判断是否需要扫 bucket（flag 未置位即 corruption）。作者同意方向但倾向放后续独立补丁。
- **John Stultz（v3 阶段 review）**：提醒静态 key 竞态「不仅跨 CPU，也跨同一 CPU 上的 jump_label callsite」，enqueue/dequeue 竞态同核也可能发生——这一修正被吸收进 v3/v4 文案。
- **Christian Loehle（今天）**：质疑 `nr_running` 判定的充分性——CFS 带宽节流会递减 `nr_running` 而不调 `uclamp_rq_dec()`，clamp 必须保持有效。这是当前**未解决的分歧点**：idle-entry 纠错到底该以什么信号判定「可安全重置」，需要作者细化。

## 合入评估
*likelihood=medium*。方向（idle 入口纠错）已获 Peter Zijlstra 基本认可，v2 起已解决链接错误，系列保持最小化、目标进 LTS。当前卡点：Christian Loehle 提出的 `nr_running` 判定不足（带宽节流场景）尚未回应，*blocking_issues*：idle-entry 纠错的触发条件需覆盖 CFS throttling 递减 `nr_running` 但仍持有合法 clamp 的情况；*next_action*：作者确认 `nr_running` 之外还需什么信号来判定 clamp 状态失效，修订后发 v5。

## 效果评估
暂无合入后的性能数据；v2 阶段作者用 `sched_feat` 强制注入额外 inc 制造失衡来验证纠错路径（可见 WARN 出现、cpufreq 频率 spike；关闭该 sched_feat 后 idle reset 能修复状态），属正确性验证而非性能收益，未见 bench 数据。

## 我可以参与的点
- **review**：可结合 `kernel/sched/fair.c` 的 `dequeue_task_fair()` 节流路径，帮作者核对「带宽节流递减 `nr_running` 但保留 uclamp 计数的完整触发链」，验证 Christian 提出的边界是否还有其他同类路径（如 RT/DEADLINE 类迁移、`DEQUEUE_MOVE` 等）。
- **testing**：在启用 `CONFIG_UCLAMP_TASK` + CFS 带宽节流（`cpu.cfs_quota_us`/`period`）的环境下复现「idle 入口误判」场景，回帖给作者确认 v4 是否需要补丁。

## 参考链接
- lore thread（v4 cover）: https://lore.kernel.org/all/20261029131354.11030-1-qyousef@layalina.io/
- v1: https://lore.kernel.org/all/20261024233945.74794-1-qyousef@layalina.io/
- v2: https://lore.kernel.org/all/20261025162612.360033-1-qyousef@layalina.io/
- Christian Loehle 的 review: https://lore.kernel.org/all/c4740152-e873-4409-b3a8-16c5a49548dd@arm.com/

---
id: sched-20261029-001
date: 2026-10-29
subject: "sched/uclamp: Fix race condition leading to imbalanced uclamp_rq"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261029131354.11030-1-qyousef@layalina.io>"
lore_url: "https://lore.kernel.org/all/20261029131354.11030-1-qyousef@layalina.io/"
authors: [Qais Yousef]
maintainers_involved: [Peter Zijlstra]
current_version: v4
patch_series:
  - version: v1
    msgid: "<20261024233945.74794-1-qyousef@layalina.io>"
    date: 2026-10-24
    summary: "单补丁：不堵 static key 竞态，改为 idle 入口纠错（进入 idle 时检测并重置失衡的 uclamp_rq）"
    review_outcome: "首次发布，当日 kernel test robot 报 arm/arc allnoconfig 下 init_uclamp_rq 重复符号链接错误"
  - version: v2
    msgid: "<20261025162612.360033-1-qyousef@layalina.io>"
    date: 2026-10-25
    summary: "修 init_uclamp_rq 链接错误（补 static inline dummy），idle 检测加 WARN_ON"
    review_outcome: "Peter Zijlstra 建议 uclamp_flags 折进 hole、用 UCLAMP_FLAG_IDLE 判断是否扫 bucket"
  - version: v3
    msgid: null
    date: 2026-10-28
    summary: "吸收 John Stultz 对 v2 的 review：更新 commit 文案（static key 竞态同样可发生在同一 CPU 的 callsite 之间），对 force_idle 路径加 rq->nr_running guard"
    review_outcome: "当日缓存未取到 v3 补丁正文，仅有作者回帖摘要"
  - version: v4
    msgid: "<20261029131354.11030-2-qyousef@layalina.io>"
    date: 2026-10-29
    summary: "拆为 2 补丁：1/2 竞态修复本体，2/2 用 wrapper 替换 open-coding 的 UCLAMP_FLAG_IDLE"
    review_outcome: "Christian Loehle 质疑仅检查 nr_running 不足（CFS 带宽节流递减 nr_running 但不调 uclamp_rq_dec），尚未回应"
upstream_commit: null
fixes_commit: "46609ce227039"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "idle-entry 纠错触发条件（nr_running）是否覆盖 CFS 带宽节流递减 nr_running 但保留合法 clamp 的场景"
  next_action: "作者细化 idle-entry 纠错的触发信号以覆盖 CFS throttling 边界，修订后发 v5"
contribution_opportunities:
  - kind: review
    description: "核对 dequeue_task_fair() 节流路径外还有哪些路径会递减 nr_running 但不调 uclamp_rq_dec，帮作者判定触发信号"
  - kind: testing
    description: "在 CONFIG_UCLAMP_TASK + CFS 带宽节流环境下复现 idle 入口误判，回帖确认 v4 是否需补丁"
generated_at: "2026-10-30T09:30:00"
source_email_count: 7
related_articles: [sched-20261025-001, sched-20261026-002]
tags: [uclamp]
---