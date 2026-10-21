---
id: sched-20261021-003
date: 2026-10-21
subject: 'sched/fair: Introduce the SMT_BUDDY_ASSIST feature'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261020083746.37068-1-likunyu@open-hieco.net>
lore_url: https://lore.kernel.org/all/20261020083746.37068-1-likunyu@open-hieco.net/
authors:
- Li kunyu
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261020083746.37068-1-likunyu@open-hieco.net>
  date: 2026-10-20
  summary: RFC 六补丁：SMT sibling push / is_smt_buddy_run / sibling 排除 / newidle 限 LLC
    / burst 阈值 / 文档
  review_outcome: Peter 系统性否定（风格、SMT mask 假设、静态阈值、debugfs 误用），给出平均 rq-depth + 轮转替代方向
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 方案（静态阈值+仅 idle+NO_HZ 依赖）被质疑，需重设计
  - 代码风格需整体重写
  next_action: 作者吸收 Peter 替代方向后重写方案与代码再提交
contribution_opportunities:
- kind: discussion
  description: 评估 Peter 的平均 rq-depth 跟踪 + 轮转新任务替代方案的可行性
- kind: review
  description: 在非 x86 多线程 SMT 架构上验证 is_smt_buddy_run 等 SMT 拓扑假设
generated_at: '2026-10-22T01:30:00'
source_email_count: 7
related_articles: []
tags:
- cfs
- load_balance
- hyperthreading
title: 'sched/fair: Introduce the SMT_BUDDY_ASSIST feature'
layout: article
---

## TL;DR
Li kunyu 发往 sched 的 RFC 六补丁系列「SMT Buddy Assist」：利用 SMT 兄弟核互相「assist」，在周期性负载均衡里向 SMT sibling push、push 成功后排除该 sibling、newidle 均衡限制到 LLC 域，并加入 burst 阈值，目标是降低突发唤醒下的任务分布不均。当日 Peter Zijlstra 逐一给出了相当严厉的 review——代码缩进「horrific」、误以为 SMT mask 只有 2 个 CPU、静态阈值「horrible」并给出跟踪平均 rq-depth + `cpumask_any_distribute()` 轮转的替代方向；Kayra Cizmeci 也质疑 cover 里 benchmark 的「acceptable」表述。RFC 尚未获得方向性认可。

## 背景与问题
系列要解决「突发唤醒导致任务分布不均」：当一批任务同时被唤醒（burst），周期性负载均衡没能及时把它们摊开，导致个别 CPU 过载而 SMT 兄弟空闲。作者提出的「SMT Buddy Assist」思路是让 SMT 兄弟核在 burst 场景下互相协助分摊，具体落到 6 个补丁（见技术方案）。属新特性提案，处于 RFC 早期。

## 技术方案
RFC 六补丁（`kernel/sched/fair.c` + docs）：
1. 周期性负载均衡里新增 SMT sibling push（`sched/fair: Add SMT sibling push in periodic load balance`）。
2. 新增 `is_smt_buddy_run()` 在 buddy 运行时跳过 SMT 域（`Add is_smt_buddy_run() to skip SMT domain`）。
3. push 成功后排除 SMT sibling（`SMT sibling exclusion after successful push`）。
4. 把 newidle 均衡限制到 LLC 域（`Restrict newidle balance to LLC domain`）。
5. 为大规模 burst 加任务 burst 阈值（`Add task burst threshold for large-scale bursts`）。
6. 文档（`sched/docs: Add documentation for SMT Buddy Assist feature`）。

## 版本演进与当前进展
*current_version: v1（RFC）*。系列于 2026-10-20 发出，当日无维护者回帖；2026-10-21 收到 Peter Zijlstra 对 6 个补丁的逐封 review 与 Kayra 对 cover 的质疑，尚未出 v2。

## Maintainer 意见与讨论焦点
Peter Zijlstra 的逐封意见（整体偏负面，且先声明「不要在高层面反馈出来之前就急着发新版本」）：
- 代码风格：多次「horrific indenting fail」「恐怖地糟糕——用循环 + atomic bit clear 去清一个本地 cpumask」。
- 2/6：作者注释假设「SMT mask 永远只有 2 个 CPU」，Peter 指出大量架构并非如此。
- 4/6：「本可以直接 fiddle `SD_BALANCE_NEWIDLE`，却写得不可读、又违反编码风格（多行块必须加大括号）」。
- 5/6：「不理解为何依赖 NO_HZ、为何只考虑 idle CPU；静态阈值 horrible」——建议跟踪 root domain 里平均 rq-depth，当局部 rq-depth 达到其倍数（如 3）时回退到 `cpu = cpumask_any_distribute(p->cpus_ptr)` 轮转新任务并重置周期性负载均衡周期。
- 6/6：「NO！这不是接口，注意那个 `debug`」——文档把 debug 接口当成了特性接口。
Kayra Cizmeci 对 cover 的 benchmark 表述质疑：「按什么标准算 acceptable？如果有误差为何还要提」。

## 合入评估
*likelihood=low*。RFC 初版即收到核心维护者的系统性否定（编码风格、对 SMT 拓扑的错误假设、静态阈值方案、debugfs 误当接口），并给出明确的替代方向。*blocking_issues*：方案本身（静态阈值 + 仅 idle CPU + NO_HZ 依赖）被质疑，需按 Peter 建议重设计；代码风格需整体重写。*next_action*：作者吸收 Peter 的替代方向（平均 rq-depth 跟踪 + 轮转），重写方案与代码后再提交。

## 效果评估
cover 声称有 benchmark 结果「acceptable」，但 Kayra 质疑其标准与误差表述，未给出可核验的量化数字；其余补丁无独立效果数据。属作者主观性能主张，未见可靠数据。

## 我可以参与的点
- `discussion`：Peter 提出的「跟踪平均 rq-depth + 轮转新任务」替代方案目前无人深入展开，可协助评估其可行性或补数据。
- `review`：系列涉及 SMT 拓扑假设（多 CPU SMT mask），可在非 x86 多线程 SMT 架构（如部分 arm64/IBM）上验证 `is_smt_buddy_run()` 等假设是否成立。

## 参考链接
- cover：https://lore.kernel.org/all/20261020083746.37068-1-likunyu@open-hieco.net/
- Peter 对 5/6 的替代方向：https://lore.kernel.org/all/20261021125419.GK2823843@noisy.programming.kicks-ass.net/
- Kayra 对 cover 的质疑：https://lore.kernel.org/all/atiy9PAq4lvXxWj1@scheduler.schedules/
