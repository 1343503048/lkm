# cpufreq: schedutil: Serialize start against rate limit updates

> **subject**：`cpufreq: schedutil: Serialize start against rate limit updates`

## TL;DR

Hui Su 发的一枚 schedutil 并发竞态修复：`rate_limit_us_store()`（sysfs 写 `rate_limit_us`）持 governor 属性集的 `update_lock`，而 `sugov_start()` 读写同一 tunable 时**不加锁**，两条路径交错会让 sysfs 里显示新值、内存里 `freq_update_delay_ns` 还是旧值，且这个陈旧延迟会一直滞留到下一次限速更新或 governor 重启。补丁在 `sugov_start()` 里给 `sugov_update_rate_limit_us()` 加同一把锁，改动只有 4 行、远离调度热路径。

## 背景与问题

`sugov_start()`（schedutil 在 policy 上启动时）会调用 `sugov_update_rate_limit_us()` 从 tunable 读 `rate_limit_us` 并刷新 `freq_update_delay_ns`；`rate_limit_us_store()` 则是在用户写 sysfs `rate_limit_us` 时更新同一 tunable。后者持有 governor 属性集的 `update_lock`，前者不加锁，于是可出现如下交错：

```
sugov_start()               rate_limit_us_store()
----                        ----
读旧 rate_limit_us
                            写新 rate_limit_us
                            发布新 delay
发布旧 delay
```

结果 sysfs 里的 tunable 已是新值、`freq_update_delay_ns` 仍是旧值。这不同于一次性的撕裂读——陈旧 delay 会持续生效，直到另一次限速更新或 governor 重启才被纠正。

## 技术方案

改动只在 `kernel/sched/cpufreq_schedutil.c` 的 `sugov_start()`（+4 行）：在 `sugov_update_rate_limit_us(sg_policy)` 前后用 `sg_policy->tunables->attr_set.update_lock` 加解锁，与 `rate_limit_us_store()` 串行化。作者特意指出「这把锁本来就在冷路径（governor 启动/配置）上，不碰调度热路径」。

`Fixes: 9bdcb44e391d ("cpufreq: schedutil: New governor based on scheduler utilization data")`。

## 版本演进与当前进展

v1 刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点

当日无回帖，无维护者表态。

## 合入评估

*likelihood=unknown*。单枚 4 行的竞态修复、带 `Fixes:` 标签、改动面极小且明确避开热路径，但刚发出、尚无任何 review，无法判断 maintainer 是否会因为「这个 tunable 竞态在实际场景里是否真的值得加锁」而要求补充触发证据。*blocking_issues*：无 review。*next_action*：等 Rafael/Viresh 等 cpufreq/schedutil 维护者的 review。

## 效果评估

无量化数据；预期效果是消除 `rate_limit_us` sysfs 值与内部 `freq_update_delay_ns` 的长期不一致。

## 我可以参与的点

- `review`：评估这个竞态是否真的能在现实中触发（`sugov_start` 与 sysfs 写的并发窗口），以及加锁是否引入与 `rate_limit_us_store` 的锁序/死锁风险。
- `testing`：在有 schedutil 的机器上快速切换 governor / 写 `rate_limit_us`，验证无回归。

## 参考链接

- lore（补丁）: https://lore.kernel.org/all/20260929103635.3780346-1-sh_def@163.com/

---
id: sched-20260929-001
date: '2026-09-29'
subject: 'cpufreq: schedutil: Serialize start against rate limit updates'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260929103635.3780346-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20260929103635.3780346-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260929103635.3780346-1-sh_def@163.com>'
    date: '2026-09-29'
    summary: 'sugov_start() 用 attr_set.update_lock 包裹 sugov_update_rate_limit_us()，与 rate_limit_us_store() 串行化'
    review_outcome: '无回帖'
upstream_commit: null
fixes_commit: '9bdcb44e391d'
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: '等 cpufreq/schedutil 维护者 review'
contribution_opportunities:
  - kind: review
    description: '评估竞态现实可触发性与加锁锁序/死锁风险'
  - kind: testing
    description: '在 schedutil 机器上快速切换 governor/写 rate_limit_us 验证无回归'
generated_at: '2026-09-30T01:15:00'
source_email_count: 1
related_articles: []
tags:
  - cpufreq
---