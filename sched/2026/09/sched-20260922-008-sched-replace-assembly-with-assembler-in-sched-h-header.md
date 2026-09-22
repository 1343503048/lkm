# sched: Replace __ASSEMBLY__ with __ASSEMBLER__ in sched.h header

## TL;DR
Thomas Huth 把 `<uapi/linux/sched.h>`（及 perf 工具里的同名 uapi 头）里的 `__ASSEMBLY__` 守卫宏标准化为 `__ASSEMBLER__`，消除用户态/内核态切换时的困惑。补丁当日即被合入 `tip/sched/core`（commit `a9b3c7570564`）。

## 背景与问题
GCC/Clang 编译汇编时自动定义 `__ASSEMBLER__`，而 `__ASSEMBLY__` 只是内核 Makefile 里额外定义的宏，两者语义易混，尤其在用户态与内核态代码间切换、或处理本应使用 `__ASSEMBLER__` 的 uapi 头时。

## 技术方案
把 `#ifndef __ASSEMBLY__` 改为 `#ifndef __ASSEMBLER__`，仅涉及 `include/uapi/linux/sched.h` 与 `tools/perf/trace/beauty/include/uapi/linux/sched.h` 各 1 行。作者说明这是从更早的一个大补丁中拆出以便 review。

## 版本演进与当前进展
v1 当日发出，当日即由 tip-bot 合入 `tip/sched/core`（`a9b3c7570564de40acb0998ab85c89d546b2122f`，作者 Thomas Huth，提交者 Ingo Molnar）。

## Maintainer 意见与讨论焦点
无公开 review 讨论，Ingo Molnar 直接收取。无争议。

## 合入评估
likelihood=merged。已合入 `tip/sched/core`。blocking_issues 无。

## 效果评估
无性能影响，纯头文件宏标准化（消除语义混淆）。

## 我可以参与的点
当前阶段暂无明显参与空间，可持续观察后续版本（若作者继续推进更大范围的 `__ASSEMBLY__` → `__ASSEMBLER__` 清理）。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260922064641.61120-1-thuth@redhat.com/
- tip commit: https://git.kernel.org/tip/a9b3c7570564de40acb0998ab85c89d546b2122f

---
id: sched-20260922-008
date: '2026-09-22'
subject: 'sched: Replace __ASSEMBLY__ with __ASSEMBLER__ in sched.h header'
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: '<20260922064641.61120-1-thuth@redhat.com>'
lore_url: 'https://lore.kernel.org/all/20260922064641.61120-1-thuth@redhat.com/'
authors:
  - 'Thomas Huth'
maintainers_involved:
  - 'Ingo Molnar'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260922064641.61120-1-thuth@redhat.com>'
    date: '2026-09-22'
    summary: '将 uapi sched.h 的 __ASSEMBLY__ 守卫标准化为 __ASSEMBLER__'
    review_outcome: '当日合入 tip/sched/core'
upstream_commit: 'a9b3c7570564de40acb0998ab85c89d546b2122f'
fixes_commit: null
merged_branch: 'tip/sched/core'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '已合入，无后续动作'
contribution_opportunities: []
generated_at: '2026-09-23T00:00:00'
source_email_count: 2
related_articles: []
tags:
  - sched_debug
---