# sched/isolation: Prevent out-of-bounds read in isolcpus= boot parameter parser

## TL;DR
这不是技术讨论，而是一次**处置方式的变更通知**：Aaron Tomlin 的 `isolcpus=` 解析器越界读修复自 2026-05-23 发出、经 Valentin Schneider 评审后至今无进展，作者宣布放弃单独推进，把它作为前置补丁折叠进即将到来的 multiqueue CPU isolation 系列 v16，并承诺保留 Valentin 的 `Reviewed-by`、`Fixes:` 标签与 `Cc: stable`。我对照本地内核树（Linux 7.2-rc6，已确认 `kernel/sched/isolation.c` 与该版本一致）确认这个越界读确实存在，位置在 `housekeeping_isolcpus_setup()` 跳过未知子参数后的无条件 `str++`。**值得关注的点恰恰是这个处置决定本身**：一个已获 R-b、需要进 stable 的小修复被绑上一个已迭代到 v16 的大系列，等于把 stable 回合时点交给了大系列的合入节奏。

## 背景与问题
`isolcpus=` 是启动期解析的内核命令行参数，由 `kernel/sched/isolation.c` 的 `housekeeping_isolcpus_setup()` 处理，解析结果决定 housekeeping cpumask（哪些 CPU 被排除在调度域/nohz/managed irq 之外）。

越界读的成因在 Linux 7.2-rc6 的代码里可以直接看到（`kernel/sched/isolation.c:314` 起）：

```c
	while (isalpha(*str)) {
		if (!strncmp(str, "nohz,", 5))        { str += 5;  ... continue; }
		if (!strncmp(str, "domain,", 7))      { str += 7;  ... continue; }
		if (!strncmp(str, "managed_irq,", 12)){ str += 12; ... continue; }

		/*
		 * Skip unknown sub-parameter and validate that it is not
		 * containing an invalid character.
		 */
		for (par = str, len = 0; *str && *str != ','; str++, len++) {
			if (!isalpha(*str) && *str != '_')
				illegal = true;
		}

		if (illegal) {
			pr_warn("isolcpus: Invalid flag %.*s\n", len, par);
			return 0;
		}

		pr_info("isolcpus: Skipped unknown flag %.*s\n", len, par);
		str++;
	}
```

内层 `for` 有两个终止条件：遇到 `,` 或遇到字符串结束符 `\0`。前三个已知分支都是 `str += N`，N 已经把逗号算进去了，所以停在 `\0` 时 `while (isalpha(*str))` 会正常退出。但**未知子参数分支的收尾是无条件 `str++`**——它假定内层循环一定停在逗号上。当命令行以一个未知 flag 结尾且没有尾随逗号时（例如 `isolcpus=foobar`），内层循环停在 `\0`，`str++` 把指针推到终止符**之后**，紧接着 `while (isalpha(*str))` 就读到了字符串边界外的一个字节。

影响范围（我基于主线代码的推断，邮件正文未获取到，故不作为补丁自陈转述）：
- 触发条件苛刻——必须能改内核命令行，且必须使用未知 flag 且不带尾随逗号；这本身已要求 root/物理访问权限，不构成提权面。
- 后果取决于越界那一个字节的取值：若恰好是字母，循环会带着一个已越过终止符的指针继续解析；退出循环后 `housekeeping_setup(str, flags)` 拿到的是**指向字符串末尾之后**的指针去解析 cpulist，可能产生错误的 housekeeping 掩码，或在开启 KASAN 的启动上报越界读。
- 同一函数里还有个相邻瑕疵（不是本补丁主题）：`illegal` 一旦置位就不会在多轮迭代间复位，不过置位后立即 `return 0`，实际不构成问题。

## 技术方案
补丁正文（diff）未获取到——本缓存只有 Aaron 09-10 的回复，原始补丁 `<20260523210214.593704-1-atomlin@atomlin.com>` 与 Valentin 的评审 `<xhsmhh5n81310.mognet@vschneid-thinkpadt14sgen2i.remote.csb>` 均不在邮箱缓存内，按数据源边界不去 lore 回捞。

从作者回复能确定的方案要点只有处置层面，而非代码层面：
- 修复将作为 **prerequisite patch** 放在 multiqueue CPU isolation 系列 v16 的最前面，因为该系列「modifies this exact parser logic in kernel/sched/isolation.c」——即大系列会改写同一段解析逻辑，两者必须在同一个基线上落地，否则冲突。
- 明确目标是「ensuring a bisectable baseline」：修复先进，大系列再在其上改动，保证每一步可 bisect。
- 保留 `Reviewed-by: Valentin Schneider`、`Fixes:` 标签与 `Cc: stable`。

按 7.2-rc6 的代码看，最小修复形态应当是把 `str++` 改为只在停在逗号时才前进（例如 `if (*str) str++;` 或把循环条件改为 `while (*str && isalpha(*str))`），但**这是我基于代码的推测，不是邮件内容**，实际补丁写法未获取到。

## 版本演进与当前进展
- **v1**：2026-05-23 发出（msgid `<20260523210214.593704-1-atomlin@atomlin.com>`）。
- **评审**：Valentin Schneider 给出 Reviewed-by（具体时间未获取到，Aaron 称「no further movement on this thread since June」，即评审发生在 6 月）。
- **2026-09-10**：Aaron 回复 Valentin，宣布折叠进 multiqueue CPU isolation v16 作为前置补丁。这是该线程三个多月来的唯一新动作。
- **当前版本仍为 v1**，没有 v2；下一版将以 v16 系列的一部分形式出现，而非独立补丁。
- multiqueue CPU isolation 系列本身已迭代到 v15（即将出 v16），说明大系列长期未合入。

## Maintainer 意见与讨论焦点
- **Valentin Schneider**：唯一评审者，已给 Reviewed-by，对修复本身无异议（评审原文未获取到，仅从 Aaron 「will retain your Reviewed-by: tag」的表述确认其存在与有效性）。Aaron 的这封回复是**告知而非征询**——他没有问「可不可以折叠」，而是直接说明打算这么做。Valentin 在 09-10 缓存截止前未回应该通知。
- 无 NAK、无技术分歧。
- 真正值得质疑的不是代码而是**流程**，且当日无人提出：一个已获 R-b、带 `Fixes:` 与 `Cc: stable` 的越界读修复，被绑定到一个已迭代 15 版仍未合入的大系列上，等于让 stable 树多等一个不确定的周期。常规做法是让小修复先独立进 `sched/urgent` 或 tip，再由大系列 rebase 到它之上——Aaron 选择相反顺序，理由是「大系列会改写同一段解析逻辑」，但这个理由只解释了为什么两者不能并行推进，并不解释为什么修复必须等大系列。
- Ingo Molnar / Peter Zijlstra 当日未参与。

## 合入评估
likelihood: medium。

依据：修复本身阻力极小——已有 Valentin 的 Reviewed-by、有 `Fixes:` 标签、`Cc: stable`、改动局限在启动期一个解析函数、无功能行为变更风险。但它现在的命运与 multiqueue CPU isolation v16 绑定，而该系列 15 版未合入说明其自身仍有未解决的争议或规模问题，因此实际合入时点不可预测。

blocking_issues：
- 修复不再独立投递，进度取决于 v16 系列能否被 sched 维护者接受。
- Valentin 尚未对「折叠进 v16」这一处置表态；若他认为应先独立进 stable，作者需要改回单发。
- 补丁正文与 `Fixes:` 指向的具体 commit 均未获取到，无法核验修复范围是否覆盖上述越界路径的全部入口。

next_action：作者在 v16 中把该修复作为 patch 01 发出；更稳的做法是先按 v1 原样（或带 changelog 说明）单独重发一次争取进 `sched/urgent` + stable，v16 再 rebase。

## 效果评估
暂无效果数据。这是一个越界读修复，不涉及性能；邮件中也未提及复现方式（KASAN splat、具体命令行、触发架构）——这些都在未获取到的原始补丁正文里。

我基于本地内核树（Linux 7.2-rc6）的代码审阅确认了缺陷存在（`housekeeping_isolcpus_setup()` 未知 flag 分支的无条件 `str++`），这是**代码审阅结论，不是测试结果**；未实际构造 `isolcpus=foobar` 启动验证。

## 我可以参与的点
- **推动解耦（discussion）**：这是本线程最有价值的一件事——在原线程回复，指出带 `Cc: stable` 的越界读修复不应等待一个已迭代 15 版的大系列，建议 Aaron 单独重发 v2 走 `sched/urgent`，v16 再 rebase 到它之上；同时可请 Valentin 就处置方式表个态。成本低、对 stable 用户有实际收益。
- **补复现与验证（testing）**：在开启 `CONFIG_KASAN` 的内核上用 `isolcpus=<未知flag>`（不带尾随逗号）启动，确认是否报越界读、以及 housekeeping 掩码是否被错误设置，把结果回帖。当日线程里完全没有复现数据，这是明显的信息缺口。
- **审 v16 的前置补丁顺序（review）**：等 v16 发出后，核对修复是否真的排在改写同一解析逻辑的补丁之前、bisect 基线是否成立，以及 `Fixes:` 与 `Cc: stable` 是否如承诺保留。
- 相邻背景可参考 sched-20260802-001（同文件 `kernel/sched/isolation.c` 的 housekeeping cpumask 释放时机修复），两者都属 housekeeping 初始化路径的小修复，合入路径可互为参照。

## 参考链接
- 原始补丁 v1（线程根，2026-05-23）: https://lore.kernel.org/all/20260523210214.593704-1-atomlin@atomlin.com/
- Aaron Tomlin 的处置通知（本日邮件）: https://lore.kernel.org/all/lthk2ykbvh6wef6arzlhpquupesg3wzacrsdib7d4skw5jy667@6flolvclefda/
- Valentin Schneider 的评审（被回复邮件）: https://lore.kernel.org/all/xhsmhh5n81310.mognet@vschneid-thinkpadt14sgen2i.remote.csb/
- Fixes: 指向的 commit: 未获取到（原始补丁正文不在邮箱缓存内）
- upstream commit / stable 回合: 未获取到（尚未合入）

---
id: sched-20260910-015
date: 2026-09-10
subject: "sched/isolation: Prevent out-of-bounds read in isolcpus= boot parameter parser"
subsystem: sched
type: fix
status: superseded
severity: low
thread_root_msgid: "<20260523210214.593704-1-atomlin@atomlin.com>"
lore_url: "https://lore.kernel.org/all/20260523210214.593704-1-atomlin@atomlin.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: "2026-09-11T01:15:00"
authors:
  - "Aaron Tomlin"
maintainers_involved:
  - "Valentin Schneider"
patch_series:
  - version: v1
    msgid: "<20260523210214.593704-1-atomlin@atomlin.com>"
    date: "2026-05-23"
    summary: "修复 isolcpus= 解析器 housekeeping_isolcpus_setup() 的越界读；补丁正文未获取到（不在邮箱缓存内），仅能从作者后续回复确认其带 Fixes: 标签与 Cc: stable。"
    review_outcome: "Valentin Schneider 给出 Reviewed-by（约 6 月，评审原文未获取到）；此后线程无进展，作者于 09-10 宣布折叠进 multiqueue CPU isolation v16 作为前置补丁，承诺保留 R-b、Fixes 与 Cc stable。"
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "修复不再独立投递，合入时点绑定在已迭代 15 版仍未合入的 multiqueue CPU isolation 系列上"
    - "Valentin Schneider 未对「折叠进 v16」这一处置方式表态"
    - "补丁正文与 Fixes: 指向的 commit 未获取到，无法核验修复是否覆盖越界路径全部入口"
  next_action: "在 v16 中作为 patch 01 发出；更稳的做法是先单独重发争取进 sched/urgent + stable，v16 再 rebase 到其上"
contribution_opportunities:
  - kind: discussion
    description: "在原线程建议解耦：带 Cc stable 的越界读修复不应等待大系列，请 Aaron 单独重发 v2 走 sched/urgent，并请 Valentin 就处置方式表态"
  - kind: testing
    description: "在 CONFIG_KASAN 内核上用 isolcpus=<未知flag>（不带尾随逗号）启动，确认是否报越界读及 housekeeping 掩码是否被错误设置，把复现结果回帖（当前线程完全没有复现数据）"
  - kind: review
    description: "v16 发出后核对该修复是否真的排在改写同一解析逻辑的补丁之前、bisect 基线是否成立、Fixes 与 Cc stable 是否如承诺保留"
source_email_count: 1
related_articles:
  - "sched-20260802-001"
tags:
  - affinity
  - topology
  - nohz
---
