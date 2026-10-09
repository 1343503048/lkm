# tick/sched: /proc/stat idle time exceeds wall time since v7.2

## TL;DR

Stian Halseth 报告一个 v7.2-rc1 起的回归：NO_HZ_IDLE + TICK_CPU_ACCOUNTING 内核上 `/proc/stat` 统计的 idle 时间**超过墙钟时间**——按「1 − idle 率」算 CPU 使用率的监控在空闲机器上直接显示负数。两台机器实测（60s 窗口、/proc/stat + /proc/timer_list 的 idle_sleeps）：SPARC T7-1（7.3-rc5、HZ=100、256 CPU）平均每秒 1.0057 倍、最差 CPU 1.44 倍（92 次 tick 停/秒、每次停多计 4.8ms）；amd64 Opteron（7.2.7、HZ=1000）空闲时 +0.03%/+0.06%，但 CPU1 上每 3.7ms 唤醒一个任务时 +13.1%（285 次 tick 停/秒、每次 0.46ms）——两机都呈「每次 tick 停约多计半个 tick」。报告者给出根因分析（非 bisect）：cf6444c3e1bb（"tick/sched: Unify idle cputime accounting"）让 dyntick-idle 时间与 tick 采样时间共享 `cpustat[CPUTIME_IDLE]`，idle 退出时 `kcpustat_dyntick_stop()` 已把 idle 时间计到当下，而重启的 tick 仍按旧周期整周期记账——首个 tick 把 idle 退出前的那段又记一遍。他已有修复思路（在 `kcpustat_dyntick_stop()` 记录重叠、首个 tick 剔除，修复后两机 idle/墙钟比回到 1.0000），正补 IRQ_TIME_ACCOUNTING 与 KVM steal time 测试后发出。`#regzbot introduced: cf6444c3e1bb`。

## 背景与问题

- v7.2 前：`/proc/stat` 的 idle 读 `ts->idle_sleeptime`，tick 喂的是另一个不使用的计数器，无重复计数。
- cf6444c3e1bb 统一记账后：dyntick-idle 时间与 tick 采样时间共用 `cpustat[CPUTIME_IDLE]`。idle 退出时 `kcpustat_dyntick_stop()` 把 idle 时间计到「现在」；tick 按旧周期重启，首个 tick 经 `account_process_tick()` 又整记一个 `TICK_NSEC`——其中 idle 退出之前的部分刚被记过 → 每次停/启循环多计约半个 tick。
- 影响面：所有 NO_HZ_IDLE + TICK_CPU_ACCOUNTING 配置；高频短睡眠负载（如 3.7ms 周期任务）最严重（+13.1%）；监控侧「使用率 = 1 − idle 率」出现负值。
- 首报内核：v7.2-rc1 起（报告者按代码阅读定位，未 bisect）。

## 技术方案

报告者已有修复（未发）：在 `kcpustat_dyntick_stop()` 里记录重叠量、首个 tick 记账时剔除。自测效果：两机 idle/墙钟比回到 1.0000；唤醒负载下 −0.1%（280 次 tick 停/秒）。正在补 IRQ_TIME_ACCOUNTING 与 KVM steal time 场景验证后发出。

## 版本演进与当前进展

- 10-04 首报（`<20261004142724.3896396-1-stian@itx.no>`），regzbot 登记 `introduced: cf6444c3e1bb`。无回帖；补丁在作者本地测试中。

## Maintainer 意见与讨论焦点

- 无回帖。涉事 commit cf6444c3e1bb 作者（tick/sched 维护圈，Frederic Weisbecker 一线）未表态；根因分析目前只有报告者单方论证（其自述「from reading the code (not bisected)」）。

## 合入评估

*likelihood=unknown*。回归真实、数据充分、有候选修法；但无维护者介入、根因未经第二方确认、补丁未发。*blocking_issues*：补丁未发出（IRQ_TIME/steal time 验证中）；无维护者表态。*next_action*：作者发补丁后等 tick/sched 维护者确认根因与修法。

## 效果评估

量化充分：SPARC T7-1（256 CPU、HZ=100）平均 1.0057x、最差 1.44x；amd64（HZ=1000）空闲 +0.03%/+0.06%、3.7ms 唤醒负载 +13.1%；每 tick 停多计量级（4.8ms @ HZ=100、0.46ms @ HZ=1000）与「半 tick」假设吻合。修复后自测 1.0000。

## 我可以参与的点

- `review`：独立复核根因——对照 v7.1/v7.2 的 `kcpustat_dyntick_stop()` 与 `account_process_tick()` 交互，验证「重叠双计」论证（报告者明说未 bisect，第二方代码论证能显著加速 maintainer 定位）。
- `testing`：在 IRQ_TIME_ACCOUNTING / VIRT_CPU_ACCOUNTING_GEN 配置下复测（作者尚缺这两路的完整数据），回帖补充。

## 参考链接

- lore（回归报告）: https://lore.kernel.org/all/20261004142724.3896396-1-stian@itx.no/

---
id: sched-20261004-002
date: '2026-10-04'
subject: 'tick/sched: /proc/stat idle time exceeds wall time since v7.2'
subsystem: sched
type: regression
status: under_review
severity: medium
thread_root_msgid: '<20261004142724.3896396-1-stian@itx.no>'
lore_url: 'https://lore.kernel.org/all/20261004142724.3896396-1-stian@itx.no/'
authors:
  - 'Stian Halseth'
maintainers_involved: []
current_version: v0
patch_series: []
upstream_commit: null
fixes_commit: 'cf6444c3e1bb'
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '补丁未发出（IRQ_TIME/steal time 验证中）'
    - '根因仅报告者单方论证、无维护者表态'
  next_action: '作者发补丁后等 tick/sched 维护者确认'
contribution_opportunities:
  - kind: review
    description: '对照 v7.1/v7.2 代码独立复核「重叠双计」根因论证'
  - kind: testing
    description: 'IRQ_TIME_ACCOUNTING / VIRT_CPU_ACCOUNTING_GEN 配置下复测补数据'
generated_at: '2026-10-05T01:00:00'
source_email_count: 1
related_articles: []
tags:
  - nohz
  - tick
  - regression
---
