# Improving latency of short slice tasks

## TL;DR
Vincent Guittot（Linaro，sched 维护者兼本文作者）的 18 补丁 v2 系列，目标系统性地降低短 slice 任务（低时延敏感的小任务）的调度时延：一组 EEVDF 的 lag/slice 处理改进（decay lag、idle 唤醒时 reset lag、per-CPU cache min_slice、按 min_slice 选 CPU、wake_affine 时比较 min slice），加一个新引入的「fair push 任务机制」（把不该在本 CPU 跑、或在本 CPU 排不上队的任务推到更合适的 CPU，含 force-push 变体），并让 EAS 的能耗模型在选 CPU 时把任务 slice 纳入考量。今天 Tim Chen、Kayra Cizmeci、Chen Yu 密集 review，抓出 force-push 早退、push static key 泄漏、slice 判断顺序等几处问题，Vincent 逐一确认修，系列处于活跃评审、v3 在望。

## 背景与问题
短 slice 任务（小忙小睡、频繁唤醒的时延敏感任务）在 EEVDF 下仍面临两类时延来源：一是 EEVDF 的 lag/slice 记账让这类任务唤醒后未必能在最快能运行的 CPU 上跑（lag 累积、wake_affine 未比较 slice、选 CPU 未看 min_slice）；二是 CFS 没有类似 RT 的 push 机制——当一个短任务在某个 CPU 上排不到队首时，无法被「推」到更合适的 CPU，只能等本地调度机会。EAS 的 `feec()` 选 CPU 时也不看任务 slice，可能把短任务摆到 slice 上不占优的核。此前作者先把其中几枚（min slice check、compare min slice during wake_affine）作为独立补丁发过，本系列把它们整合进一个完整的 18 补丁 v2。

## 技术方案
18 枚分三块：

1. **EEVDF 时延基础**（patch 01-05）：`decay positive lag of sleeping entities`（休眠实体的正 lag 衰减）、`Reset lag when waking up on idle cpu`（idle 唤醒 reset lag）、`Add per cpu cached min_slice`（per-CPU cache 当前最小 slice）、`Compare min slice during wake_affine`、`Add min slice check when selecting CPU`（选中能最快跑该任务的 CPU）。
2. **fair push 机制**（patch 06-14）：`Prepare select_task_rq_fair() for new cases`（复用选核逻辑给 push）、`Add push task mechanism for fair`（类似 RT push 的公平类 push）、`Optimize push task mechanism`、`Add rq flag to tick parameters`、`Add force push task mechanism`（force-push 变体）、`Support not wakeup case in select_idle_sibling`（非唤醒路径也用 select_idle_sibling）、`Try to push short slice task on a better CPU`、`Push short slice task that are not picked`、`Enable push task for preempt short`（PREEMPT_SHORT 作为首个 push 使用者）。
3. **EAS 整合**（patch 15-18）：`Rework feec() to use cost instead of spare capacity`、`Take into account slice in EAS`（EAS 选核把任务 slice 与目标核 min_slice 比较）。

关键设计取舍：push 机制被设计成「默认不启用、被使用者触发才开」（`sched_push_task` static branch），PREEMPT_SHORT 短任务是其第一个使用者，作者明确后续要扩展到 cache-aware 调度等。

## 版本演进与当前进展
*current_version: v2*（18 枚，`<20261002154415.2270586-1-vincent.guittot@linaro.org>`，10-02 发出）。今天的评审聚焦代码级问题：

- 02/18（reset lag）：改 typo（Vincent「will fix the typo」）。
- 06/18（prepare select_task_rq_fair）：对「push 时要不要更新 recent_used_cpu」存在分歧——Vincent 认为 push 选核应与 wakeup 选核一致，若落到同一 CPU 则 recent_used_cpu=prev 合理，倾向不特殊处理。
- 10/18（force push）：Kayra 质疑 `fair_check_pushable_task()` 因 `nr_running>1` 早退使 push 永不触发；Vincent 表示「This is on purpose」——该函数本就是用来到断是否 push，短任务不 push 已孤身在 rq 上的任务；同时承认 factorize 时漏掉了 tick 与 put 事件的一个关键 diff（「will fix」的错误）。
- 11/18（not wakeup case）：Vincent 承认漏了 `idle_cpu_without()` 里 nr_running 检查，将合并修复（「I missed this part and will fix it」）。
- 14/18（enable push for preempt short）：Kayra 实测发现 push static key 计数在 PREEMPT_SHORT 关闭后仍持续增长（不递减）；Vincent 确认「This should not happen. I will fix it」。
- 18/18（slice in EAS）：Tim Chen 指出 slice 检查在「Favor previous CPU」之前、可导致任务被叠到忙碌的 prev_cpu；建议同时计算 target_first 与 min_first。Kayra 补充 ULONG_MAX 不总代表 rq 空闲。Vincent「yes, I will fix it」。

## Maintainer 意见与讨论焦点
- **Tim Chen（Intel）**：18/18 的 slice 判断顺序有缺陷——当 prev_cpu 忙碌、空闲 CPU X 被扫到时，slice 检查会败给「Favor previous CPU」，把任务叠到忙碌 prev_cpu；提出 `target_first/min_first` 双双计算后比较的改法（附 diff）。
- **Kayra Cizmeci**：做最细致的代码审查与实测。三处实质发现：force-push 的早退语义（被作者解释为有意）；push static key 只增不减的泄漏（实测 `static_key_count` 日志，作者确认是 bug）；18/18 中 ULONG_MAX 不代表 rq 空、slice 比较的边界 case。
- **Chen Yu（Intel）**：push 选核后 recent_used_cpu 的更新语义。
- **Vincent Guittot（作者/维护者）**：多数 ack + 2 个确认的 bug（11/18 nr_running 检查、14/18 static key 泄漏）+ 18/18 slice 顺序。整体方向无争议，收敛到代码修正。

## 合入评估
*likelihood=medium*。方向积极（作者即子模块维护者、评审者均为资深 sched 开发者），但 v2 仍在修代码级 bug（force-push 早退澄清、static key 泄漏、slice 判断顺序），且 push 机制的演进空间（cache-aware 等后续使用者）意味着设计还会动。*blocking_issues*：① 14/18 static key 泄漏、11/18 nr_running 检查、18/18 slice 顺序三处待修并等复审；② force-push 的「孤身任务不 push」语义需在 cover/changelog 写清以免再被误读。*next_action*：Vincent 修完上述问题发 v3。

## 效果评估
今日评审为代码级讨论，未见新 benchmark 数据。系列整体目标（短 slice 任务时延）有明确方向，但本日邮件未附量化收益。此前作者相关的 min-slice 选择补丁已有独立数据（见相关历史文章），本系列整体收益待 v3 或后续实测。

## 我可以参与的点
- `testing`：在有大核/小核或 EAS 平台（如 big.LITTLE）上跑短 slice 敏感负载（cyclictest、短任务 ping-pong），对比 v2 前后时延与 push 触发频率。
- `review`：复核 14/18 push static key 的启用/禁用对称性，以及 18/18 slice 比较在「ULONG_MAX 表示空闲 rq 但 rq 可能非空」边界下的正确性。
- `discussion`：force-push 与 push 的语义边界（何时该 push 孤身任务）是否足够普适。

## 参考链接
- 系列 cover (v2): https://lore.kernel.org/all/20261002154415.2270586-1-vincent.guittot@linaro.org/
- Tim Chen 18/18 回复: https://lore.kernel.org/all/179bcb50be21f834423f9b5c068b5fce4cb65871.camel@linux.intel.com/
- Kayra 14/18 回复: https://lore.kernel.org/all/20261009111627.4861-1-kayracizmeci@gmail.com/

---
id: sched-20261009-004
date: '2026-10-09'
subject: 'Improving latency of short slice tasks'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20261002154415.2270586-1-vincent.guittot@linaro.org>'
lore_url: 'https://lore.kernel.org/all/20261002154415.2270586-1-vincent.guittot@linaro.org/'
authors:
  - 'Vincent Guittot'
maintainers_involved:
  - 'Vincent Guittot'
  - 'Tim Chen'
  - 'Chen Yu'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20261002154415.2270586-1-vincent.guittot@linaro.org>'
    date: '2026-10-02'
    summary: '18 枚：EEVDF lag/slice 改进 + fair push 机制 + EAS slice 整合'
    review_outcome: 'Tim Chen/Kayra/Chen Yu 抓到 static key 泄漏、slice 判断顺序、nr_running 检查等 bug，作者确认修'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '14/18 static key 泄漏、11/18 nr_running 检查、18/18 slice 顺序待修'
    - 'push 机制的演进空间使设计可能再动'
  next_action: '作者修完 bug 发 v3'
contribution_opportunities:
  - kind: testing
    description: 'EAS/大小核平台跑短 slice 敏感负载对比前后时延'
  - kind: review
    description: '复核 static key 启用/禁用对称性与 slice 比较边界'
generated_at: '2026-10-10T01:30:00'
source_email_count: 14
related_articles: []
tags:
  - cfs
  - eevdf
  - preempt
  - load_balance
---