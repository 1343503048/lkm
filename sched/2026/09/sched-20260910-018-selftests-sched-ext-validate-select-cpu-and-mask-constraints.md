# selftests/sched_ext: Validate select_cpu_and mask constraints

## TL;DR
本文为增量更新，完整背景见 related_articles 中的 sched-20260909-005。09-10 01:57 Tejun Heo 回复作者以 text/plain 附件重发的那一版，"Hello, Tianyi. Applied to sched_ext/for-7.4."——这枚此前是本批四枚 sched_ext 自测补丁里**唯一被打回**的一枚，现在已进 `sched_ext/for-7.4` topic 分支。另需修正前文的一处时序判断：Tejun 09-09 02:01 那两条意见（`p->cpus_ptr` 在 PREEMPT_RCU 下的假阳性、固定 `cpu_set_t` 在 >1024 CPU 时 EINVAL）回复的是 **v1** 而非 v2（已核对其 `in_reply_to` 指向 v1 msgid），因此 v2 更可能就是针对这两条的修订版；但 v2 的 changelog 与正文都不在缓存内，无法逐条核对。

## 背景与问题
（增量文章，完整背景见 sched-20260909-005。）

`scx_bpf_select_cpu_and()` 允许 BPF 调度器把选核限制在给定 cpumask 内，此前该约束没有自测覆盖，本补丁补的就是这一块。Tejun 对 v1 提出两条实现缺陷：

1. 被测 syscall 运行在 migration disabled 状态下，开 `CONFIG_PREEMPT_RCU` 时「完成选核」与「执行校验」之间可能发生抢占，`migrate_disable_switch()` 会把 `p->cpus_ptr` 收窄到当前运行 CPU，导致合法选择被判为失败（假阳性）；应改校「请求时的 affinity」。
2. 固定大小的 `cpu_set_t` 只能表示 1024 个 CPU，`nr_cpu_ids > 1024` 的机器上即便任务只用低编号 CPU，`sched_getaffinity()` 也会返回 EINVAL；应改用动态分配掩码。

## 技术方案
v1/v2 的补丁正文均不在邮箱缓存内，用例的具体组织方式与断言层次未获取到。可从 Tejun 的 review 反推的只有：用例调用 `sched_getaffinity()` 取掩码，并在 select 之后与 `p->cpus_ptr` 比对——这正是被打回的两点。

本日确定的不是方案而是**处置结果**：Tejun 直接收取了作者以附件重发的那一版（`<CACGbirTEtYnxiZW0EnOCHbZt66=t-A_Nppp0ChRfM9G2ZD5+aQ@mail.gmail.com>`），进 `sched_ext/for-7.4`。从他 24 小时前刚提出两条明确要改的意见、24 小时后即收取同一线程的 v2 来看，v2 极可能已按意见修订（校请求 affinity + 动态掩码）——**这是推断，不是邮件内容**，v2 正文未获取到，无法证实。

## 版本演进与当前进展
- v1：`<20260906144029.848978-1-hi@tychen.cc>`（09-06，正文未缓存）。
- 09-09 02:01：Tejun 回复 **v1**（其 `in_reply_to` 与 subject "Re: [PATCH] ..." 均指向 v1，本日已核对），提出上述两条意见。
- 09-09：作者一次 `[PATCH v2 RESEND]`（`<CACGbirQ-xfWymbY9Z440sjbUseLRuaPFT17mBAwddeN7wqVi-w@mail.gmail.com>`）因 Gmail 出站折长行破坏补丁空白符，被作者本人要求维护者忽略。
- 09-09 23:25：作者说明投递问题，并以 text/plain 附件重发**内容未改动**的 v2（`<CACGbirTEtYnxiZW0EnOCHbZt66=t-A_Nppp0ChRfM9G2ZD5+aQ@mail.gmail.com>`），说明外部收到的附件能过 `b4` 与 `git am`。
- **09-10 01:57（本日）**：Tejun "Applied to sched_ext/for-7.4."。
- 当前版本 v2，状态由 under_review 转为已进 topic 分支。

## Maintainer 意见与讨论焦点
- **Tejun Heo（sched_ext 维护者）**：本批四枚自测补丁（另三枚见 sched-20260909-003 / 004 / 006）中唯一被他打回的一枚，也是最后一枚被收取的。收取时未附加任何条件、未要求再出 v3。
- 焦点已从技术转向**投递工程**：作者明确记录了 Gmail 出站会折长行并破坏补丁空白符、改用 text/plain 附件即可通过 `b4` / `git am`。Tejun 在收到干净副本后两小时内即完成收取，说明此前拖延的直接原因确实是补丁无法被正常 `git am`，而非内容分歧。
- 无 NAK、无遗留分歧。前文记录的「两条意见无人从技术角度回应」这一状态，随 v2 被收取而实际关闭——但**关闭方式是推断的**（收取即认可），线程里没有作者对两条意见的逐条书面回应。

## 合入评估
likelihood: merged。

已进 `sched_ext/for-7.4` topic 分支，剩下的只是随该分支进入 mainline 的时间问题。改动范围限于 `tools/testing/selftests/sched_ext`，不影响内核运行时行为，风险接近零。

blocking_issues：无。需要留意的是「v2 是否真的解决了 PREEMPT_RCU 假阳性与 >1024 CPU 的 EINVAL」这一点在线程中没有书面确认，若实际未解决，问题会在相应配置上跑测试时才暴露。

next_action：等 `sched_ext/for-7.4` 合入主线；作者/测试者宜在 `CONFIG_PREEMPT_RCU` 与 `nr_cpu_ids > 1024` 两类环境上实跑一次，确认 Tejun 提的两个失效模式确实已消除。

## 效果评估
无 benchmark（自测补丁）。

本线程最有价值的可复用结论仍是 Tejun 描述的那个失效模式本身：`migrate_disable_switch()` 在 `CONFIG_PREEMPT_RCU` 下会把 `p->cpus_ptr` 收窄到当前运行 CPU，因此**任何从任务侧反查 affinity 约束的测试代码都会在该配置下产生假阳性**。这条不属于本补丁，属于通用坑。

第二个可复用结论来自作者：Gmail 出站折行会破坏 patch 空白符，text/plain 附件是可验证有效的绕法。

## 我可以参与的点
- **在两类未验证配置上实跑（testing）**：`CONFIG_PREEMPT_RCU`（含 PREEMPT_RT）与 `nr_cpu_ids > 1024` 的大核数机器。前者验证假阳性是否消除，后者验证动态掩码是否真的避开 EINVAL——这两类环境在整条线程里始终无人验证，补丁却已被收取，是目前唯一实质性的验证缺口。
- **排查同类缺陷（review）**：检查 `tools/testing/selftests/sched_ext` 其余用例是否也用固定 `cpu_set_t`；若是，那是一类会在大型机上普遍失败的测试缺陷，可作为一个独立清理系列发出。
- 本补丁已合入 topic 分支，直接的评审参与空间已关闭。

## 参考链接
- Tejun Heo 的收取通知（本日邮件）: https://lore.kernel.org/all/5b44f63388fc7eab10c9b481b1a8096b@kernel.org/
- 被收取的 v2（text/plain 附件重发版）: https://lore.kernel.org/all/CACGbirTEtYnxiZW0EnOCHbZt66=t-A_Nppp0ChRfM9G2ZD5+aQ@mail.gmail.com/
- v1（线程根，Tejun 两条意见的回复对象）: https://lore.kernel.org/all/20260906144029.848978-1-hi@tychen.cc/
- Tejun Heo 对 v1 的 review: https://lore.kernel.org/all/53d04980eecb0e5f6eeea25a5cf0dcf5@kernel.org/
- 作者关于 Gmail 投递问题的说明: https://lore.kernel.org/all/CACGbirTmyi0LHZEr4xOwg_WgFALarFVPMm7JhHBbXwG10PF3KQ@mail.gmail.com/
- upstream commit: 未获取到（已进 topic 分支，缓存内无 tip-bot 回帖）
- stable backport: 不适用（selftests 改动）

---
id: sched-20260910-018
date: 2026-09-10
subject: "selftests/sched_ext: Validate select_cpu_and mask constraints"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<20260906144029.848978-1-hi@tychen.cc>"
lore_url: "https://lore.kernel.org/all/5b44f63388fc7eab10c9b481b1a8096b@kernel.org/"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.4"
current_version: v2
generated_at: "2026-09-11T01:45:00"
authors:
  - "Tianyi Chen"
maintainers_involved:
  - "Tejun Heo"
patch_series:
  - version: v1
    msgid: "<20260906144029.848978-1-hi@tychen.cc>"
    date: "2026-09-06"
    summary: "为 scx_bpf_select_cpu_and() 的 cpumask 约束新增 selftest 用例；正文未获取到。"
    review_outcome: "09-09 02:01 Tejun Heo 打回两条：CONFIG_PREEMPT_RCU 下 migrate_disable_switch() 会把 p->cpus_ptr 收窄到运行 CPU 造成假阳性，应改校请求的 affinity；固定 cpu_set_t 在 nr_cpu_ids>1024 时使 sched_getaffinity() 返回 EINVAL，应改用动态掩码。（本日核对其 in_reply_to 确为 v1，前文误记为针对 v2。）"
  - version: v2
    msgid: "<CACGbirTEtYnxiZW0EnOCHbZt66=t-A_Nppp0ChRfM9G2ZD5+aQ@mail.gmail.com>"
    date: "2026-09-09"
    summary: "正文与 changelog 未获取到。一次 [PATCH v2 RESEND] 因 Gmail 出站折长行破坏空白符被作者要求忽略，随后以 text/plain 附件重发内容未改动的 v2。"
    review_outcome: "09-10 01:57 Tejun Heo: Applied to sched_ext/for-7.4，未附加条件、未要求 v3。"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "等 sched_ext/for-7.4 合入主线；建议在 CONFIG_PREEMPT_RCU 与 nr_cpu_ids>1024 两类环境实跑，确认 Tejun 指出的两个失效模式已消除（线程中无书面确认）"
contribution_opportunities:
  - kind: testing
    description: "在 CONFIG_PREEMPT_RCU（含 PREEMPT_RT）与 nr_cpu_ids>1024 的大核数机器上实跑该用例并回帖——补丁已被收取但这两类环境始终无人验证，是当前唯一实质性缺口"
  - kind: review
    description: "排查 tools/testing/selftests/sched_ext 其余用例是否同样使用固定 cpu_set_t，若是可作为独立清理系列发出"
source_email_count: 1
related_articles:
  - "sched-20260909-005"
  - "sched-20260909-003"
  - "sched-20260909-004"
  - "sched-20260909-006"
tags:
  - sched_ext
  - preempt
  - affinity
---
