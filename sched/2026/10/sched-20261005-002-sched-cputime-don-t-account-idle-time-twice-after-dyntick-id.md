# sched/cputime: Don't account idle time twice after dyntick-idle

> **subject**：`sched/cputime: Don't account idle time twice after dyntick-idle`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261004-002：Stian Halseth 报告 v7.2-rc1 起回归——NO_HZ_IDLE + TICK_CPU_ACCOUNTING 下 `/proc/stat` idle 时间**超过墙钟时间**（SPARC T7-1 最差 CPU 1.44x、Opteron 3.7ms 唤醒负载 +13.1%），根因指向 cf6444c3e1bb（统一 idle cputime 记账）后 dyntick-idle 记账与重启 tick 首个整周期记账重叠双计；修复思路已有但未发。`#regzbot introduced: cf6444c3e1bb`。
- sched-20261005-002（今天）：**修复补丁正式发出**（`Fixes: cf6444c3e1bb7`，3 文件 +49/−11）——`kernel_cpustat` 新增 `idle_dyntick_entry`/`idle_tick_overlap` 两个字段，`kcpustat_dyntick_stop()` 记录「tick 停止时已过掉的周期份额」，首个 tick 经新增 `tick_cputime()` 只记 `TICK_NSEC − overlap`。六组实测全部回到 1.000x（SPARC 1.44→1.0000、KVM guest 1.53→0.998）。**Frederic Weisbecker（涉事代码维护者）当日即回复**：确认思路成立（"That makes sense"），并指出一个嵌套场景 bug——idle 退出后很快重入时 `kcpustat_dyntick_start()` 会覆盖前一次 overlap，首个 tick 应扣除两次 overlap 之和（但仅对 tick X 有效，下一周期须忽略旧 overlap）；另要求 `#ifdef` 换成 `IS_ENABLED()`。Leemhuis 把 Ahmed Shaltout 的疑似同款报告拉进 CC。未解释残余：steal time + 3.7ms 睡眠下 +0.3%~+1.3%。

## 背景与问题

（承接 sched-20261004-002）cf6444c3e1bb 统一 idle cputime 记账后，dyntick-idle 时间与 tick 采样共用 `cpustat[CPUTIME_IDLE]`：idle 退出时 `kcpustat_dyntick_stop()` 已把 idle 时间计到「现在」，而重启的 tick 沿用旧周期，首个 tick 又整记一个 `TICK_NSEC`——idle 退出前的那段被记两遍。影响所有 NO_HZ_IDLE + TICK_CPU_ACCOUNTING 配置，高频短睡眠负载最严重（每次停/启循环约多计半个 tick）。今天补丁落地，问题本身未变；新增暴露的子问题是「idle 退出后短期内重入」时 overlap 的覆盖丢失（Frederic 指出）。

## 技术方案

补丁（`<20261004184701.4112237-1-stian@itx.no>`，v1）：

- `struct kernel_cpustat` 新增 `idle_dyntick_entry`（dyntick 进入时刻）与 `idle_tick_overlap`（本次 idle 与 tick 周期的重叠量），均在 `CONFIG_HAVE_VIRT_CPU_ACCOUNTING_IDLE=n` 路径下生效。
- `kcpustat_dyntick_stop(now, tick_start)`（签名加参）：`tick_start = max(tick_start, idle_dyntick_entry)`，若 `now > tick_start` 则 `idle_tick_overlap = now − tick_start`——即记录「idle 结束时，当前 tick 周期里已经被 idle 记账覆盖的部分」。
- `kcpustat_dyntick_start()`：记录 `idle_dyntick_entry = now`、清零 overlap。
- 新增 `tick_cputime()`：`TICK_NSEC − __this_cpu_xchg(kernel_cpustat.idle_tick_overlap, 0)`；`account_process_tick()` 与 `irqtime_account_process_tick()` 的记账量从「整 TICK_NSEC × ticks」改为按此函数取值（`irqtime_account_process_process_tick` 的参数从 `int ticks` 改为 `u64 cputime`）。
- tick-sched.c 侧在 tick 停止/重启路径携带周期起点信息（+23/−3）。

测试方法：`/proc/stat` 对比 `CLOCK_MONOTONIC`，30-60s 窗口、单 CPU 循环睡眠任务；覆盖 IRQ_TIME_ACCOUNTING 开/关、highres=off、KVM steal time、强制每轮 idle 重启 tick 的 test-only 改动。

**Frederic 的 review**（`<asOK7M4Re5aYqmsl@localhost.localdomain>`）：

- 嵌套场景：`TICK_NSEC=100`、`next_tick=X`；第一次停/启 `overlap=10`（X−80 退出），schedule 后 tick 未触发即再次停/启 `overlap=5`（X−5 退出）——第二次 start 覆盖了前一次的 10。tick X 应记 `TICK_NSEC − 15` 而非 `TICK_NSEC − 5`；且只对 tick X 有效，X+TICK_NSEC 的下一周期须忽略旧 overlap。
- 风格：`Please use IS_ENABLED()`。
- 作者自述「sleep deprived」请对方复核——该分析按其自评尚需二次确认。

## 版本演进与当前进展

- 10-04：回归报告 + regzbot 登记（sched-20261004-002）。
- 10-05（今天）：修复 v1 发出（`<20261004184701.4112237-1-stian@itx.no>`，`Fixes: cf6444c3e1bb7`）；Frederic 当日 review（嵌套 overlap + IS_ENABLED）；Leemhuis（`<26e8c75d-a2d1-4803-a369-be38acc13af5@leemhuis.info>`）CC Ahmed Shaltout（其 10 月初报告疑似同款问题：`E76BE609-83E4-4FB6-88B8-191F7816EFD6@gmail.com`）。

## Maintainer 意见与讨论焦点

- **Frederic Weisbecker**（tick/cputime 一线维护者、cf6444c3e1bb 相关代码作者圈）：思路认可 + 一个正确性边界（嵌套 overlap 覆盖）+ 一个风格要求（IS_ENABLED）。这是该回归首度获得维护者级 review。
- **Thorsten Leemhuis**（regression tracker）：主动关联 Ahmed Shaltout 的独立报告，扩大验证样本。
- **Stian Halseth**（作者）：正文自曝未解释残余（steal + 3.7ms 睡眠 +0.3%~+1.3%）；嵌套场景尚未回应。
- 焦点：overlap 累积的正确性（Frederic 场景是否真实出现在 tick 停止→重启→再停止的紧凑序列中）；残余误差归属（作者已论证 -1.8% 是 hypervisor 迟投递、无物记账，+0.3%~+1.3% 未解释）。

## 合入评估

*likelihood=high*。回归真实、根因清晰、维护者当日即回复且未质疑方向、修复带六组量化数据与 `Fixes:` 标签；剩一个已点名的边界修正（嵌套 overlap）与风格项。*blocking_issues*：嵌套 overlap 场景需 v2 处理（累积两次 overlap 且只对首个 tick 生效）；`IS_ENABLED()` 风格项；+0.3%~+1.3% 残余未解释（非阻塞）。*next_action*：作者按 Frederic 意见发 v2，随后进 tick/sched 紧急修复通道（regzbot 已跟踪，回归在 v7.2 系列，回合 stable 可能性高）。

## 效果评估

量化充分（作者自测，/proc/stat 对比 CLOCK_MONOTONIC，60s 窗口）：

| 平台 | 负载 | 修复前 | 修复后 |
|---|---|---|---|
| SPARC T7-1, HZ=100 | 正常负载最差 CPU（~95 tick 停/s） | 1.44 | 1.0000 |
| SPARC T7-1, HZ=100 | 3.7ms 睡眠 | — | 1.0001 |
| SPARC T7-1, HZ=100 | 25ms 睡眠 | — | 0.9996 |
| Opteron, HZ=1000 | 3.7ms 睡眠 | 1.131 | 0.999 |
| x86_64 KVM guest, HZ=250 | 3.7ms 睡眠 | 1.53 | 0.998 |
| 同 guest | 9ms 睡眠 | 1.195 | 0.982 |

-1.8%（长睡眠 guest）经作者论证为 idle tick 迟投递、无物可记（迟滞量与观测差值 2ms/s 内吻合，steal time 下 8ms/s 内），修复前被双计掩盖；T7-1 上在噪声内。steal + 3.7ms 睡眠下 +0.3%~+1.3% 未解释。

## 我可以参与的点

- `review`：复核 Frederic 的嵌套场景——构造「tick 停止→重启→tick 未触发→再停止」的紧凑序列（或用作者提供的 test-only 强制重启补丁），确认 overlap 覆盖丢失是否真实可达，为 v2 的累积逻辑提供触发证据。
- `testing`：在 CONFIG_VIRT_CPU_ACCOUNTING_GEN（vtime）配置下复测——该路径走 `kcpustat_dyntick_*` 的 stub（本补丁不覆盖），确认 vtime 内核无同款双计，补全 Frederic 关注的配置矩阵。
- `testing`：按 Leemhuis 的关联，跟进 Ahmed Shaltout 报告的场景是否被本补丁覆盖（其报告现象是否消失），在 regzbot 线程回报结果。

## 参考链接

- 修复补丁 v1: https://lore.kernel.org/all/20261004184701.4112237-1-stian@itx.no/
- Frederic review: https://lore.kernel.org/all/asOK7M4Re5aYqmsl@localhost.localdomain/
- Leemhuis 关联 Ahmed 报告: https://lore.kernel.org/all/26e8c75d-a2d1-4803-a369-be38acc13af5@leemhuis.info/
- 回归报告（10-04）: https://lore.kernel.org/all/20261004142724.3896396-1-stian@itx.no/
- Ahmed Shaltout 疑似同款报告: https://lore.kernel.org/all/E76BE609-83E4-4FB6-88B8-191F7816EFD6@gmail.com/

---
id: sched-20261005-002
date: '2026-10-05'
subject: 'sched/cputime: Don''t account idle time twice after dyntick-idle'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20261004184701.4112237-1-stian@itx.no>'
lore_url: 'https://lore.kernel.org/all/20261004184701.4112237-1-stian@itx.no/'
authors:
  - 'Stian Halseth'
maintainers_involved:
  - 'Frederic Weisbecker'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261004184701.4112237-1-stian@itx.no>'
    date: '2026-10-05'
    summary: '记录 dyntick-idle 与 tick 周期重叠量，首个 tick 剔除重叠部分'
    review_outcome: 'Frederic 认可思路；指出嵌套 overlap 覆盖丢失 + IS_ENABLED 风格项'
related_articles:
  - sched-20261004-002
upstream_commit: null
fixes_commit: 'cf6444c3e1bb'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: '嵌套 overlap 场景需 v2 修正；IS_ENABLED 风格项'
  next_action: 'v2 处理 Frederic 意见后进 tick/sched 修复通道'
generated_at: '2026-10-06T01:00:00'
---
