# cpufreq: schedutil: Serialize start against rate limit updates

> **subject**：cpufreq: schedutil: Serialize start against rate limit updates

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20260929-001 / 20261006-008：Hui Su 修 schedutil 并发竞态——`rate_limit_us_store()`（写 sysfs）持 `update_lock`，而 `sugov_start()` 读写同一 tunable 不加锁，交错会让 `freq_update_delay_ns` 缓存陈旧并持续生效；Zhongqiu Han 给 Reviewed-by 并确认 `Fixes:` 准确、指出补丁无法干净 backport。
- sched-20261007-006：Hui Su 发 v2——在 `include/linux/cpufreq.h` 加 `gov_attr_set_lock()/unlock()` 通用 helper 并让 `sugov_start()` 使用。
- sched-20261013-014（今天）：Rafael 否决通用 helper 方案（「I'd rather not do this」），要求改为 schedutil 本地的 scoped 包装（`guard(mutex)` 包住 `sugov_update_rate_limit_us()`）；Hui Su 当天发 v3 采纳（新增 `sugov_update_rate_limit_us_sync()`）。另有 Nirjhar Roy 追问该包装能否复用到 `governor_store()`。

## 背景与问题
（承接 20261006-008）`sugov_start()`（schedutil 在 policy 上启动时）调 `sugov_update_rate_limit_us()` 从 tunable 读 `rate_limit_us` 刷新 `freq_update_delay_ns`；`rate_limit_us_store()` 持 governor 属性集的 `update_lock` 更新同一 tunable。前者不加锁可交错：sysfs 显示新值、内存缓存仍是旧值，陈旧 delay 一直滞留到下次限速更新或 governor 重启。`Fixes: 9bdcb44e391d`。

## 技术方案
v3（`kernel/sched/cpufreq_schedutil.c` +11/−1）：
- 新增 schedutil 本地包装 `sugov_update_rate_limit_us_sync()`：`guard(mutex)(&sg_policy->tunables->attr_set.update_lock); sugov_update_rate_limit_us(sg_policy);` 并加注释说明「未同步的 start 会用基于旧 tunable 值的 delay 覆盖新值」。
- `sugov_start()` 改用该包装——贯彻 Rafael「不要通用 gov_attr_set helper、改做 schedutil 本地 scoped wrapper，并解释为何要锁」的意见。
- `rate_limit_us_store()` 继续持 `update_lock` 调用裸 helper。

## 版本演进与当前进展
v3 今日首发（`<20261013034235.2678177-1-sh_def@163.com>`）。相对 v2：撤掉 `include/linux/cpufreq.h` 里的通用 `gov_attr_set_lock()/unlock()`，改为 schedutil 本地 scoped wrapper 并澄清注释。今日 Nirjhar Roy 进一步问：该包装能否也用于 `governor_store()`（后者目前直接 `mutex_{lock,unlock}`）——尚未见答复。

## Maintainer 意见与讨论焦点
- **Rafael J. Wysocki**（cpufreq/schedutil 维护者）：否决 v2 通用 helper 路线，要求 schedutil 本地 scoped wrapper + 说明锁为何必要（v3 已满足）。
- **Zhongqiu Han**：Reviewed-by 随系列保留。
- **Nirjhar Roy**：提出包装复用（governor_store）的后续问题，待答。

## 合入评估
*likelihood=medium*。Rafael 的意见已被 v3 落实、有 Reviewed-by、维护者直接介入评审，但 v3 尚未被正式 Ack，且 Nirjhar 的复用疑问待答。*blocking_issues*：v3 待 Rafael 复审收取；`governor_store()` 复用问题未答。*next_action*：Rafael 复审 v3 后收取。

## 效果评估
无性能数字（锁在 governor 启动/配置冷路径，作者明确不碰调度热路径）；修复消除 sysfs 值与时延缓存的不一致。

## 我可以参与的点
- review/discussion：回应 Nirjhar 的「包装能否用于 governor_store()」问题——评估把 schedutil 本地包装推广到其它 governor 属性集加锁点的收益与风险。

## 参考链接
- v3 lore：https://lore.kernel.org/all/20261013034235.2678177-1-sh_def@163.com/
- v2 lore：https://lore.kernel.org/all/20261007155820.3194105-1-sh_def@163.com/

---
id: sched-20261013-014
subject: 'cpufreq: schedutil: Serialize start against rate limit updates'
date: 2026-10-13
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260929103635.3780346-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20261013034235.2678177-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved:
  - 'Rafael J. Wysocki'
current_version: v3
patch_series:
  - version: v2
    msgid: '<20261007155820.3194105-1-sh_def@163.com>'
    date: 2026-10-07
    summary: '加 gov_attr_set_lock/unlock 通用 helper 并让 sugov_start 使用'
    review_outcome: 'Rafael 否决通用 helper，要求 schedutil 本地 scoped wrapper'
  - version: v3
    msgid: '<20261013034235.2678177-1-sh_def@163.com>'
    date: 2026-10-13
    summary: 'schedutil 本地 sugov_update_rate_limit_us_sync() 包装，澄清注释'
    review_outcome: 'Rafael 意见已落实，待复审；Nirjhar 问 governor_store 复用'
upstream_commit: null
fixes_commit: '9bdcb44e391d'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'v3 待 Rafael 复审收取；governor_store 复用问题未答'
  next_action: 'Rafael 复审 v3 后收取'
contribution_opportunities:
  - kind: discussion
    description: '回应包装能否用于 governor_store() 的推广问题'
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 4
related_articles:
  - sched-20261006-008
  - sched-20261007-006
tags: [cpufreq]
---