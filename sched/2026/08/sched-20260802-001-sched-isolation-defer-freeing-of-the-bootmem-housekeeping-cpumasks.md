# sched/isolation: Defer freeing of the bootmem housekeeping cpumasks

# sched/isolation: 推迟释放 bootmem housekeeping cpumask

## TL;DR

`housekeeping_init()` 在 deferred struct page 初始化完成之前调用 `memblock_free()` 释放 bootmem cpumask，在 `CONFIG_DEFERRED_STRUCT_PAGE_INIT=y` 时每种 housekeeping 类型触发一条 WARN 并给内核打上 `G W` 污点。补丁把释放动作推迟到 `core_initcall`。方案简单、有明确复现、有 mm 侧维护者背书，合入可能性高，值得关注但参与空间有限。

## 背景与问题

启动早期 `housekeeping_setup()` 在解析 `isolcpus=` / `nohz_full=` 命令行时从 memblock 分配 housekeeping cpumask —— 此时页分配器还不存在。随后 `housekeeping_init()` 用 `kmalloc()` 重新分配一份，好让后续运行时更新能用 `kfree()` 释放旧 mask，并顺手用 `memblock_free()` 归还早期的 memblock 分配。

问题出在这个"顺手归还"的时机上。`housekeeping_init()` 由 `start_kernel()` 在 `mm_core_init()` 之后调用，此时 `slab_is_available()` 已为真，于是 `memblock_phys_free()` 走进 `__free_reserved_area()` 路径。但它仍远早于 `page_alloc_init_late()`，在 `CONFIG_DEFERRED_STRUCT_PAGE_INIT=y` 下 memory map 的延迟初始化部分尚未就绪，`__free_reserved_area()` 直接拒绝：

```
Cannot free reserved memory because of deferred initialization of the memory map
WARNING: mm/memblock.c:904 at __free_reserved_area+0xde/0xf0, CPU#0: swapper/0/0
Call Trace:
 memblock_phys_free+0xe4/0x120
 housekeeping_init+0x149/0x170
 start_kernel+0x5b6/0x800
```

每种在用的 housekeeping 类型各触发一次。作者在一台 112 CPU 双路 Dell PowerEdge R750（2x Xeon Gold 6330，2 NUMA node，128 GiB，v7.2-rc5 + PREEMPT_RT）上同时使用 `isolcpus=` 与 `nohz_full=` 时看到 **四条 splat**，内核被打上 `G W` 污点。

值得注意的是：**实际并没有内存泄漏**。一个 cpumask 远小于一页，`__free_reserved_area()` 本来也没有整页可以还给 buddy allocator。所以症状纯粹是启动噪音加污点标记，严重度定为 low。

坏的 `memblock_free()` 自 v7.0 的 `27c3a5967f05`（"sched/isolation: Convert housekeeping cpumasks to rcu pointers"）就存在，只是到 v7.1 引入 `59bd1d914bb5`（"memblock: warn when freeing reserved memory before memory map is initialized"）加上 WARN 之后才暴露出来。

对照当前主线 `kernel/sched/isolation.c`，`housekeeping_init()` 中的 `memblock_free(omask, cpumask_size());` 确实还在原地，补丁尚未落地。

## 技术方案

思路直白：**记录而非立即释放**。

新增一个 `__initdata` 数组保存被替换下来的 bootmem mask：

```c
static struct cpumask *housekeeping_bootmem_masks[HK_TYPE_MAX] __initdata;
```

`housekeeping_init()` 里把原来的 `memblock_free(omask, cpumask_size())` 换成 `housekeeping_bootmem_masks[type] = omask;`，真正的释放挪到一个新的 `core_initcall`：

```c
static int __init housekeeping_free_bootmem_masks(void)
{
	enum hk_type type;

	for (type = 0; type < HK_TYPE_MAX; type++)
		memblock_free(housekeeping_bootmem_masks[type], cpumask_size());

	return 0;
}
core_initcall(housekeeping_free_bootmem_masks);
```

两个关键设计取舍：

1. **为什么是 `core_initcall` 而不是 `early_initcall`**：作者明确论证了 `early_initcall` 仍然太早 —— `kernel_init_freeable()` 会先跑 `do_pre_smp_initcalls()`，再才轮到 `page_alloc_init_late()`。`core_initcall` 位于 `page_alloc_init_late()` 之后，才是安全窗口。

2. **kmalloc 失败路径的行为保持不变**：`housekeeping_init()` 没能成功替换的 mask（因为 `kmalloc()` 失败）根本不会被记录进数组，因此会一直存活下去，与现有错误处理语义一致。

**被放弃的备选方案**：Mike Rapoport 还建议过让 `housekeeping_setup()` 做一次覆盖全部 `HK_TYPE_MAX` mask 的单次 memblock 分配，之后统一释放这一块区域。作者评估后认为"改动面更大而在此处没有额外收益"，选择了更简单的版本。这一取舍写在了 patch 的 `---` 之下（不进 commit log），属于给 reviewer 看的说明。

## 版本演进与当前进展

当前为 v1，2026-08-02 19:56（北京时间）发出，当日无 review 回帖。

补丁带有完整的溯源信息：`Fixes: 27c3a5967f05`、`Closes: https://bugzilla.kernel.org/show_bug.cgi?id=221804`、指向 linux-mm 讨论线程的 `Link:`，以及 `Suggested-by: Mike Rapoport (Microsoft)`。这说明问题此前已在 linux-mm 上讨论过，本次是把讨论结果落成 sched 侧的具体补丁 —— 属于"讨论已收敛后的提交"，而非新开话题。

## Maintainer 意见与讨论焦点

当日邮件中**没有维护者回帖**。可提取的间接信号：

- Mike Rapoport（memblock 维护者）是方案的建议人，`Suggested-by` 标签意味着 mm 侧对整体思路已有共识。
- 作者主动抛出了一个待定问题："自 27c3a5967f05 以来这个坏的 memblock_free 就存在，但既然什么都没真正泄漏、影响只是一条警告加 G W 污点，我没有 Cc stable —— 如果你们希望加上，说一声。"（*"Since nothing is actually leaked and the effect is a warning plus a G W taint, I did not Cc stable -- say the word if you would rather have it there."*）这是明确留给维护者裁决的开放项。
- sched 侧（Peter Zijlstra、Frederic Weisbecker）尚未对 `core_initcall` 这个具体时机点表态。

目前**没有任何分歧或反对意见**，但也还没有正式的 Acked-by / Reviewed-by。

## 合入评估

合入可能性判定为 **high**，依据：

- 问题真实可复现，有 bugzilla 编号（221804）与完整 splat；
- `Fixes:` 指向明确，责任边界清楚；
- 方案由 memblock 维护者建议，mm 侧阻力小；
- 改动局限在 `kernel/sched/isolation.c` 单文件 23 行新增，无跨子系统影响；
- 作者同时做了实机验证（补丁前四条 splat、补丁后零条）与 x86_64 defconfig + `CONFIG_NO_HZ_FULL` + `CONFIG_DEFERRED_STRUCT_PAGE_INIT` 的编译验证。

卡点仅两项，且都是程序性的：stable 归属待定、sched 维护者尚未确认 initcall 时机。预计走 `tip/sched/core`（如果维护者认为 WARN 影响足够大也可能进 `sched/urgent`）。

## 效果评估

作者给出的是**定性且可验证**的结果，不是主观判断：

- 打补丁前：112 CPU 双路机器上启动出现 **4 条 WARN**（每种在用的 housekeeping 类型一条），内核被标记 `G W`；
- 打补丁后：**0 条**。

内存占用方面作者明确说明"两种做法都不会真正丢失内存"（*"No memory is actually lost either way"*），因此不存在内存回收收益。**无性能数据，也不需要** —— 这是启动期一次性路径，不涉及运行时开销。

复现环境完整披露：

```
rcu_nocbs=8-55,64-111 nohz_full=managed_irq,nohz,domain,8-55,64-111
isolcpus=managed_irq,nohz,domain,8-55,64-111 kthread_cpus=0-3,56-59
irqaffinity=4-7,60-63 rcutree.kthread_prio=21
```

## 我可以参与的点

- **复核 initcall 时机**：这是补丁的核心正确性论断。作者论证了 `early_initcall` 太早、`core_initcall` 恰好，但没有 reviewer 独立确认过。可以对照 `init/main.c` 中 `do_basic_setup()`（跑 `core_initcall`）与 `kernel_init_freeable()` 中 `page_alloc_init_late()` 的实际先后顺序核对一遍，确认无误后回帖 `Reviewed-by`。这是低成本、高价值的参与点。
- **Tested-by**：如果手头有支持 `CONFIG_DEFERRED_STRUCT_PAGE_INIT=y` 的多 NUMA 节点机器，按作者给的命令行复现 WARN 再验证补丁，回帖测试结果。作者只在一台 R750 上验证过，多一个平台的数据有帮助。
- **就 stable 归属发表意见**：这是作者显式征求意见的开放问题，有 stable 分支维护经验的人可以直接回答。

参与门槛低但影响有限 —— 这是个小修补，不适合作为深度介入调度子系统的切入点。

## 参考链接

- lore thread: 未获取到（IMAP 邮件头未暴露原始 Message-ID）
- bugzilla: https://bugzilla.kernel.org/show_bug.cgi?id=221804
- 前置讨论（patch 中 Link 标签）: https://lore.kernel.org/linux-mm/20260728134016.674388f101f141362598240f@linux-foundation.org/
- tip-bot commit: 未获取到
- stable backport: 无（作者未 Cc stable）

---
subject: "sched/isolation: Defer freeing of the bootmem housekeeping cpumasks"
id: sched-20260802-001
date: 2026-08-02
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "unknown"
lore_url: "unknown"
authors: [Ionut Nechita]
maintainers_involved: [Mike Rapoport]
current_version: v1
patch_series:
  - version: v1
    msgid: "<uid-15170@qq-imap>"
    date: 2026-08-02
    summary: "把 housekeeping_init() 中对 bootmem cpumask 的 memblock_free() 推迟到 core_initcall，绕开 deferred struct page init 未完成时 __free_reserved_area() 拒绝释放的 WARN。"
    review_outcome: "v1 当日刚发出，暂无 review 回帖；方案本身出自 Mike Rapoport 在 linux-mm 线程中的建议。"
upstream_commit: null
fixes_commit: "27c3a5967f05"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "是否需要 Cc stable 尚未定论：作者认为只是 WARN + G W taint、无实际内存泄漏，故未加 stable 标签，把决定权留给维护者。"
    - "尚无 sched 侧维护者（Peter Zijlstra / Frederic Weisbecker）回帖确认 core_initcall 时机选择。"
  next_action: "等待 Frederic Weisbecker 或 Peter Zijlstra 对 initcall 时机与 stable 归属表态；Mike Rapoport 给出 Acked-by 后基本可进 tip/sched/core。"
contribution_opportunities:
  - kind: review
    description: "复核 core_initcall 是否确实晚于 page_alloc_init_late()——作者已论证 early_initcall 太早，但 core_initcall 与 page_alloc_init_late 的先后可以再独立确认一遍并回帖。"
  - kind: testing
    description: "在 CONFIG_DEFERRED_STRUCT_PAGE_INIT=y + nohz_full/isolcpus 的机器上复现四条 WARN 并验证补丁消除告警，回帖 Tested-by。"
generated_at: "2026-08-03T00:15:00"
source_email_count: 1
related_articles: []
tags: [nohz, affinity, topology, x86]
---
