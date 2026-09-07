# sched/numa: stop VMA scan filters from gating promotion

## TL;DR

Gregory Price（Meta）的 2 补丁系列指出 NUMA balancing 的 VMA 级扫描过滤器在内存分层场景下语义已经变了：分层模式下 hint fault 不是「socket 驻留信号」而是**提升机制本身**，被扫描排除的 VMA 会被永久排除在提升之外。他不移除任何过滤器，而是新增 `vma->numab_state->slow_only`，让被拒的 VMA 也扫、但只把非顶层节点的 folio 标记为可 trap。09-05 首发即被 sashiko 机器人测出一个真实逻辑缺陷，作者已给出两行修正并预告「下周测完发 v2」。

## 背景与问题

`task_numa_work()` 在标记 VMA 之前套了一串 VMA 级过滤器，它们都是 hint fault 还只是「socket 驻留信号」的年代写的——那时跳过一个 VMA 只损失一点分辨率。分层内存下前提不成立：慢层 folio 之所以会被考虑提升，正是因为扫描标记了它、随后又被访问；而过滤器的输入又来自扫描自身产生的 fault，于是形成自我锁死。

两个具体过滤器：

1. **per-VMA PID 过滤器**：`vma_is_accessed()` 要求扫描线程在 `vma->numab_state->pids_active[]` 里有自己的 hash 位，而该位唯一的设置者 `vma_set_access_pid_bit()` 只在 NUMA hint fault 时被调用；PROT_NONE 扫描是 hint fault 的唯一来源，于是「没 hint fault 过的 VMA 看起来从未被访问」，可以让新扫描数小时甚至数天不产生 fault。作者逐条说明现有三个逃生机制都不解决问题：`numa_scan_offset` 只救游标所在的那个 VMA；`get_nr_threads()` 那个来自 `f22cde4371f3` ("sched/numa: Fix the vma scan starving issue") 的 horizon 要付 `nr_threads` 轮扫描序列，可能极其庞大；`vma_pids_forced` 重试只在 VMA 链表末尾触发、且只扫一个 VMA。
2. **只读文件映射排除**（`NUMAB_SKIP_SHARED_RO`，由 `4591ce4f2d22` ("sched/numa: Do not trap hinting faults for shared libraries") 引入），前提是「这类页会被 cache 复制、不会迁移，trap 了纯亏」。分层下慢层 folio 会按热度被提升，这个前提失效。

实测代价（768G DRAM + 256G CXL，两个 ~430GB 高线程数据库、各自含一个 300GB+ 的 shmem/tmpfs VMA，`numa_balancing=2`）：大 shmem VMA 占满一整轮扫描的游标，另有 **84G 分散在 2537 个 VMA 上因「不活跃」被跳过**，其中一个 20G 哈希表 **100% 落在 CXL 上**；主程序二进制 **185M 里有 169M（91%）堆在 CXL**。

## 技术方案

- 两个补丁都不删过滤器。核心是给 `struct vma_numab_state` 加一个 `slow_only`（`include/linux/mm_types.h` +7），置位后这一轮该 VMA 的扫描只考虑非顶层节点的 folio，因此**提升候选来自整个地址空间，而顶层 folio 的标记范围与原来完全一致**——作者据此论证放置行为不变，只是新增了提升候选。
- Patch 1 让被 `vma_is_accessed()` 拒绝的 VMA 在 `slow_only` 约束下仍被扫描；并有意不动 `prev_scan_seq`：受限扫描走完 VMA 但并未完整扫过，若在那里更新 `prev_scan_seq` 会永久解除上面提到的 `get_nr_threads()` horizon。
- Patch 2 复用同一机制扫描只读文件映射（`slow_only = ro_file`），并说明其副作用可控：被 `slow_only` 限定的扫描从不把已在顶层的页设为可 trap，慢层页只付一次 hint fault，而这次 fault 正是换来提升的那一步；提升成功时仍会把顶层目标节点上报给 `task_numa_fault()`、照常进入 `numa_faults[]`，改变的只是「哪些 VMA 能产生这种 fault」。
- 涉及 `kernel/sched/fair.c`（+41/-6）、`include/linux/mm_types.h`、`mm/mempolicy.c`，共 +47/-10。两个补丁各自带 `Fixes:`（patch 1 为 `fc137c0ddab2` "sched/numa: enhance vma scanning logic"，patch 2 为 `c574bbe91703` "NUMA balancing: optimize page placement for memory tiering system"），patch 1 还提到该问题是 `d230991493b5` ("mm: mempolicy: fix automatic numa balancing for shmem") 修好 shmem 扫描后被暴露出来的。

## 版本演进与当前进展

- 09-05 首发（subject 无版本号，视作 v1），当天作者自己补了两条回帖处理 sashiko 的发现：
  - patch 1 上接受：无条件写 `slow_only = false` 会让「分两轮扫完的 VMA」在不管 `vma_is_accessed()` 活动的情况下被提前重新纳入，修正为 `if (mm->numa_scan_offset <= vma->vm_start) vma->numab_state->slow_only = false;`；patch 2 上把 `slow_only = false` 改成 `slow_only = ro_file`。
  - patch 2 上部分拒绝：不认为会造成无谓重扫（游标阻止重启，绕回时 `reset_ptenuma_scan()` 会推进 sequence），也不认为有并发扫描器 / ptl 竞争（`mm->numa_next_scan` 每个扫描周期只放行一个），且重扫路径会命中 `pte_protnone()` 直接跳过。
- 作者明确「I'll follow up with a v2 next week after I test it」。截至 09-07 缓存中未见 v2，也未见任何人类维护者回帖、无 tip 收树迹象。

## Maintainer 意见与讨论焦点

- **人类维护者：本批缓存正文中未获取到任何回帖**，也没有 `Acked-by` / `Reviewed-by`。这条线上的第一份「评审意见」来自 sashiko 自动评审机器人，而它这次提的是真问题（`slow_only` 的提前复位），作者已照改。
- 值得注意的是作者的论证方式：他不否认过滤器存在的价值，而是把「placement 行为不变」作为不变式来框定改动范围（顶层 folio 永远不会在原本不会被标记的地方被标记）。这种以「只新增提升候选、不改变放置」为约束的写法，正是为了降低 mm/调度维护者的接受门槛。
- 与作者自己那条 `vma_pids_forced` / horizon 的逐条拆解一起看，本系列实际在挑战一个长期假设：NUMA balancing 的扫描预算优化（少扫无用 VMA）与分层内存的提升需求（必须扫到慢层页）方向相反。

## 合入评估

**likelihood: possible。**

依据：问题真实、数据硬（同一环境的前后带宽/延迟对比 + 逐 VMA 的量化归因）、两个补丁都带 `Fixes:` 且刻意把改动限制成「只增加提升候选、不改放置」，作者对现有逃生机制为什么不够也给了逐条说明。

卡点：
1. v1 已被测出一个真实缺陷（`slow_only` 无条件复位），作者自己说下周才发 v2，等于当前版本不可合；
2. 完全没有人类评审参与——涉及 `mm/mempolicy.c` 与 `include/linux/mm_types.h`，需要 mm 一侧（分层内存维护者）与调度一侧同时表态；
3. 方案是「被过滤的 VMA 也扫，只是限制到慢层 folio」，扫描开销与 `ptl` 争用的担忧虽被作者反驳，但反驳只有推理没有实测数据（他把这项排除在系列之外），维护者很可能仍要求给开销数字；
4. 分层内存的 NUMA 提升策略近期还在被 `d230991493b5` 等改动重塑，存在方案被更大范围重构吸收的风险。

下一步：等 v2（含 sashiko 修正 + 作者测试），以及看是否出现人类维护者的评审。

## 效果评估

有，且是本日几篇里最完整的一组。768G DRAM + 256G CXL、两个 ~430GB 数据库服务：

| 指标 | 打补丁前 | 打补丁后 |
|---|---|---|
| DRAM 带宽 | 从 200GB/s 衰减到 150GB/s | 稳定在 200–250GB/s |
| CXL 带宽 | 从 5GB/s 爬升到 45GB/s 后被卡住 | 稳定在约 7–10GB/s |
| 请求延迟 | 从 800us 涨到 5ms（跟随 CXL 带宽） | 800us–2ms（跟随请求负载） |

结构性指标：patch 1 让那个原本 100% 落在 CXL 的 20G 哈希表稳定为 DRAM/CXL 各 50%；patch 2 让主程序二进制的层级驻留改为跟随运行时负载。

## 我可以参与的点

- 直接可做的复现与验证：在有 CXL/慢层内存的机器上跑 `numa_balancing=2`，用 `trace_sched_skip_vma_numa()` 的 `NUMAB_SKIP_PID_INACTIVE` / `NUMAB_SKIP_SHARED_RO` 统计被跳过 VMA 的字节数——作者给出的「84G / 2537 个 VMA」这类归因数字目前只有他一家，独立复现本身就是有效回帖。
- 可复核的具体代码点：`slow_only` 与 `prev_scan_seq` 的关系（作者论证受限扫描不能更新 `prev_scan_seq`，否则永久解除 `get_nr_threads()` horizon，这条不变式很容易被后续重构破坏）；以及他对 sashiko 的反驳是否覆盖「多个 mm 并发扫描同一 file-backed VMA」的情形——他的论据是 per-mm 的 `mm->numa_next_scan`，但只读文件映射的 folio 是跨 mm 共享的，这一层作者正文里没展开。
- 帮作者补上被他排除的部分：受限扫描的额外 CPU 开销与 `ptl` 争用实测（他明确说这靠推理）。这是能被采纳的贡献，也是合入前最可能被维护者要的东西。
- 用户视角：OLK/内部内核若已有内存分层或「DRAM + 远程内存」形态，本系列的「扫描预算 vs 提升覆盖」张力会原样出现，且它对 shmem/tmpfs 大段的处理与容器化数据库场景直接相关；反过来，如果 6.6 侧不打算跟进 hint-fault 提升机制，这类上游演进只需知晓不必回合。
- 顺带一提：两个补丁都带 `Assisted-by: Claude:claude-opus-5`，同日 Tim Chen 的 cache 修复也带同类标记——上游这条线已明显出现 AI 辅助评审/写作的工作方式，值得作为观察上游动态的一个信号。

## 参考链接

- 0/2 cover letter：https://lore.kernel.org/all/20260904182006.1562449-1-gourry@gourry.net/
- 1/2 与 2/2：https://lore.kernel.org/all/20260904182006.1562449-2-gourry@gourry.net/ 、https://lore.kernel.org/all/20260904182006.1562449-3-gourry@gourry.net/
- 作者对 sashiko 发现的回应（patch 1 / patch 2）：https://lore.kernel.org/all/apsWE-y0nV5r1_5Z@gourry-fedora-PF4VCD3F/ 、https://lore.kernel.org/all/apsX_E8GBzfp6lui@gourry-fedora-PF4VCD3F/
- 相关代码：
  - `kernel/sched/fair.c` `task_numa_work()` / `vma_is_accessed()` / `vma_set_access_pid_bit()` / `reset_ptenuma_scan()`
  - `include/linux/mm_types.h` `struct vma_numab_state`
  - 被修复的 commit：`fc137c0ddab2`、`c574bbe91703`；相关前置：`f22cde4371f3`、`4591ce4f2d22`、`d230991493b5`
---
id: sched-20260905-006
date: '2026-09-05'
subject: 'sched/numa: stop VMA scan filters from gating promotion'
subsystem: sched
type: feature
status: under_review
severity: medium
thread_root_msgid: '<20260904182006.1562449-1-gourry@gourry.net>'
lore_url: https://lore.kernel.org/all/20260904182006.1562449-1-gourry@gourry.net/
upstream_commit: null
fixes_commit: 'fc137c0ddab2'
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Gregory Price
maintainers_involved: []
patch_series:
- 'sched/numa: do not let the per-VMA PID filter gate promotion'
- 'sched/numa: scan read-only file mappings in tiering mode'
merge_assessment:
  likelihood: possible
  blocking_issues:
  - 'v1 被 sashiko 测出 slow_only 无条件复位导致 VMA 被提前重新纳入，作者已确认待发 v2'
  - '无任何人类维护者回帖，需 mm 与调度两侧同时认可'
  - '受限扫描的额外开销与 ptl 争用只有推理、无实测数据'
  - '分层内存提升策略近期仍在被其他 mm 改动重塑'
  next_action: '等含 sashiko 修正的 v2；跟进是否出现人类评审与开销数据'
contribution_opportunities:
  - '独立复现 NUMAB_SKIP_* 归因数据（被跳过 VMA 的字节数）'
  - '为受限扫描补上 CPU 开销与 ptl 争用实测'
  - '复核 slow_only 与 prev_scan_seq 不变式，以及跨 mm 共享只读文件映射的并发扫描'
source_email_count: 5
related_articles: []
tags:
- numa_balancing
---
