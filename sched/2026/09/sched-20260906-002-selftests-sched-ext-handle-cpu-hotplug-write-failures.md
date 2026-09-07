# selftests/sched_ext: Handle CPU hotplug write failures

## TL;DR

Tianyi Chen 修 `tools/testing/selftests/sched_ext/hotplug.c`：`toggle_online_status()` 会打印 CPU 状态变更失败的日志，但把 write 的返回值丢掉，于是一次失败的 offline 写永远不会触发测试在等的调度器退出，用例无限挂住。改为返回 write 结果、在必需的 CPU 状态变更失败时同时终止两个 hotplug 用例并释放已获取的调度器资源，交给既有 cleanup 回调重试恢复 CPU1。v1 于 09-06 发出，带 `Fixes: a5db7817af78`，本日无人回帖。

## 背景与问题

`test_hotplug()` 通过写 `/sys/devices/system/cpu/cpu1/online` 制造 offline→online（或反向）转换，再等待 `UEI_EXITED()`。但 `toggle_online_status()` 只做 `if (ret != 0) fprintf(stderr, ...)`，返回值不传出。写失败时状态没变、期望的调度器退出根本不会发生，测试就在 `while (!UEI_EXITED(...)) sched_yield();` 上无限自旋，把一个真实失败伪装成挂起。此外正常路径里「恢复 CPU」的写同样无人检查失败。

## 技术方案

`toggle_online_status()` 返回 `file_write_long()` 的结果；`test_hotplug()` 引入 `status = SCX_TEST_FAIL` 与两条错误出口 `out_destroy_link` / `out_destroy_skel`：onlining 用例在初始 offline 失败时直接销毁 skel，中途恢复失败时先销毁 link 再走清理，`!onlining` 分支的恢复写同样判失败；只有全部成功才置 `SCX_TEST_PASS`。设计上刻意不在错误路径里自己把 CPU 拉回来，而是释放调度器资源后由既有 cleanup 回调重试恢复 CPU1。改动 +23/-11，全在测试代码内。

## 版本演进与当前进展

v1（09-06 21:55，msgid `<20260906135534.749534-1-hi@tychen.cc>`）首次发出，无重发、无回帖。补丁自述的验证是在双 vCPU VM、内核与 selftests 同源构建下完成。

## Maintainer 意见与讨论焦点

截至本日邮件，无维护者回帖，也未见任何 `Acked-by`/`Reviewed-by`（Tejun Heo 本日未回）。作者自行处理的两处值得注意：一是错误路径选择依赖 cleanup 回调恢复 CPU1，而非就地重试；二是补丁按当前上游惯例标注了 `Assisted-by: LLM`。这两点目前都没有异议，但也没有人背书。

## 合入评估

`likelihood=medium`。有利因素：改动完全局限在 `tools/testing/selftests/sched_ext/`，带 `Fixes: a5db7817af78 ("sched_ext: Add selftests")`，且给出了可复现的注入式验证。卡点：本日前无任何 review；该补丁会改变既有用例的失败语义（原本挂住的场景开始返回 1、恢复 CPU 失败也算 FAIL），维护者可能要求同时说明 CI 上是否会出现新的红灯。属测试树小修，通常由 sched_ext 维护者直接收，无需 tip 流程。

## 效果评估

邮件中未提供性能数据，给出的是测试正确性数据：用 strace 向 10 次 CPU 状态 write 逐个注入 EIO，修复后测试返回 1、CPU1 仍在线、cleanup 之后 sched_ext 处于 disabled；原始测试只要前两次写中任意一次失败就 3 秒内无法结束。把 online 文件设为只读同样能产生失败而不挂起；正常 hotplug 用例修改前后都通过。

## 我可以参与的点

- review 具体点：`test_hotplug()` 里原本就存在直接 `return SCX_TEST_FAIL` 的早退分支，本次新增的是两条 goto 出口，值得核对所有分支（尤其 `cbs_defined` 时写 `SCX_KIND_VAL(SCX_EXIT_UNREG_BPF)` 的路径）在 link/skel/调度器资源的释放上是否一致，别留下新的泄漏或 CPU 卡在 offline 的状态。
- 帮跑验证：把这套 selftests 在真机（非双 vCPU VM）与不同 CPU 拓扑下重复 EIO 注入，确认 cleanup 回调恢复 CPU1 的可靠性，是对维护者最直接的补充信息。
- 回合提示：若 OLK 分支把 sched_ext selftests 一并带上了，这个补丁会让原本挂死的用例开始返回 FAIL——回合时要同时调整 CI 的期望值，否则会误判为新增回归。

## 参考链接

- 本补丁: https://lore.kernel.org/all/20260906135534.749534-1-hi@tychen.cc/
- tip-bot commit: 未获取到
- stable backport: 未获取到
- 相关：[[sched-20260906-001]]

---
id: sched-20260906-002
date: '2026-09-06'
subject: 'selftests/sched_ext: Handle CPU hotplug write failures'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260906135534.749534-1-hi@tychen.cc>
lore_url: https://lore.kernel.org/all/20260906135534.749534-1-hi@tychen.cc/
upstream_commit: null
fixes_commit: a5db7817af78
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Tianyi Chen
maintainers_involved: []
patch_series:
- version: v1
  msgid: <20260906135534.749534-1-hi@tychen.cc>
  date: '2026-09-06'
  summary: selftests/sched_ext/hotplug.c 的 toggle_online_status() 记录 CPU 状态变更失败日志却丢弃 write 返回值，hotplug 用例因此可能在一次从未触发的调度器退出上无限等待。改为返回 write 结果，必需的 CPU 状态变更失败时终止两个 hotplug 用例（新增 out_destroy_link/out_destroy_skel 出口）、释放已获取的调度器资源，由既有 cleanup 回调重试恢复 CPU1；正常恢复 CPU 失败同样判 FAIL。+23/-11。
  review_outcome: 截至本日无回帖、无 Acked-by/Reviewed-by
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 本日前无任何维护者 review 背书
  - 改变了既有用例的失败语义（挂住变成返回 1、恢复 CPU 失败也算 FAIL），可能需说明对 CI 的影响
  next_action: 等待 Tejun 或 sched_ext selftests 维护者回应；可先在新硬件上重复 EIO 注入验证
contribution_opportunities:
- kind: review
  description: 核对 test_hotplug() 各分支（含 cbs_defined 路径与原有的直接 return SCX_TEST_FAIL 早退）在 link/skel/调度器资源释放上是否一致，是否会把 CPU 留在 offline 状态
- kind: testing
  description: 在真机与不同 CPU 拓扑下重复 strace EIO 注入（覆盖 10 次 CPU state write），确认 cleanup 回调恢复 CPU1 的可靠性，并把结果回到线程里
source_email_count: 1
related_articles:
- sched-20260906-001
tags:
- sched_ext
---
