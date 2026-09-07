# deadlock from exec_update_lock and reading procfs

## TL;DR

Benjamin Peterson 报告：带上 `6650527444da ("proc: protect ptrace_may_access() with exec_update_lock (part 1)")` 之后，FUSE 服务器在实际负载下死锁——正在 `execve` 的进程在 `do_close_on_exec()` 里关 O_CLOEXEC 文件、同步等 FUSE 回复，而 FUSE daemon 处理 flush 时读 `/proc/PID/stat` 要拿同一把 `exec_update_lock` 读锁，形成环形等待。09-01 当天无人回帖；**09-03 Jann Horn 认账并挂了 `#regzbot ^introduced: 6650527444da`，承诺跟进**。这是 exec/procfs 锁顺序问题，不在 `kernel/sched/`，但表现是任务卡在 `schedule()` 上（hung task 视角看到的正是调度栈）。

## 背景与问题

`exec_update_lock` 是 mm 侧的守卫锁，用来让「ptrace/procfs 观察一个正在 exec 的进程」与 exec 本身互斥；`6650527444da` 把 `ptrace_may_access()` 这条路径纳入它的保护范围（procfs 读 `/proc/PID/stat` 会走 `do_task_stat()`）。问题在于 exec 路径本身在锁的覆盖范围内做了**可以无限期等待用户态**的事：

```
__schedule+0x505/0xc00
schedule+0x27/0xc0
request_wait_answer+0x158/0x2a0
__fuse_simple_request+0xd7/0x290
fuse_flush+0x1a4/0x1e0
filp_flush+0x30/0x60
filp_close+0x13/0x30
do_close_on_exec+0x114/0x160
begin_new_exec+0x553/0xb50
load_elf_binary+0x2da/0x1770
? load_misc_binary+0x275/0x390 [binfmt_misc]
bprm_execve+0x241/0x5f0
```

而同一时刻 FUSE daemon 阻塞在：

```
rwsem_down_read_slowpath+0x25c/0x480
down_read_killable+0x48/0xc0
do_task_stat+0x7f/0xec0
proc_single_show+0x51/0xc0
seq_read_iter+0x11f/0x460
vfs_read+0xe8/0x360
```

即：execve 持写锁语义范围内 → 等 FUSE daemon 干活；daemon 读该 PID 的 procfs → 等同一把锁的读侧。触发条件很具体，也很容易在真实栈里出现：**FUSE 文件系统 + 被关闭的 fd 带 O_CLOEXEC（exec 时由 `do_close_on_exec()` 关）+ daemon 在 flush 回调里读被 flush 进程的 `/proc/PID/stat`**。报告的定性是「原先在补丁评审里只被当作理论可能性，现在成了实际问题」，并直接提出修法问题：能否把 `do_close_on_exec()` 移出 `exec_update_lock` 的覆盖范围。

## 技术方案

邮件里没有补丁，只有方案询问。可选形状有三类，报告点第一类：

1. **缩小临界区**：把 `do_close_on_exec()` 挪出 `exec_update_lock` 的写侧保护范围。代价是 exec 期间文件表已经换掉、而 mm 尚未完全就绪的那段窗口重新对 procfs 观察者暴露——正是该锁当初要堵的洞。
2. **让 FUSE 侧不等待**：flush 回调里不读该进程的 procfs（用户态规避，不改内核）。
3. **改成可失败/可超时的取锁**：`down_read_killable()` 已经是 killable，但对 daemon 而言被杀等于 FUSE 请求失败，语义上不可接受。

报告倾向 1，并明确它属于设计权衡而非明显 bug 修复；这也是需要 Jann Horn（该保护方向的作者）来判断的点。

## 版本演进与当前进展

- 09-01 22:49 报告发出（独立新线程，无 `In-Reply-To`）。**当日无人回帖。**
- 补跑补充（后续缓存）：09-03 02:04 Jann Horn 回帖 `Ugh, sorry about that.` + `#regzbot ^introduced: 6650527444da` + `I will take a look at this soon.`——即该问题已被 regzbot 登记为回归、并由当事维护者认领。截至 09-07 缓存未见修复补丁。

## Maintainer 意见与讨论焦点

- 本日无维护者表态，讨论焦点只有一个：**锁的覆盖范围是否应该包含会同步等待用户态的 `do_close_on_exec()`**。报告者给出的判断是这一步在原评审里被承认过是理论风险。
- 与本日另一条 exec 路径修复同源：`sched/cache: Fix use-after-free of the mm replaced by exec`（sched-20260901-001）处理的正是「exec 换 mm 时 `p->mm` 无生命周期保护」，两者都是 `begin_new_exec()` 长临界区外溢到别的子系统造成的后果，可以在同一次 review 里一起看。
- 无人提出「这是 FUSE 的使用错误」这一反驳（09-01 范围内），因此分歧尚未展开。

## 合入评估

`likelihood = unknown`（还没有补丁可评估合入）。可判断的是**推进状态**：regzbot 已挂 introduced 标签、当事维护者已认领，因此预期会有正式修复或明确的「用户态规避」结论。卡点：修在 fs/proc、fs/exec 还是 fuse 侧，取决于「exec 期间是否允许观察到半新 mm」这个语义选择；`6650527444da` 是 part 1，说明原作者本来就打算继续推进保护范围，缩小临界区与该意图直接冲突。

## 效果评估

无量化数据，只有两份可直接对照的阻塞栈与一条明确的复现形态（FUSE + O_CLOEXEC + daemon 读 `/proc/PID/stat`）。死锁是二值现象，不涉及性能回退幅度。**影响范围**：任何用 FUSE（含网络/沙箱文件栈）且在 exec 路径上关带 O_CLOEXEC fd 的系统，属于可用性级问题，不是概率性性能问题。

## 我可以参与的点

- **给出复现与影响面数据**：这份报告只有一例现场。写一个最小复现（FUSE daemon 在 `flush()` 里读 `/proc/<flushing pid>/stat`）并回帖，能直接决定它是否被当作 must-fix 进 stable；这类数据目前线程里完全没有。
- **锁顺序走查**：`begin_new_exec()` 里哪些步骤会等待外部（`do_close_on_exec()` 是最明显的一个），可以整理成清单回帖，帮 Jann Horn 判断缩小临界区还是移出某几步；这与 cpuset/proc 侧读进程信息的实现方同样相关。
- **回合自查**：若自家内核已带 `6650527444da` 或其等价改动（ptrace/procfs 与 exec 互斥），且线上跑 FUSE，这条要在别人踩到之前先确认。

## 参考链接

- lore thread: https://lore.kernel.org/all/f5e8166a-88be-46c5-8939-1e5227ffe4c2@app.fastmail.com/
- 报告引用的原评审线程（理论可能性）: https://lore.kernel.org/all/CAG48ez2pmuoTCZh_AVKDDLeQEYmm=gLMgThnqFhRMFfZvABpdw@mail.gmail.com/
- Jann Horn 09-03 认领（含 regzbot 标签）: https://lore.kernel.org/all/CAG48ez3AYt=dYMYLEEhkrzO740wNsD1_3zZbKqo7MXThqEA+Zg@mail.gmail.com/
- 涉及 commit: `6650527444da`（`proc: protect ptrace_may_access() with exec_update_lock (part 1)`）
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260901-014
subject: "deadlock from exec_update_lock and reading procfs"
date: '2026-09-01'
subsystem: sched
type: bug
status: under_review
severity: critical
thread_root_msgid: "<f5e8166a-88be-46c5-8939-1e5227ffe4c2@app.fastmail.com>"
lore_url: "https://lore.kernel.org/all/f5e8166a-88be-46c5-8939-1e5227ffe4c2@app.fastmail.com/"
authors: [Benjamin Peterson]
maintainers_involved: [Jann Horn]
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - "09-01 当日无任何回帖，也没有补丁，只有修法询问"
  - "修复位置未定：缩小 exec_update_lock 覆盖范围与该锁的设计意图（part 1 之后还要继续扩大保护）冲突"
  next_action: "等 Jann Horn（09-03 已认领并挂 regzbot introduced）给出补丁或明确的用户态规避结论；社区需要最小复现"
contribution_opportunities:
  - kind: testing
    description: "写最小复现（FUSE daemon 在 flush 回调读 /proc/<pid>/stat，另一进程 exec 且关闭 O_CLOEXEC fd）并回帖，用于确认影响面与 stable 定级"
  - kind: review
    description: "整理 begin_new_exec() 中会同步等待外部的步骤清单（do_close_on_exec 是其一），供锁顺序决策参考"
  - kind: review
    description: "自查自家分支是否已带 6650527444da 等价改动且线上跑 FUSE，必要时提前规避"
source_email_count: 1
related_articles:
  - "sched-20260901-001"
tags:
- hang
generated_at: '2026-09-07'
---
