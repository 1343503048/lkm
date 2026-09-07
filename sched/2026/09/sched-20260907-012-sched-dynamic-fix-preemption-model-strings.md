# sched: dynamic: Fix preemption model strings

## TL;DR

本文为增量更新，完整背景见 sched-20260905-004（Mark Rutland 的单补丁，修 PREEMPT_DYNAMIC 简化后 `preempt_modes[]` 与被删枚举值不同步，导致栈回溯里的抢占模型字符串错位、`/sys/kernel/debug/sched/preempt` 输出为空；Peter Zijlstra 已在 09-02 收进 `tip/sched/core`）。本日新增的只是**第一个运行时功能验证**：Mete Durlu（IBM）在 s390 上实测 `preempt` 节点读写，输出已正确（`echo full > preempt` 后读回 `(full) lazy`，`echo lazy > preempt` 后读回 `full (lazy)`），并给出 `Tested-by`。合入状态没有变化——补丁本日早已在 tip，这个 tag 不会出现在那个 commit 里。

## 背景与问题

前作已把根因写清：`9650ce11f2e3` ("sched: dynamic: Simplify preempt model accessors") 删掉了 `preempt_dynamic_none` / `preempt_dynamic_voluntary` 两个枚举值，但 `const char *preempt_modes[]` 仍保留 4 个字符串，下标与枚举不再一一对应，于是 `preempt_model_str()` 打印错模型、`sched_dynamic_show()` 输出空内容；报告人是 Jinjie Ruan（华为）。

需要区分的是：本日均无涉及**调度行为**的改动，修的全是「字符串/展示」这一层。`preempt` 节点是 PREEMPT_DYNAMIC 简化后仅剩 full/lazy 两个模型的呈现面，s390 因为支持 `CONFIG_ARCH_HAS_PREEMPT_LAZY` 恰好是唯一能同时看到两个模型串的架构之一，所以第一次运行时验证自然出自 IBM。

## 技术方案

补丁本体（+3/-9，`kernel/sched/core.c` 1 行、`kernel/sched/debug.c` -8/+2）见前作；本日邮件不含任何代码变化，只有 Mete Durlu 贴出的交互记录：

```
$ echo full > preempt
$ cat preempt
(full) lazy

$ echo lazy > preempt
$ cat preempt
full (lazy)
```

两组输出说明两件事：`sched_dynamic_show()` 不再返回空串；带括号的串标注的是**当前生效的模型**，另一个作为可选项随后列出——这与修复前「数组下标错位 → 起始索引算错 → 整个列表被跳过」的表现正好互为反证。作者的评语是 `The sched_dynamic_show() output looks correct now, and the code looks much nicer without those conditional indices.`

## 版本演进与当前进展

- 09-02 11:16 Mark Rutland 投递（无版本号，一次性投递）；同日 12:54 Peter Zijlstra 以 committer 身份合入 `tip/sched/core`。该 commit hash（`ef9293b3b797...`）来自前作 sched-20260905-004 的记录（tip-bot2 通知），**本日邮件本身不含任何 commit hash**。
- 09-05 kernel test robot 报 74 个 config 全 BUILD SUCCESS（跨 22+ 架构），但那只是编译级验证。
- 09-07 03:28 Mete Durlu（IBM）在 s390 上完成运行时验证并附 `Tested-by: Mete Durlu <meted@linux.ibm.com>`——这是该修复的第一份行为级证据。
- 由于入树在前、验证在后，本线程中未见维护者用带 Tested-by 的版本重写 commit 的记录（未获取到）。

## Maintainer 意见与讨论焦点

- **Mete Durlu（linux.ibm.com）**：无异议、无修改要求，只是补测试并主动送 tag（`Feel free to put my tested by.`）。这条回帖的实际作用是给「入 tip 的 trivial fix」补上运行时覆盖面。
- **Peter Zijlstra / Mark Rutland**：本日未再发言。
- 讨论焦点因此从「怎么修」转到「验证还缺哪些架构」：`preempt_modes[]` 与 `enum preempt_dynamic` 的一致性只在有 lazy/preempt 动态切换的 arch 上才会暴露，目前线程里只有 s390 的一份实测；而该 commit 已被 steal governor v12 直接用作 `tip/sched/core` 的 rebase 基线（前作已记录），意味着它会随那条主线被大量二次测试顺带覆盖。

## 合入评估

`likelihood=merged`。已进 `tip/sched/core`（hash `ef9293b3b797228fead10b55ed6bfb99bb7976b4`，取自前作记录），本日的 s390 `Tested-by` 属于入树后的追加信任票，不构成新的合入条件。

`severity=low`：受影响的是可观测性（回溯里的模型字符串、debugfs 展示），不改调度决策。卡点：无。剩下的是随 sched/core 进 mainline 的时间点，以及 `Fixes: 9650ce11f2e3` 是否走 -stable——本线程仍未出现 `Cc: stable`，由维护者决定。

## 效果评估

无性能数据，属正确性修复。本日新增的效果证据是行为级的两条读回结果（`(full) lazy` / `full (lazy)`），修复前同一节点输出为空、回溯里的抢占模型字符串错位。加上前作记录的 74 config 构建通过，目前该修复的验证矩阵是「编译面全覆盖 + 运行时仅 s390」。

## 我可以参与的点

- **补运行时覆盖，成本几乎为零**：该 commit 已在 tip，`Tested-by` 仍可回馈（后续若有 -stable 回合，测试记录会提高它的回合优先级）。在 arm64/x86 上按 Mete 的同样方法过一遍 `preempt` 节点读写 + 一次栈回溯（`echo 1 > /proc/sysrq-trigger` 或 `cat /proc/<pid>/stack`）确认模型串不再错位即可；0day 那封邮件也明说后续还会测更多 config，覆盖仍有空间。
- **把这条坑固化成内部回归检查项**：只要删过 `enum preempt_dynamic` 的取值，就必须同步收缩 `preempt_modes[]`，否则是静默的字符串错位（不 panic、不报错，只影响诊断）。OLK 分支若做过 PREEMPT_DYNAMIC / 抢占模型相关的裁剪或简化，直接对照检查这两处是否一一对应；本线程的原始触发者是华为内部的报告（`Reported-by: Jinjie Ruan`），说明我们已经是这条链上的贡献方，把它转成 checklist 是顺理成章的收尾。
- **可顺带补的接口一致性检查**：`preempt` 现在只剩 full/lazy 两个取值，但写接口是否对 `none`/`voluntary` 之类的历史输入给出合理报错、`cat` 在无 `ARCH_HAS_PREEMPT_LAZY` 的平台上的输出形态，本线程都没讨论过。若自家产品要给用户暴露抢占模型切换，这些边界值得先测清楚再决定要不要回馈上游。

## 参考链接

- 相关文章/系列：
  - [[sched-20260905-004]] 前作：根因、diff 与 tip 合入记录。
  - [[sched-20260903-013]] PREEMPT_DYNAMIC 简化 v2（引入该不一致的那轮改动）。
  - [[sched-20260902-002]] PREEMPT_DYNAMIC 简化系列首发记录。
- 原始补丁: https://lore.kernel.org/all/20260902101637.232129-1-mark.rutland@arm.com/
- tip-bot2 合入通知（前作引用）: https://lore.kernel.org/all/178834676769.3717435.18409512288803533130.tip-bot2@tip-bot2/
- 本日 Mete Durlu 的 s390 验证: https://lore.kernel.org/all/2eaa56ab-7013-4fc1-99f0-db9c7e4b5c5f@linux.ibm.com/
- 相关代码/commit：
  - `ef9293b3b797` "sched: dynamic: Fix preemption model strings"（hash 取自前作记录）
  - `9650ce11f2e3` ("sched: dynamic: Simplify preempt model accessors")
  - `kernel/sched/core.c` `preempt_modes[]` / `preempt_model_str()`；`kernel/sched/debug.c` `sched_dynamic_show()`
- stable backport: 未获取到

---
id: sched-20260907-012
date: '2026-09-07'
subject: 'sched: dynamic: Fix preemption model strings'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: '<20260902101637.232129-1-mark.rutland@arm.com>'
lore_url: https://lore.kernel.org/all/2eaa56ab-7013-4fc1-99f0-db9c7e4b5c5f@linux.ibm.com/
upstream_commit: 'ef9293b3b797228fead10b55ed6bfb99bb7976b4'
fixes_commit: '9650ce11f2e3'
merged_branch: 'tip/sched/core'
current_version: v1
generated_at: '2026-09-07'
authors:
- Mark Rutland
maintainers_involved:
- Peter Zijlstra
- Mete Durlu
patch_series:
- version: v1
  msgid: <20260902101637.232129-1-mark.rutland@arm.com>
  date: '2026-09-02'
  summary: 'preempt_modes[] 收缩为 "full","lazy",NULL 以与删除 none/voluntary 后的枚举对齐；sched_dynamic_show() 去掉按 CONFIG_PREEMPT_RT/CONFIG_ARCH_HAS_PREEMPT_LAZY 计算的起始下标与预数组长度的循环，改为遇到 NULL 即终止。+3/-9。本日邮件不含代码变化，仅 Mete Durlu 在 s390 的运行时验证。'
  review_outcome: 'Peter Zijlstra 09-02 直接合入 tip/sched/core；09-05 0day 报 74 config BUILD SUCCESS；本日 09-07 Mete Durlu 给 Tested-by（preempt 节点读回 (full) lazy / full (lazy) 均正确）。'
merge_assessment:
  likelihood: merged
  blocking_issues:
  - 无：已入 tip/sched/core，本日仅是追加测试证据
  - 本线程仍无 Cc: stable，9650ce11f2e3 的 -stable 回合情况未获取到
  next_action: 跟踪其随 sched/core 进 mainline 的时点；在自己关注的 arch 上补 preempt 节点与回溯字符串的运行时 Tested-by
contribution_opportunities:
- kind: testing
  description: 在 arm64/x86 上重复 Mete Durlu 的 preempt 节点读写与栈回溯模型串检查，补 s390 之外的运行时覆盖并可回馈 Tested-by
- kind: new_patch
  description: 内部分支若做过 preempt 模型枚举/访问器简化，检查 preempt_modes[] 与 enum preempt_dynamic 是否仍一一对应，把该检查固化为回归项
source_email_count: 1
related_articles:
- sched-20260905-004
- sched-20260903-013
- sched-20260902-002
tags:
- preempt
- sched_debug
---
