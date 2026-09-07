# sched: dynamic: Fix preemption model strings

## TL;DR

Mark Rutland 的单补丁修掉 PREEMPT_DYNAMIC 简化留下的收尾问题：枚举值 `preempt_dynamic_none` / `preempt_dynamic_voluntary` 被删掉后 `preempt_modes[]` 没同步，导致栈回溯里的抢占模型字符串错位、`/sys/kernel/debug/sched/preempt` 输出为空。Peter Zijlstra 在补丁发出约一个半小时后即合入 `tip/sched/core`（`ef9293b3b797`）；本日的邮件是 0day 的构建结果——74 个 config 全部 BUILD SUCCESS。

## 背景与问题

`9650ce11f2e3` ("sched: dynamic: Simplify preempt model accessors") 简化抢占模型访问器时删除了 `preempt_dynamic_none` 与 `preempt_dynamic_voluntary` 两个枚举值，但 `const char *preempt_modes[]` 仍是 `"none", "voluntary", "full", "lazy", NULL`。由于数组下标要与枚举取值对齐，`preempt_model_str()` 与 `sched_dynamic_show()` 从此取到错误的字符串：回溯里打印出错误的抢占模型，`/sys/kernel/debug/sched/preempt` 甚至输出空内容。问题由 Jinjie Ruan（华为）报告。

## 技术方案

- `preempt_modes[]` 收缩为 `"full", "lazy", NULL`，与仅剩的两个枚举值对齐。
- 由于 `CONFIG_PREEMPT_DYNAMIC` 现在依赖 `CONFIG_ARCH_HAS_PREEMPT_LAZY`、只剩 full/lazy 两个模型，`sched_dynamic_show()` 不再需要跳过任何字符串：删掉按 `IS_ENABLED(CONFIG_PREEMPT_RT) || IS_ENABLED(CONFIG_ARCH_HAS_PREEMPT_LAZY)` 计算的起始下标 `i` 和先数数组长度的循环，改为「遇到 NULL 终止」的直接遍历。
- `kernel/sched/core.c` 1 行、`kernel/sched/debug.c` -8/+2，共 +3/-9。

## 版本演进与当前进展

- 09-02 11:16 (UTC+1) Mark Rutland 投递（无版本号，一次性投递，Cc Mete Durlu / Peter Zijlstra / Shrikanth Hegde）；同日 12:54 Peter Zijlstra 以 committer 身份合入 tip。
- 09-05 11:12 kernel test robot 报 `[tip:sched:core] BUILD SUCCESS ef9293b3b797228fead10b55ed6bfb99bb7976b4`：74 个 config 构建通过、4 个跳过，覆盖 alpha/arc/arm/arm64/csky/hexagon/i386/loongarch/m68k/microblaze/mips/nios2/openrisc/parisc/powerpc/riscv/s390/sh/sparc/sparc64/um/x86_64/xtensa，gcc-11/14/16.1.0 与 clang-17/19/20/22/24；elapsed time 3774m，并说明「后续几天可能还会测更多 config」。
- 09-07 Mete Durlu（IBM）在 s390 上做了功能验证并给出 `Tested-by`：`echo full > preempt` 后读回 `(full) lazy`，`echo lazy` 后读回 `full (lazy)`，认为输出已正确、去掉条件索引后的代码更干净。
- 本日邮件本身不含新代码，是纯构建/合入进展。该 commit 还被 steal_governor v12 明确用作 rebase 基线（cover 写「tip/sched/core at commit: 'ef9293b3b797 (...)'」），说明它已成为该主线的落脚点。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：未回帖讨论内容，直接以 committer 身份收进 `tip/sched/core`（CommitterDate 2026-09-02 12:54 +02:00），从投递到入树约 1.5 小时——对这类「上次简化留下的字符串错位」他按 trivial fix 处理。
- **Mete Durlu（linux.ibm.com）**：09-07 提供 s390 实测与 `Tested-by`，但这是在入树之后，因此该 tag 不会出现在 `ef9293b3b797` 的 commit message 里（正文中未见后续更新）。
- 正文中未见对实现方式的异议：唯一的意见来自原作者自述的因果说明（枚举删了、数组忘了改）。
- 报告者 **Jinjie Ruan（华为）** 的 `Reported-by` 说明这条不一致是华为侧测出来的，属外部测试对 PREEMPT_DYNAMIC 简化的直接回馈。

## 合入评估

**likelihood: likely（实际已合入）。** 已在 `tip/sched/core`，`upstream_commit = ef9293b3b797228fead10b55ed6bfb99bb7976b4`，0day 跨 22 个架构 74 config 构建全通过，s390 上运行时输出也被确认正确。

卡点：无。剩下的只是随 sched/core 进入主线 merge window 的时间点，以及 `Fixes: 9650ce11f2e3` 是否会走 -stable（本邮件线程里未出现 `Cc: stable`，是否 -stable 由维护者决定，正文中未提及）。

## 效果评估

无性能数据，属正确性修复。可观测的效果证据：0day 的 74 config BUILD SUCCESS；Mete Durlu 的 s390 行为验证显示 `/sys/kernel/debug/sched/preempt` 现在能正确打印 `(full) lazy` / `full (lazy)`（修复前该文件输出为空、回溯里的模型字符串错误）。

## 我可以参与的点

- 这是一条典型的「回合前先看是否踩到同一坑」的补丁：若 OLK-6.6 或内部内核做过 `preempt动态切换 / 9650ce11f2e3` 相关的 PREEMPT_DYNAMIC 简化，务必检查 `preempt_modes[]` 与 `enum preempt_dynamic` 是否仍然一一对应——只要删过枚举值，就会出现回溯字符串错位这种静默错误。
- 低成本可回馈上游的点：在自己关注的 config 组合（尤其 `PREEMPT_RT=n/y`、`ARCH_HAS_PREEMPT_LAZY` 各种开关）下过一遍 `/sys/kernel/debug/sched/preempt` 读写与 `preempt_model_str()` 回溯输出，缺的 arch 覆盖可以补 `Tested-by`；0day 邮件里明说「后续几天可能还会测更多 config」，还有空间。
- 若报告人来自华为内部（`Reported-by: Jinjie Ruan`），可以顺着这条线把「简化后 PREEMPT_DYNAMIC 的字符串/接口一致性」整理成内部回归检查项，避免同类问题在回合时重复出现。
- 与调度器其他日报内容关联：该 commit 是 steal_governor v13/v12 系列的 rebase 基线，跟踪该系列时可以直接把它当作 tip/sched/core 的时间锚点。

## 参考链接

- 相关文章/系列：
  - [[sched-20260903-013]] PREEMPT_DYNAMIC 简化 v2 0/6。
- 原始补丁：https://lore.kernel.org/all/20260902101637.232129-1-mark.rutland@arm.com/
- tip 合入通知（tip-bot2）：https://lore.kernel.org/all/178834676769.3717435.18409512288803533130.tip-bot2@tip-bot2/
- 本日 0day 构建结果：https://lore.kernel.org/all/202609051102.q7DwMELZ-lkp@intel.com/
- Mete Durlu 的 s390 验证：https://lore.kernel.org/all/2eaa56ab-7013-4fc1-99f0-db9c7e4b5c5f@linux.ibm.com/
- 相关代码/commit：
  - `ef9293b3b797` "sched: dynamic: Fix preemption model strings"
  - `kernel/sched/core.c` `preempt_modes[]` / `preempt_model_str()`
  - `kernel/sched/debug.c` `sched_dynamic_show()`
  - 被修复的 commit：`9650ce11f2e3` ("sched: dynamic: Simplify preempt model accessors")
---
id: sched-20260905-004
date: '2026-09-05'
subject: 'sched: dynamic: Fix preemption model strings'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: '<20260902101637.232129-1-mark.rutland@arm.com>'
lore_url: https://lore.kernel.org/all/20260902101637.232129-1-mark.rutland@arm.com/
upstream_commit: 'ef9293b3b797228fead10b55ed6bfb99bb7976b4'
fixes_commit: '9650ce11f2e3'
merged_branch: 'tip/sched/core'
current_version: v1
generated_at: '2026-09-07'
authors:
- Mark Rutland
maintainers_involved:
- Peter Zijlstra
patch_series:
- 'sched: dynamic: Fix preemption model strings'
merge_assessment:
  likelihood: merged
  blocking_issues:
  - '无：已合入 tip/sched/core 并通过 74 config 构建'
  next_action: '跟踪其随 sched/core 进入 mainline；确认 9650ce11f2e3 是否需要 -stable'
contribution_opportunities:
  - '在 OLK-6.6 回合侧检查 preempt_modes[] 与 enum preempt_dynamic 是否错位'
  - '补 PREEMPT_RT / ARCH_HAS_PREEMPT_LAZY 各组合下的 preempt 接口回归与 Tested-by'
source_email_count: 1
related_articles:
- sched-20260903-013
tags:
- preempt
- sched/core
---
