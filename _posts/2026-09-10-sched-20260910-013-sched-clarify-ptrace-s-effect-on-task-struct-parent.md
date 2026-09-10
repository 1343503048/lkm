---
id: sched-20260910-013
date: 2026-09-10
subject: 'sched: clarify ptrace''s effect on task_struct->parent'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <20260910041721.8135-1-zhangcoder@yeah.net>
lore_url: https://lore.kernel.org/all/20260910041721.8135-1-zhangcoder@yeah.net/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-11T00:58:00'
authors:
- Ziran Zhang
maintainers_involved:
- Oleg Nesterov
patch_series:
- version: v1
  msgid: <20260910041721.8135-1-zhangcoder@yeah.net>
  date: '2026-09-10'
  summary: 把 include/linux/sched.h 中 parent 字段的单行注释扩成块注释，说明被 ptrace 期间由 tracer 临时替换；5
    insertions / 1 deletion，No functional change。
  review_outcome: Oleg Nesterov 认为是 overdocumentation，先质疑是否需要更新该注释，随后给出单行替代措辞 ->real_parent
    or ptracer；作者当天认同。
- version: v2
  msgid: <20260910133027.8453-1-zhangcoder@yeah.net>
  date: '2026-09-10'
  summary: '改用 Oleg 提议的单行措辞，1 insertion / 1 deletion，新增 Suggested-by: Oleg Nesterov
    <oleg@redhat.com>。'
  review_outcome: v2 发出后至当日缓存截止无人回帖，尚无 Reviewed-by/Acked-by。
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 缺 Oleg Nesterov（或 Ingo/Peter）对 v2 的显式 Reviewed-by/Acked-by
  - Oleg 初始保留意见「Not sure this comment needs to be updated」未被正式消除，存在被直接丢弃的可能
  next_action: 等 Oleg 对 v2 表态；数日无回应则作者可在原线程 ping 一次并说明已完全采用其建议措辞
contribution_opportunities: []
source_email_count: 4
related_articles: []
tags: []
title: 'sched: clarify ptrace''s effect on task_struct->parent'
layout: article
---

## TL;DR
纯注释补丁，零功能改动：`task_struct->parent` 的注释没说清「被 ptrace 时会临时指向 tracer」。v1 写了 4 行长注释，Oleg Nesterov 认为是 overdocumentation 并给出一行版本，作者当天接受并在 13 分钟后发出 v2（1 insertion / 1 deletion，带 `Suggested-by: Oleg Nesterov`）。v2 目前无人回帖，但措辞出自该字段的实际维护者，合入阻力很小——值得关注的不是补丁本身，而是它顺带明确了 `parent` 与 `real_parent` 的语义边界。

## 背景与问题
`struct task_struct` 里有两条父子链：`real_parent` 是真实父进程，`parent` 是「SIGCHLD 的接收者、`wait4()` 汇报的对象」。主线 `include/linux/sched.h:1087` 的注释只有一行：

```c
	/* Real parent process: */
	struct task_struct __rcu	*real_parent;

	/* Recipient of SIGCHLD, wait4() reports: */
	struct task_struct __rcu	*parent;
```

问题在于：这行注释没有说明 `parent` 在 ptrace 期间会被替换。实际语义由 `kernel/ptrace.c:87` 的 `__ptrace_link()` 决定——`child->parent = new_parent;`（同时把 child 挂到 tracer 的 `ptraced` 链表），而 `real_parent` 保持不变；`__ptrace_unlink()` 再把它移回原父进程。也就是说 `parent` 是一个**可被临时改写**的字段，只读注释的人容易把 `parent` 当成恒等于 `real_parent` 的别名，在写遍历进程树、发信号或做 `wait4()` 相关逻辑时踩坑。

## 技术方案
v1 的做法是把单行注释扩成多行块注释，显式写出「正常情况与 `real_parent` 相同，但被 ptrace 期间由 tracer 临时替换」：

```c
-	/* Recipient of SIGCHLD, wait4() reports: */
+	/*
+	 * Recipient of SIGCHLD, wait4() reports. Normally the same as
+	 * real_parent, but temporarily replaced by the tracer while the
+	 * task is ptraced.
+	 */
 	struct task_struct __rcu	*parent;
```

v2 放弃这种写法，改用 Oleg 提议的单行版本，把「或然关系」压缩进原句尾部：

```c
-	/* Recipient of SIGCHLD, wait4() reports: */
+	/* Recipient of SIGCHLD, wait4() reports: ->real_parent or ptracer */
```

取舍点很清楚：v1 信息更全但占 5 行，v2 只用 `->real_parent or ptracer` 6 个词就把「两种可能取值」说完了。Oleg 的判断是 `task_struct` 这种被无数人读的结构体里，注释长度本身就是成本，而 `parent` 的取值集合是内核开发者应当已知的基础事实，不需要展开成段落。作者在回复中直接认同（"Agreed, the long form is overdocumenting it."）。

被放弃的备选方案即 v1 的长注释形式——放弃理由是冗余而非不准确。

## 版本演进与当前进展
- **v1**（2026-09-10 12:17，`<20260910041721.8135-1-zhangcoder@yeah.net>`）：`include/linux/sched.h` 5 insertions / 1 deletion，块注释形式，声明 "No functional change."。
- **Oleg Nesterov 回复**（20:54，`<aqKobFZ_a_Nvj_Wi@redhat.com>`）：开头即表态 "Well. Not sure this comment needs to be updated..."，随后给出单行替代措辞。
- **作者认同**（21:16，`<20260910131656.7470-1-zhangcoder@yeah.net>`）：承诺发 v2。
- **v2**（21:30，`<20260910133027.8453-1-zhangcoder@yeah.net>`）：1 insertion / 1 deletion，changelog 写明 "Use Oleg's minimal wording suggestion to adjust comment."，并加 `Suggested-by: Oleg Nesterov <oleg@redhat.com>`。
- 当前状态：v2 发出后至 09-10 缓存截止（当日邮件已全部拉取，无取正文失败）**无人回帖**，既无 Reviewed-by 也无进一步意见。

## Maintainer 意见与讨论焦点
- **Oleg Nesterov（Red Hat，ptrace/信号子系统长期维护者）**：唯一发言的资深成员。态度是「半保留」——他先质疑这个注释是否有必要更新（"Not sure this comment needs to be updated..."），但并没有 NAK，而是给出了他认为可接受的最小形式。这等于把「改不改」的争议降级为「怎么改」，且方案由他本人提供，因此 v2 再被退回的可能性很低。
- 焦点不在正确性而在**注释密度**：`task_struct` 是内核最热的结构体之一，Oleg 明确使用了 "overdocumentation" 这个词，这是内核核心代码评审里对文档类补丁的典型反对口径。
- 未决问题：Oleg 的第一句保留意见（是否根本不需要改）没有在 v2 中被正式撤回或确认。若他后续以「其实不必改」收尾，这个补丁可能被直接丢弃而非合入。
- Ingo Molnar / Peter Zijlstra（`include/linux/sched.h` 的实际归口）当天未参与。

## 合入评估
likelihood: medium。

理由：措辞由该领域的权威评审者本人给出，作者已带 `Suggested-by` 标签发出 v2，改动只有 1 行注释、零功能风险、不需要任何测试数据。但**尚无正式的 Reviewed-by/Acked-by**，且 Oleg 开头那句「不确定是否需要更新」的保留意见没有被明确消除；这类一行注释补丁在 tip 树里通常随大批量注释清理一起进，也可能被静默搁置。

blocking_issues：缺 Oleg（或 Ingo/Peter）对 v2 的显式 R-b/A-b；Oleg 对「是否需要这条注释」的初始保留未正式表态。

next_action：等 Oleg 对 v2 回一句 Reviewed-by；若数日无回应，作者可在原线程 ping 一次并说明 v2 已完全采用其建议措辞。

## 效果评估
无性能/行为数据可言——补丁自陈 "No functional change."，diff 只涉及注释文本，编译产物不变。可验证的正确性只有一条：v2 的措辞与 `kernel/ptrace.c` 中 `__ptrace_link()` / `__ptrace_unlink()` 的实际行为一致（`parent` 指向 tracer，`real_parent` 不变），已对照本地主线代码确认。

## 我可以参与的点
当前阶段暂无明显参与空间：措辞已由 Oleg 定稿、作者已采纳并发出 v2，再提意见只会拖延一个一行注释补丁。可持续观察 Oleg 是否给出 Reviewed-by。

若要扩展，有一个相邻的、确实还没人做的点：`task_struct` 中同样受 ptrace 影响的 `ptrace_entry`、`ptraced`、`ptrace_message` 等字段的注释也只在 `kernel/ptrace.c` 侧有详细说明，头文件里同样偏薄；可以基于同一口径提一个小型注释补齐系列（new_patch）。但这属于主动找活，Oleg 的 "overdocumentation" 表态说明这类补丁在本区域并不受欢迎，投入前应先在线程里问一句。

## 参考链接
- v1 补丁: https://lore.kernel.org/all/20260910041721.8135-1-zhangcoder@yeah.net/
- Oleg Nesterov 的评审意见: https://lore.kernel.org/all/aqKobFZ_a_Nvj_Wi@redhat.com/
- 作者认同回复: https://lore.kernel.org/all/20260910131656.7470-1-zhangcoder@yeah.net/
- v2 补丁（当前版本）: https://lore.kernel.org/all/20260910133027.8453-1-zhangcoder@yeah.net/
- upstream commit: 未获取到（尚未合入）
