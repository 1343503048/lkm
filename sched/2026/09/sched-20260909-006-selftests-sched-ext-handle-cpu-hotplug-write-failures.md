# selftests/sched_ext: Handle CPU hotplug write failures

## TL;DR

本文为增量更新，`hotplug.c` 丢 write 返回值导致测试无限挂住的完整分析见 related_articles 中的 sched-20260906-002。09-09 02:01 Tejun Heo 回「Applied to sched_ext/for-7.4」收下这枚补丁——从此一次失败的 CPU 状态写入会让用例立刻判 FAIL，而不是把真实失败伪装成 3 秒以上的挂起。

## 背景与问题

`test_hotplug()` 靠写 `/sys/devices/system/cpu/cpu1/online` 制造 offline/online 转换，然后等 `UEI_EXITED()`。原先 `toggle_online_status()` 只在 `ret != 0` 时 fprintf 一句，返回值不传出。写失败时状态根本没变、期望的调度器退出不会发生，测试就在 `while (!UEI_EXITED(...)) sched_yield();` 上无限自旋。正常路径里「恢复 CPU」的那次写同样没人检查。

## 技术方案

`toggle_online_status()` 返回 `file_write_long()` 的结果；`test_hotplug()` 引入 `status = SCX_TEST_FAIL` 与 `out_destroy_link` / `out_destroy_skel` 两条错误出口：onlining 用例在初始 offline 失败时直接销毁 skel，中途恢复失败时先销毁 link 再走清理，`!onlining` 分支的恢复写同样判失败；只有全部成功才置 `SCX_TEST_PASS`。错误路径刻意不自己把 CPU 拉回来，而是释放调度器资源后交给既有 cleanup 回调重试恢复 CPU1。+23/-11，全在测试代码内。

## 版本演进与当前进展

- v1（09-06 21:55，`<20260906135534.749534-1-hi@tychen.cc>`，`Fixes: a5db7817af78 ("sched_ext: Add selftests")`，标注 `Assisted-by: LLM`）。
- 09-09 02:01 Tejun Heo 回 "Applied to sched_ext/for-7.4."（`<47ce114f204b0c2f630bcdb2900cd5b0@kernel.org>`），无 v2。

## Maintainer 意见与讨论焦点

无意见，直接收取。09-06 那篇里我列的两个关注点——错误路径依赖 cleanup 回调恢复 CPU1 而非就地重试、以及该改动会改变既有用例的失败语义（原本挂住的场景开始返回 1）——维护者本日都没有回应，按「未被质疑但也没被背书」记录。同日该作者另外两枚测试补丁一枚被直接收取、一枚被打回，本补丁属于前者。

## 合入评估

`likelihood=merged`。已进 `sched_ext/for-7.4`。测试树小修，无需 tip 流程，风险只在语义变化本身：以前表现为挂起的场景现在会立刻 FAIL，若有人依赖该用例的「超时」行为，会看到新的红灯。

## 效果评估

无性能数据，作者给的是故障注入验证：在双 vCPU VM、内核与 selftests 同源构建下，用 strace 向 10 次 CPU 状态 write 逐个注入 EIO，修复后测试返回 1，且 cleanup 之后 CPU1 仍在线、sched_ext 处于 disabled；原始测试只要前两次写中任意一次失败就 3 秒内无法结束。把 online 文件设为只读同样能产生失败而不挂起；正常 hotplug 用例修改前后都通过。均为作者自测，未见第三方复核。

## 我可以参与的点

- `testing`：在支持 hotplug 的机器（尤其带 `CONFIG_CPU_HOTPLUG` 限制或不可热插的 CPU0 平台）上跑这个用例，确认「恢复失败也算 FAIL」在新的 CPU 拓扑上不会误报。
- `review`：同类模式在 selftests 里通常不止一处——可以把 `tools/testing/selftests/` 下其它「写了但丢弃返回值然后轮询等待」的地方扫一遍，那类问题一律表现为挂起而非失败。

## 参考链接

- v1 补丁: https://lore.kernel.org/all/20260906135534.749534-1-hi@tychen.cc/
- Tejun Heo 收取回帖: https://lore.kernel.org/all/47ce114f204b0c2f630bcdb2900cd5b0@kernel.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: "sched-20260909-006"
date: "2026-09-09"
subject: "selftests/sched_ext: Handle CPU hotplug write failures"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "20260906135534.749534-1-hi@tychen.cc"
lore_url: "https://lore.kernel.org/all/47ce114f204b0c2f630bcdb2900cd5b0@kernel.org/"
upstream_commit: null
fixes_commit: "a5db7817af78"
merged_branch: "sched_ext/for-7.4"
current_version: v1
generated_at: "2026-09-10T00:40:00"
authors:
  - "Tianyi Chen"
maintainers_involved:
  - "Tejun Heo"
patch_series:
  - version: v1
    msgid: "20260906135534.749534-1-hi@tychen.cc"
    date: "2026-09-06"
    summary: "hotplug.c 的 toggle_online_status() 返回 write 结果；test_hotplug() 新增 SCX_TEST_FAIL 初值与 out_destroy_link/out_destroy_skel 两条错误出口，必需的 CPU 状态写失败即判 FAIL 并释放调度器资源，由既有 cleanup 回调重试恢复 CPU1；正常恢复写失败也判 FAIL。+23/-11。"
    review_outcome: "09-09 02:01 Tejun Heo 回复 Applied to sched_ext/for-7.4，直接收取。"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "等待随 sched_ext/for-7.4 进入 mainline；关注失败语义变化后是否有依赖原挂起行为的用例转红"
contribution_opportunities:
  - kind: testing
    description: "在 CPU 拓扑各异的机器上跑该 hotplug 用例，确认「恢复失败也算 FAIL」在 CPU0 不可热插等平台上不会误报"
  - kind: review
    description: "在 tools/testing/selftests 下排查其它「写后丢弃返回值再轮询等待」的地方，那类缺陷一律表现为挂起而非失败"
source_email_count: 1
related_articles:
  - "sched-20260906-002"
tags:
  - "sched_ext"
  - "affinity"
---
