# cpufreq: schedutil: Serialize start against rate limit updates

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20260929-001 / 20261006-008：Hui Su 修 schedutil 并发竞态——`rate_limit_us_store()` 持 `update_lock`，`sugov_start()` 读写同一 tunable 不加锁，交错会让 `freq_update_delay_ns` 缓存陈旧并持续生效；Zhongqiu Han 给 Reviewed-by。
- sched-20261007-006：Hui Su 发 v2——加 `gov_attr_set_lock()/unlock()` 通用 helper 并让 `sugov_start()` 使用。
- sched-20261013-014：Rafael 否决通用 helper 方向，要求 schedutil 本地 scoped wrapper；v3 落地 `sugov_update_rate_limit_us_sync()`。
- sched-20261015-024（今天）：Rafael Wysocki 表示「Applied as 7.4 material, thanks!」——v3 已收取，作为 7.4 材料合入。

## 背景与问题
（承接 20261006-008）`sugov_start()` 调 `sugov_update_rate_limit_us()` 从 tunable 读 `rate_limit_us` 刷新 `freq_update_delay_ns`；`rate_limit_us_store()` 持 governor 属性集的 `update_lock` 更新同一 tunable。前者不加锁可交错：sysfs 显示新值、内存缓存仍是旧值，陈旧 delay 一直滞留到下次限速更新或 governor 重启。`Fixes: 9bdcb44e391d`。

## 技术方案
（承接 v3）v3（`kernel/sched/cpufreq_schedutil.c` +11/−1）：新增 schedutil 本地包装 `sugov_update_rate_limit_us_sync()`，用 `guard(mutex)(&sg_policy->tunables->attr_set.update_lock)` 包裹 `sugov_update_rate_limit_us(sg_policy)` 并加注释；`sugov_start()` 改用该包装，`rate_limit_us_store()` 继续持锁调裸 helper。今日确认合入。

## 版本演进与当前进展
- v1 → v2（通用 helper）→ v3（本地 scoped wrapper，回应 Rafael 意见）→ 今日 Rafael 应用为 7.4 material。

## Maintainer 意见与讨论焦点
Rafael J. Wysocki（cpufreq/schedutil 维护者）最终「Applied as 7.4 material, thanks!」，此前「不要通用 gov_attr_set helper、改本地 scoped wrapper」的意见已被 v3 落实，无遗留分歧。

## 合入评估
*likelihood=merged*。v3 已被 Rafael 收取为 7.4 材料。*blocking_issues*：无。*next_action*：随 7.4 开发周期进入主线（或 cpufreq 分支）。

## 效果评估
无量化数据，属并发正确性修复（消除陈旧 delay 滞留）。

## 我可以参与的点
当前阶段暂无明显参与空间，已被维护者收取。

## 参考链接
- Rafael 的应用确认：https://lore.kernel.org/all/CAJZ5v0g1vmjdVBs6A0AEzcfNJb-uX7uvxQgRb6ieGzA6e3HKKA@mail.gmail.com/
- v3 patch：https://lore.kernel.org/all/20261013034235.2678177-1-sh_def@163.com/

---
id: sched-20261015-024
date: 2026-10-15
subject: "cpufreq: schedutil: Serialize start against rate limit updates"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<20261013034235.2678177-1-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/20261013034235.2678177-1-sh_def@163.com/"
authors: ["Hui Su"]
maintainers_involved: ["Rafael J. Wysocki"]
current_version: v3
patch_series:
  - version: v1
    msgid: null
    date: 2026-09-29
    summary: "修 sugov_start 与 rate_limit_us_store 的 tunable 竞态"
    review_outcome: "Zhongqiu Han Reviewed-by"
  - version: v2
    msgid: null
    date: 2026-10-07
    summary: "加 gov_attr_set_lock/unlock 通用 helper"
    review_outcome: "Rafael 否决通用 helper 方向"
  - version: v3
    msgid: "<20261013034235.2678177-1-sh_def@163.com>"
    date: 2026-10-13
    summary: "schedutil 本地 sugov_update_rate_limit_us_sync() scoped wrapper"
    review_outcome: "Rafael 应用为 7.4 material"
upstream_commit: null
fixes_commit: "9bdcb44e391d"
merged_branch: null
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "随 7.4 开发周期进主线"
contribution_opportunities: []
generated_at: "2026-10-16T01:05:00"
source_email_count: 1
related_articles: ["sched-20260929-001", "sched-20261006-008", "sched-20261007-006", "sched-20261013-014"]
tags: [cpufreq]
---