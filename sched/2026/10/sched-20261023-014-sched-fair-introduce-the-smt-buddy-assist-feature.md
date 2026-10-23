# sched/fair: Introduce the SMT_BUDDY_ASSIST feature

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20261021-003：Li kunyu 发往 sched 的 RFC 六补丁系列「SMT Buddy Assist」：利用 SMT 兄弟核互相 assist，在周期性负载均衡里向 SMT sibling push、push 成功后排除该 sibling、newidle 均衡限制到 LLC 域，并加 burst 阈值，目标是降低突发唤醒下的任务分布不均。当日 Peter Zijlstra 给出严厉 review（代码缩进「horrific」、误以为 SMT mask 只有 2 CPU、静态阈值「horrible」，并给出跟踪平均 rq-depth + `cpumask_any_distribute()` 轮转的替代方向）；Kayra Cizmeci 也质疑 cover 里 benchmark 的「acceptable」表述。
- sched-20261022-008：Peter 进一步否定「用 SMT push 硬扛跨 LLC 迁移」的方向——「这是 cache-aware scheduling 该解决的问题」，并指路 Tim Chen 的 cache-aware 系列与 Vincent 的相关补丁；作者回帖感谢，表示后续版本将加用户接口（`always|advise|never`）、改为检查 `cfs.h_nr_runnable`。
- sched-20261023-014（今天）：Tim Chen 与 Chen Yu 分别给出实操建议与方向性质疑——Tim 建议作者先试 `relax_domain_level=` 启动参数阻止 newidle 跨 NUMA 均衡并量化收益；Chen Yu 追问「要优化的场景里工作线程之间是否共享数据」，若共享应走 cache-aware + prctl、若不共享且内存占用高应靠 NUMA balancing，并指路 Jianyong Wu 的多 LLC/节点 cache-aware 扩展系列。

## 背景与问题
（承接 sched-20261021-003 → sched-20261022-008）系列要解决「突发唤醒导致任务分布不均」：一批任务同时被唤醒（burst）时，周期性负载均衡没能及时摊开，导致个别 CPU 过载而 SMT 兄弟空闲。Peter 已把问题定性为「跨 LLC 的过度迁移」，主张诉诸 cache-aware scheduling。今天 Tim/Chen Yu 把讨论再推进一步：先澄清「工作线程之间是否共享数据」这一前提，因为它决定了该用 cache-aware（共享、要共置）还是 NUMA balancing（不共享、要就近内存）。

## 技术方案
（承接 003/008）RFC 六补丁（`kernel/sched/fair.c` + docs）：周期性负载均衡里新增 SMT sibling push、`is_smt_buddy_run()` 跳过 SMT 域、push 成功后排除 sibling、newidle 均衡限制到 LLC 域、大规模 burst 阈值、文档。今日无新补丁；新增两条外部替代/验证建议：

- Tim Chen：让作者在现有内核上试 `relax_domain_level=` 启动参数（配合 `grep . /sys/kernel/debug/sched/domains/cpu0/domain*/{name,level,flags}` 定位 NUMA 层并确认 `SD_BALANCE_NEWIDLE` 是否已关闭），先量化「阻止 newidle 跨 NUMA 均衡」能带来多少收益，再决定是否值得为它加机制。
- Chen Yu：先厘清负载类型——(1) 线程共享数据 → cache-aware + prctl（并提到一个增强 prctl 聚合度的提案 [1]）；(2) 线程不共享数据且内存占用高 → NUMA balancing（并追问为何 NUMA balancing 没抑制跨节点迁移、是否平台上被禁用）；另指路 Jianyong Wu 把 cache-aware 扩展到多 preferred LLC/节点的系列 [2]。

## 版本演进与当前进展
*current_version: v1（RFC）*（`<20261020083746.37068-1-likunyu@open-hieco.net>`）。当日无新版本，为方向性讨论（Tim/Chen Yu 的替代建议与前提澄清）。

## Maintainer 意见与讨论焦点
- Tim Chen（Intel，cache-aware 系列作者）：未直接否定，而是给「先做减法验证」路径——用现有 `relax_domain_level` 量化阻止 newidle 跨 NUMA 的收益。
- Chen Yu（Intel）：从「数据是否共享」这一根本前提切入，倾向把问题引向已有的 cache-aware / NUMA balancing 机制，而非新造 SMT push 机制；明确指出补丁 4（禁止 newly-idle 跨节点均衡）是主线，1/2/3/5 是为其服务的配套。
- 作者上日已承诺后续版本加用户接口、改查 `cfs.h_nr_runnable`，但今日未见作者回应 Tim/Chen Yu 的新质疑。

## 合入评估
*likelihood=low*。RFC 早期，主维护者 Peter 已对技术路线持保留、Tim/Chen Yu 又各自指向不同既有机制；作者尚未用数据回应「SMT push 相对 cache-aware/NUMA balancing 的增量价值」。*blocking_issues*：需先厘清负载共享模式、证明 SMT push 的增量价值或吸收 cache-aware 思路重设计。*next_action*：作者先用 `relax_domain_level`/cache-aware 量化收益，并回应 Chen Yu 的共享数据前提问题后再定。

## 效果评估
今日无新 benchmark。作者 cover 里的 benchmark 表述此前已被 Kayra 质疑「acceptable」定义不清，尚未补量化数据。

## 我可以参与的点
- *kind: discussion*：就「突发唤醒分布不均」在不同负载（共享数据 vs 独立线程）下应诉诸 SMT push、cache-aware 还是 NUMA balancing 给出判别依据。
- *kind: testing*：在作者的目标平台上用 `relax_domain_level` 复现并量化收益，帮助判断是否需要新机制。

## 参考链接
- Tim Chen 回帖: https://lore.kernel.org/all/6d8ff4593cc93c0033c6537eeac281085726c220.camel@linux.intel.com/
- Chen Yu 回帖: https://lore.kernel.org/all/atozo8vLDlOB6Vau@chenyu-dev/
- 前文: sched-20261021-003 / sched-20261022-008

---
id: sched-20261023-014
date: 2026-10-23
subject: "sched/fair: Introduce the SMT_BUDDY_ASSIST feature"
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<20261020083746.37068-1-likunyu@open-hieco.net>"
lore_url: "https://lore.kernel.org/all/20261020083746.37068-1-likunyu@open-hieco.net/"
authors: ["Li kunyu"]
maintainers_involved: ["Peter Zijlstra", "Tim Chen", "Chen Yu"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261020083746.37068-1-likunyu@open-hieco.net>"
    date: 2026-10-20
    summary: "SMT sibling push + newidle 限 LLC + burst 阈值等 6 补丁"
    review_outcome: "Peter 严厉 review；Tim/Chen Yu 指向 cache-aware/NUMA balancing"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues: ["未厘清负载共享模式", "未证明 SMT push 相对 cache-aware/NUMA balancing 的增量价值"]
  next_action: "先用 relax_domain_level/cache-aware 量化收益并回应共享数据前提"
contribution_opportunities:
  - kind: discussion
    description: "就共享数据 vs 独立线程负载该诉诸哪类机制给出判别依据"
  - kind: testing
    description: "在目标平台用 relax_domain_level 复现并量化收益"
generated_at: "2026-10-24T09:13:00"
source_email_count: 2
related_articles: ["sched-20261021-003", "sched-20261022-008"]
tags: [cfs, load_balance, hyperthreading]
---