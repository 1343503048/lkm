# tcp: Skip cond_resched() in inet_csk_listen_stop() under BPF context

## TL;DR

Jiayuan Chen 的 `bpf,tcp: Fix bpf_sock_destroy() on TIME_WAIT and listener socks` 系列于 09-06 15:41 以 `[PATCH bpf v2 0/3]` 重发，本篇对应的 2/3 是相对上一版新增的一片：`bpf_sock_destroy()` 在 tcp iterator 的 `rcu_read_lock()` 下对「accept 队列里仍有子连接」的 listener 调 `tcp_abort()`，走到 `inet_csk_listen_stop()` 里那个 `cond_resched()` 时报出 might_sleep，补丁让该路径在 BPF 上下文下跳过这个让出点。**该系列不在 sched 主题缓存里**（`tcp:`/`bpf:` 前缀被关键字过滤），时间线取自当日全量清单，本篇 2/3 与那条回帖的正文已按 UID 从邮箱取回核对：改动只有 1 行守卫（`net/ipv4/inet_connection_sock.c`，+2/-1）并带 `Fixes: 4ddbcb886268`；截至 09-07 没有人类维护者表态，唯一实质意见来自 bpf-ci 自动评审，它认可代码形态、但认为 commit message 的理由不成立。v1 与 v2(1/2) 的正文未取，只做版本对照。

## 背景与问题

cover letter 的摘要写明这条系列修 `bpf_sock_destroy()` 的两个 bug：一是 `sk->sk_protocol` 的越界读——该字段位于 `struct sock` 而非 `struct sock_common`，而 tcp iterator 交给 kfunc 的 TIME_WAIT / NEW_SYN_RECV sock 并不是 `struct sock`，读它就是越过对象边界；二是 listener 上 destroy 时的 might_sleep splat。2/3 的摘要给出触发条件：`bpf_sock_destroy()` 从 tcp iterator 中、在 `rcu_read_lock()` 下运行，若目标 sock 是 accept 队列仍有子连接的 listener，`tcp_abort()` 会进入 `inet_csk_listen_stop()`，其中的 `cond_resched()` 在原子/RCU 上下文里就是非法让出点。BUG 的具体行号与三级持锁列表见「效果评估」，取自本篇正文。

对调度侧的意义：这是一个 `cond_resched()` 使用规范的实例——它必须在可睡眠上下文里调用，网络栈在 RCU read-side 临界区内依赖它是不成立的。

## 技术方案

实现是给这个让出点加一层上下文守卫：只在非 BPF 上下文时保留原来的让出。作者的理由是复用既有判定 —— `4ddbcb886268` 引入 `bpf_sock_destroy()` 时已经用 `has_current_bpf_ctx()` 保护了 `tcp_abort()`/`udp_abort()` 里的 `lock_sock()`，只是漏了 listener 这条路径。补丁只覆盖 `inet_csk_listen_stop()` 中这一处 `cond_resched()`，同函数内其它潜在睡眠点未加守卫。

## 版本演进与当前进展

以下均来自缓存中的主题、发件人与时间戳（+08:00）：

- 09-03 20:52 v1 `[PATCH bpf 1/2]`（`sk_protocol` 越界读）+ `2/2`（selftests/bpf: Test bpf_sock_destroy() on a TIME_WAIT sock）；22:01 `bot+bpf-ci@kernel.org` 自动回帖，22:34 作者回复该机器人。
- 09-04 17:49 `[PATCH bpf v2 1/2]` + `2/2`（selftest 仍只有 TIME_WAIT 一个 subtest）；18:50 又是 `bot+bpf-ci` 自动回帖。
- 09-06 15:41 以 `[PATCH bpf v2 0/3]`（`<20260906074135.185212-1-jiayuan.chen@linux.dev>`）重发，从 2 片扩为 3 片：新增本篇 2/3（`...-3-...`），3/3（`...-4-...`）的 selftest 由「仅 TIME_WAIT」扩展为「TIME_WAIT 与 listener」两个 subtest。
- 09-06 16:23 `bot+bpf-ci@kernel.org` 对本篇发出自动评审（`<0aa6425f9e8f32705ae827f6325b29079234c3f3d0c7b2cdefba3e5b50432766@mail.kernel.org>`），内容是具体的技术意见，见下节；作者当日未回应。
- 本日缓存中未见任何人类维护者对这条系列回帖，也仍未见 v3。

## Maintainer 意见与讨论焦点

人类维护者：未获取到。BPF 侧（Alexei Starovoitov、Daniel Borkmann）、netdev 侧与 sched 侧截至 09-07 都没出现在这条线程里。唯一的实质意见来自 bpf-ci 自动评审机器人，它把矛头指向 commit message 而不是代码：

> Is the justification "it can't reschedule there anyway" accurate?

机器人的两点依据值得记下来：

1. `CONFIG_PREEMPT_DYNAMIC=y` 且以 `preempt=none` 或 `preempt=voluntary` 启动时，`cond_resched()` 展开为 `__cond_resched()`，**确实能让出**；splat 本身就是证据 —— `preempt_count: 0` 而 `RCU nest depth: 1`，此时 `should_resched(0)` 可为真并走到 `preempt_schedule_common()`。
2. `CONFIG_PREEMPT_RCU=n` 时 `rcu_read_lock()` 等同 `preempt_disable()`，`__cond_resched()` 会落到 `rcu_all_qs()` → `rcu_qs()`，等于在 RCU 读临界区内上报一个假的 quiescent state —— 这已经超出 debug check 的范畴，是正确性问题。

因此它建议把理由改写为「该循环运行在 iterator 的 RCU 读临界区内，既不能让出也不能上报 quiescent state」，同时明确写了代码本身没问题：`The code change itself is correct and matches the existing pattern in tcp_abort() and udp_abort().` 需要提醒的是，这是 AI 生成的评审（机器人自述 `AI reviewed your patch`），两点推断合理但仍需作者自行验证，不能当作维护者意见。

## 合入评估

`likelihood=unknown` —— 不是方向有疑问，而是还没有任何人类维护者表态。有利项：缺陷是硬约束类（完整 splat + 明确触发条件）、自带 selftest、`Fixes:` 标签齐全、改动 1 行且沿用 kfunc 引入时既有的 `has_current_bpf_ctx()` 模式，自动评审也认可代码形态。卡点：commit message 的安全性论证被指出不成立，需要重写；跨 bpf + tcp 两个子系统，要 netdev 与 BPF 两侧都点头；缓存里未见 `Cc: stable`，是否走 stable 目前无据。

## 效果评估

无性能数据，这也不需要一个 —— 修的是确定性 splat。作者给出的现场：`BUG: sleeping function called from invalid context at net/ipv4/inet_connection_sock.c:1523`，`RCU nest depth: 1, expected: 0`、`preempt_count: 0`、`in_atomic(): 0`，内核 `7.2.0+`，进程 `test_progs`。持锁链自下而上是 `bpf_seq_read()` 的 `&p->lock` → `bpf_iter_tcp_seq_show()` 的 `sk_lock-AF_INET6` → `bpf_iter_run_prog()` 的 `rcu_read_lock`，调用链 `bpf_sock_destroy() → tcp_abort() → inet_csk_listen_stop()`。注意 `in_atomic(): 0` 与 `preempt_count: 0` 恰好说明让出在那种配置下真的会发生，这正是机器人争议的出处。验证证据是 3/3 的两个 selftest subtest。

## 我可以参与的点

- 机器人要的是把理由改对，不是改代码：可先在 `preempt=none`/`preempt=voluntary` 与 `PREEMPT_RCU=n` 两种配置下实测这个 `cond_resched()` 到底会不会让出、会不会走到 `rcu_qs()`，用数据替作者补一句准确表述，顺带检查 `inet_csk_listen_stop()` 内其余睡眠点是否需要同样守卫。
- 可帮跑：`tools/testing/selftests/bpf/prog_tests/sock_destroy.c`（v2 3/3 修改的文件）里的 TIME_WAIT 与 listener 两个 subtest，在带 accept 队列子连接的 listener 上验证 might_sleep splat 是否消失；若能给 bpf-ci 之外的真实回归反馈，对这类跨子系统补丁帮助最大。
- 与本用户工作的关联：这是 `cond_resched()` 在 `rcu_read_lock()` 下被误用的典型样本。OLK-6.6 若回合了 `bpf_sock_destroy()` 一类会深入协议栈的 kfunc，需要连带审视其在 RCU/原子路径上的让出点，而不是只看补丁本身。

## 参考链接

- 线程根（0/3 cover）: https://lore.kernel.org/all/20260906074135.185212-1-jiayuan.chen@linux.dev/
- 1/3 `bpf: Fix out-of-bounds read of sk_protocol in bpf_sock_destroy()`: https://lore.kernel.org/all/20260906074135.185212-2-jiayuan.chen@linux.dev/
- 2/3 本篇: https://lore.kernel.org/all/20260906074135.185212-3-jiayuan.chen@linux.dev/
- 3/3 selftests: https://lore.kernel.org/all/20260906074135.185212-4-jiayuan.chen@linux.dev/
- bpf-ci 自动评审回帖: https://lore.kernel.org/all/0aa6425f9e8f32705ae827f6325b29079234c3f3d0c7b2cdefba3e5b50432766@mail.kernel.org/
- 被修复的 commit: `4ddbcb886268`（bpf: Add bpf_sock_destroy kfunc）
- tip-bot commit / stable backport: 未获取到

---
id: sched-20260906-006
date: '2026-09-06'
subject: 'tcp: Skip cond_resched() in inet_csk_listen_stop() under BPF context'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260906074135.185212-1-jiayuan.chen@linux.dev>
lore_url: https://lore.kernel.org/all/20260906074135.185212-3-jiayuan.chen@linux.dev/
upstream_commit: null
fixes_commit: 4ddbcb886268
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Jiayuan Chen
maintainers_involved: []
patch_series:
- version: v1
  msgid: null
  date: '2026-09-03'
  summary: '[PATCH bpf 1/2] bpf: Fix out-of-bounds read of sk_protocol in bpf_sock_destroy() + [PATCH bpf 2/2] selftests/bpf: Test bpf_sock_destroy() on a TIME_WAIT sock。正文未拉取。'
  review_outcome: 09-03 22:01 bot+bpf-ci@kernel.org 自动回帖，22:34 作者回复该机器人；未见人类维护者意见
- version: v2
  msgid: null
  date: '2026-09-04'
  summary: '[PATCH bpf v2 1/2] + [PATCH bpf v2 2/2]，selftest 仍仅覆盖 TIME_WAIT sock。正文未拉取。'
  review_outcome: 09-04 18:50 bot+bpf-ci 自动回帖；未见人类维护者意见
- version: v2
  msgid: <20260906074135.185212-1-jiayuan.chen@linux.dev>
  date: '2026-09-06'
  summary: '09-06 15:41 以 [PATCH bpf v2 0/3] 重发并扩为 3 片：1/3 仍为 sk_protocol 越界读；新增 2/3 tcp: Skip cond_resched() in inet_csk_listen_stop() under BPF context（本篇）；3/3 selftest 扩为 Test bpf_sock_destroy() on TIME_WAIT and listener socks。cover 摘要：修 sk_protocol 越界读与 listener 上的 might_sleep splat 两个 bug。'
  review_outcome: 16:23 bot+bpf-ci 自动评审（AI）：代码形态正确且与 tcp_abort()/udp_abort() 既有模式一致，但「它不能让出」的理由在 PREEMPT_DYNAMIC(none/voluntary) 与 PREEMPT_RCU=n 下不成立，要求改写 commit message；作者未回应，无人类维护者 Acked-by/Reviewed-by/NAK
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 截至 09-07 无人类维护者表态，唯一实质意见来自 bot+bpf-ci 自动评审（AI 生成）
  - commit message 的安全性论证被指不成立：PREEMPT_DYNAMIC 的 none/voluntary 下 cond_resched() 真会让出，PREEMPT_RCU=n 下会经 rcu_all_qs() 在 RCU 读临界区内上报假 quiescent state
  - 跨 bpf/net/sched 原语的修复，需 netdev 与 BPF 维护者共同认可
  next_action: 等作者回应 bpf-ci 意见或给出改写理由的 v3；人类维护者的 Reviewed-by/Acked-by 仍缺；可跑 v2 3/3 新增的 sock_destroy selftest
contribution_opportunities:
- kind: testing
  description: 跑 tools/testing/selftests/bpf/prog_tests/sock_destroy.c 的 TIME_WAIT 与 listener 两个 subtest，确认 listener 带 accept 队列子连接时不再出现 might_sleep splat
- kind: new_patch
  description: OLK-6.6 若回合 bpf_sock_destroy() 一类会深入协议栈的 kfunc，需连带审视其在 rcu_read_lock/原子上下文中的 cond_resched() 让出点
source_email_count: 6
related_articles: []
tags:
- sched/core
- preempt
---
