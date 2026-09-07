# sched/debug: Validate writes to the scan_size_mb debugfs knob

## TL;DR

`scan_size_mb` 在 `task_scan_min()` 和 `task_nr_scan_windows()` 里都是除数，而 `debugfs_create_u32()` 对写入值一律接受，所以两类取值直接把内核打死：写 0 触发 divide error Oops，写 2^24 的倍数在 4K 页上让 `MB_TO_PAGES()` 的 32 位移位绕回 0 再触发一次除零。作者 09-05 以 `[PATCH v2 RESEND]` 原样重发（代码与 v2 无差别），理由是「两处写入在 v7.3-rc 仍能 panic，mainline 与 tip/sched/core 里这个 knob 仍是裸 `debugfs_create_u32()`」。补丁已带 Chen Yu 的 `Reviewed-by`，缺的是维护者收树。

## 背景与问题

`sysctl_numa_balancing_scan_size` 从 sysctl 迁到 debugfs 时丢了合法性校验：原先的 sysctl 表项用 `.extra1 = SYSCTL_ONE` 卡下界，迁移时 `tunable_scaling` 拿到了 `sched_scaling_fops` 所以保住了校验，`scan_size_mb` 退化成普通 u32，上界则从来没实现过。后果是两条独立的崩溃路径：

- 写 0：`task_scan_min()` 里 `windows = MAX_SCAN_WINDOW / scan_size` 除零，Oops 落在 `task_scan_max+0x30`（`task_scan_min()` 被内联进去），调用链 `init_numa_balancing() → __sched_fork() → sched_fork() → copy_process() → kernel_clone()`。作者特别指出触发条件是 `CLONE_VM` 的子线程而非普通 fork——新地址空间会在 `init_numa_balancing()` 提前返回。
- 写 2^24 的倍数（4K 页）：`MB_TO_PAGES()` 对 `unsigned int` 做移位，结果绕回 0，`task_nr_scan_windows()` 除零，Oops 落在 `task_nr_scan_windows.isra.0+0x5c/0x70`。

## 技术方案

- 用自定义 `file_operations`（`sched_numa_scan_size_fops`）替换 `debugfs_create_u32("scan_size_mb", ...)`，写路径 `kstrtouint_from_user(ubuf, cnt, 0, &mb)` 以 base 0 解析，保留原来 16 进制写法可用的行为。
- 校验为 `if (!mb || mb > NUMA_SCAN_SIZE_MB_MAX) return -EINVAL;`，其中 `NUMA_SCAN_SIZE_MB_MAX = (UINT_MAX >> (20 - PAGE_SHIFT))`（4K 页即 16777215），一次覆盖除零与移位绕回两类。
- 取值非法时返回 `-EINVAL` 而不是静默夹取，理由是 knob 已在 `Documentation/scheduler/sched-debug.rst` 里作为控制扫描速率的接口被文档化。
- 只动 `kernel/sched/debug.c`，+50/-1，整块包在 `#ifdef CONFIG_NUMA_BALANCING` 内。

## 版本演进与当前进展

- v1（08-10）→ v2（08-10）：唯一实质改动是按 Chen Yu 的意见把解析基数从 10 改成 0，以免 `echo 0x100 > scan_size_mb` 变成 `-EINVAL`；changelog 里点名了 `simple_attr_write_xsigned()` 这个被替换掉的 helper。
- v2 → v2 RESEND（09-05）：代码与说明「No changes since v2」，重发动机是该问题在 v7.3-rc 仍复现、主线与 tip/sched/core 仍未修。
- 同期存在**另一个人的同问题补丁**：Li RongQing（Baidu）的 `[PATCH, Resend, v2] sched/debug: Reject invalid writes to numa_balancing scan_size_mb`（最早 07-23，07-31 自己 Ping 过一次）。他用 `DEFINE_DEBUGFS_ATTRIBUTE()` + `debugfs_create_file_unsafe()`，非法值返回 `-ERANGE`，条件是 `val == 0 || val > UINT_MAX`。
- 三条记录都带同一个 `Fixes: 8a99b6833c88 ("sched: Move SCHED_DEBUG sysctl to debugfs")`；截至 09-05 两边都没有 tip-bot 收树迹象。

## Maintainer 意见与讨论焦点

- **Chen Yu（Intel）** 是这条线上唯一给实质意见的人：v1 上先提「`kstrtouint_from_user(ubuf, cnt, 0, &mb)?`」并解释被替换的 `debugfs_create_u32()` 路径在 `simple_attr_write_xsigned()` 里用的是 base 0，然后「Others look ok to me, with above fix... Reviewed-by: Chen Yu」。该 `Reviewed-by` 已带进 v2 与 v2 RESEND 的 commit message。
- Chen Yu 同时也是本仓库当天另一条 cache-aware 修复（`nr_pref_llc_running`，同日另一篇）的建议人，说明他在持续跟踪 `sched/cache` / NUMA balancing 调试接口这一片区域。
- **Peter Zijlstra / Ingo Molnar 在这批缓存正文里没有回帖**——这是该补丁三周没能进树的实际卡点，而非技术异议。
- 两个系列之间**没有人互相引用**，正文里看不到任何「谁取代谁」的讨论。

## 合入评估

**likelihood: likely**（作为带 `Fixes:` + `Reviewed-by:` 的独立修复被收进 tip/sched/core 或 sched/urgent）。

依据：可稳定复现的内核 panic、根因清楚（debugfs 迁移丢校验）、改动局部且只碰 `kernel/sched/debug.c`、已有 NUMA balancing 方向的 `Reviewed-by`、作者还额外确认了 tip/sched/core 上问题依旧。

卡点：与 Li RongQing 的同问题补丁撞车，维护者需要二选一或者被要求合并两者意见；两个方案在**覆盖面上不等价**——Li 版只拒 0 与超过 `UINT_MAX`，`2^24`（16777216）小于 `UINT_MAX` 会被接受，因此 `MB_TO_PAGES()` 绕回那条路径依然会 panic，Zhan 版两条都拒；另外返回码风格不一致（`-ERANGE` vs `-EINVAL`）以及 `debugfs_create_file_unsafe()` vs `debugfs_create_file()` 的取舍。缺 tip 维护者表态；无 `Cc stable`（`8a99b6833c88` 属较早改动，是否走 -stable 由维护者决定）。

## 效果评估

邮件给的是正确性验证而非性能数据：2 节点 qemu guest 上，未打补丁的 v7.2-rc6 两次写入分别在上面两个 RIP 处 panic；打上补丁后写 0、`2^24`、`3*2^24` 均得到 `-EINVAL`，写 512 正常生效。v2 RESEND 另补充在 v7.3-rc 上两处 panic 依旧成立。无调度性能数据。

## 我可以参与的点

- 最有价值的一条回帖：直接指出 Li RongQing 版未覆盖 `MB_TO_PAGES()` 移位绕回（`val > UINT_MAX` 在 4K 页下挡不住 `2^24`），并给出 `NUMA_SCAN_SIZE_MB_MAX = UINT_MAX >> (20 - PAGE_SHIFT)` 这个随 `PAGE_SHIFT` 推导的界，帮维护者把两个系列收敛成一个。这类「等价补丁该选哪个」的技术对比正是能被采纳的意见。
- 复核大页/非 4K 页配置下的界是否正确：`PAGE_SHIFT` 为 16（或 arm64 64K 页）时 `20 - PAGE_SHIFT` 的位移量会变化，值得用 `sizeof`/编译期断言确认上界仍然精确。
- 顺手审计同一目录下其余裸 `debugfs_create_u32()` 项（`scan_delay_ms` / `scan_period_min_ms` / `scan_period_max_ms` / `hot_threshold_ms`）是否也有被当作除数或移位量的取值，扩展成一个小系列；这比单独修一个 knob 更容易被 tip 接受。
- 回合到 OLK-6.6 时：该 bug 的前提是 sysctl→debugfs 迁移（`8a99b6833c88`），需要先确认 6.6 是否已含该迁移，若仍为 sysctl 则 `extra1 = SYSCTL_ONE` 的下界还在、但 2^24 绕回仍可能存在——这是可验证的回合差异点。

## 参考链接

- v2 RESEND（09-05，本邮件）：https://lore.kernel.org/all/20260905085005.1290752-1-zhanxusheng@xiaomi.com/
- v2 与 v1（作者正文中逐字给出的链接）：https://lore.kernel.org/all/20260810142050.3828587-1-zhanxusheng@xiaomi.com/ 、https://lore.kernel.org/all/20260810081829.3149958-1-zhanxusheng@xiaomi.com/
- 同问题的另一条线（Li RongQing）：https://lore.kernel.org/all/20260822023313.1721-1-lirongqing@baidu.com/
- 相关代码：
  - `kernel/sched/debug.c` `sched_numa_scan_size_fops` / `sched_init_debug()`
  - `kernel/sched/fair.c` `task_scan_max()` / `task_scan_min()` / `task_nr_scan_windows()` / `MB_TO_PAGES()`
  - 引入问题的 commit：`8a99b6833c88` ("sched: Move SCHED_DEBUG sysctl to debugfs")
---
id: sched-20260905-002
date: '2026-09-05'
subject: 'sched/debug: Validate writes to the scan_size_mb debugfs knob'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: '<20260810081829.3149958-1-zhanxusheng@xiaomi.com>'
lore_url: https://lore.kernel.org/all/20260810081829.3149958-1-zhanxusheng@xiaomi.com/
upstream_commit: null
fixes_commit: '8a99b6833c88'
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Zhan Xusheng
maintainers_involved:
- Chen Yu
patch_series:
- 'sched/debug: Validate writes to the scan_size_mb debugfs knob'
merge_assessment:
  likelihood: likely
  blocking_issues:
  - '与 Li RongQing 的同问题补丁撞车，维护者需二选一'
  - '三周无人收树，缺 tip 维护者表态'
  - '-ERANGE 与 -EINVAL 的返回码风格需统一'
  next_action: '回帖指出 Li 版未覆盖 MB_TO_PAGES() 移位绕回，推动两条线合并'
contribution_opportunities:
  - '对比两个同问题补丁的覆盖面差异并回帖'
  - '复核 PAGE_SHIFT 非 4K 时 NUMA_SCAN_SIZE_MB_MAX 上界是否精确'
  - '审计同目录其他裸 debugfs_create_u32 项是否存在同类除数/移位风险'
source_email_count: 1
related_articles: []
tags:
- sched_debug
- numa_balancing
---
