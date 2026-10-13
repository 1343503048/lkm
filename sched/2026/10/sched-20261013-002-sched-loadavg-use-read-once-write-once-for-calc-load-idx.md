# sched/loadavg: Use READ_ONCE/WRITE_ONCE for calc_load_idx

> **subject**：sched/loadavg: Use READ_ONCE/WRITE_ONCE for calc_load_idx

## TL;DR
Hui Su 发一枚 KCSAN 数据竞争修复：`calc_load_idx` 在 NO_HZ fold 路径被 `calc_load_write_idx()` 无锁读、在全局负载路径被 `calc_global_nohz()` 更新，但读写仍是普通 C 访问，KCSAN 报 `calc_global_load / calc_load_nohz_fold` 竞争。补丁给这两处补 `READ_ONCE()`/`WRITE_ONCE()`，保持既有 `smp_wmb()/smp_rmb()` 顺序不变，改动 2 行。

## 背景与问题
NO_HZ fold 路径从 `calc_load_write_idx()` 无锁读 `calc_load_idx`，而 `calc_global_nohz()` 在 jiffies_lock 串行化的全局路径更新它。此前 commit `caeb5882979b`（"sched/loadavg: Use {READ,WRITE}_ONCE() for sample window"）已给 `calc_load_update` 补过 ONCE 访问，但 `calc_load_idx` 参与同一跨 CPU 协议、顺序由既有 `smp_wmb()/smp_rmb()` 对保证，其访问却仍是普通 C 访问。KCSAN 观察到并发访问：

```
BUG: KCSAN: data-race in calc_global_load / calc_load_nohz_fold
write by interrupt on cpu 3:  calc_global_load+0x392/0x420 ...
read by task 0 on cpu 5:     calc_load_nohz_fold+0x7a/0x110 ...
value changed: 0x00000033 -> 0x00000034
```

`Fixes: 5167e8d5417b ("sched/nohz: Rewrite and fix load-avg computation -- again")`。

## 技术方案
单补丁 `kernel/sched/loadavg.c`（+2/−2）：
- `calc_load_write_idx()` 里 `int idx = calc_load_idx;` → `int idx = READ_ONCE(calc_load_idx);`
- `calc_global_nohz()` 里 `calc_load_idx++;` → `WRITE_ONCE(calc_load_idx, READ_ONCE(calc_load_idx) + 1);`

保持既有内存顺序与写者串行化不变；`calc_load_read_idx()` 只被 jiffies_lock 串行化的全局路径使用，无需访问器。

## 版本演进与当前进展
v1 今日首发（`<20261013142552.262520-1-sh_def@163.com>`），暂无 review 或回帖。

## Maintainer 意见与讨论焦点
当日无回帖、无维护者表态。

## 合入评估
*likelihood=high*（评审无异议待收取）。KCSAN 数据竞争修复的改动极小、方向标准（与既有 `calc_load_update` 的 ONCE 处理一致）、带准确 `Fixes:` 标签。*blocking_issues*：尚无 review。*next_action*：等 SCHED 维护者 review 后收取。

## 效果评估
无性能数字；补丁作者明示「保持既有内存顺序与写者串行化不变」，即不改变行为、仅消除 KCSAN 噪声（修复的是数据竞争诊断，非功能/性能问题）。

## 我可以参与的点
当前阶段暂无明显参与空间，改动极小且为标准 KCSAN 风格修复；可持续观察是否被收取。

## 参考链接
- 补丁 lore：https://lore.kernel.org/all/20261013142552.262520-1-sh_def@163.com/

---
id: sched-20261013-002
subject: 'sched/loadavg: Use READ_ONCE/WRITE_ONCE for calc_load_idx'
date: 2026-10-13
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20261013142552.262520-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20261013142552.262520-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261013142552.262520-1-sh_def@163.com>'
    date: 2026-10-13
    summary: '给 calc_load_idx 的 lockless 读写补 READ_ONCE/WRITE_ONCE'
    review_outcome: '暂无 review'
upstream_commit: null
fixes_commit: '5167e8d5417b'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 'SCHED 维护者 review 后收取'
contribution_opportunities: []
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 1
related_articles: []
tags: [cfs]
---