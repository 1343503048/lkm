# tag: mm

共 3 篇

- [sched-20260918-014](../../2026/09/sched-20260918-014-sched-numa-scan-read-only-file-mappings-in-tiering-mode.md) `fix/medium/under_review` — 增量更新：Gregory Price 的 NUMA tiering 修复（v2 系列 3/4，让 tiering 模式也扫描只读文件映射）本日集中讨论 VMA 判定语义——David Hildenbrand 认为函数名误导、应用新 VMA flags API；Lorenzo Stoakes 给出详尽的 VMA 标志分析并建议引入 `vma_maps_shared_readonly_file()` 
- [sched-20260918-003](../../2026/09/sched-20260918-003-sched-mmcid-bound-the-cid-allocation-busy-wait.md) `fix/medium/under_review` — Jiakai Xu 提交修复：为 `mm_get_cid()` 的无界自旋加 32 次重试上限，耗尽时返回 `MM_CID_UNSET` 让任务无 CID 运行、下次调度再重试。这避免了 CID 耗尽时 rq 锁 + 关中断自旋导致的 RCU stall / 整机 lockup 以及模式切换 fixup 线程的 livelock。Peter Zijlstra 强烈质疑——"horribly wro
- [sched-20260803-011](../../2026/08/sched-20260803-011-posix-cpu-timers-use-after-free-in-exec-failure-path.md) `bug/high/under_review` — 修复 exec 失败路径中 posix-cpu-timers 引用已释放 mm/sighand 的 use-after-free。附 Fixes 标签与 KASAN 报告，合入可能性高。
