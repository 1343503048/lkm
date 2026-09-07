# sched_ext: pass the initial cpu.idle state in scx_cgroup_init_args

## TL;DR

**这是 08-24/08-25 已报道系列（sched-20260824-001、sched-20260825-005）的增量更新，本日报道的是合入结果而非新讨论。** 09-01 05:59 Tejun Heo 一句话收尾：`Applied 1 to sched_ext/for-7.3-fixes and 2 to sched_ext/for-7.4, with Andrea's Reviewed-by from the cover added to 2 and the subjects capitalized.` 即 `cpu.idle` 初值缺失的修复（1/2）按 fixes 走 7.3，纯重命名（2/2）按 cleanup 走 7.4。值得注意的是**时序**：这个应用发生在 Tejun 08-31 发出、09-01 05:05 已被 Linus 合入的 `sched_ext-for-7.3-rc1-fixes` tag **之后**（该 pull 里 Tao Cui 只有 1 篇 docs 提交，见 sched-20260901-012），所以 1/2 不在 v7.3-rc1 修复集合内，要等下一个 fixes pull。截至缓存覆盖的 09-07，尚未看到后续 pull。

## 背景与问题

机制部分与 08-25 报道一致，这里只重述必要的一环：`struct scx_cgroup_init_args` 是内核在 `ops.cgroup_init()` 时把一个 cgroup 的初始 CPU 控制参数交给 BPF 调度器的载体，此前只带 `weight` 与 `bw_period_us/bw_quota_us/bw_burst_us`，**不带 `cpu.idle`**。后果是：调度器加载（或 cgroup 在其下上线）之前就已经被设成 `cpu.idle=1` 的 cgroup，在 BPF 调度器眼里是 non-idle，只有等 `cpu.idle` 被**再次写入**时才会通过 `ops.cgroup_set_idle()` 得知。作者原话：

> A cgroup that was already configured idle before the scheduler was loaded (or before it was onlined under it) is presented as non-idle, and the BPF scheduler only learns about it if cpu.idle is written again later.

对混部场景这就是行为差异：`cpu.idle` 是 SCHED_IDLE 的 cgroup 等价物，若调度器在 init 阶段看不到它，它会按普通权重调度该组，直到下一次人工改写。

## 技术方案

`kernel/sched/ext/internal.h` 的 `struct scx_cgroup_init_args` 末尾加一个字段（带注释点明它就是 `cpu.idle` 表达的 SCHED_IDLE 配置）：

```
+	/* whether the cgroup is configured SCHED_IDLE via cpu.idle */
+	bool			sched_idle;
```

并在**全部四处**构造该结构体的地方填上，这也是 1/2 的实际覆盖面：

- `scx_tg_online()` — cgroup 上线到调度器之下；
- `scx_cgroup_init()` — 调度器加载时已存在的 cgroup；
- `scx_cgroup_claim_subtree()` / `scx_cgroup_return_subtree()`（`kernel/sched/ext/sub.c`）— 子调度器（sub-scheduler）cgroup 接管/交还路径。

2/2 是配套清理：`struct scx_task_group`（`include/linux/sched/ext.h`）里的 `bool idle` 改名 `bool sched_idle`，与 `scx_cgroup_init_args.sched_idle` 对齐。改名理由由 Tejun 在 v2 时给出，作者照抄进 commit message：

> In sched_ext, a bare "idle" reads as CPU idle state (ops.update_idle(), idle cpumasks, scx_bpf_pick_idle_cpu()). cpu.idle is the cgroup analog of the SCHED_IDLE policy, so please name the field sched_idle instead.

v3 相对 v2 的四点变化（cover 自述）：字段改名 `sched_idle`（Tejun 意见）、把 `tg->scx.idle` 的重命名拆成独立 2/2「so 1/2 stays minimal for stable backport」、补 `Fixes:` 标签（Andrea 意见）、在 current linux-next 上重生（顺带解决 v2 报的 CI 冲突）。整套 2 patch 的 diffstat 是 4 文件 +11/-4。

## 版本演进与当前进展

- **v1**（08-24，`<20260824133954.561956-1-cui.tao@linux.dev>`）→ **v2**（08-24，`<20260824142817.568085-1-cui.tao@linux.dev>`）→ 08-25 00:54 Tejun 要求改名 `<20eb5e65cb330a6f9cc41781af302873@kernel.org>`。
- **v3**（08-25 10:35，cover `<20260825023557.27881-1-cui.tao@linux.dev>`）：拆成 1/2 修复 + 2/2 重命名，补 `Fixes: 347ed2d566da ("sched/ext: Implement cgroup_set_idle() callback")`。
- 08-25 13:51 Andrea Righi 在 cover 上 `Reviewed-by`（`<ao0tfbNNcs514WgU@gpd4>`，"This looks good to me."）。
- **09-01 05:59 Tejun Heo 分拆应用**（`<32bb40e15ac938fc380e4a65eebf3f9a@kernel.org>`）：1/2 → `sched_ext/for-7.3-fixes`，2/2 → `sched_ext/for-7.4`；把 cover 上的 `Reviewed-by` 挪到 2/2；subject 首字母大写。系列到此关闭，无 v4。
- 由本系列派生的后续：08-25 13:20 作者提出 `scx_group_set_idle()` 对同值重写也会投递 `ops.cgroup_set_idle()`，并明确「The fix is a one-line guard, but **it reads the field renamed here**, so I'll post it on top of this series once it lands.」（`<b53c61a1-4d7d-4232-941f-d48b0563d4ed@linux.dev>`）。09-01 11:11 该补丁以 v1/v2 出现（见 sched-20260901-008），其 diff 里读的确实是 `tg->scx.sched_idle`——即它的前提是 2/2 先进树。

## Maintainer 意见与讨论焦点

- **Tejun Heo**：全程只在两件事上表态——命名（v2 时）与落地拆分（09-01）。拆分本身是最有信息量的部分：**同一个 2-patch 系列被投到两个不同目的地的分支**，修复进 `for-7.3-fixes`（会经下一次 pull 进 mainline 并成为 stable 候选），机械重命名进 `for-7.4`（合并窗口）。作者的拆 patch 决策（「so 1/2 stays minimal for stable backport」）正是为了让这一手成为可能；如果他当时把改名和修复混在一个 commit 里，维护者就只能二选一。
- **Andrea Righi（NVIDIA）**：本系列的实际早期评审者，贡献点有两处：`sub.c` 的两条 handover 路径（作者 08-25 10:20 致谢「for catching the sub.c handover paths earlier」，`<bd013141-0635-49ea-8c1b-f18133138678@linux.dev>`）与 `Fixes:` 标签；最终 `Reviewed-by` 给在 cover 上，由 Tejun 落到 2/2。
- **一处标签流转细节**：1/2 的 trailer 里本身就带了 `Reviewed-by: Andrea Righi`，而 2/2 没有——所以 Tejun 特意说明「Andrea's Reviewed-by from the cover added to 2」。作者此前也预告过改名是机械的、保留 tag（"The rename is mechanical, so I kept the tag, but I'm happy to wait for a re-review if you prefer."）。这类「评审标签是否随机械改动沿用」的处理方式值得记下来。
- 无人质疑方案，无人要求 benchmark。

## 合入评估

`likelihood = merged`，且**已是既成事实的 accepted**：两半都已进 tj/sched_ext 分支。逐片看：

- 1/2（修复，`Fixes: 347ed2d566da`）在 `sched_ext/for-7.3-fixes`，但**不在** `sched_ext-for-7.3-rc1-fixes`（08-31 发 pull、09-01 05:05 合入 mainline，merge commit `bf1079577a116f0685e7025b9ee2547345ee1c63`）里，因为 Tejun 应用它的时间在那之后；它需要下一个 sched_ext fixes pull 才进 mainline，随后才是 stable 回合候选。
- 2/2（重命名）在 `sched_ext/for-7.4`，7.4 合并窗口才可见。
- 截至缓存中的 09-07，未再出现 sched_ext 的 GIT PULL，因此两半都**还没有 mainline commit hash**（`upstream_commit: null`，未获取到）。
- 无阻塞问题。唯一需要留意的是依赖链：09-01 那条重复投递修复（sched-20260901-008）读的是重命名后的字段，所以它只能落在 2/2 之后，即最早也是 7.4 的树。

## 效果评估

作者自述的验证是**功能级、非性能级**：

> Verified in a VM with a probe scheduler printing the init args: a cgroup configured cpu.idle=1 before loading shows sched_idle=1 in ops.cgroup_init(), the default shows 0, and later cpu.idle writes still come through ops.cgroup_set_idle(). The sub-scheduler paths are compile-tested only.

即 `scx_tg_online()`/`scx_cgroup_init()` 两条主路径有探针实测，而 **sub-scheduler 的 claim/return subtree 两条路径只有编译验证**——这是本系列留下的唯一实证缺口，且恰好是较新、较少被跑到的 sub-scheduler 特性代码。无性能数据，也不需要：补丁不触碰热路径，只在 init 时多赋一个 bool。

## 我可以参与的点

- **补上那条实测缺口（零门槛、有明确认领对象）**：写一个打印 `ops.cgroup_init()` 参数的探针调度器，在启用 sub-scheduler 的配置下走一遍 `scx_cgroup_claim_subtree()` / `scx_cgroup_return_subtree()`，确认接管/交还时 `sched_idle` 与实际 `cpu.idle` 一致。作者自己声明了 compile-tested only，这类补测回帖最受欢迎。
- **回合前的规避（若自家分支带 sched_ext 且在用 cpu.idle）**：1/2 落地前，BPF 调度器拿不到初值，正确做法是在 scheduler start / cgroup init 回调里**自己去 cgroupfs 读一次 `cpu.idle`**，不要依赖 `scx_cgroup_init_args`。这是本补丁修复的直接用户可见后果。
- **学一下 patch 拆分**：修复 + 机械重命名分开、并且刻意让修复那片保持最小，使维护者能把两片送到不同分支。OLK 类长期分支里大量「修复 + 顺手改名」的本地补丁可以照这个方式重切，能显著提高回合成功率。
- **回合冲突预告**：2/2 改了 `include/linux/sched/ext.h` 的 `struct scx_task_group`（`idle` → `sched_idle`）并在 `kernel/sched/ext/internal.h` 加字段。任何触碰 `tg->scx.idle` 的 out-of-tree 补丁在跟这个改动时都会冲突；若在 7.3-fixes 与 7.4 之间半路回合，注意 `scx_group_set_idle()` 的字段名在不同分支不一致。

## 参考链接

- lore thread (v3 cover): https://lore.kernel.org/all/20260825023557.27881-1-cui.tao@linux.dev/
- 1/2: https://lore.kernel.org/all/20260825023557.27881-2-cui.tao@linux.dev/
- 2/2: https://lore.kernel.org/all/20260825023557.27881-3-cui.tao@linux.dev/
- Tejun 的改名要求: https://lore.kernel.org/all/20eb5e65cb330a6f9cc41781af302873@kernel.org/
- Andrea Righi Reviewed-by: https://lore.kernel.org/all/ao0tfbNNcs514WgU@gpd4/
- 09-01 Tejun Applied 回执: https://lore.kernel.org/all/32bb40e15ac938fc380e4a65eebf3f9a@kernel.org/
- 派生的重复投递问题报告: https://lore.kernel.org/all/b53c61a1-4d7d-4232-941f-d48b0563d4ed@linux.dev/
- tip-bot commit: 未获取到（截至 09-07 缓存内无后续 sched_ext pull）
- stable backport: 未获取到（1/2 带 `Fixes: 347ed2d566da`，需先进 mainline）

---
id: sched-20260901-017
subject: "sched_ext: pass the initial cpu.idle state in scx_cgroup_init_args"
date: '2026-09-01'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<20260825023557.27881-1-cui.tao@linux.dev>"
lore_url: "https://lore.kernel.org/all/32bb40e15ac938fc380e4a65eebf3f9a@kernel.org/"
authors: [Tao Cui, Tejun Heo, Andrea Righi]
maintainers_involved: [Tejun Heo, Andrea Righi]
current_version: v3
patch_series:
  - version: v1
    msgid: "<20260824133954.561956-1-cui.tao@linux.dev>"
    date: '2026-08-24'
    summary: '在 scx_cgroup_init_args 中新增 idle 字段并在构造处填充'
    review_outcome: 'Andrea Righi 指出漏了 sub.c 的两条 handover 路径；建议补 Fixes: 标签'
  - version: v2
    msgid: "<20260824142817.568085-1-cui.tao@linux.dev>"
    date: '2026-08-24'
    summary: '补齐路径后重发'
    review_outcome: 'Tejun Heo 08-25 要求字段改名 sched_idle，并建议一并重命名 tg->scx.idle；另有 CI 冲突报告'
  - version: v3
    msgid: "<20260825023557.27881-1-cui.tao@linux.dev>"
    date: '2026-08-25'
    summary: '字段改名 sched_idle；拆为 1/2 修复 + 2/2 重命名（保持 1/2 最小以利 stable 回合）；补 Fixes: 347ed2d566da；在 current linux-next 重生'
    review_outcome: 'Andrea Righi 在 cover 上 Reviewed-by；09-01 Tejun 应用：1 -> sched_ext/for-7.3-fixes，2 -> sched_ext/for-7.4，cover 的 Reviewed-by 落到 2/2，subject 首字母大写'
upstream_commit: null
fixes_commit: "347ed2d566da"
merged_branch: "sched_ext/for-7.3-fixes (1/2), sched_ext/for-7.4 (2/2)"
merge_assessment:
  likelihood: merged
  blocking_issues:
  - "1/2 的应用时间晚于 sched_ext-for-7.3-rc1-fixes（09-01 05:05 已合入 mainline），故需下一个 sched_ext fixes pull 才进 mainline"
  - "2/2 落在 for-7.4，须等 7.4 合并窗口"
  next_action: "跟踪下一次 sched_ext pull 取得 1/2 的 mainline hash；作者称 sub-scheduler 两条路径仅 compile-tested，可补实测"
contribution_opportunities:
  - kind: testing
    description: "用探针调度器在启用 sub-scheduler 的配置下实测 scx_cgroup_claim_subtree()/scx_cgroup_return_subtree() 的 sched_idle 是否正确（作者仅 compile-tested）"
  - kind: extend
    description: "1/2 落地前，BPF 调度器需在 cgroup init 时自行读 cpu.idle 兜住初值"
  - kind: review
    description: "2/2 重命名 struct scx_task_group 的 idle 字段；任何触碰 tg->scx.idle 的 out-of-tree 补丁都会冲突，7.3-fixes 与 7.4 之间字段名不一致"
source_email_count: 6
related_articles:
  - "sched-20260824-001"
  - "sched-20260825-005"
  - "sched-20260901-008"
  - "sched-20260901-012"
tags:
- sched_ext
- cgroup
generated_at: '2026-09-07'
---
