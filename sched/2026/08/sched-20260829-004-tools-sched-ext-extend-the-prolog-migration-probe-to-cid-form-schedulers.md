# tools/sched_ext: Extend the prolog migration probe to cid-form schedulers

## TL;DR

David Carlier 的单补丁修 sched_ext 库头里的一个探针漏挂：`scx_lib_init_probe` 只 fentry 挂在 `bpf_scx_reg()` 上，而 **cid 形态的调度器走的是另一个注册入口 `bpf_scx_reg_cid()`**，探针根本不触发，于是 `__scx_prolog_disables_migration` 一直停在编译期默认值。补丁给 cid 路径补一个同体探针（用 `SEC("?fentry/...")` + `__SCX_OPS_OPEN()` 按符号存在与否 autoload，因为该符号 v7.2 才有），同时**把这个默认值从 `true` 翻成 `false`**——后者改的是"探针没跑时往哪一侧退化"的安全方向，当天无人 review，是这条补丁最该被审视的部分。

## 背景与问题

- sched_ext 的 BPF 调度器需要一个能回答"任务 @p 是否被 `migrate_disable()` 钉住"的 helper `is_migration_disabled()`。难点在于 BPF 代码执行期间 `current` **总是**被钉住：非 sleepable 程序的 prolog（`__bpf_prog_enter`）会 `migrate_disable()`、epilog 再放开，所以 `p->migration_disabled == 1` 是歧义值（分不清是 prolog 给的还是任务自己有的）。
- 库头用一次性探针来消歧：`scx_lib_init_probe` 是一个 fentry 程序，挂在 `bpf_scx_reg()`（`bpf_sched_ext_ops` 的 `.reg` 回调）上，靠 userspace 创建 struct_ops link 的自然调用链自动 attach，在 `ops.init()` 之前读当前任务的 `migration_disabled`，把"这个内核的 prolog 到底会不会禁迁移"记进 `__scx_prolog_disables_migration`。
- **漏挂**：存在第二种 vtable `bpf_sched_ext_ops_cid`，它的 `.reg` 指向的是**另一个函数** `bpf_scx_reg_cid()`。cid 形态调度器由此进入内核，原探针所在的 `bpf_scx_reg()` 不在其调用链上 → 探针永不触发 → flag 保持编译期值。作者同时指出，两个 `.reg` 都是 vtable 成员、都早于 `ops.init()`，因此不会被内联掉（这正是探针可行的前提）。

## 技术方案

- 把探针主体抽成 `static __always_inline void __scx_record_prolog_migration(void)`，两个 `SEC` 程序共用同一实现，避免逻辑复制：
  - `SEC("fentry/bpf_scx_reg")` 的 `scx_lib_init_probe`（原有）；
  - 新增 `SEC("?fentry/bpf_scx_reg_cid")` 的 `scx_lib_init_probe_cid`。
- **为什么要 `?` + 手动 autoload**：`bpf_scx_reg_cid()` 从 v7.2 才存在，而这份 `common.bpf.h` 要给更老内核编译调度器；用 `?` 前缀让程序在无该符号时安全跳过，再由 `__SCX_OPS_OPEN()` 里 `__COMPAT_has_ksym("bpf_scx_reg_cid")` 命中时 `bpf_program__set_autoload(..., true)` 打开。这是 sched_ext 生态标准的"向后兼容 fentry"写法。
- **默认值翻转**：`bool __scx_prolog_disables_migration __weak = true;` → 无初值（即 `false`）。作者的 reasoning 有两层：① `false` 对应 `is_migration_disabled(current)` **过度报告"迁移被禁用"**的那一侧——后果只是退回 local-only dispatch，属于安全失败；② 覆盖"只 attach 了 struct_ops map、没 attach fentry 程序"的 loader（探针同样不会跑）。
- 顺带把注释里的告警保留并收敛：prolog 最多给 `migration_disabled` 加 1；若读到 `> 1`，说明在 prolog 之前就有东西禁了迁移，探针结论不可靠，需要审计。

**被放弃的备选**（作者自己给出的理由）：让 cid 形态复用同一个 `bpf_scx_reg` 探针不成立（两个 vtable 入口是不同函数）；把默认值保持 `true` 也不行——按新注释的读法，`true` 恰恰是把歧义值 `== 1` 归给 prolog、从而报告"可迁移"，属于危险的欠报告方向。

## 版本演进与当前进展

- 当日（8/29 20:20）v1 发出，`Cc: Changwoo Min`（sched_ext 侧相关作者），**无人回复、无 Acked-by/Reviewed-by**，v1 即当前版本。
- 只有 2 个文件、+32/−24 行，属库头改动，不涉及内核侧 `kernel/sched/ext.c`。

## Maintainer 意见与讨论焦点

- 本日内**没有维护者表态**，因此争议点是我从补丁自身读出来的、社区大概率会问的两处：
  1. **默认值翻转的安全性论证是否成立**。旧注释明写"Defaults to true (conservative)…Under-reporting can crash the scheduler, so we err high"；新注释改成"the default is false for loaders that never attach the probes"。同一个 knob 的"哪一侧才是保守"被反过来说，必须有人确认 `is_migration_disabled()` 在当前 helper 实现下 `false` 确实意味着过度报告而非欠报告——这是唯一可能导致调度器崩溃的那类错误。
  2. **探针覆盖是否完备**。sched_ext 现在有多种 struct_ops 变体；只补 cid 一个入口，等于默认"以后新增 vtable 时要记得再来加探针"。是否可以改成不依赖具体 `.reg` 符号（例如挂在更早/更通用的点上，或在 `ops.init()` 里直接探测），是接口层面的可讨论点。
- 无 NAK、无分歧记录（因为还没有 reviewer）。

## 合入评估

**possible**。探针漏挂部分是明确的真 bug、改动局部、沿用生态既有惯例（`?` + `__COMPAT_has_ksym` + autoload），大概率会被 sched_ext 侧接受；卡点在默认值翻转——它改变的是未探针情况下的失败方向，若 reviewer 不同意这个方向，补丁会被拆成"只加探针"与"改默认值"两半。当天没有任何 ack/NAK，也无 stable/tip 记录。

## 效果评估

暂无效果数据。邮件里没有列出哪些真实调度器（cid 形态）受影响、也没有 attach 前后 flag 取值的实测或崩溃/退化案例；"默认值翻转会更安全"属于作者的代码推理，未见测试支撑。

## 我可以参与的点

- **验证默认值方向**：拿一个 cid 形态调度器（或任意 sched_ext 调度器）在开/不开该补丁下跑，检查 `is_migration_disabled(current)` 在 `migration_disabled == 1` 时的返回值，用结果回帖表态这侧到底是过报告还是欠报告——这是本补丁目前唯一缺的评审输入，成本很低。
- **补 loader 侧覆盖**：作者提到"只 attach struct_ops map 而不 attach fentry 程序"的 loader 场景，可以给 `tools/sched_ext` 的 selftest 加一例，把探针是否触发变成可断言的检查，避免以后新增 vtable 又漏挂。
- **接口层面提问**：讨论是否有必要为每种 struct_ops 变体配一个探针，还是改用统一探测点；这个问题目前没人回应。
- **回合判断**：属于 `tools/` 用户侧 BPF 库头，不影响内核 ABI；OLK-6.6 若要带 sched_ext 用户态库，可按上游合入结果跟进，无需提前回合。

## 参考链接

- lore thread（v1，当日唯一邮件）: https://lore.kernel.org/all/20260829122035.58018-1-devnexen@gmail.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260829-004
date: '2026-08-29'
subject: "tools/sched_ext: Extend the prolog migration probe to cid-form schedulers"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260829122035.58018-1-devnexen@gmail.com>"
lore_url: "https://lore.kernel.org/all/20260829122035.58018-1-devnexen@gmail.com/"
authors: [David Carlier]
maintainers_involved: [Changwoo Min]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260829122035.58018-1-devnexen@gmail.com>"
    date: 2026-08-29
    summary: "为 bpf_scx_reg_cid() 增加同体 prolog 探针（SEC(?fentry) + __COMPAT_has_ksym 控制 autoload），并把 __scx_prolog_disables_migration 默认值从 true 改为 false"
    review_outcome: "v1 刚发出，当天无人回复，无 Acked-by/Reviewed-by"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "无人 review；默认值翻转改变了未探针时的失败方向，安全性论证尚未被确认"
    - "未列出受影响的真实调度器与实测证据"
    - "探针按 struct_ops 变体逐个挂载，缺长期可维护方案"
  next_action: "需要 sched_ext 维护者确认默认值方向，并建议补 selftest 断言探针是否触发"
contribution_opportunities:
  - kind: testing
    description: "实测 is_migration_disabled(current) 在 migration_disabled==1 且探针未跑时的返回值，验证默认值翻转是否真的偏向过度报告"
  - kind: new_patch
    description: "给 tools/sched_ext 加一个断言 prolog 探针已触发的 selftest，覆盖只 attach struct_ops map 的 loader"
  - kind: discussion
    description: "讨论是否为每种 struct_ops 变体各自挂探针，还是改用统一探测点"
generated_at: "2026-09-07T22:06:23"
source_email_count: 1
related_articles: []
tags: [sched_ext, affinity]
---
