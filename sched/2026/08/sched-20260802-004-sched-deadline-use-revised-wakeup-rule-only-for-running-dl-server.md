# scheduler fix

# sched/deadline: revised wakeup rule 仅用于 running 状态的 dl_server（已进 tip/sched/urgent）

## TL;DR

Ingo Molnar 于 2026-08-02 向 Linus 发出 `sched-urgent-2026-08-02` pull request，仅含一个补丁：Gabriele Monaco 修正 deferred DL server 的唤醒逻辑，让它真正做到"延迟唤醒"。改动 1 文件 2 增 1 删，**已合入 tip/sched/urgent，无需跟进**。

## 背景与问题

`SCHED_DEADLINE` 的 dl_server 机制用于给非 DL 任务（CFS/RT）提供带宽保障。其中 **deferred DL server**（`dl_defer`）的设计意图是：不立刻开始消耗带宽，而是推迟到确有需要时才激活，避免在系统空闲时白白占用 DL 带宽。

问题在于唤醒路径上应用了 **revised wakeup rule**。这条规则源自 DL 理论中对任务唤醒时剩余 runtime/deadline 是否需要重新初始化的判定 —— 当前主线 `kernel/sched/deadline.c` 中相关注释位于第 951 行附近，描述"重新初始化任务的 runtime 与 deadline 后，revised wakeup rule..."。

对普通 DL 实体，这条规则是正确的。但对**尚未 running 的 deferred dl_server** 无差别地套用，会导致其唤醒不再被延迟 —— 也就是说 deferred 语义被破坏，server 提前活了过来。

Pull request 中 Ingo 对该修复的一句话概括是：

> Fix wakeups of deferred DL servers to be actually deferred

"to be **actually** deferred"（真正做到延迟）这个措辞本身就说明：deferred 机制此前存在名不副实的行为偏差。

严重度定为 medium：不涉及崩溃或死锁，但影响 DL 带宽的实际分配行为，属于语义正确性问题，且被判定为需要走 urgent 路径而非常规 sched/core，说明维护者认为不宜等到下个合并窗口。

## 技术方案

补丁标题即方案：**`sched/deadline: Use revised wakeup rule only for running dl_server`** —— 给 revised wakeup rule 的应用加上"仅当 dl_server 处于 running 状态"的前置条件。

改动规模：

```
 kernel/sched/deadline.c | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)
```

净增一行、修改一行，是典型的条件收窄型修复。

对照当前主线 `kernel/sched/deadline.c`，与 deferred server 相关的关键位置包括第 1034 行的 `} else if (dl_server(dl_se) && dl_se->dl_defer) {` 分支，以及第 1137-1140 行 `dl_server_min_res` 与 `dl_server_timer()` 附近的 defer timer 处理逻辑。修复应落在唤醒路径上判定是否套用 revised rule 的分支处。

**注意**：pull request 邮件按惯例只包含 diffstat 与 shortlog，**不含补丁正文**。因此本文无法给出具体的条件表达式，也不清楚补丁的原始提交讨论中是否存在过备选方案 —— 当日邮件中未捕获到该补丁的原始提交线程。

## 版本演进与当前进展

**已完成合入流程**，无版本迭代记录（当日邮件仅捕获到 pull request，未捕获到原始 patch 提交与 review 线程）。

进展节点：

- Commit `1842bf97af109f5ebf830175c9725bf81ebb78b1` 已在 `tip/sched/urgent`；
- Ingo Molnar 于 2026-08-02 15:51（北京时间）以 tag `sched-urgent-2026-08-02` 向 Linus 发出 pull request；
- 拉取地址：`git://git.kernel.org/pub/scm/linux/kernel/git/tip/tip.git`。

本次 pull request **只含这一个补丁**，说明当前 sched 侧没有其他积压的紧急修复 —— 这本身是一个有用的信号：调度子系统近期状态平稳。

## Maintainer 意见与讨论焦点

**无争议，无分歧。**

Ingo Molnar 作为 tip 树维护者的动作本身即最强背书：补丁能进入 `sched/urgent` 分支并被打包送往 Linus，意味着它已通过 tip 树的 review 流程。Ingo 在 pull request 中未附加任何保留意见或说明性备注，正文仅有标准的拉取指引与 shortlog。

需要如实说明的**信息盲区**：当日邮件流中**没有捕获到该补丁的原始提交与 review 讨论**（可能发生在 8 月 2 日之前）。因此：

- 无法给出 review 过程中是否有人提出过异议；
- 无法确认是否讨论过其他修法；
- 无法确认是否有 `Fixes:` 标签指向具体引入 commit（`fixes_commit` 字段填 null 表示未获取到，而非确认不存在）。

这些空白不影响合入结论 —— 已进 urgent 分支是既成事实 —— 但影响对问题历史的完整理解。

## 合入评估

**已合入（merged）**，评估阶段结束。

- 分支：`tip/sched/urgent`
- Commit：`1842bf97af109f5ebf830175c9725bf81ebb78b1`
- Pull request tag：`sched-urgent-2026-08-02`
- 剩余流程：Linus 拉取即进主线，属于常规操作，无阻塞因素。

进 `urgent` 而非 `core` 分支意味着维护者判定该修复不应等待下一个合并窗口。**未见 stable 回合信息** —— pull request 中没有 stable 相关标注，当日也未捕获到 stable-commit bot 回帖。如果引入该问题的 commit 已存在于已发布内核中，后续可能会有独立的 stable 回合动作，值得留意。

## 效果评估

**暂无效果数据。**

Pull request 邮件不包含性能数据、benchmark 结果或复现验证 —— 这是 pull request 的常规形式，不是本补丁的缺陷。唯一可提取的效果描述是行为层面的定性说明："deferred DL server 的唤醒现在真正被延迟了"。

由于未捕获到原始提交线程，无法得知作者在提交时是否附带了复现步骤或量化数据。如需了解实际影响幅度（例如 deferred server 提前激活对 CFS 任务带宽的挤占程度），需回溯该补丁的原始提交邮件。

## 我可以参与的点

**当前阶段暂无参与空间。**

补丁已通过 review、已进 tip/sched/urgent、已送 Linus —— 流程上没有任何可介入的环节，`contribution_opportunities` 如实填为空数组。

若对 dl_server 机制本身有兴趣，可考虑的**间接方向**（非本系列的参与点，仅作跟进建议）：

- 回溯该补丁的原始提交线程（commit `1842bf97af10` 的 lore 讨论），了解 deferred server 的设计权衡；
- 关注该修复是否需要 stable 回合 —— 若引入 commit 已在发布版本中而无人提出回合，这是一个可以提问的空白点；
- deferred DL server 是相对新且讨论活跃的机制，后续版本大概率还有调整，可作为长期跟踪对象。

## 参考链接

- lore thread: 未获取到（IMAP 邮件头未暴露原始 Message-ID）
- pull request: `git://git.kernel.org/pub/scm/linux/kernel/git/tip/tip.git sched-urgent-2026-08-02`
- tip-bot commit: `1842bf97af109f5ebf830175c9725bf81ebb78b1`（tip/sched/urgent）
- stable backport: 未获取到

---
subject: "scheduler fix"
id: sched-20260802-004
date: 2026-08-02
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "unknown"
lore_url: "unknown"
authors: [Gabriele Monaco]
maintainers_involved: [Ingo Molnar, Linus Torvalds]
current_version: v1
patch_series:
  - version: v1
    msgid: "<uid-15025@qq-imap>"
    date: 2026-08-02
    summary: "修正 deferred DL server 的唤醒行为：revised wakeup rule 只应用于已处于 running 状态的 dl_server，使 deferred DL server 的唤醒真正被延迟。"
    review_outcome: "已通过 tip 树 review 并进入 sched/urgent，由 Ingo Molnar 发起 pull request 送往 Linus。"
upstream_commit: "1842bf97af109f5ebf830175c9725bf81ebb78b1"
fixes_commit: null
merged_branch: "tip/sched/urgent"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "无需额外动作；已在 sched-urgent-2026-08-02 tag 中送 Linus，等待合入主线即可。"
contribution_opportunities: []
generated_at: "2026-08-03T00:15:00"
source_email_count: 1
related_articles: []
tags: [deadline, dl_server]
---
