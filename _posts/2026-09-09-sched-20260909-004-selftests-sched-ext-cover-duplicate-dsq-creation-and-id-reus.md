---
id: sched-20260909-004
date: '2026-09-09'
subject: 'selftests/sched_ext: Cover duplicate DSQ creation and ID reuse'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: 20260906144044.849222-1-hi@tychen.cc
lore_url: https://lore.kernel.org/all/87d38cf2983a82fc89e18112510f5091@kernel.org/
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
current_version: v1
generated_at: '2026-09-10T00:40:00'
authors:
- Tianyi Chen
maintainers_involved:
- Tejun Heo
patch_series:
- version: v1
  msgid: 20260906144044.849222-1-hi@tychen.cc
  date: '2026-09-06'
  summary: 为 sched_ext selftests 补 DSQ 重复创建与 DSQ ID 复用两种情形的覆盖；补丁正文不在当天邮件缓存内，实现细节未获取到，此处仅按邮件主题与维护者回帖记录范围限于
    tools/testing/selftests/sched_ext/。
  review_outcome: 09-09 02:01 Tejun Heo 回复 Applied to sched_ext/for-7.4，直接收取，无修改要求。
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 等待随 sched_ext/for-7.4 进入 mainline
contribution_opportunities:
- kind: testing
  description: 在启用 sched_ext 的机器上跑完整 selftests 套件，确认新增的 DSQ 重复创建/ID 复用用例不 flaky
source_email_count: 1
related_articles: []
tags:
- sched_ext
title: 'selftests/sched_ext: Cover duplicate DSQ creation and ID reuse'
layout: article
---

## TL;DR

Tianyi Chen 为 sched_ext selftests 补 DSQ 创建路径的覆盖（重复创建同一个 DSQ、以及 DSQ ID 被复用这两种情形），09-09 02:01 被 Tejun Heo 以「Applied to sched_ext/for-7.4」直接收下。需要说明的是：本日报只拿到维护者的收取回帖，补丁原文不在邮件缓存里，因此**具体加了哪几个用例、断在哪个 kfunc 上未获取到**，本文只对可核实的进展下结论。

## 背景与问题

可核实的部分：DSQ（dispatch queue）是 sched_ext 里由调度器在 `select_cpu`/`init` 阶段显式创建的对象，ID 由内核分配并可在使用完毕后被复用。这意味着「用同一 ID 重复创建」和「拿到重复 ID」是两条真实存在的边界路径。标题本身表明该补丁的意图是给这两条路径补上测试覆盖，而不是修内核缺陷——测试侧的缺口填补。更细的动机描述需要补丁的 commit message，本日未获取到。

## 技术方案

未获取到——补丁正文不在当天的 sched 邮件缓存中（当天只有 Tejun Heo 的收取回帖这一封），缓存里也没有该邮件的 UID 可直接回取，因此不猜测实现细节。可确认的只有改动范围限于 `tools/testing/selftests/sched_ext/`。

## 版本演进与当前进展

- v1 线程根：`<20260906144044.849222-1-hi@tychen.cc>`（该 msgid 取自 09-09 收取回帖的 `In-Reply-To` 头，发出日期为 09-06；本日报的当天缓存内没有其正文）。
- 09-09 02:01 Tejun Heo 回复 "Hello, Tianyi. Applied to sched_ext/for-7.4. Thanks."（`<87d38cf2983a82fc89e18112510f5091@kernel.org>`），无 v2，无修改要求。

## Maintainer 意见与讨论焦点

Tejun Heo 未提出任何意见即收取。值得对照的是同一天作者在另外两枚测试补丁上的态度完全不同：`selftests/sched_ext: Validate select_cpu_and mask constraints` 被打回要求两处实质修改（见 sched-20260909-005），而 `Handle CPU hotplug write failures`、`Fail interrupted test runs` 与本补丁一样直接收取。也就是说这轮里「需要作者改」的只有那一个用例，本补丁不在其中。

## 合入评估

`likelihood=merged`。已进 `sched_ext/for-7.4` topic 分支。测试补丁，无功能回归面。

## 效果评估

未获取到——没有补丁正文，也就没有作者自述的验证方式或结果可引用。

## 我可以参与的点

- `review`：等 v1 正文可从邮箱回取后，确认这两个新用例是否真的能覆盖到 `scx_bpf_dsq_create`（或对应的用户态创建入口）的重复创建与 ID 复用分支，还是只覆盖了返回值；如果有分支没被真正打到，可以补后续用例。目前证据不足，不宜先下结论。
- `testing`：在启用了 sched_ext 的机器上跑完整 selftests 套件，确认新用例在当前内核上不 flaky——测试新增用例最常见的后续问题就是稳定性。

## 参考链接

- 线程根（补丁本体，正文未获取到）: https://lore.kernel.org/all/20260906144044.849222-1-hi@tychen.cc/
- Tejun Heo 收取回帖: https://lore.kernel.org/all/87d38cf2983a82fc89e18112510f5091@kernel.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到
