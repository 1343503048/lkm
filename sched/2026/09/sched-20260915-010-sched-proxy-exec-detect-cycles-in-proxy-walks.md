# sched/proxy_exec: Detect cycles in proxy walks

## TL;DR
本文为增量更新。Zhidao Su 的 v5「用序列标记检测 proxy walk 环」今日（09-15）获 Hui Su 回复：Hui Su 称正在实验同一环检测问题的不同取舍，已作为独立 RFC 发出（sched/proxy_exec: detect cycles without persistent walk state），并简述其 Online Brent 方案与 v5 的核心差异——不往 task_struct/rq 加状态、不需激活时复位、复用真实 owner walk 而非另做 preflight；代价是 Brent 可能在 walk 短暂闭合 blocked_donor 环后才检出。合入判断 unknown。

## 背景与问题
承 proxy_exec 环检测主线（见 related_articles 与 sched-20260915-009）：blocked_on 链成环会让 `find_proxy_task()` 持 rq->lock 死循环。Zhidao Su 的 v5 用「task_struct + rq 序列状态 + 激活时复位标记」检测重复；本日 Hui Su 从旁给出一个免持久状态的替代取舍，作为对 v5 方案的独立评审视角。

## 技术方案
本日 v5 线程无新代码。Hui Su 的回复概述其替代方案的要点并附对比测试线索：环检测状态局部于真实 owner walk；不加 task_struct/rq 状态、不要激活时标记复位；复用 walk 的 owner 解析；代价是允许短暂 backlink 窗口。并附上与 v5 同基/同配置对比的结论（正常无环路径 ns/call 在测试深度上相当）。

## 版本演进与当前进展
v5 自 07-22 发出后进入长尾讨论；本日是 Hui Su 的旁路回应（指向其 09-15 的 RFC），非 v5 自身版本更新。作者 Zhidao Su 尚未就 Hui Su 的替代方案在本线程表态。

## Maintainer 意见与讨论焦点
- **Hui Su**（非维护者，替代方案作者）：指出 v5 持久标记 + 激活复位的成本，并提出免持久状态的 Brent 方案，核心设计问题是「避免持久 task/rq 访问状态是否值得接受短暂 backlink 窗口」。
- 无维护者对 v5 的直接表态；两个方案（序列标记 vs Online Brent）尚未有定论。

## 合入评估
*likelihood=unknown*。v5 本身无维护者 A/N/T，且出现了竞争方案；环检测的设计取舍（持久状态 vs 短暂环窗口）未决。*blocking_issues*：无维护者评审结论；存在替代方案分流。*next_action*：等 proxy_exec 维护者比较 v5 与 Hui Su RFC 两个方案后定方向。

## 效果评估
Hui Su 附带的对比结论（相对 v5）：正常无环 find_proxy_task() 的 ns/call 在测试深度上相当（详见其 RFC cover 的 depth 16-1024 表格）。v5 自身的性能数据在更早线程中，未在本日邮件重复。属作者主观对比描述，测试覆盖有限（作者已声明不覆盖所有调度交错）。

## 我可以参与的点
- kind=review：对比 v5 序列标记与 Online Brent 两个方案在「并发唤醒/迁移」路径下的正确性差异，形成第三方评审意见。
- kind=discussion：就「持久访问状态 + 激活复位」vs「短暂 backlink 窗口」的取舍给出分析，帮助维护者定夺。

## 参考链接
- Hui Su 回帖：https://lore.kernel.org/all/f2f8ba0f978a894a949bf7b993594d4e.sh_def@163.com/
- Zhidao Su v5：https://lore.kernel.org/r/20260722120346.93000-1-soolaugust@gmail.com/

---
id: sched-20260915-010
date: '2026-09-15'
subject: 'sched/proxy_exec: Detect cycles in proxy walks'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: '<20260722120346.93000-1-soolaugust@gmail.com>'
lore_url: 'https://lore.kernel.org/all/f2f8ba0f978a894a949bf7b993594d4e.sh_def@163.com/'
authors:
  - 'Zhidao Su'
maintainers_involved: []
current_version: v5
patch_series:
  - version: v5
    msgid: '<20260722120346.93000-1-soolaugust@gmail.com>'
    date: '2026-07-22'
    summary: '用 task_struct + rq 序列状态 + 激活时复位标记检测 proxy walk 环'
    review_outcome: 'Hui Su 提出免持久状态的 Brent 替代方案并附对比数据，维护者未表态'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '无维护者评审结论'
    - '存在替代方案分流'
  next_action: '等维护者比较 v5 与 Hui Su RFC 两个方案后定方向'
contribution_opportunities:
  - kind: review
    description: '对比序列标记与 Online Brent 在并发唤醒/迁移路径下的正确性差异'
  - kind: discussion
    description: '就持久状态 vs 短暂 backlink 窗口的取舍给出分析'
generated_at: '2026-09-16T01:05:00'
source_email_count: 1
related_articles:
  - 'sched-20260915-009'
tags:
  - proxy_execution
---