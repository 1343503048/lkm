---
id: sched-20261030-017
date: 2026-10-30
subject: 'selftests: cpufreq: stop CPU hotplug loop after cpufreq update test'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261030104213.2030283-1-xiongyining1480@phytium.com.cn>
lore_url: https://lore.kernel.org/all/20261030104213.2030283-1-xiongyining1480@phytium.com.cn/
authors:
- Yining Xiong
maintainers_involved: []
current_version: v3
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无 cpufreq/kselftest 维护者的 Ack
  next_action: 等 cpufreq/kselftest 维护者 review 收取
contribution_opportunities:
- kind: testing
  description: 跑 special-tests.sh 的 hotplug 测试，确认异常中断后无残留 reboot_cpu 进程
- kind: review
  description: 核对 hotplug 子进程推迟启动后是否仍全程覆盖 hotplug 竞争
generated_at: '2026-10-31T09:00:00'
source_email_count: 3
related_articles: []
tags:
- cpufreq
title: 'selftests: cpufreq: stop CPU hotplug loop after cpufreq update test'
layout: article
---

## TL;DR
Yining Xiong 修 cpufreq selftests 的 hotplug 测试：原 `hotplug_with_updates_cpu()` 用固定 5000 次循环触发 CPU hotplug，存在①测试结束后后台 hotplug 任务仍继续跑（冗余 on/offline）、②cpufreq 频率设置慢时 hotplug 循环可能在频率更新完成前就退出（破坏测试目的）两个问题。v3 改用信号通知终止无限 hotplug 循环（`trap 'quit=1' SIGTERM` + 子进程 while 循环），并加 EXIT trap 清理 hotplug 子进程；且把 hotplug 子进程的启动推迟到 governor 切换与 sysfs 频率读取之后（避免目标 CPU 离线时 `-EBUSY`）。Zhongqiu Han 已给 **Reviewed-by**（v3）。

## 背景与问题
`tools/testing/selftests/cpufreq/special-tests.sh` 的 `hotplug_with_updates_cpu()` 通过「一边切换 governor/读写 sysfs 频率、一边对目标 CPU 反复 offline/online」来验证 cpufreq 与 CPU hotplug 的同步。两个缺陷：固定 `seq 1 5000` 循环结束后，后台 `reboot_cpu` 进程若未被回收会继续跑；且当频率 setup 较慢时，5000 次循环可能在 sysfs 频率更新真正完成前就已退出，测试失去覆盖意义。

## 技术方案
v3（`tools/testing/selftests/cpufreq/special-tests.sh`，+24/-6）：
- 把固定次数循环换成**信号驱动的无限循环**：子进程内 `trap 'quit=1' SIGTERM` + `while [ "$quit" -eq 0 ]; do reboot_cpu "$1"; done`，由主测试在完成后 `kill -s SIGTERM` 终止；
- 新增 `hotplug_cleanup()`，并在 `hotplug_with_updates()` 里挂 `trap 'hotplug_cleanup' EXIT`，异常退出时也能清理 hotplug 子进程；
- hotplug 子进程改为在 governor 切换与 `scaling_available_frequencies`/`scaling_min_freq` 读取**之后**才启动，避免目标 CPU 离线时报 `-EBUSY`。
作者还就 EXIT trap 在 SIGINT/SIGTERM/SIGHUP 下的行为做了主 shell/子 shell 两场景自测（均能触发清理）。

## 版本演进与当前进展
*current_version: v3*（2026-10-30 发出）。v1 用固定循环；v2 改用「信号通知 + EXIT trap」，但仍用 stop file（有可预测临时路径问题，被 Sashiko 指出）；v3 吸收安全/健壮性意见（信号通知代替 stop file、EXIT 清理、推迟 hotplug 启动避免 EBUSY）。

## Maintainer 意见与讨论焦点
- **Zhongqiu Han（Qualcomm，reviewer，非 maintainer）**：给 v3 **Reviewed-by**。
- **作者**：对 v2 的 review（信号 vs stop file、EXIT trap 语义）逐条回应，并在 v3 修正。
- **未解决**：cpufreq/kselftest 维护者（Rafael/Viresh/Shuah）尚未表态收取。

## 合入评估
*likelihood=medium*。已获一张 Reviewed-by、改动合理；但需维护者（Shuah 的 kselftest 或 Rafael 的 cpufreq）最终收取，当日尚无。*blocking_issues*：无维护者 Ack。*next_action*：等 cpufreq/kselftest 维护者 review 收取。

## 效果评估
无性能数据；作者给出 EXIT trap 在主/子 shell 下的行为自测（SIGINT/TERM/HUP 均能正确清理），验证了清理逻辑的健壮性。

## 我可以参与的点
- **testing**：在本地跑 `special-tests.sh` 的 hotplug 测试，确认异常中断后无残留 `reboot_cpu` 进程。
- **review**：核对 v3 中 hotplug 子进程「推迟启动」后是否仍能在频率更新全程覆盖 hotplug 竞争。

## 参考链接
- lore thread（v3）: https://lore.kernel.org/all/20261030104213.2030283-1-xiongyining1480@phytium.com.cn/
