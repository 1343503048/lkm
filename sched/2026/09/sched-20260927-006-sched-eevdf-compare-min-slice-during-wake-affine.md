# sched/eevdf: Compare min slice during wake_affine

## TL;DR

本文为增量更新，完整脉络见 related_articles（Vincent Guittot 的 8 补丁「Improving latency of short slice tasks」系列中的 patch 7/8）。

- sched-20260921-001：系列 v1 发出，patch 7/8 在 wake_affine 阶段新增 `wake_affine_slice()`，检查唤醒 CPU 是否会因自身 slice 更长而被抢占。
- sched-20260922-011：Peter Zijlstra 对系列密集 review，核心分歧在 patch 4/8 衰减算法。
- sched-20260927-006（今天）：Kayra Cizmeci 对 7/8 提 review 疑问——现行逻辑在 `se->slice` 小于某 CPU 的 min_slice 时优先选该 CPU，Kayra 认为「落到 min_slice 更大的 CPU 更好」，并给出替代 diff，请 Vincent 确认。

## 背景与问题

（承接 sched-20260921-001）EEVDF 下短 slice 任务的 CPU 选择阶段（`select_task_rq_fair` / `wake_affine`）此前不考虑 min slice，短 slice 任务可能被放到会先运行长 slice 任务（被立即抢占）的 CPU 上。patch 7/8 正是为此在 wake_affine 里加入 min slice 判断。

## 技术方案

（承接 sched-20260921-001）patch 7/8 在 wake_affine 中新增 `wake_affine_slice()`：比较 `se->slice` 与 prev/this CPU 的 `get_rq_min_slice()`，若 `se->slice` 小于 prev CPU 的 min_slice 则选 prev_cpu，否则若小于 this CPU 的 min_slice 则选 this_cpu，都不满足则返回 `nr_cpumask_bits`（不表态）。

今天 Kayra 给出替代 diff（`<20260926181840.3107-1-kayracizmeci@gmail.com>`）：

```c
u64 min_prev = get_rq_min_slice(cpu_rq(prev_cpu));
u64 min_this = get_rq_min_slice(cpu_rq(this_cpu));

if (se->slice >= max(min_prev, min_this))
    return nr_cpumask_bits;

return min_prev >= min_this ? prev_cpu : this_cpu;
```

即：`se->slice` 都不小于两 CPU min_slice 时不表态，否则选 min_slice 更大的那个 CPU。

## 版本演进与当前进展

- v1（2026-09-21，patch 7/8 `<20260921152238.3804392-8-vincent.guittot@linaro.org>`）。
- 09-22：Peter 对系列 review（对应 sched-20260922-011）。
- 09-27：Kayra 对 7/8 提出疑问并给替代 diff，本日 Vincent 未回复。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci**（今日）：举反例——this_cpu min_slice=7、prev_cpu min_slice=5、`se->slice`=4，现行逻辑因 `se->slice < prev 的 5` 而选 prev_cpu（min_slice 更小）。Kayra 质疑「落到 min_slice 更大的 CPU 不是更好吗？」，并提出「选 min_slice 更大者」的替代 diff，态度是请 Vincent 指正（「I may be getting something wrong, please correct me」）。
- Vincent Guittot（作者/维护者）本日未回复，此疑问待解。

## 合入评估

*likelihood=unknown*（就本 patch 而言）。patch 7/8 属维护者自研系列、方向与 EEVDF 一脉相承，但今日新增「选 min_slice 更大 vs 避免被更短 slice 抢占」的方向性疑问，尚未有 Vincent 或 Peter 的裁决。*blocking_issues*：Kayra 的语义疑问待回复；该 patch 与 8/8 的重复扫描问题（Peter 前一日意见）一并待调整。*next_action*：Vincent 回复 Kayra，澄清 wake_affine_slice 的选择语义或采纳替代 diff。

## 效果评估

本 patch 无单独效果数据；系列整体 benchmark 见 sched-20260921-001（cyclictest 99.9 分位与最大延迟显著下降、hackbench +8%~+30%）。

## 我可以参与的点

- `review`：辨析 Kayra 的替代 diff（选 min_slice 更大者）与原逻辑（避免被更短 slice 抢占）在何种负载下等价/分歧——短 slice 任务选 min_slice 更大的 CPU 是否等价于「获得更长可运行窗口」。
- `discussion`：就 7/8 的方向性疑问给出分析或小规模实测（如 cyclictest 对照两种逻辑）。

## 参考链接

- patch 7/8: https://lore.kernel.org/all/20260921152238.3804392-8-vincent.guittot@linaro.org/
- Kayra 回复: https://lore.kernel.org/all/20260926181840.3107-1-kayracizmeci@gmail.com/
- 系列 cover: https://lore.kernel.org/all/20260921152238.3804392-1-vincent.guittot@linaro.org/

---
id: sched-20260927-006
date: 2026-09-27
subject: "sched/eevdf: Compare min slice during wake_affine"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260921152238.3804392-8-vincent.guittot@linaro.org>"
lore_url: "https://lore.kernel.org/all/20260926181840.3107-1-kayracizmeci@gmail.com/"
authors:
  - "Vincent Guittot"
maintainers_involved:
  - "Peter Zijlstra"
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260921152238.3804392-8-vincent.guittot@linaro.org>"
    date: 2026-09-21
    summary: "wake_affine 新增 wake_affine_slice()：se->slice 小于 prev/this CPU min_slice 时优先选该 CPU，否则不表态。"
    review_outcome: "Peter 09-22 系列级 review；Kayra 09-27 质疑应选 min_slice 更大的 CPU 并给替代 diff，Vincent 未回复。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "Kayra 对「选 min_slice 更大 vs 避免被更短 slice 抢占」的语义疑问待回复"
    - "与 8/8 的重复扫描问题（Peter 前一日意见）待调整"
  next_action: "Vincent 回复 Kayra，澄清选择语义或采纳替代 diff"
contribution_opportunities:
  - kind: review
    description: "辨析 Kayra 替代 diff 与原逻辑在不同负载下的等价/分歧"
  - kind: discussion
    description: "就 7/8 方向性疑问给出分析或小规模 cyclictest 对照实测"
generated_at: "2026-09-28T09:00:00"
source_email_count: 1
related_articles:
  - sched-20260921-001
  - sched-20260922-011
tags:
  - eevdf
  - load_balance
---