# sched/wait: Clarify WF_SYNC wakeup semantics

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260923-005：Shubhang Kaushik 的 WF_SYNC 唤醒语义文档修复 v3（单枚）——在 `WF_SYNC` 标志定义旁内联注释契约、删除 waitqueue 过时措辞，获 Peter Zijlstra 认可。
- sched-20260925-002：tip-bot 首次发出合入通知——commit e4c353c3933968fe8efecb269fdbe3baa1d1ddd0 已进 tip/sched/core。
- sched-20260926-001（今天）：tip-bot 再次发出合入通知 commit 627ea30aca3b309af40cdd07a35eb1027ba4a0bc，subject 由「sched:」调整为「sched/wait:」；原因是原 commit 丢失了作者的 SOB（因补丁 commit message 里的 `---` 分隔符），Shrikanth Hegde 发现并指出，Ingo Molnar 手动补回 `Signed-off-by: Shubhang Kaushik (Ampere) <sh@gentwo.org>`。

## 背景与问题

（承接 sched-20260925-002）同步 waitqueue 唤醒的注释长期声称「同步 wakee 不会被迁移到其他 CPU」，但调度器唤醒路径并不保证这一点。`WF_SYNC` 只是建议性提示：调用者预期 waker 很快调度离开；调度类可用它做放置或抢占，但调用者不能依赖它阻止迁移、保持 CPU 局部性或让 wakee 下一个运行。错误的文档会误导使用方做出不成立的假设。

今天的新进展不是正文而是元数据问题：首次合入的 commit 缺了作者的 Signed-off-by，后人需要知道「为什么会有第二次合入通知」。

## 技术方案

（承接 sched-20260925-002）把契约放到 `WF_SYNC` 标志定义旁（`kernel/sched/sched.h`），删除 `kernel/sched/wait.c` 的过时措辞，带锁 helper 引用不带锁变体。合入 diffstat：kernel/sched/sched.h 与 kernel/sched/wait.c 共 12 insertions(+), 19 deletions(-)。代码内容今天无变化，变化只在 commit 元数据（subject 带 `sched/wait:` 前缀 + 补回 SOB）。

## 版本演进与当前进展

- v3（2026-09-22，`<20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org>`）：单枚，收敛为 WF_SYNC 定义旁内联注释。
- 09-25：首次合入 tip/sched/core（commit e4c353c3933968fe8efecb269fdbe3baa1d1ddd0，见 sched-20260925-002）。
- 09-26：tip-bot 对同一改动再次发合入通知，commit 627ea30aca3b309af40cdd07a35eb1027ba4a0bc（CommitterDate 09-25 20:32 +02:00），Committer/作者 SOB 完整。

## Maintainer 意见与讨论焦点

- **Shrikanth Hegde**（`<31c9b2b9-7532-4de5-b0c4-bc283a931cb3@linux.ibm.com>`）：指出首次合入的 commit 缺 Shubhang 的 SOB，判断原因「Likely caused by the --- tag in his commit message」——补丁 body 里的 `---` 分隔符让应用工具把后面的 SOB 段当作 diff 分离符吞掉了。
- **Ingo Molnar**（`<ara--PcvTbdm1zbs@gmail.com>`）：确认已补上 SOB，原话 "I've added Shubhang's SOB which is missing from the commit... Which I suppose got lost in some patch application mishap, because it's present in the original."
- 无 NAK、无遗留分歧；这轮讨论只涉及commit元数据完整性，不改动代码。

## 合入评估

已合入 tip/sched/core（*likelihood=merged*），最终落点 commit 627ea30aca3b309af40cdd07a35eb1027ba4a0bc。纯文档/注释修复向的内联收敛，无阻塞项。

## 效果评估

文档/注释修复，无 benchmark 或运行时数据；效果体现在 API 契约表述的准确性上，属静态可证。暂无效果数据。

## 我可以参与的点

修复已合入，当前阶段暂无明显参与空间。

## 参考链接

- lore（tip-bot 二次合入通知）: https://lore.kernel.org/all/179036141797.2819794.7397034938096207501.tip-bot2@tip-bot2/
- Ingo 补 SOB: https://lore.kernel.org/all/ara--PcvTbdm1zbs@gmail.com/
- Shrikanth 指出缺 SOB: https://lore.kernel.org/all/31c9b2b9-7532-4de5-b0c4-bc283a931cb3@linux.ibm.com/
- gitweb: https://git.kernel.org/tip/627ea30aca3b309af40cdd07a35eb1027ba4a0bc

---
id: sched-20260926-001
date: 2026-09-26
subject: "sched/wait: Clarify WF_SYNC wakeup semantics"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<179036141797.2819794.7397034938096207501.tip-bot2@tip-bot2>"
lore_url: "https://lore.kernel.org/all/179036141797.2819794.7397034938096207501.tip-bot2@tip-bot2/"
upstream_commit: "627ea30aca3b309af40cdd07a35eb1027ba4a0bc"
fixes_commit: null
merged_branch: "tip/sched/core"
current_version: v3
generated_at: "2026-09-27T01:20:00"
authors:
  - "Shubhang Kaushik (Ampere)"
maintainers_involved:
  - "Peter Zijlstra"
  - "Ingo Molnar"
patch_series:
  - version: v3
    msgid: "<20260922-sched-wf-sync-doc-v3-1-23ebe9e27bef@gentwo.org>"
    date: 2026-09-22
    summary: "单枚：WF_SYNC 定义旁内联注释 + 删除过时 waitqueue 措辞"
    review_outcome: "09-25 首次合入，09-26 因缺 SOB 重新应用为 627ea30aca3b（subject 调整为 sched/wait:）"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入 tip/sched/core，等待进入合并窗口"
contribution_opportunities: []
source_email_count: 3
related_articles:
  - "sched-20260925-002"
  - "sched-20260923-005"
  - "sched-20260918-001"
tags:
  - cfs
---