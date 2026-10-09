---
id: sched-20261007-006
date: '2026-10-07'
subject: 'cpufreq: schedutil: Serialize start against rate limit updates'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260929103635.3780346-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261007155820.3194105-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved:
- Zhongqiu Han
current_version: v2
patch_series:
- version: v1
  msgid: <20260929103635.3780346-1-sh_def@163.com>
  date: '2026-09-29'
  summary: sugov_start() 直接持 attr_set.update_lock 串行化
  review_outcome: 10-06 Zhongqiu Han R-b + helper 化 nit + backport 警告
- version: v2
  msgid: <20261007155820.3194105-1-sh_def@163.com>
  date: '2026-10-07'
  summary: 新增 gov_attr_set_lock()/unlock() helper，sugov_start() 改用；R-b 携带
  review_outcome: 待 maintainer 收取
upstream_commit: null
fixes_commit: 9bdcb44e391d
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Viresh/Rafael 仍未表态
  next_action: 等 cpufreq/schedutil 维护者收取
generated_at: '2026-10-08T01:00:00'
contribution_opportunities:
- kind: testing
  detail: 并发 governor 切换 + sysfs 写验证 v2 与 v1 行为等价
source_email_count: 2
related_articles:
- sched-20260929-001
- sched-20261006-008
tags:
- cpufreq
title: 'cpufreq: schedutil: Serialize start against rate limit updates'
layout: article
---

> **subject**：`cpufreq: schedutil: Serialize start against rate limit updates`
> 本文为增量更新，完整脉络见下。

## TL;DR

- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-001-cpufreq-schedutil-serialize-start-against-rate-limit-updates.html">sched-20260929-001</a>：Hui Su 发的一枚 schedutil 并发竞态修复：`rate_limit_us_store()`（sysfs 写 `rate_limit_us`）持 governor 属性集的 `update_lock`，而 `sugov_start()` 读写同一 tunable 时**不加锁**，两条路径交错会让 sysfs 里显示新值、内存里 `freq_update_delay_ns` 还是旧值，且这个陈旧延迟会一直滞留到下一次限速更新或 governor 重启。补丁在 `sugov_start()` 里给 `sugov_update_rate_limit_us()` 加同一把锁，改动只有 4 行、远离调度热路径。当日无回帖。
- <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-008-cpufreq-schedutil-serialize-start-against-rate-limit-updates.html">sched-20261006-008</a>：Qualcomm 的 Zhongqiu Han 给出 **Reviewed-by**，确认 `Fixes:` 标签准确，同时指出**该补丁无法干净地 backport**（目标代码已被重构）；nit 建议把取锁包成 `gov_attr_set_lock()` helper；并说明自己考虑过删 `freq_update_delay_ns` 缓存的无锁设计、因热路径乘法开销而放弃。
- <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-006-cpufreq-schedutil-serialize-start-against-rate-limit-updates.html">sched-20261007-006</a>（今天）：Hui Su 回复「Agreed, I'll wrap the governor attribute set locking in helpers and send v2 shortly」，当晚即发 **v2**——`include/linux/cpufreq.h` 新增 `gov_attr_set_lock()`/`gov_attr_set_unlock()` 两个 static inline helper（+10），`sugov_start()` 改用 helper（+4），锁细节收进属性集接口内；**Zhongqiu Han 的 Reviewed-by 直接带入 v2**。

## 背景与问题

`sugov_start()`（schedutil 在 policy 上启动时）会调用 `sugov_update_rate_limit_us()` 从 tunable 读 `rate_limit_us` 并刷新 `freq_update_delay_ns`；`rate_limit_us_store()` 则在用户写 sysfs `rate_limit_us` 时更新同一 tunable。后者持 governor 属性集的 `update_lock`，前者不加锁，交错时 sysfs 显示新值、`freq_update_delay_ns` 留旧值，且陈旧 delay 持续生效到下一次限速更新或 governor 重启。Zhongqiu Han 已确认 `Fixes: 9bdcb44e391d` 定位准确（竞态自 schedutil 引入起存在），但主线代码此后被重构、无法原样 backport。今天无新背景，进入 v2 收尾。

## 技术方案

v2（`<20261007155820.3194105-1-sh_def@163.com>`，2 文件 +14/−0）：

- `include/linux/cpufreq.h`：在 `to_gov_attr_set()` 旁新增两个 static inline——`gov_attr_set_lock(struct gov_attr_set *attr_set)`（`mutex_lock(&attr_set->update_lock)`）与 `gov_attr_set_unlock()`（对应 unlock）。锁的获取/释放细节收进属性集接口，调用方不再裸碰内部锁。
- `kernel/sched/cpufreq_schedutil.c` 的 `sugov_start()`：`sugov_update_rate_limit_us(sg_policy)` 前后改用 `gov_attr_set_lock()/gov_attr_set_unlock()`（原 v1 是直接 `mutex_lock(&sg_policy->tunables->attr_set.update_lock)`）。
- 核心语义与 v1 完全一致：与 `rate_limit_us_store()` 串行化，锁只在冷路径（governor 启动）。
- `Fixes: 9bdcb44e391d`；`Reviewed-by: Zhongqiu Han`（10-06 给出、v2 携带）。

## 版本演进与当前进展

- v1（09-29）：4 行直接加锁（<a class="article-ref" href="/lkm/2026/09/29/sched-20260929-001-cpufreq-schedutil-serialize-start-against-rate-limit-updates.html">sched-20260929-001</a>）。
- 10-06：Zhongqiu Han R-b + helper 化 nit + backport 警告（<a class="article-ref" href="/lkm/2026/10/06/sched-20261006-008-cpufreq-schedutil-serialize-start-against-rate-limit-updates.html">sched-20261006-008</a>）。
- 10-07：作者同意并当日发 v2 落实 helper 化，R-b 携带。**尚无 maintainer（Viresh Kumar/Rafael Wysocki）表态**，未进任何分支。

## Maintainer 意见与讨论焦点

Zhongqiu Han（Qualcomm）的 nit 已被 v2 完全吸收——讨论焦点清零。v2 之后无新回复。cpufreq/schedutil 维护者（Viresh/Rafael）全程未表态是唯一的推进缺口。

## 合入评估

*likelihood=medium*。加分项：唯一 reviewer 意见已落实、R-b 携带、补丁极小（+14）、`Fixes:` 准确、无争议。扣分项：给 R-b 的不是 subsystem maintainer，Viresh/Rafael 零表态；helper 化后触碰 `include/linux/cpufreq.h` 公共头，理论上多一层「是否该放这里」的 review 面。*blocking_issues*：schedutil maintainer 无回应。*next_action*：等 Viresh/Rafael 收取；无进一步作者动作空间。

## 效果评估

无量化数据；预期效果与 v1 相同——消除 `rate_limit_us` sysfs 值与 `freq_update_delay_ns` 的长期不一致。v2 的额外收益是接口卫生（锁细节内聚到 gov_attr_set），无行为差异。

## 我可以参与的点

- `testing`：并发 governor 切换 + `rate_limit_us` sysfs 写，验证 v2 与 v1 行为等价。
- 回合视角：Zhongqiu 已警告「无法干净 backport」；OLK-6.6 回合需手工适配（6.6 的 `sugov_start()`/tunables 结构同名但刷新点可能不同），helper 若 6.6 的 `cpufreq.h` 没有 `gov_attr_set` 内联位可退回 v1 形态的直接加锁。

## 参考链接

- v2 补丁: https://lore.kernel.org/all/20261007155820.3194105-1-sh_def@163.com/
- Hui Su 的回复: https://lore.kernel.org/all/179138341312.2968831.4961276880957777576.schedutil-helper-reply@163.com/
- 相关文章：<a class="article-ref" href="/lkm/2026/09/29/sched-20260929-001-cpufreq-schedutil-serialize-start-against-rate-limit-updates.html">sched-20260929-001</a>（v1）、<a class="article-ref" href="/lkm/2026/10/06/sched-20261006-008-cpufreq-schedutil-serialize-start-against-rate-limit-updates.html">sched-20261006-008</a>（R-b 与 nit）
