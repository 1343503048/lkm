# sched: Restart fair hrtick after same-task repicks

## TL;DR
Shubhang Kaushik 的 v3：fair hrtick 是一次性定时器，hrtick 到期后的 same-task repick 会跳过 `set_next_task_fair()`，导致下一个公平抢占点没有 armed 的 hrtick，造成调度延迟。方案引入 `SNT_REPICK` 区分 next==prev 路径。v3 按 Zhan Xusheng 上轮意见**去掉了 SCHED_DEADLINE 的 SNT_REPICK rearm**（DL 的 `put_prev_task_dl()` 会被跳过、`dl_se->runtime` 可能陈旧）。本日 Zhan Xusheng 给出 Reviewed-by，合入概率中等偏上。

## 背景与问题
fair hrtick 是 one-shot 定时器。hrtick 到期触发 `resched_curr()` 后进入 `schedule()`，若 `pick_task_fair()` 又选中同一任务，`put_prev_set_next_task(rq, prev, next)` 因 `next == prev` 直接返回，不经过 `set_next_task_fair()`，于是没有新 hrtick 被 armed——下一个公平抢占点丢失，任务得以超时运行。

## 技术方案
在 `next == prev` 路径引入 `SNT_REPICK` 枚举值，让 `set_next_task()` 在 repick 场景被调用；`set_next_task_fair()` 对 `SNT_REPICK` 跳过任务切换工作、只重启 fair hrtick。`hrtick_start()` 在 `schedule()` 期间记录延迟，`hrtick_schedule_exit()` 重新 arm 定时器。各调度类（rt/stop/fair/idle/deadline/ext）的 `set_next_task()` 签名从 `bool first` 改为 `enum snt_e type`；DL 与其它非 fair 类对 `SNT_REPICK` 直接返回（不重启 DL hrtick）。

## 版本演进与当前进展
- **v3**（本日 105793，`<20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org>`）：按 Zhan Xusheng 意见去掉 v2 里 SCHED_DEADLINE 的 SNT_REPICK hrtick rearm。
- v2/v1 回顾：v2 把 fair 专属 rearm 状态换成 `SNT_REPICK`、同时重启 fair 与 DL；v1 为初始实现。完整背景见 sched-20260914-009。

## Maintainer 意见与讨论焦点
- **Zhan Xusheng（reviewer）**：本日给出 `Reviewed-by`，并补充技术论证——`put_prev_task_fair()` 对 next==prev 同样被跳过，但 fair 因 `rq->cfs.curr` 持有实体、`pick_task_fair()` 的 `update_curr_eevdf()` 恰好刷新 `hrtick_start_fair()` 读取的实体，DL 没有对应物；建议给 `SNT_NORMAL` vs `SNT_PICK` 补注释以免三函数之外悄悄破坏不变量；用编译器验证过转换（逐类改回 bool 会编译失败），rt/stop/fair/idle/deadline W=1 干净，ext.c 因 BTF/pahole 缺失未编译但改名安全。
- 无 NAK；遗留项仅注释与 ext.c 的编译验证。

## 合入评估
likelihood=medium。修复目标明确、带实测延迟数据、已获 Reviewed-by，但尚未有 sched 维护者 Ack，且 `SNT_NORMAL/SNT_PICK` 语义注释与 ext.c 的 BTF 编译验证尚未完成。blocking_issues：无实质阻塞，待维护者评审 + 补注释/ext 编译验证。next_action：作者补注释、请有 BTF 环境者编译 ext.c，等维护者收取。

## 效果评估
作者测试（HRTICK + DELAY_DEQUEUE，base_slice_ns=3000000）：p90 延迟 3.998ms→3.053ms，p99 5.144ms→4.533ms。HRTICK_DL stress-ng 冒烟测试 baseline 与 v3 均完成 2691 bogo ops、无新增 dmesg 告警；`CONFIG_HIGH_RES_TIMERS=n`（禁用 HRTICK）也能正常启动并跑完 stress-ng。Zhan 4 CPU 开机 + panic_on_warn=1 下四个 spinner 干净，未复现延迟数字。

## 我可以参与的点
- kind=testing：在带 BTF 的环境编译 `CONFIG_SCHED_CLASS_EXT`，验证 ext.c 的 `set_next_task_scx()` 改名后无遗漏。
- kind=review：核对 `SNT_REPICK` 下 DL/RT 直接返回是否覆盖所有 next==prev 场景、无副作用遗漏。

## 参考链接
- v3 patch：https://lore.kernel.org/all/20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org/
- Zhan Xusheng Reviewed-by：https://lore.kernel.org/all/20260916032150.487242-1-zhanxusheng@xiaomi.com/

---
id: sched-20260916-017
date: '2026-09-16'
subject: 'sched: Restart fair hrtick after same-task repicks'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org>'
lore_url: 'https://lore.kernel.org/all/20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org/'
authors:
  - 'Shubhang Kaushik'
maintainers_involved: []
current_version: v3
patch_series:
  - version: v3
    msgid: '<20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org>'
    date: '2026-09-15'
    summary: 'SNT_REPICK 重启 fair hrtick，按意见去掉 DL rearm'
    review_outcome: 'Zhan Xusheng Reviewed-by'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: '补注释、请有 BTF 环境者编译 ext.c，等维护者收取'
contribution_opportunities:
  - kind: testing
    description: '在带 BTF 环境编译 CONFIG_SCHED_CLASS_EXT 验证 set_next_task_scx 改名'
  - kind: review
    description: '核对 SNT_REPICK 下 DL/RT 直接返回是否覆盖所有 next==prev 场景'
generated_at: '2026-09-17T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260914-009
tags:
  - cfs
---