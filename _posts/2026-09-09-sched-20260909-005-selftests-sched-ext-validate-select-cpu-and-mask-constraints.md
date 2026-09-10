---
id: sched-20260909-005
date: '2026-09-09'
subject: 'selftests/sched_ext: Validate select_cpu_and mask constraints'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260906144029.848978-1-hi@tychen.cc>
lore_url: https://lore.kernel.org/all/53d04980eecb0e5f6eeea25a5cf0dcf5@kernel.org/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-10T00:40:00'
authors:
- Tianyi Chen
maintainers_involved:
- Tejun Heo
patch_series:
- version: v1
  msgid: <20260906144029.848978-1-hi@tychen.cc>
  date: '2026-09-06'
  summary: 为 scx_bpf_select_cpu_and() 的 cpumask 约束新增 selftest 用例；补丁正文不在当天缓存内，用例组织细节未获取到。
  review_outcome: 无人回帖。
- version: v2
  msgid: <CACGbirQ-xfWymbY9Z440sjbUseLRuaPFT17mBAwddeN7wqVi-w@mail.gmail.com>
  date: '2026-09-09'
  summary: 内容与 v1 的关系未在缓存中可证；作者 09-09 23:25 说明这次 RESEND 因 Gmail 出站折长行破坏了补丁空白符，请维护者忽略，并以
    text/plain 附件重发了未改动的 v2。
  review_outcome: 09-09 02:01 Tejun Heo 打回两条：CONFIG_PREEMPT_RCU 下抢占可让 migrate_disable_switch()
    把 p->cpus_ptr 收窄到运行 CPU，从而误判合法选择，应改校请求的 affinity；固定 cpu_set_t 在 nr_cpu_ids>1024
    时使 sched_getaffinity() 返回 EINVAL，应改用动态分配掩码。两条意见到当天结束无人从技术角度回应。
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Tejun Heo 要求把校验对象从 p->cpus_ptr 改为请求的 affinity，否则在 CONFIG_PREEMPT_RCU 下会产生假阳性失败
  - Tejun Heo 要求把固定大小 cpu_set_t 换成动态分配掩码，否则在 nr_cpu_ids > 1024 的机器上 sched_getaffinity()
    直接 EINVAL
  - 当天作者只处理了投递问题（Gmail 折行破坏空白符），两条技术意见尚未回应
  next_action: 作者按两条意见出 v3，并确认改用 text/plain 附件投递后 b4/git am 能正常取出补丁
contribution_opportunities:
- kind: testing
  description: 在 CONFIG_PREEMPT_RCU 与 nr_cpu_ids>1024 两类环境上验证改版后的用例能否真正跑通并回帖结果，这两类配置目前无人验证
- kind: review
  description: 排查 selftests/sched_ext 目录内其它用例是否同样使用固定 cpu_set_t，那是一类会在大型机上普遍失败的测试缺陷
- kind: discussion
  description: 确认改校请求的 affinity 之后用例是否仍覆盖原本想测的约束（p->cpus_ptr 恰是内核实际看到的掩码），这一语义差异在邮件里尚无人说明
source_email_count: 2
related_articles: []
tags:
- sched_ext
- preempt
title: 'selftests/sched_ext: Validate select_cpu_and mask constraints'
layout: article
---

## TL;DR

Tianyi Chen 给 `scx_bpf_select_cpu_and()` 的 cpumask 约束加自测用例，09-09 02:01 被 Tejun Heo **打回**，指出两处会让用例自己出错的问题：一是在 `CONFIG_PREEMPT_RCU` 下用 `p->cpus_ptr` 反查会误判，二是固定大小的 `cpu_set_t` 在 `nr_cpu_ids > 1024` 的机器上会让 `sched_getaffinity()` 直接 EINVAL。当天 23:25 作者又追加了一封道歉信，说明之前那次 v2 RESEND 是 Gmail 出站把长行折行破坏了补丁空白符，改以 text/plain 附件重发未改动的 v2。这是本批四枚测试补丁里唯一还没被收取的一枚。

## 背景与问题

`sced_ext` 的 `scx_bpf_select_cpu_and()` 允许 BPF 调度器把 CPU 选择限制在一个给定 cpumask 内。约束是否真的被遵守（选出的 CPU 一定在该 mask 里、mask 为空时的行为等）此前没有自测覆盖，这个补丁就是补这块。

但测试代码本身有两个正确性缺陷，Tejun 在回帖里逐条点出：

1. **用 `p->cpus_ptr` 校验会误判**。被测试的那次 syscall 运行在 migration disabled 状态下；开了 `CONFIG_PREEMPT_RCU` 时，「完成 CPU 选择」与「执行校验」之间可能发生抢占，而 `migrate_disable_switch()` 会把 `p->cpus_ptr` 收窄到当前正在运行的那个 CPU。于是用例会在**选择本身合法**的情况下把它判为失败——一个假阳性，且只在 PREEMPT_RCU 配置下出现。Tejun 的要求是改校「请求的 affinity」，而不是校 `p->cpus_ptr`。
2. **`cpu_set_t` 尺寸写死**。固定大小的 `cpu_set_t` 只能表示 1024 个 CPU；在 `nr_cpu_ids` 超过 1024 的机器上，即便任务只用低编号 CPU，`sched_getaffinity()` 也会返回 EINVAL。Tejun 要求换成动态分配的 mask。

## 技术方案

补丁正文不在当天邮件缓存里（当天只有 Tejun 的 review 与作者关于投递问题的说明），因此用例的具体组织方式、断在哪一层未获取到。可从 review 反推的只有：它调 `sched_getaffinity()` 取掩码、并在 select 之后把结果与 `p->cpus_ptr` 做比对。这两点正是被打回的地方。

## 版本演进与当前进展

- v1：`<20260906144029.848978-1-hi@tychen.cc>`（09-06，正文未缓存）。
- 09-09 02:01 Tejun Heo 打回（`<53d04980eecb0e5f6eeea25a5cf0dcf5@kernel.org>`），列出上面两条。
- 09-09 23:25 作者说明：此前那封 `Re: [PATCH v2 RESEND]`（`<CACGbirQ-xfWymbY9Z440sjbUseLRuaPFT17mBAwddeN7wqVi-w@mail.gmail.com>`）请维护者忽略——他在排查另一条 MM 系列的投递路径时确认，Gmail 出站会折长行并破坏补丁空白符；已经把**未做改动的 v2** 以 text/plain 附件重发（`<CACGbirTEtYnxiZW0EnOCHbZt66=t-A_Nppp0ChRfM9G2ZD5+aQ@mail.gmail.com>`），并说明外部收到的附件能过 `b4` 与 `git am`。

也就是说：v2 尚未针对 Tejun 的两条意见做任何调整，作者当天只解决了投递问题。

## Maintainer 意见与讨论焦点

意见全部来自 Tejun Heo，两条都是明确要改而非风格建议，且第 1 条涉及真实的误判风险（PREEMPT_RCU 下的假阳性会让这个用例在有价值的配置上不可用）。作者当天没有回这两条技术问题，只回了投递问题——**这两条意见目前处于未回应状态**。

另一件值得记的事是投递本身：作者明确说 Gmail 出站路径会破坏补丁空白符，并给出了「改用 text/plain 附件」的绕法。这不是调度器的问题，但对任何用 Gmail 发 patch 的人是实用信息。

## 合入评估

`likelihood=medium`。补丁方向没有争议（Tejun 对本批其它三枚都直接收取，说明他愿意要这些覆盖），卡点纯粹是这两处实现问题。第 1 条要求换校验对象（校请求的 affinity 而不是 `p->cpus_ptr`）、第 2 条要求动态 mask，都是可机械完成的改动，作者完成度高，出 v3 只是时间问题。

`next_action`：作者按两条意见出 v3，并显式说明校验改成了比较请求时的 affinity，以及动态 mask 的处理方式；同时确认改用附件投递后 `b4 am` 能正常取到补丁。

## 效果评估

无 benchmark。有价值的信息是 Tejun 描述的那个失效模式本身：`migrate_disable_switch()` 在 PREEMPT_RCU 下把 `p->cpus_ptr` 收窄到运行 CPU——这条不属于本补丁，而是任何「从任务侧反查 affinity 约束」的测试代码都会踩的通用坑，值得记住。

## 我可以参与的点

- `testing`：作者改完之后，这个用例的价值取决于它能不能在 `CONFIG_PREEMPT_RCU` 与 `nr_cpu_ids > 1024` 两类机器上真正跑起来。前者需要 PREEMPT_RCU（含 PREEMPT_RT）配置，后者只有大核数服务器才有；如果你有 >1024 CPU 的机器，跑一遍并把结果回帖就是直接补上目前没人验证的那一角。
- `discussion`：Tejun 的两条意见到当天结束仍无人从技术角度回应，可以帮忙确认改用「请求的 affinity」后，用例是否仍能覆盖到它原本想测的约束（因为 `p->cpus_ptr` 恰恰是内核最终实际看到的掩码，两者语义差别值得在邮件里说清楚）。
- `review`：检查 sched_ext selftests 目录里是否还有其它用例同样用固定 `cpu_set_t` ——如果是，这是一类会普遍性地在大型机上失败的测试缺陷。

## 参考链接

- 线程根（补丁本体，正文未获取到）: https://lore.kernel.org/all/20260906144029.848978-1-hi@tychen.cc/
- Tejun Heo 的 review: https://lore.kernel.org/all/53d04980eecb0e5f6eeea25a5cf0dcf5@kernel.org/
- 作者关于 Gmail 投递问题的说明: https://lore.kernel.org/all/CACGbirTmyi0LHZEr4xOwg_WgFALarFVPMm7JhHBbXwG10PF3KQ@mail.gmail.com/
- 被要求忽略的那次 RESEND: https://lore.kernel.org/all/CACGbirQ-xfWymbY9Z440sjbUseLRuaPFT17mBAwddeN7wqVi-w@mail.gmail.com/
- 以 text/plain 附件重发的 v2: https://lore.kernel.org/all/CACGbirTEtYnxiZW0EnOCHbZt66=t-A_Nppp0ChRfM9G2ZD5+aQ@mail.gmail.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
