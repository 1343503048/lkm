# sched/proxy: allow SCHED_PROXY_EXEC with PREEMPT_RT

## TL;DR
Quchaosheng 发补丁允许 `CONFIG_SCHED_PROXY_EXEC` 与 `CONFIG_PREEMPT_RT` 同时编译，修掉此前 Kconfig `depends on !PREEMPT_RT` 挡住的一批编译错误。v2 当日紧跟 v1 发出（只改 Cc、注释缩进与措辞）。但 PREEMPT_RT 维护者（linutronix）在回帖中质疑该组合在 RT 下运行时是"空转"（blocked_on 恒为 NULL、不会有实际代理执行效果），作者随即表示若被认为不值得携带可撤回。合入前景不明朗。

## 背景与问题
`CONFIG_SCHED_PROXY_EXEC` 的 Kconfig 一直带着 `depends on !PREEMPT_RT`，注释写着 "Avoid some build failures w/ PREEMPT_RT until it can be fixed"。这些编译失败是真实存在的——同时开启两个选项后 `kernel/sched/core.c` 报 4 处错误：`clear_task_blocked_on` 指针类型不兼容、`struct mutex` 无 `wait_lock` 成员、`__get_task_blocked_on`/`__mutex_owner` 未声明。

根因：proxy execution 机制通过 `task_struct::blocked_on` 跟踪任务阻塞的 mutex，并在 `find_proxy_task()` 里沿链查找，代码是围绕原生 `struct mutex` 写的（直接内嵌 `wait_lock`、owner 存 `atomic_long_t`）。而在 PREEMPT_RT 下 `struct mutex` 变成 `struct rt_mutex` 的包装，两个成员都挪进内嵌的 `rt_mutex_base`，且 RT 分支的 blocked_on 访问器被 stub 成 `struct rt_mutex *` 参数——所以 `find_proxy_task()` 连编译都过不去。

## 技术方案
补丁把两类独立成因分别处理：
1. **头文件类型不匹配**：PREEMPT_RT 分支的 blocked_on 辅助函数参数声明为 `struct rt_mutex *`，而所有调用点传的是 `struct mutex *`（源自 `__ww_mutex_die()`/`__ww_mutex_wound()` 的历史演进）。统一参数类型。
2. **成员访问适配**：在 RT 下通过 `rtmutex.wait_lock` 取 `wait_lock`、通过 `rt_mutex_owner()` 取 owner，并移除 `include/linux/sched.h` 中参数类型与任何调用点都不匹配的 RT stub。

最终摘掉 `depends on !PREEMPT_RT`，让 `SCHED_PROXY_EXEC` + `PREEMPT_RT` 组合可编译。

## 版本演进与当前进展
- v1（09-21 上午）发出后，PREEMPT_RT 维护者回帖质疑"使能一个在 RT 下静默什么都不做的配置"是否值得。
- v2（09-21 当日）紧随发出，作者自述只修了 Cc 地址、注释缩进与那条注释的措辞，实质内容与 v1 相同，并明确"本线程仍是做决定的正确地点"。

## Maintainer 意见与讨论焦点
- **PREEMPT_RT 维护者（linutronix，回帖 msgid `<20260921100921.PsZhWgmh@linutronix.de>` 被作者引用，原始邮件未在本日缓存中）**：核心质疑是——补丁在 RT 下运行时"什么都不做"：`p->blocked_on` 只在原生 mutex 慢路径（`kernel/locking/mutex.c`）里、且位于现有 `#ifndef CONFIG_PREEMPT_RT` 块内被设置，因此 RT 下 `blocked_on` 恒为 NULL、`task_is_blocked()` 恒为 false，`find_proxy_task()` 走 `if (!mutex)` 分支提前返回，补丁新增的两个访问器成了死代码。
- 作者在回帖中承认这一点："enabling a config that silently does nothing is a fair objection, and teaching the RT mutex to maintain blocked_on is the real work here."，并明确表态"如果这不值得携带，我宁愿撤回补丁，而不是为之争辩"。

## 合入评估
*likelihood=low*。补丁本身让一个 Kconfig 已自述为 broken 的组合重新可编译，纯属使能动作；但 RT 维护者的"运行时无实际效果"质疑成立，作者已表示愿意撤回。*blocking_issues*：该组合在 RT 下不产生真实代理执行语义，仅为死代码编译通过。*next_action*：要么作者落地"让 RT mutex 维护 blocked_on"的真正工作，要么撤回；若以纯编译修复定位，需说服维护者接受"为将来铺路"的价值。

## 效果评估
无性能数据。补丁仅解决编译层面的兼容性，作者明确说明运行期行为在 RT 下改变为零。

## 我可以参与的点
- **new_patch / discussion**：真正有价值的工作是"让 PREEMPT_RT 的 rt_mutex 也维护 `blocked_on`"，使 proxy execution 在 RT 下生效——可基于此研究 RT mutex 与 proxy execution 的交互并发后续补丁。
- 也可回帖讨论：使能一个当前无运行时效果的配置组合是否有长期价值（例如为后续 RT + proxy 工作消除编译障碍）。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260921081525.2982361-1-quchaosheng000406@163.com/

---
id: sched-20260921-003
date: '2026-09-21'
subject: 'sched/proxy: allow SCHED_PROXY_EXEC with PREEMPT_RT'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260921081525.2982361-1-quchaosheng000406@163.com>'
lore_url: 'https://lore.kernel.org/all/20260921081525.2982361-1-quchaosheng000406@163.com/'
authors:
  - 'Quchaosheng'
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260921081525.2982361-1-quchaosheng000406@163.com>'
    date: '2026-09-21'
    summary: '统一 blocked_on 辅助函数参数类型并适配 RT mutex 成员访问，摘掉 depends on !PREEMPT_RT'
    review_outcome: 'RT 维护者质疑补丁在 RT 下运行时无实际效果（死代码）'
  - version: v2
    msgid: '<20260921102712.3245860-1-quchaosheng000406@163.com>'
    date: '2026-09-21'
    summary: '仅修 Cc 地址、注释缩进与措辞，内容同 v1'
    review_outcome: '作者表态若被认为不值得携带可撤回'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - 'RT 下 blocked_on 恒为 NULL，补丁新增访问器为死代码，无实际代理执行效果'
  next_action: '作者需实现 RT mutex 维护 blocked_on 的真正工作，或撤回补丁'
contribution_opportunities:
  - kind: new_patch
    description: '研究并实现 PREEMPT_RT 下 rt_mutex 维护 blocked_on，使 proxy execution 在 RT 生效'
  - kind: discussion
    description: '回帖讨论使能该配置组合（当前无运行时效果）的长期价值与是否值得携带'
generated_at: '2026-09-22T01:10:00'
source_email_count: 3
related_articles: []
tags:
  - proxy_execution
  - preempt
---