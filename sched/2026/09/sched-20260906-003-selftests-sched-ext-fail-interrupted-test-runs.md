# selftests/sched_ext: Fail interrupted test runs

## TL;DR

Tianyi Chen 修 `tools/testing/selftests/sched_ext/runner.c` 的一行退出码逻辑：SIGINT/SIGTERM 会置 `exit_req` 让 runner 提前停止，但退出状态只反映失败用例数，于是「被中断且已跑完的用例都没失败」会返回 0，被调用方（CI）当成通过。改成 `failed > 0 || exit_req` 即返回 1。v1 于 09-06 发出，带 `Fixes: 9d851afa4826`，本日无人回帖。

## 背景与问题

`9d851afa4826 ("selftests/sched_ext: Abort test loop on signal")` 引入了信号处理：收到 SIGINT/SIGTERM 时设置 `exit_req`，主循环据此在跑完剩余用例前退出。但 `main()` 结尾仍是 `return failed > 0 ? 1 : 0;`。中断场景下 `failed` 为 0，整体退出码就是成功——把「没跑完」误报成「全通过」，对 CI 来说是最坏的一类错误。

## 技术方案

单行改动：把 `exit_req` 并入失败条件（`return failed > 0 || exit_req ? 1 : 0;`）。刻意不去新增独立的退出码或改变统计口径，结果计数仍然只覆盖实际跑过的用例，只是让「被中断」可被调用方观察到。

## 版本演进与当前进展

v1（09-06 21:54，msgid `<20260906135507.749280-1-hi@tychen.cc>`）首次发出，无重发、无回帖。作者自述的验证方式是在 GDB 下对真实 runner 注入信号。

## Maintainer 意见与讨论焦点

截至本日邮件，无维护者回帖，也未见 `Acked-by`/`Reviewed-by`。补丁本身没有语义争议点：它只让一个原本被吞掉的失败条件可见。作者同样标注了 `Assisted-by: LLM`。

## 合入评估

`likelihood=likely`。依据：单行、方向明确（把中断显式视为非成功）、带 `Fixes:` 指向引入该行为的那个 commit、且给出了四种注入场景的前后对比。改动不可能引入内核侧回归，测试树维护者可直接 take。卡点：本日前无人回帖；唯一可能的分歧是「被中断」是否应该与「失败」共用同一个退出码 1（而非用独立的 exit code 区分），邮件中未见这类讨论。

## 效果评估

邮件中未提供性能数据，给出的是行为验证：在 GDB 下分别于「首个用例之前」和「示例用例通过之后」投递 SIGINT 与 SIGTERM，共四种组合，原始 runner 四种情况全部返回 0，修复后返回 1；正常的 `-h`、`-l`、`-t example` 调用仍然返回 0。

## 我可以参与的点

- 最直接的贡献是把它接到 CI 上验证：在有超时/中断的 sched_ext 测试作业里确认中断现在会产生非零退出码，顺便看是否有别的用例因这个改动而暴露出此前被掩盖的中断。
- 如果 OLK 的调度器 CI 也用了 sched_ext selftests 的 runner，注意该改动会让「人为 Ctrl-C / 超时杀进程」变成 FAIL，需要在流水线里区分对待，否则会出现难以解释的红灯。
- 可以顺手复核 runner 中其它以 `exit_req` 提前 break 的统计口径（`failed`/`passed` 计数是否也应符合「只统计实际跑过的用例」这一描述），邮件中作者声称如此但只有一行代码，值得核一遍。

## 参考链接

- 本补丁: https://lore.kernel.org/all/20260906135507.749280-1-hi@tychen.cc/
- tip-bot commit: 未获取到
- stable backport: 未获取到
- 相关：[[sched-20260906-001]]

---
id: sched-20260906-003
date: '2026-09-06'
subject: 'selftests/sched_ext: Fail interrupted test runs'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260906135507.749280-1-hi@tychen.cc>
lore_url: https://lore.kernel.org/all/20260906135507.749280-1-hi@tychen.cc/
upstream_commit: null
fixes_commit: 9d851afa4826
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Tianyi Chen
maintainers_involved: []
patch_series:
- version: v1
  msgid: <20260906135507.749280-1-hi@tychen.cc>
  date: '2026-09-06'
  summary: 'selftests/sched_ext/runner.c：SIGINT/SIGTERM 置 exit_req 使 runner 提前停止，但退出码只反映 failed 计数，被中断且已完成用例全通过时返回 0。改为 return failed > 0 || exit_req ? 1 : 0，让调用方能区分被中断与成功；结果计数仍只统计实际跑过的用例。runner.c 单行改动（+1/-1）。'
  review_outcome: 截至本日无回帖、无 Acked-by/Reviewed-by
merge_assessment:
  likelihood: likely
  blocking_issues:
  - 本日前无人回帖，仍缺维护者 ack
  - 潜在分歧：被中断是否应与真实失败共用退出码 1，邮件中未见讨论
  next_action: 等待 sched_ext 维护者 take；可在 CI 上确认中断现在会产生非零退出码
contribution_opportunities:
- kind: testing
  description: 在带超时/人为中断的 sched_ext 测试作业里跑该 runner，确认退出码变化并检查是否有此前被掩盖的中断用例开始暴露
- kind: review
  description: 复核 runner.c 中其它依赖 exit_req 提前退出的统计口径，确认 failed/passed 计数确实只覆盖实际跑过的用例
source_email_count: 1
related_articles:
- sched-20260906-001
tags:
- sched_ext
---
