---
id: sched-20260906-006
date: '2026-09-06'
subject: 'tcp: Skip cond_resched() in inet_csk_listen_stop() under BPF context'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
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
  summary: '[PATCH bpf 1/2] bpf: Fix out-of-bounds read of sk_protocol in bpf_sock_destroy()
    + [PATCH bpf 2/2] selftests/bpf: Test bpf_sock_destroy() on a TIME_WAIT sock。正文未拉取。'
  review_outcome: 09-03 22:01 bot+bpf-ci@kernel.org 自动回帖，22:34 作者回复该机器人；未见人类维护者意见
- version: v2
  msgid: null
  date: '2026-09-04'
  summary: '[PATCH bpf v2 1/2] + [PATCH bpf v2 2/2]，selftest 仍仅覆盖 TIME_WAIT sock。正文未拉取。'
  review_outcome: 09-04 18:50 bot+bpf-ci 自动回帖；未见人类维护者意见
- version: v2
  msgid: null
  date: '2026-09-06'
  summary: '09-06 15:41 以 [PATCH bpf v2 0/3] 重发并扩为 3 片：1/3 仍为 sk_protocol 越界读；新增 2/3
    tcp: Skip cond_resched() in inet_csk_listen_stop() under BPF context（本篇）；3/3 selftest
    扩为 Test bpf_sock_destroy() on TIME_WAIT and listener socks。cover 摘要：修 sk_protocol
    越界读与 listener 上的 might_sleep splat 两个 bug。'
  review_outcome: 16:23 bot+bpf-ci 对 2/3 自动回帖（正文未拉取）；本日无任何人类维护者 Acked-by/Reviewed-by/NAK
merge_assessment:
  likelihood: unclear
  blocking_issues:
  - 本日及此前均无人类维护者表态，唯一回帖来自 bot+bpf-ci 自动化
  - 正文未拉取，无法确认 BPF 迭代上下文的识别方式与跳过 cond_resched() 的安全性论证
  - 跨 bpf/net/sched 原语的修复，需 netdev 与 BPF 维护者共同认可
  next_action: 手动抓取 09-06 [PATCH bpf v2 0/3] 与 2/3 正文后再判定；同时跑 v2 3/3 新增的 sock_destroy
    selftest
contribution_opportunities:
- kind: testing
  description: 跑 tools/testing/selftests/bpf/prog_tests/sock_destroy.c 的 TIME_WAIT
    与 listener 两个 subtest，确认 listener 带 accept 队列子连接时不再出现 might_sleep splat
- kind: backport
  description: OLK-6.6 若回合 bpf_sock_destroy() 一类会深入协议栈的 kfunc，需连带审视其在 rcu_read_lock/原子上下文中的
    cond_resched() 让出点
source_email_count: 5
related_articles: []
tags:
- sched/core
- preempt
title: 'tcp: Skip cond_resched() in inet_csk_listen_stop() under BPF context'
layout: article
---

## TL;DR

Jiayuan Chen 的 `bpf,tcp: Fix bpf_sock_destroy() on TIME_WAIT and listener socks` 系列于 09-06 15:41 以 `[PATCH bpf v2 0/3]` 重发，本篇对应的 2/3 是相对上一版新增的一片：`bpf_sock_destroy()` 在 tcp iterator 的 `rcu_read_lock()` 下对「accept 队列里仍有子连接」的 listener 调 `tcp_abort()`，走到 `inet_csk_listen_stop()` 里那个 `cond_resched()` 时报出 might_sleep，补丁让该路径在 BPF 上下文下跳过这个让出点。**必须说明：本系列在当日邮件缓存里只有主题与摘要片段，正文一封都没拉取到**，所以下面的实现细节与维护者态度均为「未获取到」。

## 背景与问题

cover letter 的摘要写明这条系列修 `bpf_sock_destroy()` 的两个 bug：一是 `sk->sk_protocol` 的越界读——该字段位于 `struct sock` 而非 `struct sock_common`，而 tcp iterator 交给 kfunc 的 TIME_WAIT / NEW_SYN_RECV sock 并不是 `struct sock`，读它就是越过对象边界；二是 listener 上 destroy 时的 might_sleep splat。2/3 的摘要给出触发条件：`bpf_sock_destroy()` 从 tcp iterator 中、在 `rcu_read_lock()` 下运行，若目标 sock 是 accept 队列仍有子连接的 listener，`tcp_abort()` 会进入 `inet_csk_listen_stop()`，其中的 `cond_resched()` 在原子/RCU 上下文里就是非法让出点。摘要在此处被截断，BUG 的具体行号与持锁列表正文未拉取到。

对调度侧的意义：这是一个 `cond_resched()` 使用规范的实例——它必须在可睡眠上下文里调用，网络栈在 RCU read-side 临界区内依赖它是不成立的。

## 技术方案

主题给出的手法是「在 BPF 上下文下跳过 `inet_csk_listen_stop()` 里的这个 `cond_resched()`」，即在非 BPF 路径保留原有让出点。具体如何识别当前处于 BPF 迭代上下文、以及是否用同样的判定覆盖 `inet_csk_listen_stop()` 中其它可能睡眠的点，正文未拉取到，无法确认，因此也无法评估它对既有 RCU/抢占语义的影响。

## 版本演进与当前进展

以下均来自缓存中的主题、发件人与时间戳（+08:00）：

- 09-03 20:52 v1 `[PATCH bpf 1/2]`（`sk_protocol` 越界读）+ `2/2`（selftests/bpf: Test bpf_sock_destroy() on a TIME_WAIT sock）；22:01 `bot+bpf-ci@kernel.org` 自动回帖，22:34 作者回复该机器人。
- 09-04 17:49 `[PATCH bpf v2 1/2]` + `2/2`（selftest 仍只有 TIME_WAIT 一个 subtest）；18:50 又是 `bot+bpf-ci` 自动回帖。
- 09-06 15:41 以 `[PATCH bpf v2 0/3]` 重发，从 2 片扩为 3 片：新增本篇 2/3（listener 上的 `cond_resched()`），3/3 的 selftest 由「仅 TIME_WAIT」扩展为「TIME_WAIT 与 listener」两个 subtest；16:23 `bot+bpf-ci` 对本篇 2/3 自动回帖（正文未拉取，内容无法判断）。
- 本日缓存中未见任何人类维护者对这条系列回帖，也仍未见 v3。

## Maintainer 意见与讨论焦点

未获取到。本日与该系列相关的唯一回帖来自 `bot+bpf-ci@kernel.org`（自动化 CI），Alexei Starovoitov、Daniel Borkmann 等 BPF 维护者以及网络侧维护者在缓存邮件中均未表态；调度器维护者也未参与（`cond_resched()` 属调度原语，但没有 sched 侧人出现在这条线程里）。「是否应改到更上层的 tcp iterator 去规避、而不是在 `inet_csk_listen_stop()` 内打补丁」这类问题在邮件中并无出处，不能当作已有分歧。

## 合入评估

`likelihood=unclear`。依据：修复动机（RCU 读临界区内的 `cond_resched()`）本身是硬约束类问题，作者一路补齐 selftest，方向不会被质疑；但截至本日没有人类维护者的 `Reviewed-by`/`Acked-by`，也没有 `Cc: stable` 或合入 `bpf`/`net` 树的迹象，加上正文缺失、无法判断维护者是否要求换实现位置。卡点：跨子系统（bpf + tcp）需要 netdev 与 BPF 两侧共同认可，且本篇落在 `net/ipv4/inet_connection_sock.c` 的热路径上，跳过让出点的论证必须由正文支撑。下一步建议直接到 lore 读 09-06 的 0/3 与 2/3 正文再判定。

## 效果评估

邮件正文未拉取，无法给出效果数据。可确认的只有：这是一条有确定复现路径的 might_sleep/崩溃类问题（作者摘要里给出了 splat 与触发条件），并且 v2 的 3/3 新增了两个 selftest subtest（`tcp_timewait` 与 listener 场景），即修复自带可验证用例——这是本系列目前唯一的验证证据。

## 我可以参与的点

- 先补证据：这条系列的正文不在本地缓存里，值得手动抓一次 09-06 的 `[PATCH bpf v2 0/3]` 与 `2/3` 正文，重点确认它如何判定「BPF 迭代上下文」、以及是否覆盖 `inet_csk_listen_stop()` 中其它潜在睡眠点。
- 可帮跑：`tools/testing/selftests/bpf/prog_tests/sock_destroy.c`（v2 3/3 修改的文件）里的 TIME_WAIT 与 listener 两个 subtest，在带 accept 队列子连接的 listener 上验证 might_sleep splat 是否消失；若能给 bpf-ci 之外的真实回归反馈，对这类跨子系统补丁帮助最大。
- 与本用户工作的关联：这是 `cond_resched()` 在 `rcu_read_lock()` 下被误用的典型样本。OLK-6.6 若回合了 `bpf_sock_destroy()` 一类会深入协议栈的 kfunc，需要连带审视其在 RCU/原子路径上的让出点，而不是只看补丁本身。

## 参考链接

- 无法给出 lore 永久链接：本系列 5 封邮件（0/3、1/3、2/3、3/3 与 1 条机器人回帖）在缓存中只有索引级主题与摘要，未记录 Message-ID，正文未拉取到。
- tip-bot commit: 未获取到
- stable backport: 未获取到
