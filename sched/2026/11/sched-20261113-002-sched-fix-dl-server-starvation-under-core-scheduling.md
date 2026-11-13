# sched: Fix DL server starvation under core scheduling

## TL;DR
Fernand Sieber（Amazon）发五补丁系列修复 core scheduling 下 DL server 饥饿：默认 fair server（50ms/1s）预留 5% CPU，但一个 CFS 任务在 SMT sibling 上与带 cookie 的 SCHED_FIFO 任务同核运行时，实测只拿到 0.000% 而非 5%；ext server 同样饿死。两个独立机制共同导致（core-wide pick 对 `rq->dl_server` 的交接处理错误 + deferred server 被误计 forced-idle 时间），单独修任一处份额仍在 ~0%。带自测与 5s 窗口实测数据（tip 10/10 失败 0.000%，全系列 31/31 通过 3.99-5.19%）。

## 背景与问题
在 core scheduling 下，DL server 为其预留 CPU 时间的类几乎拿不到时间。默认 fair server（50ms/1s）应预留 5%；实测一个 CFS 任务在 SMT sibling 上、旁边跑一个带 cookie 的 SCHED_FIFO 任务时，只测到 0.000% 而非 5%。ext server 以同样方式饿死 sched_ext 任务。

两个独立机制同时出错：
1. core-wide 选择对 `rq->dl_server` 的交接处理错误——把 stale link 传给 idle（随后强制 sibling idle 并触发 forced-idle WARN）、fast path 丢失 sibling 的 link、且在 `p->dl_server` 置位之前就对 pick 排序（patch 1-3，`Fixes: bd9bbc96e835`）。
2. 独立的：deferred server 被计上其 rq 的 forced-idle 时间，导致其 runtime 在被 throttle 期间就耗尽，`replenish_dl_new_period()` 把激活推后整整一个 period，下一段 forced idle 又把它再推后（patch 4，`Fixes: a110a81c52a9`）。

任一处单独修复，份额仍停留在 ~0%。

## 技术方案
- patch 1 `sched/core: Clear stale rq->dl_server when core-sched replaces a pick`
- patch 2 `sched/core: Keep a sibling's DL server link in the core-wide pick`
- patch 3 `sched/core: Rank DL server picks as deadline in the core-wide pick`
- patch 4 `sched/deadline: Don't charge core-sched forced idle to the DL servers`
- patch 5 新增 `selftests/sched/cs_dl_server_test.c`：一个带 cookie 的 FIFO spinner 占一个 sibling、一个无 cookie 的 CFS spinner 占另一个，检查 CFS 份额是否达到 fair server 预留的一半（默认 2.5%）。QEMU `-smp 4,cores=2,threads=2` 运行。

作者注明本系列借助 AI 编码助手编写，但已全部 review 与测试。

## 版本演进与当前进展
v1 刚发出，尚无 review 意见。

## Maintainer 意见与讨论焦点
当日无维护者回帖。核心争议点潜在在于：patch 3「把 DL server pick 按 deadline 排序到 core-wide pick」会改变 core scheduling 下的选择语义，需 deadline/core-sched 维护者（Juri Lelli、Peter Zijlstra）确认。

## 合入评估
系列带两个明确 `Fixes:` 标签与可复现的自测，且单独修复无效（需整套）的结论有数据支撑，合入概率中等偏高；暂无阻塞项，等待 deadline 维护者评审。

## 效果评估
5s 窗口实测：plain tip 10/10 失败（0.000%）；打全系列后 31/31 通过（3.99-5.19%，对比预留 5%）。数据来自作者 QEMU 环境，非独立第三方复现。

## 我可以参与的点
- **testing**：在真实带 core scheduling 的硬件（如启用 HT 隔离的生产机）上跑 `cs_dl_server_test` 或等价的 FIFO+CFS 同核场景，验证份额是否恢复到预留值。
- **review**：审阅 patch 3 把 DL server pick 按 deadline 排序对 core-wide pick 语义的影响。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261112161548.78189-1-sieberf@amazon.com/

---
id: sched-20261113-002
subject: "sched: Fix DL server starvation under core scheduling"
date: 2026-11-13
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<20261112161548.78189-1-sieberf@amazon.com>"
lore_url: "https://lore.kernel.org/all/20261112161548.78189-1-sieberf@amazon.com/"
authors: [Fernand Sieber]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261112161548.78189-1-sieberf@amazon.com>"
    date: 2026-11-13
    summary: "五补丁修复 core scheduling 下 DL server 饥饿 + cs_dl_server_test 自测"
    review_outcome: "刚发出，暂无 review 意见"
upstream_commit: null
fixes_commit: "bd9bbc96e835"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: "等待 deadline / core-sched 维护者评审 patch 3 的选择语义"
contribution_opportunities:
  - kind: testing
    description: "在真实 core scheduling 硬件上验证 DL server 份额恢复"
  - kind: review
    description: "审阅 patch 3 按 deadline 排序对 core-wide pick 语义的影响"
generated_at: "2026-11-14T01:30:00"
source_email_count: 6
related_articles: []
tags: [deadline, dl_server, core_sched]
---
