# sched_ext: fix vtime priority queue inversion on wide vtime spread

## TL;DR

Tao Cui 先用探针调度器「复现」出 DSQ vtime 优先队列顺序翻转、部分任务饿死，进而把内核侧比较器从回绕语义的 `time_before64()` 换成朴素 `u64 <`。**同一天被 Andrea Righi 与 Tejun Heo 双双否掉**：`dsq_vtime` 按定义就是一个滚动游标（rolling cursor），回绕比较才是文档约定的语义，作者的探针喂的是违反前提的输入。作者当日承认 1/2 写错并撤回，改成 Tejun 建议的文档补丁 + 修 `scx_flatcg` 里唯一真正违反该约束的比较器，v2 当晚发出。

## 背景与问题

`scx_bpf_dsq_insert_vtime()` 允许 BPF 调度器给任务指定 vtime，DSQ 用 `scx_dsq_priq_less()` 按 vtime 排序，比较方式是 `time_before64()` —— 一个**回绕（cyclic）比较**，只在同一队列内的值相差小于 2^63 时与真实先后一致。这与 CFS 的做法同构，但 CFS 用 `min_vruntime` 钳制主动维持该不变量，而 sched_ext 的 `dsq_vtime` 直接来自 BPF 程序，内核不做钳制。

作者的观察是：既然内核不维持这个不变量，就有调度器能把值相差超过 2^63 的任务塞进同一个 DSQ，从而得到完全反掉的顺序；他声称复现了「8 个忙任务里 4 个独占 CPU、另 4 个饿死」。另一侧 `scx_flatcg` 的 `cgv_node_less()` 则用的是朴素 `<`，在 `cvtime` 自然回绕时会把回绕节点永久排到最后。

## 技术方案

- **v1（被撤回）**：把 `scx_dsq_priq_less()` 改成朴素 `u64 <`，理由是全序、永远尊重调度器要求的顺序，而 2^64 自然回绕处的错序只是有界瞬态。
- **v2（当前）**：
  1. **1/2 文档化滚动游标要求**：在 `scx_bpf_dsq_insert_vtime()` 的 kdoc 里显式写出「vtime 是滚动游标、应视为单调推进的虚拟时间戳；同一 DSQ 内用于排序的值应彼此相差小于 u64 半程（2^63），`time_before64()` 的排序才有意义」。
  2. **2/2 `scx_flatcg` 改成回绕安全比较**：`cgv_node_less()` 由 `cgc_a->cvtime < cgc_b->cvtime` 改为 `(s64)(cgc_a->cvtime - cgc_b->cvtime) < 0`，即 CFS 对 vruntime 的写法。其正确性依赖一个真实不变量——`cgrp_cap_budget()` 把每个节点钳制在 `cvtime_now` 之后不超过 `max_budget`，因此任意两节点相距远小于 2^63，回绕序与真实序一致。

关键取舍：**是修比较器，还是把隐含前提写成契约**。v1 选前者（等于放弃回绕语义），v2 选后者（保留语义 + 修掉唯一违约的消费者 + 把前提写进 kdoc）。这是 maintainer 明确要求的形状。

## 版本演进与当前进展

- **v1（2026-09-01 10:40）** 2 片，1/2 改内核比较器、2/2 修 flatcg。
  - 11:54 `bot+bpf-ci` 在 2/2 下提 `Fixes:` 标签质疑：`7b742aa2c2c9` 在该仓库不存在，真正的引入者是 `a4103eacc2ab4 ("sched_ext: Add a cgroup scheduler which uses flattened hierarchy")`（AI 审查机器人，需人工确认）。
  - 14:47 Andrea Righi 否掉 1/2，给出反例：`a = U64_MAX - 5`、`b = 3`，`time_before64(a, b)` 为真而朴素 `a < b` 会把 b 排前面；并指出这不是瞬态——回绕后新任务持续以小 vtime 入队，`a` 会被压到对端 vtime 走完几乎整个 u64 范围才轮得到，构成事实饿死。他反问 `Can we preserve time_before64() and document or enforce the half-range requirement instead?`
  - 16:29 Tejun Heo：`This doesn't make any practical sense. dsq_vtime is by (implicit) definition a rolling cursor. Please feel free to add documentation if that'd help.`
  - 17:44 作者认账：`You're both right, patch 1/2 was wrong. My probe fed values that violate the rolling-cursor assumption, and the "inversion" was the API behaving as documented. Dropping 1/2.`
- **v2（2026-09-01 22:03）** 0/2 封面写明 changelog：`drop 1/2 ... a plain comparison causes unbounded starvation at the natural wrap (Andrea, Tejun)`、`new 1/2: document the rolling-cursor requirement instead (Tejun)`、`2/2 (flatcg) unchanged`。

v2 在本日尚无 review 回帖。

## Maintainer 意见与讨论焦点

- **Andrea Righi（NAK 的技术版本）**：他不去争「会不会发生」，而是直接指出**换成朴素比较后哪一侧的行为变差**——回绕点之后先到的大 vtime 任务会被无限期推迟，这比作者声称修掉的病症更严重。反例只有两个常数，说服力来自它精确对应 kdoc 里已经写明的语义。
- **Tejun Heo（NAK 的语义版本）**：`dsq_vtime is by (implicit) definition a rolling cursor`——把问题定性为「前提没写清」而不是「实现有 bug」，并给出出路：`Please feel free to add documentation if that'd help.` v2 的 1/2 就是这个指示的直接产物。
- **`Fixes:` 标签争议未解决**：`bot+bpf-ci` 主张应指向 `a4103eacc2ab4`，作者与 Tejun 当日都未回应，v2 的 2/2 仍写 `Fixes: 7b742aa2c2c9`。这是本片目前唯一悬空的具体问题。
- **一处值得记住的通用教训**：作者最初的「复现」是他自己写的探针调度器造成的，而该调度器喂的输入本身就违反 API 约定。**sched_ext 的 BPF 侧「复现」必须先证明输入合法**，否则报出来的都是合约行为。

## 合入评估

`likelihood = likely`。v2 两片：一片纯 kdoc、一片 1 行且被两位评审人明确认可过其必要性（Andrea 与 Tejun 都要求保留回绕语义，而 flatcg 是唯一与此矛盾的比较器）。作者身份与该修法都在 sched_ext 的既有收口节奏内（同一天 Tejun 刚把 v7.3-rc1 的 fixes pull 发出去，见 sched-20260901-018）。剩余障碍只有 `Fixes:` 标签是否更正，以及是否作为 `for-7.3-fixes` 还是 `for-7.4` 收——**flatcg 在 `tools/` 下，不进 stable，通常走下个合并窗口**。

## 效果评估

- 作者给出的唯一量化数据来自其**已被否定的 v1 实验**：`Reproduced with a probe scheduler assigning half its tasks vtimes near 0 and the other half vtimes above 2^63 -- four of eight busy tasks monopolized the CPU while the other four starved.` 该结果本身是真实的，但它证明的是「违反契约时的行为」，不构成 bug 证据。
- v2 的 2/2 给出的量化论证是**可达性推导而非测试**：权重 1 的 cgroup 处在权重和为 10000 的层级里，`cvtime` 最快以 10000 倍墙钟速度推进，因此 2^64 ns 的 cvtime 距一次持续饱和运行还有数周——`unlikely but reachable on a long-running host`。验证方式仅为 `Compile-tested and smoke-tested in a VM: weight distribution and dispatch unaffected.`
- **没有任何性能数字**，两片也不改变正常情况下的调度决策。

## 我可以参与的点

- **可直接产出的一条：确认 `Fixes:` 标签**。核对 `7b742aa2c2c9` 与 `a4103eacc2ab4` 到底哪个是 `scx_flatcg` 引入提交（sched_ext 树与 bpf 树的哈希空间不同，AI 机器人很可能只在 bpf 仓库里查），并回帖给出结论。这条是当日唯一无人回应的具体待办。
- **把契约变成可测试项**：既然 v2 只是「文档化 2^63 半程要求」，可以提议在 `scx_bpf_dsq_insert_vtime()` 里对该前提加一次廉价的 `WARN`/统计（Andrea 的原话是 `document or enforce`），或至少加一个 selftest 覆盖「DSQ 内 vtime 跨度接近 2^63」时的行为。
- **同类审计**：`(s64)(a - b) < 0` 与 `time_before64()` 混用的比较器不止 flatcg 一个。可以在 `tools/sched_ext/` 与 `kernel/sched/ext/` 里做一次同类比较器排查，作为后续 patch 交出去。
- **方法论提醒（对内）**：我们在自研 BPF/调度扩展上做「饿死类」复现时，必须先固定输入是否满足 API 前提，否则容易重演本次 v1 的误报。

## 参考链接

- v1 0/2 封面: https://lore.kernel.org/all/20260901024038.730424-1-cui.tao@linux.dev/
- v1 1/2（被撤回的比较器改动）: https://lore.kernel.org/all/20260901024038.730424-2-cui.tao@linux.dev/
- Andrea Righi（反例 + 饿死分析）: https://lore.kernel.org/all/apZ06G_-oC5cTprM@gpd4/
- Tejun Heo（rolling cursor 定性）: https://lore.kernel.org/all/apaM3G2AJmYkGJW-@slm.duckdns.org/
- 作者撤回 1/2: https://lore.kernel.org/all/d8665587-a825-48d8-afb2-53fe10af0546@linux.dev/
- v2 0/2 封面: https://lore.kernel.org/all/20260901140343.764080-1-cui.tao@linux.dev/
- v2 1/2（kdoc）: https://lore.kernel.org/all/20260901140343.764080-2-cui.tao@linux.dev/
- v2 2/2（flatcg）: https://lore.kernel.org/all/20260901140343.764080-3-cui.tao@linux.dev/
- bot+bpf-ci 对 Fixes 标签的质疑: https://lore.kernel.org/all/ac57ae5abecf982961cd6baf346e19884a44be78430b563b781940b625559684@mail.kernel.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched_ext: fix vtime priority queue inversion on wide vtime spread"
id: sched-20260901-009
date: '2026-09-01'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: '<20260901024038.730424-1-cui.tao@linux.dev>'
lore_url: "https://lore.kernel.org/all/20260901140343.764080-1-cui.tao@linux.dev/"
authors: [Tao Cui, Andrea Righi, Tejun Heo]
maintainers_involved: [Tejun Heo, Andrea Righi]
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260901024038.730424-1-cui.tao@linux.dev>'
    date: '2026-09-01'
    summary: '1/2 把 scx_dsq_priq_less() 的 time_before64() 换成朴素 u64 <（理由：全序、尊重调度器要求的顺序）；2/2 把 scx_flatcg 的 cgv_node_less() 换成 (s64)(a-b) < 0'
    review_outcome: '1/2 被 Andrea Righi 以 a=U64_MAX-5/b=3 反例否掉并指出朴素比较会造成无界饿死；Tejun Heo 定性为 "dsq_vtime is by (implicit) definition a rolling cursor"，建议只补文档；作者当日承认探针输入违反前提、撤回 1/2。2/2 收到 bot+bpf-ci 对 Fixes 标签的质疑（7b742aa2c2c9 vs a4103eacc2ab4），无人回应'
  - version: v2
    msgid: '<20260901140343.764080-1-cui.tao@linux.dev>'
    date: '2026-09-01'
    summary: '按 Andrea/Tejun 的意见重做：1/2 改为在 scx_bpf_dsq_insert_vtime() kdoc 中写明 vtime 是滚动游标、同一 DSQ 内的值须彼此相差小于 2^63；2/2 flatcg 不变，其回绕比较的正确性由 cgrp_cap_budget() 的 max_budget 钳支撑'
    review_outcome: '本日尚无 review 回帖'
upstream_commit: null
fixes_commit: '06e51be3d5e7'
merged_branch: null
merge_assessment:
  likelihood: likely
  blocking_issues:
  - 'Fixes: 7b742aa2c2c9 被 bot+bpf-ci 质疑应为 a4103eacc2ab4，作者未回应'
  - '2/2 仅有 compile test + VM smoke test，未走 bpf-ci 完整回归'
  - 'v2 尚无 Reviewed-by'
  next_action: '作者确认 Fixes 标签；maintainer 决定进 for-7.3-fixes 还是 for-7.4'
contribution_opportunities:
  - kind: review
    description: '核对 scx_flatcg 引入提交究竟是 7b742aa2c2c9 还是 a4103eacc2ab4（AI 机器人只在 bpf 仓库查找），回帖给出定论——本日唯一无人回应的待办'
  - kind: new_patch
    description: '把"同一 DSQ 内 vtime 跨度须小于 2^63"从文档变成可检测项：廉价 WARN/统计，或 selftests 覆盖接近半程跨度的排序行为（Andrea 原话 document or enforce）'
  - kind: extend
    description: '审计 kernel/sched/ext 与 tools/sched_ext 中其它 vtime/时间戳比较器，找出与回绕语义不一致的朴素比较并统一'
source_email_count: 8
related_articles: [sched-20260902-005, sched-20260901-018, sched-20260901-008]
tags:
- sched_ext
- cgroup
generated_at: '2026-09-07'
---
