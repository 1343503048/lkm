# sched/stats: Fix run_delay over-count for migrated sched_delayed tasks

## TL;DR
增量更新：albin_yang 的 `run_delay` 虚增修复系列本日推进——作者给出用户态 reproducer（每次在 sched_delayed 睡眠期间发生的迁移会把整段睡眠时长 ~148ms 虚算进 run_delay），Chen Yu 给出 Reviewed-by 并附机制分析；Kayra Cizmeci 纠正了 Chen Yu 关于 `can_migrate_task()` 跳过 delayed 任务的论断，指出 active load balance（`detach_one_task()`→`active_load_balance_cpu_stop()`，迁移类型未设置为 migrate_load）路径仍有让 delayed 任务被迁移的可能。

## 背景与问题
背景见 sched-20260909-017：EEVDF 的 delayed-dequeue 任务（`!entity_eligible` 被保留在 rq 上、`se.sched_delayed` 置位）在睡眠期间被迁移时，普通迁移路径 `activate_task(dst, 0)` 会在迁移时刻重设 `last_queued`，把"迁移到唤醒"这段仍处于睡眠的时长记进了 run_delay（对 `last_queued=0` 的任务 `sched_info_arrive()` 不扣减等待）。

本日作者把这条路径做成了可复现的 reproducer，坐实"真实、用户可见"的 over-count。

## 技术方案
修复本身（见 sched-20260909-017）：迁移被 delayed 的任务时不应更新其 `last_queued` 字段，因为它并未真的变得 runnable。作者 reproducer 的构造：先起背景负载（`stress-ng --cpu $(nproc-1) &`）把 min_vruntime 顶高，一个 worker 线程在 CPU0 上烧 CPU ~80ms 后 `usleep` 150ms——此时它 `!entity_eligible` 被 delayed-dequeue（"睡眠"但仍在 rq 上）；另一线程在它入睡 ~2ms 后用 `sched_setaffinity` 把它迁到 CPU1（走 `activate_task(dst,0)` 的 plain migration 路径），复刻"仍在睡眠但重设 last_queued"。

## 版本演进与当前进展
- v1（2026-09-09，`<20260909133345.1572954-1-albin_yang@163.com>`）：修复补丁（见 sched-20260909-017）。
- 本日作者回帖（`<20260919035951.509665-1-albin_yang@163.com>`）补充 reproducer 与实测数据。
- Chen Yu（`<aq5AkZq396xkL4LW@three-body>`）给出 Reviewed-by：`last_queued` 在任务切出时被 `sched_info_arrive()` 清空，"delayed 状态与 run_delay 无关"；凡被动/主动 load balance、NUMA balancing、`sched_setaffinity` 迁移都不该在重新入队 delayed 任务时更新 `last_queued`。
- Kayra Cizmeci（`<20260919102420.108000-1-kayracizmeci@gmail.com>`）纠正：`can_migrate_task()` 会跳过 delayed 任务，除非 delayed 且迁移类型非 migrate_load；但 `can_migrate_task()` 也由 `detach_one_task()`（来自 `active_load_balance_cpu_stop()`）调用，且该处自定义 env 未设置迁移类型——即迁移类型按 migrate_load 计，此路径上 delayed 任务确实能被迁移。

## Maintainer 意见与讨论焦点
- **Chen Yu**：认可修复方向，给 Reviewed-by，并从 `last_queued`/`sched_info_arrive` 语义角度给出机理说明。
- **Kayra Cizmeci**：针对 Chen Yu "`can_migrate_task()` 跳过 delayed 任务"的表述纠正具体路径（active load balance），说明修复需要覆盖的迁移来源比 Chen 描述的更广。
- 分歧/未决：无明显对立，Kayra 的纠正补强了"bug 真实存在且路径不止一条"的结论，但也提示 commit message 的迁移路径论证需更精确。

## 合入评估
likelihood=high。作者有可复现的 reproducer、Chen Yu 已 Reviewed-by、无否决意见；但尚无 sched 统计维护者的最终收取，且 Kayra 对迁移路径的纠正建议 commit message 论证修正后更稳妥。blocking_issues：迁移路径论证（尤其 active load balance 路径）需在 commit message 中澄清。next_action：作者回应 Kayra 的路径纠正、必要时补一句 active load balance 的说明，等待维护者收取。

## 效果评估
作者 20 轮迭代数据：凡迁移落在 sched_delayed 睡眠期间，run_delay 虚增 ~148.03–148.94ms（即迁移到唤醒的整段睡眠时长），verdict 均标 BUG；其余迁移未命中该窗口的轮次 run_delay 增量为 0。打补丁后所有轮次 run_delay 增量 ~0。属真实、定量的用户可见统计误差。

## 我可以参与的点
- kind=testing：用 reproducer 在自身环境（尤其是开启 NUMA balancing、主动负载均衡压力大的场景）复测，确认 active load balance 迁移路径是否同样触发。
- kind=review：帮助厘清迁移 delayed 任务的完整来源清单，校验修复是否覆盖 `detach_one_task()`/active load balance 路径。

## 参考链接
- lore（原 patch）: https://lore.kernel.org/all/20260909133345.1572954-1-albin_yang@163.com/
- lore（Chen Yu Reviewed-by）: https://lore.kernel.org/all/aq5AkZq396xkL4LW@three-body/
- lore（Kayra 纠正）: https://lore.kernel.org/all/20260919102420.108000-1-kayracizmeci@gmail.com/

---
id: sched-20260919-004
date: '2026-09-19'
subject: 'sched/stats: Fix run_delay over-count for migrated sched_delayed tasks'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260909133345.1572954-1-albin_yang@163.com>'
lore_url: 'https://lore.kernel.org/all/20260909133345.1572954-1-albin_yang@163.com/'
authors:
  - 'albin_yang'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260909133345.1572954-1-albin_yang@163.com>'
    date: '2026-09-09'
    summary: '迁移 delayed 任务时不更新 last_queued，避免 run_delay 虚增'
    review_outcome: '本日作者补 reproducer，Chen Yu Reviewed-by，Kayra 纠正迁移路径'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - 'active load balance 等迁移路径的论证需在 commit message 澄清'
  next_action: '作者回应 Kayra 的路径纠正后，等待维护者收取'
contribution_opportunities:
  - kind: testing
    description: '复测 NUMA balancing / active load balance 压力下的迁移路径'
  - kind: review
    description: '厘清迁移 delayed 任务的完整来源，校验修复覆盖'
generated_at: '2026-09-20T09:00:00'
source_email_count: 3
related_articles:
  - sched-20260909-017
tags:
  - cfs
  - sched_debug
---