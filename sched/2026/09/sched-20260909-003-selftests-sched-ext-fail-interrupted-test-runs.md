# selftests/sched_ext: Fail interrupted test runs

## TL;DR

本文为增量更新，`runner.c` 退出码问题的完整来龙去脉见 related_articles 中的 sched-20260906-003。09-09 02:01 Tejun Heo 回「Applied to sched_ext/for-7.4」，这枚单行改动被收下：被 SIGINT/SIGTERM 打断的 sched_ext 测试运行不再返回 0，CI 从此能把「中断」和「通过」区分开。

## 背景与问题

`tools/testing/selftests/sched_ext/runner.c` 里 SIGINT/SIGTERM 会置 `exit_req` 让 runner 提前停掉剩余用例，但 `main()` 的返回式只看 `failed` 计数。结果：一次被中断、而恰好已跑过的用例全绿的运行，仍然以 0 退出，调用方无法察觉测试根本没跑完。这是 `9d851afa4826 ("selftests/sched_ext: Abort test loop on signal")` 引入中断支持时留下的缺口。

## 技术方案

`return failed > 0 ? 1 : 0;` 改成 `return failed > 0 || exit_req ? 1 : 0;`，把中断并入失败条件，同时保留「结果计数只统计实际跑过的用例」。单行改动（+1/-1），刻意不新增区分性退出码。

## 版本演进与当前进展

- v1（09-06 21:54，`<20260906135507.749280-1-hi@tychen.cc>`），带 `Fixes: 9d851afa4826`，自述在 GDB 下于首个用例之前与 example 用例通过之后各投递一次信号：原 runner 四种情形全返回 0，改后返回 1；`-h`、`-l`、`-t example` 正常调用仍返回 0。
- 09-09 02:01 Tejun Heo 回 "Applied to sched_ext/for-7.4."（`<1a60af2608a5d068d55ad5022d8221f4@kernel.org>`），无 v2、无修改要求。

## Maintainer 意见与讨论焦点

Tejun Heo 无保留收取，未回应「被中断与真实失败共用退出码 1 是否不利于区分」这一点——09-06 那篇里我把它列为唯一潜在分歧，本日邮件中没有任何人提出，作者也未主张需要独立退出码。按现状记录：这是维护者已经接受的取舍。

## 合入评估

`likelihood=merged`。已进 `sched_ext/for-7.4`。风险点只剩一个，而且不在代码里：该改动会让此前静默通过的被中断运行开始报红，如果有 CI 依赖「中断也算通过」，会在合入后暴露出来。

## 效果评估

无性能数据。作者给的是行为验证：GDB 下四种投递时机（首个用例前 / example 通过后 × SIGINT / SIGTERM）由全部返回 0 变为全部返回 1，正常三种调用方式返回值不变。属自行验证，未见第三方复核。

## 我可以参与的点

- `testing`：如果你的流水线里跑过 sched_ext selftests，合入后第一轮很可能出现新的红灯——值得先确认这些红灯确实是过去被静默吞掉的中断，而不是新 bug，并把结果回帖。
- `discussion`：若确实需要区分「中断」与「失败」，现在是一个合适的时点提出独立退出码（例如 2）；目前邮件里没人讨论过这点，属于无人占位的问题。

## 参考链接

- v1 补丁: https://lore.kernel.org/all/20260906135507.749280-1-hi@tychen.cc/
- Tejun Heo 收取回帖: https://lore.kernel.org/all/1a60af2608a5d068d55ad5022d8221f4@kernel.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: "sched-20260909-003"
date: "2026-09-09"
subject: "selftests/sched_ext: Fail interrupted test runs"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "20260906135507.749280-1-hi@tychen.cc"
lore_url: "https://lore.kernel.org/all/1a60af2608a5d068d55ad5022d8221f4@kernel.org/"
upstream_commit: null
fixes_commit: "9d851afa4826"
merged_branch: "sched_ext/for-7.4"
current_version: v1
generated_at: "2026-09-10T00:40:00"
authors:
  - "Tianyi Chen"
maintainers_involved:
  - "Tejun Heo"
patch_series:
  - version: v1
    msgid: "20260906135507.749280-1-hi@tychen.cc"
    date: "2026-09-06"
    summary: "runner.c 的 main() 退出码由 failed > 0 ? 1 : 0 改为 failed > 0 || exit_req ? 1 : 0，使被 SIGINT/SIGTERM 中断的运行返回非零；结果计数仍只覆盖实际跑过的用例。+1/-1。"
    review_outcome: "09-09 02:01 Tejun Heo 回复 Applied to sched_ext/for-7.4，直接收取。"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "等待随 sched_ext/for-7.4 进入 mainline；若 CI 出现新的红灯需确认是否为过去被吞掉的中断"
contribution_opportunities:
  - kind: testing
    description: "在自家流水线上先跑一轮 sched_ext selftests，确认合入后新增的非零退出确实来自历史被静默中断的运行，并把结果回帖"
  - kind: discussion
    description: "为「中断」与「真实失败」提出独立退出码（当前两者共用 1），邮件列表里无人讨论过这一点"
source_email_count: 1
related_articles:
  - "sched-20260906-003"
tags:
  - "sched_ext"
---
