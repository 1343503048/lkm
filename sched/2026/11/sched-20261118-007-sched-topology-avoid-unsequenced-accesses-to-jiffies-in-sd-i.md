# sched/topology: Avoid unsequenced accesses to jiffies in sd_init()

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261115-005：Nathan Chancellor 修 clang 新告警导致的构建破坏——`sd_init()` 的 designated initializer 里两处 `= jiffies`（`.last_balance`、`.last_decay_max_lb_cost`）对 volatile 变量构成未定序访问，`CONFIG_WERROR=y` / `W=1` 下 `-Wunsequenced` 报错（Fixes: 2b4cfe64dee0，Cc: stable），v1 把两处初始化移到 initializer 之外插入序列点。
- sched-20261118-007（今天）：**v2 引发维护者对「修法本身」与「jiffies 是否该是 volatile」的元讨论**——Peter 质疑「这改变看起来蠢、真有必要吗」并延伸到「volatile 的存废」，Nathan 坚持必要（UB 现在不是问题、以后可能变问题），Nick 与 David Laight 追问为何不直接改变量声明或用更清晰的写法。

## 背景与问题

（承接 sched-20261115-005）clang 改进对 volatile 变量未定序访问的告警后，`sd_init()` 的 designated initializer 里两处 `= jiffies` 触发 `-Wunsequenced`（C11 6.7.9.23 下 indeterminately sequenced 的未定序 side effect，属 UB），`CONFIG_WERROR=y`/`W=1` 下构建失败。v2 沿 v1 思路（把初始化移出 initializer 加序列点）。今日讨论从「怎么修」升级到「该不该这样修 / volatile 的语义」。

## 技术方案

今日为讨论、无新代码：

- **Peter Zijlstra**：不改代码语义的整形补丁「seems daft, is this really needed?」；并指出 jiffies 是「READ_ONCE() 推出之前的老古董」，曾想把 `task_struct::state` 的 volatile 也去掉；怀疑这是 clang 的「subtle act of sabotage」，应让 clang 回退这诡异告警（C 委员会想用 `_Atomic` 取代 volatile）。
- **Nathan Chancellor**：坚持必要——「这就像其它 UB，现在不是真问题，但未来可能变成问题」；并解释 jiffies 访问频繁（全树都在用），不适合改声明。
- **Nick Desaulniers**：也好奇 jiffies 为何声明为 volatile（常规指导是用 cast-to-volatile 指针而非声明 volatile）；并建议 diff 前后反汇编对比更直观。
- **David Laight**：指出「如今工具要 WRITE_ONCE/READ_ONCE 配对、对 plain 访问挑刺，旧的『部分 volatile』指导已过时」；并质疑 initializer 本身会生成「栈上结构体再 memcpy」的差代码。

## 版本演进与当前进展

*current_version: v2（2026-11-16 发出，`<20261116-topology-wunsequenced-v2-1-54611119172b@kernel.org>`）*。今日为讨论日，无新版本：维护者与多名 ClangBuiltLinux 相关人员就「修法必要性」与「volatile 语义」各抒己见。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched maintainer）**：质疑「整形/加序列点」的修法是否必要，主张问题根源在 clang 对 volatile 的过激告警，甚至建议让 clang 回退。
- **Nathan Chancellor（作者，ClangBuiltLinux 维护者）**：坚持补丁必要（UB 防御），jiffies 不适合改声明。
- **Nick Desaulniers / David Laight**：追问 volatile 声明来源与反汇编佐证。
- 无 NAK；分歧是「编译器告警要不要迁就」的元层面，尚无收敛。

## 合入评估

*likelihood=medium*。语义不变的构建修复本应快速合入，但 Peter 对「是否值得为 clang 告警改代码」持保留态度，且讨论被带向 volatile 存废的元话题。*blocking_issues*：Peter 对修法必要性持疑，需作者进一步说明（如反汇编对比）或等 clang 调整告警。*next_action*：Nathan 提供反汇编对比 / C11 UB 论证，或与 clang/clang 委员会确认告警行为。

## 效果评估

无运行时数据；修复的是构建期告警。作者主张消除 UB（未定序 volatile 访问），Peter 认为「不是现在的问题」。

## 我可以参与的点

- **review**：提供 `sd_init()` 修前/修后反汇编差异，验证「移出 initializer」是否确实消除多余的 volatile 访问，为「是否有必要」的争论提供客观证据。
- **discussion**：就「jiffies 应保持 volatile 声明，还是改为 READ_ONCE/WRITE_ONCE + 非 volatile」给出意见。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/20261116-topology-wunsequenced-v2-1-54611119172b@kernel.org/
- Peter 的质疑: https://lore.kernel.org/all/20261117183043.GK1813469@noisy.programming.kicks-ass.net/
- David Laight 的评论: https://lore.kernel.org/all/20261118100354.495fda73@pumpkin/

---
id: sched-20261118-007
date: '2026-11-18'
subject: "sched/topology: Avoid unsequenced accesses to jiffies in sd_init()"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261116-topology-wunsequenced-v2-1-54611119172b@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261116-topology-wunsequenced-v2-1-54611119172b@kernel.org/"
authors: [Nathan Chancellor]
maintainers_involved: [Peter Zijlstra]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261114-topology-wunsequenced-v1-1-686a36fe61f5@kernel.org>"
    date: '2026-11-15'
    summary: "把两处 jiffies 初始化移出 designated initializer"
    review_outcome: "暂无 review"
  - version: v2
    msgid: "<20261116-topology-wunsequenced-v2-1-54611119172b@kernel.org>"
    date: '2026-11-16'
    summary: "v2（细节承接 v1，修法一致）"
    review_outcome: "Peter 质疑必要性，讨论转 volatile 元话题"
upstream_commit: null
fixes_commit: "2b4cfe64dee0"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["Peter 对修法必要性持疑", "volatile 存废元讨论未收敛"]
  next_action: "Nathan 提供反汇编对比 / UB 论证，或确认 clang 告警行为"
contribution_opportunities:
  - kind: review
    description: "提供 sd_init 修前/修后反汇编差异佐证必要性"
  - kind: discussion
    description: "就 jiffies 保持 volatile 还是改 READ_ONCE/WRITE_ONCE 给出意见"
generated_at: "2026-11-19T09:00:00+08:00"
source_email_count: 5
related_articles: [sched-20261115-005]
tags: [topology]
---
