# sched/fair: Switch nohz.idle_cpus to use sbm

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261002-007 / 003-005 / 004-006：K Prateek Nayak（AMD）13 补丁 RFC v3「lib, sched: Introduce sparsebitmap (sbm)」（用 sparsebitmap 替代大机器全局 cpumask，`nohz.idle_cpus_mask` 是首个用户），有过 benchmark 归属、wakeup 形态开销等讨论，仍是 RFC 状态。
- sched-20261019-003（今天）：kernel test robot 在 i386 + clang-22 的 randconfig 上，对 13/13 `sched/fair: Switch nohz.idle_cpus to use sbm` 报了 boot 阶段 `kernel_BUG_at_kernel/smpboot.c`（`smpboot_thread_fn`），kmsg 显示 CPU3/ksoftirqd/3 触发 Oops。机器人未给根因，需作者排查。

## 背景与问题

（承接 20261002-007 → 003-005 → 004-006）sbm 系列把 `nohz.idle_cpus` 从全局 cpumask 换成 sparsebitmap，最后一个补丁 13/13 即落在 `sched/fair` 的 nohz idle CPU 跟踪上。今天 kernel test robot 在 boot 测试中对该补丁命中 `kernel BUG at kernel/smpboot.c:133`（`smpboot_thread_fn`），Taint `[T]=RANDSTRUCT`，preempt-lazy、`ksoftirqd/3` 触发 `Oops: invalid opcode`。测试机为 `qemu-system-i386 -enable-kvm -cpu SandyBridge -smp 4 -m 4G`，config `i386-randconfig-1006-20261010`。

## 技术方案

今日无新补丁，为 LKP 对既有 RFC v3 的 bug 报告。机器人附上了完整 dmesg/kmsg 与 patch 链接，并给出标准指引：若以独立补丁修复，请加 `Reported-by: kernel test robot <yi1.lai@intel.com>` 与 `Closes: https://lore.kernel.org/oe-lkp/202610190859.d3459a50-lkp@intel.com`。报告未定位根因，需作者在 sbm 版 nohz idle 跟踪路径上排查 smpboot 线程生命周期交互。

## 版本演进与当前进展

*current_version: RFC v3*（系列为 13 补丁 RFC，见 related 01002-007）。今日新增一枚 LKP 的 boot crash 报告，无作者/维护者回复。

## Maintainer 意见与讨论焦点

无维护者表态；kernel test robot 的自动报告是当天唯一声音。机器人要求若修复请回填 Reported-by/Closes 标签。

## 合入评估

*likelihood=low*（短期）。系列仍是 RFC，此前已有 Chen Yu 等的实质 review 质疑（benchmark 归属、wakeup 形态开销）；现在又新增 i386 boot 崩溃，作者需先定位并修复 13/13 的 smpboot BUG 才能继续推进。*blocking_issues*：i386 boot crash 根因未明、RFC 阶段固有讨论点未收敛。*next_action*：作者排查 smpboot.c:133 BUG 与 sbm 版 nohz.idle_cpus 的交互，修复后回填 Reported-by/Closes。

## 效果评估

LKP 给出复现条件（i386 + clang-22 + `i386-randconfig-1006-20261010` + `-smp 4`）与 Oops 栈（`smpboot_thread_fn`）。属崩溃类正确性问题，无量化性能数据。

## 我可以参与的点

- `testing`：在 i386（或其它 32 位）randconfig 上复现 boot BUG，帮助缩小触发 config 范围。
- `review`：审查 13/13 `sched/fair` 的 nohz idle_cpus→sbm 改造与 smpboot 线程初始化/清理时序是否有竞态。

## 参考链接

- LKP 报告：https://lore.kernel.org/all/202610190859.d3459a50-lkp@intel.com/
- 系列 patch 链接（报告内附）：https://lore.kernel.org/all/20261001192849.74788-14-kprateek.nayak@amd.com/

---
id: sched-20261019-003
subject: "sched/fair: Switch nohz.idle_cpus to use sbm"
date: 2026-10-19
subsystem: sched
type: bug
status: rfc
severity: high
thread_root_msgid: "<202610190859.d3459a50-lkp@intel.com>"
lore_url: "https://lore.kernel.org/all/202610190859.d3459a50-lkp@intel.com/"
authors: ["K Prateek Nayak"]
maintainers_involved: []
current_version: v3
patch_series:
  - version: v3
    msgid: "<20261001192849.74788-14-kprateek.nayak@amd.com>"
    date: 2026-10-01
    summary: "RFC v3 13/13：把 sched/fair 的 nohz.idle_cpus 跟踪切换到 sparsebitmap"
    review_outcome: "Chen Yu 等实质 review（见 related）；今日被 LKP 报 i386 boot crash"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues: ["13/13 触发 i386 boot BUG（smpboot.c:133）根因未明", "RFC 阶段讨论点未收敛"]
  next_action: "作者定位并修复 smpboot BUG，回填 Reported-by/Closes 后继续推进"
contribution_opportunities:
  - kind: testing
    description: "在 i386/32 位 randconfig 上复现 boot BUG，缩小触发 config 范围"
  - kind: review
    description: "审查 nohz idle_cpus→sbm 改造与 smpboot 线程初始化/清理的竞态"
generated_at: "2026-10-20T01:30:00"
source_email_count: 1
related_articles: ["sched-20261002-007", "sched-20261003-005", "sched-20261004-006"]
tags: [nohz, cfs, crash]
---