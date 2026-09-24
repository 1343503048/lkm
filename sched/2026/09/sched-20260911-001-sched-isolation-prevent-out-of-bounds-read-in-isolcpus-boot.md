# sched/isolation: Prevent out-of-bounds read in isolcpus= boot parameter parser

## TL;DR
Aaron Tomlin 修复 isolcpus= 启动参数解析器在字符串末尾无尾随逗号时的越界读（2 行加一个边界检查）。本文为增量更新，完整背景见 sched-20260910-015：独立投递的修复已按作者 09-10 的宣布折叠进 multiqueue CPU isolation v16 系列，当日缓存收到 v16 的 patch 4/9 全文，此前一直缺失的补丁正文（diff、Fixes、Cc stable、Reviewed-by）现在全部可核对。

## 背景与问题
housekeeping_isolcpus_setup() 解析 isolcpus= 时假设各 flag 以逗号分隔。若最后一个子参数（合法或非法，如 `isolcpus=unknown`）后面没有逗号，strncmp 严格匹配失败后落入「跳过未知子参数」的兜底 for 循环：该循环消费字符直到逗号或 `'\0'`，终止时 str 恰好停在字符串结尾的 NULL 上；循环之后代码无条件执行 `str++`，指针越过字符串进入未初始化内存，外层 `while (isalpha(*str))` 随后读取越界数据，可能导致未定义行为或启动异常。该问题由 sashiko-bot@kernel.org 报告，修复指向 `Fixes: 3662daf023500 ("sched/isolation: Allow "isolcpus=" to skip unknown sub-parameters")` 并 Cc stable。

## 技术方案
补丁仅 2 行：在内层循环与 `str++` 之间加 `if (!*str) break;`——到达字符串末尾时干净退出解析循环，不再越过 NULL 终结符。diff 见 kernel/sched/isolation.c 的 housekeeping_isolcpus_setup()，在 `pr_info("isolcpus: Skipped unknown flag %.*s\n", ...)` 之后插入边界检查。

## 版本演进与当前进展
*current_version: v16（指所属 multiqueue CPU isolation 系列的版本；修复本身的代码内容相对独立投递版无变化）*。

- v1（2026-05-23，独立投递，msgid `<20260523210214.593704-1-atomlin@atomlin.com>`）：修复越界读，Valentin Schneider 给出 Reviewed-by，长期无进展。
- 09-10：作者宣布把修复折叠进 multiqueue CPU isolation v16 作为系列内前置补丁，承诺保留 R-b、Fixes 与 Cc stable（见 sched-20260910-015）。
- v16（09-10/09-11 入缓存）：修复以 `[PATCH v16 4/9]` 形态出现在系列中，补丁正文首次可见：Reported-by sashiko-bot、Reviewed-by Valentin Schneider、Fixes 3662daf023500、Cc stable 齐全。注意实际位置是系列第 4 个补丁，而非 sched-20260910-015 中推测的「patch 01」。

## Maintainer 意见与讨论焦点
- Valentin Schneider：早在独立投递阶段已给 Reviewed-by，v16 中保留。
- 本日缓存内没有对 v16 4/9 的新讨论；该系列整体（multiqueue CPU isolation，9 个补丁、已迭代 16 版）的维护者表态情况在当日缓存中不可见，未获取到。

## 合入评估
*likelihood=medium*：修复本身内容简单、带 R-b 与 stable 标记，但合入时点仍绑定在迭代了 16 版尚未进树的 v16 系列上。*blocking_issues*：与 sched-20260910-015 相同——修复跟着一个尚未被收取的大系列走，bisect 基线取决于系列排序；Valentin 对「折叠进 v16」处置方式本身的表态仍未获取到。*next_action*：跟踪 v16 系列在 sched 树的收取情况，确认 4/9 的 bisect 位置与其 Fixes 指向的 commit 顺序成立。

## 效果评估
暂无效果数据：线程内没有复现报告或启动异常日志，sashiko-bot 的原始报告内容在缓存中未获取到（仅见 Reported-by 标签）。

## 我可以参与的点
- kind=testing：在 CONFIG_KASAN 内核上用 `isolcpus=<未知flag>`（不带尾随逗号）启动，确认修复前后是否复现越界读，把结果回帖到 v16 线程——该线程至今没有人类贴出的复现数据。
- kind=review：核对 v16 系列 4/9 的排序是否满足其 Fixes: 3662daf023500 的 bisect 基线（修复必须先于改写同一解析逻辑的补丁）。

## 参考链接
- v16 4/9 补丁（当日缓存真实 msgid）：https://lore.kernel.org/all/20260910164237.500196-5-atomlin@atomlin.com/
- 原独立修复 v1：https://lore.kernel.org/all/20260523210214.593704-1-atomlin@atomlin.com/
- Fixes 指向：3662daf023500（"sched/isolation: Allow "isolcpus=" to skip unknown sub-parameters"，hash 取自补丁正文）
- v16 系列 cover letter：未获取到（未入当日缓存）

---
id: sched-20260911-001
subject: 'sched/isolation: Prevent out-of-bounds read in isolcpus= boot parameter parser'
date: '2026-09-11'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260910164237.500196-1-atomlin@atomlin.com>'
lore_url: 'https://lore.kernel.org/all/20260910164237.500196-5-atomlin@atomlin.com/'
authors:
  - 'Aaron Tomlin'
maintainers_involved:
  - 'Valentin Schneider'
current_version: v16
patch_series:
  - version: v1
    msgid: '<20260523210214.593704-1-atomlin@atomlin.com>'
    date: 2026-05-23
    summary: '独立投递修复 isolcpus= 解析器越界读；补丁正文当时未入缓存。'
    review_outcome: 'Valentin Schneider 给出 Reviewed-by；此后长期无进展，09-10 作者宣布折叠进 v16 系列。'
  - version: v16 (系列内 4/9)
    msgid: '<20260910164237.500196-5-atomlin@atomlin.com>'
    date: 2026-09-11
    summary: '修复作为 multiqueue CPU isolation v16 的第 4 个补丁出现；2 行边界检查，R-b/Fixes/Cc stable 齐全，补丁正文首次入缓存。'
    review_outcome: '当日缓存内无对 4/9 的新讨论；v16 系列整体评审状态未获取到。'
upstream_commit: null
fixes_commit: '3662daf023500'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '合入时点绑定在迭代 16 版尚未合入的 multiqueue CPU isolation 系列上'
    - 'Valentin Schneider 对「折叠进 v16」处置方式未表态（承 sched-20260910-015）'
  next_action: '跟踪 v16 系列收取情况；核对 4/9 的 bisect 基线与 Fixes 顺序'
contribution_opportunities:
  - kind: testing
    description: '在 CONFIG_KASAN 内核用无尾随逗号的 isolcpus= 未知 flag 启动，回帖复现结果'
  - kind: review
    description: '核对 v16 系列 4/9 的排序是否满足 Fixes bisect 基线'
generated_at: '2026-09-14T11:35:00'
source_email_count: 1
related_articles:
  - 'sched-20260910-015'
  - 'sched-20260802-001'
tags:
  - affinity
  - topology
  - nohz
---
