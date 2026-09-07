---
id: sched-20260907-009
date: '2026-09-07'
subject: 'sched/numa: scan read-only file mappings in tiering mode'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <20260904182006.1562449-1-gourry@gourry.net>
lore_url: https://lore.kernel.org/all/20260904182006.1562449-3-gourry@gourry.net/
upstream_commit: null
fixes_commit: c574bbe91703
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Gregory Price
maintainers_involved: []
patch_series:
- version: v1
  msgid: <20260904182006.1562449-3-gourry@gourry.net>
  date: '2026-09-05'
  summary: 'kernel/sched/fair.c +16/-2：新增 vma_is_ro_file()；task_numa_work() 对只读 file-backed
    VMA 的跳过改为仅在未开 NUMA_BALANCING_MEMORY_TIERING 时生效，并设 vma->numab_state->slow_only
    = ro_file，使只有非顶层 folio 被置为可 hint fault。动机是分层下慢层 folio 靠 hint fault 提升，而这些 VMA
    永不被扫描；带 Fixes: c574bbe91703 与 Assisted-by: Claude:claude-opus-5。'
  review_outcome: sashiko 提出无谓重扫与并发扫描/ptl 争用疑问，作者 09-05 以游标与 per-mm numa_next_scan
    逐条反驳；09-07 作者自我修正，承认本改动捆绑了多个问题、处理并发扫描 + mode=3（_NORMAL|_TIERING）需要更复杂的改动，宣布测后发
    v2，并称既有测试仍成立、任何带 _TIERING 的 mode 目前都是坏的。无人类维护者回帖、无 tag。
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 作者自认 v1 捆绑了多个问题，且并发扫描与 mode=3 需更复杂的改动，当前版本不可合，v2 形态可能明显不同
  - 无任何人类维护者回帖；涉及 vma_numab_state 与分层提升路径，需 mm 侧与调度侧同时认可
  - 受限扫描带来的额外开销与跨 mm 并发标记干扰只有推理，没有测量数据
  - 只读文件映射在分层机上占慢层驻留的比例目前只有作者一家数据
  next_action: 等含并发扫描与 mode=3 处理的 v2；同时关注 mm 侧维护者是否出现，以及是否有人给出独立复现或开销数字
contribution_opportunities:
- kind: testing
  description: 在 CXL/慢层机型上开启分层 mode，用 trace_sched_skip_vma_numa 的 NUMAB_SKIP_SHARED_RO
    统计被跳过 VMA 的字节数及其中慢层驻留比例，给出一家之外的独立数据
- kind: discussion
  description: 补出 mode=1/2/3 下「只读文件映射是否应被扫描、受限扫描产生的 fault 是否应计入 numa_faults[] 参与 socket
    放置」的语义矩阵，作为 v2 设计输入
- kind: new_patch
  description: 针对只读 file-backed folio 跨 mm 共享导致的并发扫描干扰（作者 09-07 已承认需更复杂处理）先给出可复现用例，必要时单独成补丁
- kind: testing
  description: 内部若已有 DRAM + 远端/CXL 分层并启用 NUMA balancing 提升，可先自查可执行文件主段/共享库这类只读映射的慢层驻留是否已被系统性忽略，不必等上游
    v2
source_email_count: 1
related_articles:
- sched-20260905-006
tags:
- numa_balancing
title: 'sched/numa: scan read-only file mappings in tiering mode'
layout: article
---

## TL;DR

Gregory Price（Meta）把 NUMA balancing 的一个老例外拿到内存分层下重新审视：`task_numa_work()` 见到只读 file-backed VMA 就 `continue`（打点 `NUMAB_SKIP_SHARED_RO`），这条判断由 `4591ce4f2d22`（"sched/numa: Do not trap hinting faults for shared libraries"）写下，理由是这类页预期被 cache 复制、会在访问结点间来回搬，「If we are never going to migrate the page, it is overhead for no gain」。分层内存把这个前提推翻了——慢层 folio 正是靠 hint fault 按热度被提升的，这些页现在**能**迁，只是永远拿不到被扫描的机会。他在 768G DRAM + 256G CXL 的机器上跑约 430G 的数据库服务，观测到主程序 185M 里的 91%（169M）积在 CXL 慢层；打上补丁（对这些 VMA 带 `slow_only` 限制地扫描，只有非顶层 folio 才置成可 hint fault）后，该二进制的分层驻留能跟着运行时负载走。09-07 作者自己回贴把问题范围进一步扩大：细看之下这个改动里捆绑了几个问题，且要正确处理**并发扫描 + mode=3（`_NORMAL|_TIERING`）需要更复杂的改动**，「Will push a v2 after some additional testing」；同时强调既有测试仍然成立，并给出更重的定性——当前任何带 `_TIERING` 的 mode 因为过滤机制其实都是坏的。

## 背景与问题

`task_numa_work()` 在标记 PTE 之前会跳过一批 VMA，其中与本篇相关的是：

```
if (vma->vm_file &&
    (vma->vm_flags & (VM_READ|VM_WRITE)) == (VM_READ)) {
        trace_sched_skip_vma_numa(mm, vma, NUMAB_SKIP_SHARED_RO);
        continue;
}
```

它诞生于 hint fault 只作为「socket 驻留信号」的年代：那时跳过一个只读映射只损失一点放置分辨率，而 trap 共享库页换来的迁移大多是负收益。内存分层（`NUMA_BALANCING_MEMORY_TIERING`）之后，同一次 hint fault 变成了**提升机制本身**——慢层 folio 只有先被标记、再被访问产生 fault，才会被考虑搬到顶层。于是「永不被扫描」等价于「永不被提升」，只读文件映射（可执行文件主段、共享库）在这类机器上会单向沉积到慢层。作者的实测就是这条链路：约 430G 的数据库服务，主程序 185M 中 169M（91%）留在 CXL。

本补丁是该 2 补丁系列中的 2/2（1/2 处理 per-VMA PID 过滤器，系列整体论证与前后可见 [[sched-20260905-006]]），本篇只覆盖 2/2 这一补丁与其自身线程的进展。

## 技术方案

改动全部在 `kernel/sched/fair.c`，+16/-2，两个 hunk：

- 新增 `vma_is_ro_file(vma)`：`vma->vm_file && (vma->vm_flags & (VM_READ | VM_WRITE)) == VM_READ`，即把原来那条排除判断抽成可复用的谓词。
- 排除条件从「是只读文件映射就跳过」改为「是只读文件映射**且当前 mode 未开分层**才跳过」：
  ```
  if (!vma->vm_mm ||
      (ro_file && !(sysctl_numa_balancing_mode &
                    NUMA_BALANCING_MEMORY_TIERING))) {
  ```
- 扫描本身不加限制地走，但把该 VMA 标成受限：`vma->numab_state->slow_only = ro_file;`，即只有非顶层节点的 folio 会被置成可 hint fault。

作者给的两条安全性论证：（1）顶层 folio 在任何 mode 下都不会因这次改动而被标记，因此放置行为相对原来不变，新增的只是提升候选；（2）代价上，已在快层的页不花钱，慢层页花一次 hint fault，而这次 fault 正是换来提升的那一步。他还承认这次 fault 不是「零放置副作用」——提升成功时会把顶层目标节点上报给 `task_numa_fault()`，从而像任何一次提升一样进入 `numa_faults[]`，改变的只是「哪些 VMA 能产生这种 fault」。补丁带 `Fixes: c574bbe91703`（"NUMA balancing: optimize page placement for memory tiering system"）与 `Assisted-by: Claude:claude-opus-5`。

## 版本演进与当前进展

- 09-05 02:20 随系列首发 2/2（subject 无版本号，视作 v1；cover `<20260904182006.1562449-1-gourry@gourry.net>`）。
- 09-05 03:31 作者自贴回应 sashiko（自动评审）对本补丁的两类意见：不认为会造成无谓重扫（游标阻止重启，绕回时 `reset_ptenuma_scan()` 会推进 sequence）；也不认为有并发扫描器与 `ptl` 争用问题（`mm->numa_next_scan` 每个扫描周期只放行一个扫描者），并补充说即便重扫也会命中 `pte_protnone()` 直接跳过。
- 09-07 23:35 作者推翻自己部分答复：「On a second look, there are a few issues bundled in with this, and the change required to handle the concurrent scan + mode=3 (`_NORMAL|_TIERING`) requires a bit more complex of a change to fully resolve.」→「Will push a v2 after some additional testing」；同时明确「the existing tests still stand. As-is, any mode with `_TIERING` set is very broken at the moment because of the filtering mechanisms.」
- 截至本日缓存中无 v2、无 tip 收树迹象，也没有任何人类维护者回帖或 `Acked-by`/`Reviewed-by`。

## Maintainer 意见与讨论焦点

- **人类维护者：本批缓存正文中未获取到任何回帖**。线程里唯一的「评审」来自 sashiko 自动检查，而本日的进展仍然是作者自己的自我修正。
- **并发扫描**：这是作者 09-05 否认过、09-07 又承认需要更复杂处理的那一块。关键在于只读 file-backed 的 folio 是跨 mm 共享的，而作者的原有论据（`mm->numa_next_scan`）是 per-mm 的——多个进程同时扫描同一文件映射时，`slow_only` 作用下的标记/清除会互相影响，这一层在邮件里尚未展开。
- **mode=3（`_NORMAL|_TIERING`）的语义**：本补丁的门控只看 `sysctl_numa_balancing_mode & NUMA_BALANCING_MEMORY_TIERING`，因此 mode=3 同样会开始扫只读文件映射，而这些 fault 会经 `task_numa_fault()` 进入 `numa_faults[]`、参与 `_NORMAL` 下的 socket 级放置统计。作者把「正确处理并发扫描 + mode=3」列为需要更大改动才能解决的部分，意味着 v2 的形态可能与 v1 明显不同（例如按位分别处理，或把这类 fault 从 `_NORMAL` 统计里隔离）。
- **问题定性的升级**：作者本日把结论从「一个扫描例外在分层下不再成立」提升到「任何带 `_TIERING` 的 mode 目前都是坏的」——这是本系列最有利于按 bug/fixes 通道推进的一句话，也解释了为什么他坚持既有测试仍然有效。
- 尚未有人质疑的核心前提（也无人背书）：只读文件映射在分层机上是否**普遍**像他观测到的那样占这么大比例。

## 合入评估

`likelihood=medium`。

正向：问题真实且量化（91% / 169M 这类逐二进制的归因数字）、带 `Fixes: c574bbe91703`、机制刻意把「放置行为不变」当不变式（顶层 folio 永不被额外标记），接受门槛低；作者本人已把它定性为「当前带 `_TIERING` 的 mode 都是坏的」，走 fixes 通道的理由成立。

卡点：一是作者自己说 v1 里捆绑了多个问题、且并发扫描与 mode=3 需要更复杂的改动，等于当前版本不可合；二是完全没有人类评审，而改动涉及 `vma_numab_state`（`include/linux/mm_types.h`）与分层提升路径，需要 mm 侧（内存分层维护者）与调度侧同时认可；三是受限扫描带来的额外开销与 `ptl`/跨 mm 争用仍只有推理，没有数字；四是分层内存的 NUMA 提升策略近期仍在被其它改动重塑，存在被更大范围重构吸收的风险。

## 效果评估

有的部分是 2/2 自己的观测（均来自 09-05 的补丁正文）：机器为 768G DRAM + 256G CXL，负载是约 430G 的数据库服务；补丁前主程序二进制 185M 中 169M（91%）积在 CXL 慢层；补丁后该二进制的层级驻留能跟随运行时负载变化（作者原话只到 "the binary's tier residency tracked runtime load" 这一程度）。

必须标注的缺口：本篇（2/2）**没有**给出自己的前后延迟/带宽数字，也没有扫描耗时、hint fault 次数或 CPU 占用等开销侧证据——作者对 sashiko 的开销疑问回应的是推理而非测量；系列整体的带宽/延迟对比属于另一补丁的验证，见 [[sched-20260905-006]]。本日（09-07）邮件中没有任何新数据，v2 的承诺也未附测试计划细节。

## 我可以参与的点

- 直接可做的复现与独立数据点：在有 CXL/慢层的机器上开 `numa_balancing` 的分层 mode，用 `trace_sched_skip_vma_numa()` 的 `NUMAB_SKIP_SHARED_RO` 统计被跳过的 VMA 字节数与其中慢层驻留比例。作者这组 91%/169M 目前是全社区唯一一份，任何一份独立复现都直接推进讨论。
- 把 mode=3 的语义矩阵补出来（本线程最缺、也是 v2 设计的前置）：列出 mode=1/2/3 下「只读文件映射是否应被扫描、受限扫描产生的 fault 是否应进入 `numa_faults[]` 参与 socket 放置」的组合，并给出实现建议。作者已承认这块要更复杂的改动，谁先把矩阵讲清谁就能进设计。
- 并发扫描这个真实缺口可以单独出补丁：只读 file-backed folio 跨 mm 共享，多个 mm 的 `task_numa_work()` 在同一批 folio 上做 `PROT_NONE` 标记/恢复时的互相干扰，作者原有 per-mm 的论据覆盖不到它；先给一个能复现干扰的用例（同一大二进制被多进程映射 + 分层 mode）会很有价值。
- 内部场景自查（不等上游）：如果内部有 DRAM + 远端内存/CXL 分层并开启 NUMA balancing 提升，容器里可执行文件主段与共享库这类只读映射正是「积在慢层且永不被扫」的典型对象；绑核/cpuset 限定节点时这种偏置更难从常规统计看出来，可以先自行用 `numastat -m`/页驻留采样确认是否已中招，再决定是否需要本地跟随该系列。

## 参考链接

- 本日邮件（作者自我修正、宣布 v2）：https://lore.kernel.org/all/ap7ZXrxI05xyuNn3@gourry-fedora-PF4VCD3F/
- 系列与补丁本体：
  - 0/2 cover：https://lore.kernel.org/all/20260904182006.1562449-1-gourry@gourry.net/
  - 2/2 补丁正文（含 91%/169M 观测与 `Fixes: c574bbe91703`）：https://lore.kernel.org/all/20260904182006.1562449-3-gourry@gourry.net/
  - 作者对 sashiko 意见的回应（重扫与并发扫描）：https://lore.kernel.org/all/apsX_E8GBzfp6lui@gourry-fedora-PF4VCD3F/
- 相关代码：`kernel/sched/fair.c` `task_numa_work()` / `vma_is_ro_file()` / `reset_ptenuma_scan()` / `task_numa_fault()`；`include/linux/mm_types.h` `struct vma_numab_state`（`slow_only`）
- 被修复的 commit：`c574bbe91703`；引入例外的 commit：`4591ce4f2d22`
- 相关：[[sched-20260905-006]]（同一系列 0/2 封面的完整分析）
