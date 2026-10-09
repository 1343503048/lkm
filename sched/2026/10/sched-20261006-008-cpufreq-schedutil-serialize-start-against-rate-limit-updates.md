# cpufreq: schedutil: Serialize start against rate limit updates

> **subject**：`cpufreq: schedutil: Serialize start against rate limit updates`
> 本文为增量更新，完整脉络见下。

## TL;DR

- sched-20260929-001：Hui Su 发的一枚 schedutil 并发竞态修复：`rate_limit_us_store()`（sysfs 写 `rate_limit_us`）持 governor 属性集的 `update_lock`，而 `sugov_start()` 读写同一 tunable 时**不加锁**，两条路径交错会让 sysfs 里显示新值、内存里 `freq_update_delay_ns` 还是旧值，且这个陈旧延迟会一直滞留到下一次限速更新或 governor 重启。补丁在 `sugov_start()` 里给 `sugov_update_rate_limit_us()` 加同一把锁，改动只有 4 行、远离调度热路径。
- sched-20261006-008（今天）：Qualcomm 的 Zhongqiu Han 给出 **Reviewed-by**，并确认 `Fixes:` 标签准确；同时指出**该补丁无法干净地 backport**——目标代码在主线已被重构。两个附注：nit 建议把取锁包成 `gov_attr_set_lock()` 之类的 helper；并说明自己评审时一度考虑删掉 `freq_update_delay_ns` 缓存改无锁设计，但因热路径每次做乘法会伤性能而放弃。

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

今日增量：Zhongqiu Han 确认该问题的 `Fixes: 9bdcb44e391d` 定位准确，即竞态自 schedutil 引入起就存在；但他同时指出主线代码此后已被重构，补丁无法原样 backport 到带该 bug 的旧分支。

## 技术方案

改动只在 `kernel/sched/cpufreq_schedutil.c` 的 `sugov_start()`（+4 行）：在 `sugov_update_rate_limit_us(sg_policy)` 前后用 `sg_policy->tunables->attr_set.update_lock` 加解锁，与 `rate_limit_us_store()` 串行化。作者特意指出「这把锁本来就在冷路径（governor 启动/配置）上，不碰调度热路径」。

`Fixes: 9bdcb44e391d ("cpufreq: schedutil: New governor based on scheduler utilization data")`。

今日增量的两点讨论：

1. **helper 化建议（nit）**：Zhongqiu Han 建议把这处直接操作 `attr_set.update_lock` 的取锁包成 helper（如 `gov_attr_set_lock()`），与其他 governor 共用统一的加锁入口，避免裸拿内部锁。
2. **被否决的备选方案**：评审者考虑过删除 `freq_update_delay_ns` 缓存、每次使用时从 `rate_limit_us` 现算（彻底无锁），但由于该值位于 schedutil 的**热路径**上，每次做乘法换算会伤性能，故仍保留缓存+加锁的方案。

## 版本演进与当前进展

- v1（09-29，Hui Su）：`sugov_start()` 用 `attr_set.update_lock` 包裹 `sugov_update_rate_limit_us()`，与 `rate_limit_us_store()` 串行化。发出后一周内无回帖。
- 10-06：Zhongqiu Han 回帖给出 Reviewed-by 并附三点意见（见下节）。**尚无 v2**——helper 化的 nit 是否被作者采纳还不知道。
- 未进入任何分支，无 maintainer tag。

## Maintainer 意见与讨论焦点

Zhongqiu Han（Qualcomm，非 schedutil maintainer，但属于该子系统活跃评审者）10-06 回帖，要点：

1. **Reviewed-by** 已给出，且确认 `Fixes:` 标签准确。
2. **backport 警告**：补丁无法干净地 backport，因为代码此后被重构过——这直接影响 stable 回合价值：`Fixes:` 虽准确，回合到旧 stable 分支需要手工适配而非直接 cherry-pick。
3. **nit**：取锁包成 `gov_attr_set_lock()` helper 更好。
4. **设计讨论**：评审中考虑过删 `freq_update_delay_ns` 缓存的无锁方案，因热路径乘法开销而放弃——这等于从侧面认可了「保留缓存 + 冷路径加锁」的取舍。

无分歧、无 NAK。Viresh Kumar / Rafael Wysocki（cpufreq/schedutil maintainer）仍未表态。

## 合入评估

*likelihood=medium*（从 unknown 上调）。

- 上调依据：拿到第一枚 Reviewed-by；改动小（4 行）、带准确的 `Fixes:`、评审者确认标签准确且认可整体取舍；无任何反对意见。
- 维持 medium 而非 high 的原因：给 R-b 的不是 subsystem maintainer，Viresh/Rafael 尚未表态；helper 化 nit 可能催生一个 v2，落地节奏未定。
- *blocking_issues*：schedutil maintainer 无回应。
- *next_action*：等 Viresh/Rafael 的 review；作者若发 v2 顺手采纳 helper 化 nit，可一并带上 Zhongqiu 的 R-b。
- 回合视角（对 OLK-6.6）：Zhongqiu 明确「无法干净 backport」——6.6 的 `cpufreq_schedutil.c` 结构与当前主线差异更大，回合需手工适配，`sugov_start()`/`rate_limit_us_store()` 两函数在 6.6 里都存在，加锁思路可直接移植。

## 效果评估

无量化数据；预期效果是消除 `rate_limit_us` sysfs 值与内部 `freq_update_delay_ns` 的长期不一致。评审者对热路径开销的顾虑已通过「锁在冷路径」的设计消除。

## 我可以参与的点

- `review`/`extend`：替作者实现 `gov_attr_set_lock()` helper 化的 v2（small、低风险、容易拿到感谢 tag）；或在 v2 里验证 helper 对其他 governor（ondemand/conservative）是否同样适用。
- `testing`：在 schedutil 机器上并发执行 governor 切换与 `rate_limit_us` sysfs 写，构造原竞态并确认补丁后行为。
- 回合视角：为 OLK-6.6 手工适配这枚补丁时，注意 6.6 中 tunables 结构同名但 `freq_update_delay_ns` 刷新点可能不同，需对照 6.6 的 `sugov_update_rate_limit_us()`。

## 参考链接

- lore（v1 补丁）: https://lore.kernel.org/all/20260929103635.3780346-1-sh_def@163.com/
- lore（Zhongqiu Han 的 R-b）: https://lore.kernel.org/all/c2d93d95-e623-4910-8d92-b3e16738703c@oss.qualcomm.com/
- 相关文章：[[sched-20260929-001]]（v1 首发，当日无回帖）

---
id: sched-20261006-008
date: '2026-10-06'
subject: 'cpufreq: schedutil: Serialize start against rate limit updates'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260929103635.3780346-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20260929103635.3780346-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved:
  - 'Zhongqiu Han'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260929103635.3780346-1-sh_def@163.com>'
    date: '2026-09-29'
    summary: 'sugov_start() 用 attr_set.update_lock 包裹 sugov_update_rate_limit_us()，与 rate_limit_us_store() 串行化'
    review_outcome: '10-06 获得 Zhongqiu Han 的 Reviewed-by，附 helper 化 nit 与 backport 警告；尚无 v2'
upstream_commit: null
fixes_commit: '9bdcb44e391d'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'schedutil maintainer（Viresh/Rafael）尚未表态'
  next_action: '等 maintainer review；作者可发 v2 采纳 gov_attr_set_lock() helper 化 nit'
generated_at: '2026-10-07T01:00:00'
contribution_opportunities:
  - kind: extend
    detail: '替作者实现 gov_attr_set_lock() helper 化 v2 并回报'
  - kind: testing
    detail: '并发 governor 切换 + rate_limit_us sysfs 写构造竞态验证'
source_email_count: 1
related_articles:
  - sched-20260929-001
tags:
  - cpufreq
---
