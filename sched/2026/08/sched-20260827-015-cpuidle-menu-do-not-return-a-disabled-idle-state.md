# cpuidle: menu: Do not return a disabled idle state

## TL;DR
Xueqin Luo 本日第二封同型修复：menu governor 在 `latency_req == 0` 且 state 0 被禁用时，`menu_select()` 的提前返回分支**短路了 disable 检查**，直接返回禁用的 state 0。修法是把 `!disable` 提为整个提前返回条件的前提。与 teo 那封（sched-20260827-014）是同一 bug 类在两个 governor 上的两份补丁，当日无人回复。

## 背景与问题
`menu_select()` 的提前返回条件形如 `if (latency_req == 0 || (…… && !dev->states_usage[0].disable))`——`||` 左侧完全绕过了 disable 判断。53812cdc9100（"cpuidle: menu: Move the latency_req == 0 special case check"）引入该特殊分支时即带此缺陷。后果与 teo 相同：核心层不复核 governor 返回值，CPU 进入本被禁用的状态；禁用 state 0 的部署（裁剪/调试用途）下 PM QoS 约束为 0 时必现。

## 技术方案
把条件改写为 `!dev->states_usage[0].disable && (latency_req == 0 || ……)`，state 0 禁用时落入正常选择循环（该循环本就跳过禁用状态）。8 行内完成，不改变其余选择逻辑。

## 版本演进与当前进展
v1（`<20260827094820.3900062-1-luoxueqin@kylinos.cn>`），`Fixes: 53812cdc9100`。当日暂无 review。

## Maintainer 意见与讨论焦点
无人表态；预期讨论会集中在两封的打包与写法一致性（teo 上 Rafael 已给出钳制式写法，menu 这封作者自己也是"条件重构"式改法，与 teo 回 v2 后的最终形态是否统一待观察）。

## 合入评估
**possible**。问题真实、Fixes 齐全、diff 极小，与 teo 补丁同批被 Rafael 收走的概率高；teo 那条线的方案讨论不直接影响本补丁的写法，仅可能影响措辞统一。`next_action`：等 Rafael 回复（他当天已回复了同作者的 teo 版本）。

## 效果评估
无数据；触发路径为代码推导（`latency_req==0` + state0 disabled），未见现场报告。

## 我可以参与的点
- 与 teo 篇相同：有禁用 idle 状态实践的产品环境可帮验证两个 governor 行为一致化后的表现；亦可把该组合条件整理成 kselftest/cpuidle 测试用例补进线程。

## 参考链接
- lore: https://lore.kernel.org/all/20260827094820.3900062-1-luoxueqin@kylinos.cn/
- 姊妹补丁（teo）: https://lore.kernel.org/all/20260827090505.3703860-1-luoxueqin@kylinos.cn/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260827-015
date: '2026-08-27'
subject: "cpuidle: menu: Do not return a disabled idle state"
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: "<20260827094820.3900062-1-luoxueqin@kylinos.cn>"
lore_url: "https://lore.kernel.org/all/20260827094820.3900062-1-luoxueqin@kylinos.cn/"
authors: [Xueqin Luo]
maintainers_involved: [Rafael J. Wysocki]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260827094820.3900062-1-luoxueqin@kylinos.cn>"
    date: 2026-08-27
    summary: "menu_select() 提前返回分支补 !disable 前提，state0 禁用时走正常选择循环"
    review_outcome: "暂无 review"
upstream_commit: null
fixes_commit: "53812cdc9100"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: "等 cpuidle 维护者回复；与 teo 姊妹补丁统一处理"
contribution_opportunities:
  - kind: testing
    description: "禁用 state0 + latency_req=0 组合下验证两个 governor 行为一致"
generated_at: "2026-09-07T22:05:00"
source_email_count: 1
related_articles: [sched-20260827-014]
tags: [idle]
---
