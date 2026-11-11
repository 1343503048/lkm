# sched/eevdf: Fix sched idle task group preemption

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261106-003：Peter Zijlstra 发出 3 补丁系列修复 cgroup SCHED_IDLE 任务组的抢占问题：patch 1 用 guard 清理 `sched_group_set_idle()`、patch 2 把 `cfs_rq::idle` 改为「祖先 tg::idle 之和」、patch 3（RFC）携带 Vincent 的 `sched/eevdf: Fix sched idle task group preemption`。Kayra 指出 patch 2 有任务组创建竞态。
- sched-20261107-005：Peter 发出 patch 2 v2（并入竞态修正）；Kayra 给 patch 2 v2 与 patch 3 RFC 双 Reviewed-by；Vincent 给 patch 1 Reviewed-by。
- sched-20261109-006：Vincent 补上 patch 2 v2 的 Reviewed-by，patch 1/2 均已获 Vincent + Kayra 双维护者评审，patch 3 仍为 RFC。
- sched-20261110-011：Josh Don 补上 patch 1/2 的 Reviewed-by，但对 patch 3（RFC）提出实质设计质疑——`se_is_idle()` 检查「任何 idle 祖先」会让嵌套场景下普通任务不再抢占 SCHED_IDLE 任务；Kayra 追问「是否保留 idle 祖先组之间的 idle 差异」。
- sched-20261111-010（今天）：**Josh Don 回应 Kayra，为「检查任何 idle 祖先」的语义正名**——cgroup 属性本质上是「cgroup 层级位置相对」的，`cpu.idle` 也延续这一行为；用户可在一个 cgroup 内把一部分工作相对其主负载标记为 idle，但所有这些仍以该用户相对其他用户的优先级运行。并指出「上一版 RFC 已就此有过更充分的讨论，正因如此才落回 `find_matching_se()` 恢复方案」。

## 背景与问题

（承接 sched-20261106-003 / 20261107-005 / 20261109-006 / 20261110-011）cgroup SCHED_IDLE 任务组的抢占语义：`cfs_rq::idle` 此前只反映本组自身 idle 状态、未聚合祖先，导致嵌套 idle 判定错误。Peter 用「`cfs_rq::idle` = 祖先 tg::idle 之和」修复，并为 patch 3 的 EEVDF 抢占优化打底。今日 Josh Don 进一步阐释「检查任何 idle 祖先」是有意为之的层级相对语义，回应 Kayra 的追问。

## 技术方案

今日无新代码。Josh 对 patch 3（RFC `Fix sched idle task group preemption`）中 `se_is_idle()` 检查「任何 idle 祖先」的语义给出设计论证：

- cgroup 属性是「cgroup 层级位置相对」的——`cpu.idle` 也应如此。
- 典型场景：用户拿到一个 cgroup，可把一部分子任务相对其主负载标记为 idle（子代理），但这些任务整体仍以该用户相对系统其他用户的优先级运行。
- 正是上一版 RFC 里「更充分的讨论」让方案落回 `find_matching_se()` 的恢复方式（而非其他判定）。

这是对 20261110-011 中 Josh 自己提出的两个反例与两种修法的再解释：他并非否定「检查任何祖先」，而是说明这是期望语义，需要在实现上正确落地到 `find_matching_se()`。

## 版本演进与当前进展

*current_version: v2（patch 1/2 已获 Vincent + Kayra + Josh 三方 Reviewed-by，patch 3 仍为 RFC）*。今日无新版本，仅 Josh 对设计语义的澄清。

## Maintainer 意见与讨论焦点

- **Josh Don（Google 调度工程师 / 评审者）**：为 patch 3 的「检查任何 idle 祖先」语义正名，指出这是 cgroup 层级相对属性的一贯行为，并回溯到上一版 RFC 的结论（落回 `find_matching_se()`）。
- **Kayra Cizmeci（评审者）**：此前的追问「是否保留 idle 祖先组之间的 idle 差异」得到 Josh 的正面回应。
- patch 1/2 无争议；patch 3 的争论从「语义对不对」收敛到「如何在 `find_matching_se()` 上正确实现」的实现层面。

## 合入评估

*likelihood=medium*。patch 1/2 已三方 R-b、随时可收；patch 3 仍为 RFC，语义之争虽已澄清但尚未有新实现版本。*blocking_issues*：patch 3 需按「层级相对」语义在 `find_matching_se()` 上给出可评审的新版本。*next_action*：Peter 发 patch 3 的正式（非 RFC）版本，实现 Josh/Kayra 讨论落定的语义。

## 效果评估

暂无性能数据。本系列是抢占语义正确性修复，无量化收益。

## 我可以参与的点

- **review**：复核 patch 3 后续版本中 `se_is_idle()` 与 `find_matching_se()` 的配合是否严格满足 Josh 描述的「层级相对」语义（嵌套 idle 组下普通任务仍能抢占 SCHED_IDLE 任务）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261105165525.011876858@infradead.org/
- Josh 对语义的澄清: https://lore.kernel.org/all/CABk29NsBzdEYOdLqj9HsrCqO6RzW_G574RzY+=vJp+564R2u=w@mail.gmail.com/

---
id: sched-20261111-010
date: '2026-11-11'
subject: "sched/eevdf: Fix sched idle task group preemption"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261105165525.011876858@infradead.org>"
lore_url: "https://lore.kernel.org/all/20261105165525.011876858@infradead.org/"
authors: [Peter Zijlstra, Vincent Guittot]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261105165525.011876858@infradead.org>"
    date: '2026-11-05'
    summary: "cfs_rq::idle 改为祖先 tg::idle 之和；patch 3 RFC 携带 EEVDF idle 组抢占修复"
    review_outcome: "patch 1/2 三方 Reviewed-by；patch 3 语义澄清为层级相对、待正式版"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["patch 3 需在 find_matching_se() 上给出按层级相对语义实现的正式版"]
  next_action: "Peter 发 patch 3 正式版本"
contribution_opportunities:
  - kind: review
    description: "复核 patch 3 中 se_is_idle() 与 find_matching_se() 是否满足层级相对语义"
generated_at: "2026-11-12T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261106-003, sched-20261107-005, sched-20261109-006, sched-20261110-011]
tags: [cgroup, cfs, eevdf]
---
