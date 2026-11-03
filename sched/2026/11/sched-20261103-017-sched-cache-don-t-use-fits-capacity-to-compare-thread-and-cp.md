# sched/cache: Don't use fits_capacity() to compare thread and CPU counts

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261102-006：Zhan Xusheng 把 cache-aware 调度里 `invalid_llc_nr()` 对 `fits_capacity()` 的误用（用「线程数 vs CPU 数」比较却只为借它 20% margin）抽成独立 helper `fits_llc_nr()`（`x*5 < y*4`，与旧 `x*1280 < y*1024` 严格等价），无功能变化；动机是 Qais 的 series 会把 `fits_capacity()` 第二参数改成 CPU 编号。
- sched-20261103-017（今天）：Qais Yousef 给 Reviewed-by（"LGTM, although I hope we can do better"，追问 workaround 的是什么问题、能否去掉 magic 数）；Chen Yu 给 Reviewed-by 并详述三个反过度聚合指标的独立作用——两处 Reviewed-by 已集齐。

## 背景与问题

（承接 sched-20261102-006）`invalid_llc_nr()` 用 `fits_capacity()` 比较「线程数」与「CPU 数」只是借其 20% margin。Qais 的 capacity-aware 系列将把 `fits_capacity()` 第二参数改为 CPU 编号，届时该调用会静默把「CPU 数」当「CPU 编号」传递，属静默绑定错误。今日 Chen Yu 进一步澄清：这个 margin（80%）正是「线程过饱和」这一反过度聚合指标的保守默认，与 util、LLC 大小两个指标独立、不可删一保三。

## 技术方案

（承接）新增 `fits_llc_nr(nr_threads, nr_cpus)`：`nr_threads * 5 < (u64)nr_cpus * 4`（等价旧比较），`invalid_llc_nr()` 改调它。今日无代码变更，Qais 与 Chen Yu 均表示认同当前 patch。

## 版本演进与当前进展

*current_version: v1（2026-11-02 发出，msgid 20261102021536.1026143-1-zhanxusheng1024@gmail.com；今日仍 v1）*。今日两位关键 reviewer 给出 Reviewed-by。

## Maintainer 意见与讨论焦点

Qais（fits_capacity 系列原作者）Reviewed 但提出更高期望：「容量对比里我们曾有移动过快/过慢的问题，所以我才想移除这个 magic 数；我怀疑这能否带来全局收益——这是否是我们能做到的最好？还有 llc_aggr_tolerance、llc_imb_pct 等其它 magic」。Chen Yu（cache-aware 调度作者）Reviewed，并解释三个指标（util 的 llc_overaggr_pct、线程数的 invalid_llc_nr、LLC 大小的 exceed_llc_capacity）分别防止不同类型的过度聚合、不可简单删其一；该 80% 只是「恰好 fits_capacity 用了这个值」的保守选择。二者不冲突但侧重点不同：Qais 想终极移除 margin，Chen Yu 认为 fine-grained 控制引入后全局保守默认仍需兜底。

## 合入评估

*likelihood=high*。补丁获原作者（Chen Yu）与 fits_capacity 系列作者（Qais）双 Reviewed-by，方向无异议；只是 Qais 长期期望移除 margin 的 open 讨论不影响本补丁合入。*next_action*：等维护者收取即可。

## 效果评估

无功能变化、无性能数据；作者说明 `x*5 < y*4` 与旧比较严格等价。

## 我可以参与的点

- discussion：就「是否保留 20% margin」给出实测（聚合行为何时变化的）依据，直接回应 Qais 的追问。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261102021536.1026143-1-zhanxusheng1024@gmail.com/

---
id: sched-20261103-017
date: 2026-11-03
subject: "sched/cache: Don't use fits_capacity() to compare thread and CPU counts"
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<20261102021536.1026143-1-zhanxusheng1024@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261102021536.1026143-1-zhanxusheng1024@gmail.com/"
authors: [Zhan Xusheng]
maintainers_involved: [Qais Yousef, Chen Yu]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261102021536.1026143-1-zhanxusheng1024@gmail.com>"
    date: 2026-11-02
    summary: "fits_capacity() 误用抽出为 fits_llc_nr()，无功能变化。"
    review_outcome: "Qais 与 Chen Yu 双 Reviewed-by。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等维护者收取。"
contribution_opportunities:
  - kind: discussion
    description: "就 20% margin 去留给出实测依据，回应 Qais 的追问。"
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 3
related_articles: [sched-20261102-006]
tags: [cfs]
---