# sched/cache: Introduce helpers for task migration decisions

## TL;DR

本补丁是 Jianyong Wu 23 patch RFC v2 中的 11/23，把 LLC/NUMA 维度的迁移判据抽成可复用 helper（回帖中可见的实体包括带 `llc_imb_pct` 阈值的 `util_greater()`、按「亲和节点序列」逐级走 LLC 的 `can_migrate_node()`，以及被拿来对照的既有 `can_migrate_llc()`）。本日 Tim Chen 报告该补丁单独编译不过：`can_migrate_node()` 里 `dst_pre` 在上一个作用域声明、却在 `kernel/sched/fair.c:10855` 的 `!util_greater(u, dst_pre)` 处使用，gcc 直接报 `'dst_pre' undeclared`；作者当天确认「fix 落在 patch 20 但没有折回本补丁，整套能编是因为 patch 20 把它补上了」，承诺下一版 squash 并在发版前逐 commit 编译。这条看似琐碎的反馈对本系列很关键——它是被 Peter Zijlstra 逐条要求拆分、复审的 23 补丁，可二分性直接决定能不能被接受。

## 背景与问题

RFC v2（08-27 投递，23 个补丁）走的是「先补拓扑与统计底座，再改放置与迁移决策」的路线：前段 01~10/23 加底座（`llc_to_node()`、NUMA distance matrix、per-sd scratch、per-CPU 与 per-sd 的任务 NUMA 偏好统计等）；中段以 11/23 的迁移判据 helper 与 12/23 的 rq 亲和收益计算为起点，且从 14/23（放掉 `prefer_sibling` 限制）起已经开始改行为；后段 17/23（fine-granularity NUMA balancing）、20/23（利用率估算）才落到主路径。11/23 正处在这个「抽象层」位置，是后面若干补丁的公共依赖。

11/23 要解决的问题可以从 Peter Zijlstra 的对照读法看出：新增的判据与既有 `can_migrate_llc()` 是同一族逻辑，但行为并不自动一致（缺少 `!get_llc_stats(src_cpu)` 的提前放行、缺少 `src_util` 减去 `tsk_util` 并截断到 0），而且新 helper 需要同时服务真正的任务迁移和 `llc_balance` 这类「无具体任务」的均衡判断——后者会传 `p == NULL`。另外，imbalance 检查用的是移动前的利用率，而容量检查与防抖动检查要用移动后的利用率，「迁移前/迁移后」的口径必须在 helper 里被显式化。

本日暴露的问题是工程质量而非算法：helper 内部变量作用域跨越了 `if` 块，且修正被留在后面的 patch 20 里，导致单个 commit 不可编译。

## 技术方案

补丁本体（`kernel/sched/fair.c`）从 review 与编译错误可还原出以下结构（原邮件正文未保留在本缓存，以下为回帖中出现的实体）：

- 利用率比较宏 `util_greater(util1, util2)` 展开为 `((util1) * 100 > (util2) * (100 + llc_imb_pct))`，即带可调不平衡阈值的百分比比较。
- `can_migrate_llc()` 风格的判定：`!get_llc_stats(src_cpu)` 时以 `mig_unrestricted` 直接放行；对 `src_util` 减去 `tsk_util` 并在 0 处截断。
- helper 允许 `p == NULL`：`llc_balance` 会传入空任务，此时 `tsk_util` 记 0，决策改由 `to_pref` 路径给出。
- 同时需要「迁移前」和「迁移后」两侧利用率：现有 imbalance 检查用移动前的值，而容量检查与防抖动（anti-bounce）检查要用移动后的值，因此引出 `src_pre`/`src_post`/`dst_pre`/`dst_post` 四个显式量（Peter Zijlstra 09-01 要求显式化并要求源侧减法截断到 0，作者已接受）。
- `can_migrate_node()` 按「目标 CPU 所在节点决定的亲和节点序列」遍历：先走 target 所在节点、再走包含 `dst_cpu` 的节点；节点内按 LLC 逐个走，目标节点的走法是终结式的——一旦走到 dst LLC 即可给出结论，其后的 LLC 不影响判断。
- 遍历中用到 `get_span_stats(span)`（`get_llc_stats()` 的包装）；PZ 质疑此处 `span` 就是一个 LLC，应直接用 `get_llc_stats()`。

本日 Tim Chen 的编译输出显示问题位于 `can_migrate_node()` 内 `&& !util_greater(u, dst_pre)`（`fair.c:10855`），`dst_pre` 声明在更早的作用域。

## 版本演进与当前进展

- 08-27 20:28 Jianyong Wu（`wujianyong@hygon.cn`）投递 RFC v2 全套 23 补丁（该日邮件未进本缓存，补丁正文不可见）。
- 08-31 与 09-01 两天，Peter Zijlstra 对其中 02、04、07、08、09、10、11、12、14、17、20 共 11 个子补丁逐条回帖，11/23 收到两封（结构性质询 + 反向圣诞树排序要求）；作者 09-01 ~ 09-02 逐条答复并接受大部分改动，包括「显式 `src_pre`/`src_post`/`dst_pre`/`dst_post`」、「去掉多余 else」、「改用 `get_llc_stats()`」、「重构过深嵌套」、「逻辑运算符换到行尾」、「变量声明改为 inverse christmas tree」。
- **本日 05:11 Tim Chen 报告单独编译失败**，判断「Seems like `dst_pre` was declared in previous scope above. Likely the posted version is slightly different from the tested version.」；10:04 作者确认根因是修复只落在 patch 20 未折回 patch 11，并承诺下一版 squash 且「compile-test each individual commit before posting the next version」。
- 截至本日尚无 v3 重投，本系列仍是 RFC 状态，无任何 `Reviewed-by`/`Acked-by`。

## Maintainer 意见与讨论焦点

- **Tim Chen（本日）**：唯一的意见是「这版补丁编不过」，并给出完整 gcc 报错（`kernel/sched/fair.c:10855:69: error: 'dst_pre' undeclared`，伴随 `util_greater` 宏的 `10618:27: note` 与 `make` 递归失败链）。他的推断是「投递版本与被测版本不一致」，这是 review 中相当硬的一条质量信号。
- **Jianyong Wu（作者，本日）**：坦白承认「the `dst_pre` fix landed in patch 20 but wasn't folded back into this patch, so patch 11 alone doesn't build -- the full series builds because patch 20 fixes it」，承诺 squash 到本补丁，并在下一版前逐 commit 编译。
- **Peter Zijlstra（09-01，构成当前主要待办）**：对 11/23 的结构性意见，逐条为——`!p` 为何合法（「It isn't clear when !p would be valid. migration is always about a task, no?」，作者答 `llc_balance` 传 NULL）；与 `can_migrate_llc()` 的行为差异（缺少 `!get_llc_stats(src_cpu)` 的 `mig_unrestricted` 提前返回、缺少 `src_util -= tsk_util` 并截断到 0）；「Strictly speaking this else is superfluous」；跳过 target 与 src 之间的节点被质疑为「which are the nodes with best locality, confusing」（作者解释这是 `!to-prefer` 路径、且 dst LLC 不在该子序列中，故这些邻居节点对本次迁移无关）；`get_span_stats()` 与 `get_llc_stats()` 的取舍；「(indent is getting a little out of hand here)」；「logical operators go at the end of the previous line, your patch is inconsistent on this point」；以及「We prefer inverse xmas ordering -- where possible. So please go through the code and re-arrange things.」
- 焦点因此是两层：**语义层**（helper 与既有 `can_migrate_llc()` 的判据必须一致，亲和节点序列的遍历顺序必须能自证正确）与**可投递性层**（逐 commit 可编译、可二分）。本日这封编译报告落在后者。

## 合入评估

likelihood: **unclear**。

依据（正向）：系列已经进入 Peter Zijlstra 的逐补丁细读阶段，这本身是稀缺信号——他在两天内覆盖 11 个子补丁，作者逐条接受并要求式修改，说明讨论是有效推进而非否决；分层（底座 → helper → 放置改动）的拆法正是应对大体量系列的标准手法。

卡点：一是本日暴露的「单 commit 编不过」说明该系列的分层在编译意义上并未真正独立，而 PZ 逐条细读的前提恰恰是每层可独立验证、可二分；作者承诺的逐 commit 编译测试是下一版的硬门槛。二是 11/23 的语义问题尚未闭环——`!p` 的合法性、与 `can_migrate_llc()` 的行为差异（提前返回与 `src_util` 扣减）、以及「跳过 locality 最好的中间节点」这条解释目前只有作者单方陈述，没有 PZ 的认可。三是 23 补丁 RFC 体量大、涉及 NUMA 细粒度均衡与放置主路径，无任何 tag，也没有跨平台数据支撑；四是同一作者同期还在推进 cpufreq 压力一侧的讨论（[[sched-20260903-010]]）与 11/23 的下游依赖 [[sched-20260903-011]]，合入顺序需要明确。

## 效果评估

邮件中未提供本补丁的效果数据。本日两封邮件全部是关于编译的，唯一的「数据」是 Tim Chen 贴出的完整 make 失败输出（错误行 `fair.c:10855`、宏定义行 `fair.c:10618` 以及 `scripts/Makefile.build` 的失败链）。

证据缺口需要点明：08-27 RFC v2 的封面与各补丁正文不在缓存中，无法确认作者是否随封面发过 benchmark；11/23 的 review 与回帖中也没有出现任何性能数字。也就是说，本系列公开线程里目前可见的量化内容只有「阈值参数 `llc_imb_pct`」这一形式（`util_greater` 用百分比乘 100 比较），其默认值与调优效果均未在本日材料中出现。

## 我可以参与的点

1. 直接做作者承诺的那件事，而且成本很低：把 23 个补丁 `git am` 到基线后写一个逐 commit `make kernel/sched/fair.o`（或 `allyesconfig`/`allmodconfig` + `W=1`）的脚本，跑一遍并把失败列表回帖。这类「逐 patch 可编译/可二分」的自动化验证在社区里长期缺人做，对大体量系列的接受度影响真实。
2. 替 Peter Zijlstra 把语义差异查清：对比 `can_migrate_llc()` 与新 helper 在 `!get_llc_stats(src_cpu)` 提前返回、`src_util -= tsk_util` 截断到 0、以及 `p == NULL` 三种输入上的行为是否等价，给出一张输入/返回矩阵。这是 11/23 能否站稳的核心。
3. 「亲和节点序列」的正确性验证：作者解释「跳过 target 与 src 之间 locality 最好的节点」是因为那是 `!to-prefer` 路径且 dst LLC 不在该子序列内——可以在多节点机器上打印亲和序列与实际迁移目标，验证该论证是否只在特定拓扑（如 2 节点）下成立；节点数 ≥4 时跳过中间节点更值得怀疑。
4. 回合视角：本系列对 OLK-6.6 的直接价值在于 helper 分层与「迁移前/迁移后双口径利用率」这一设计，而不是 23 个补丁整体；若要评估，可只把 `util_greater()`/`llc_imb_pct` 这层阈值抽象与自研 LLC 均衡代码对照，判断是否值得单独移植。同时把本日的教训当成硬性验收条件——回合系列必须逐 commit 可编译。

## 参考链接

- 本补丁与关键回帖：
  - RFC v2 11/23（作者原帖，正文未保留于本缓存）：https://lore.kernel.org/all/20260827122816.756234-12-wujianyong@hygon.cn/
  - RFC v2 封面：https://lore.kernel.org/all/20260827122816.756234-1-wujianyong@hygon.cn/
  - Tim Chen 的编译失败报告（本日）：https://lore.kernel.org/all/fac52a49e611f7f6a6637f04a2e44e8c23a260c6.camel@linux.intel.com/
  - 作者确认 dst_pre 修复留在 patch 20（本日）：https://lore.kernel.org/all/7b32770ca3a8491dbf2d215fccc75702@hygon.cn/
  - Peter Zijlstra 的结构性质询：https://lore.kernel.org/all/20260901090843.GQ4120091@noisy.programming.kicks-ass.net/
  - Peter Zijlstra 的 inverse xmas tree 要求：https://lore.kernel.org/all/20260901113207.GZ687043@noisy.programming.kicks-ass.net/
  - 作者对 PZ 的逐条答复：https://lore.kernel.org/all/226d79fa93a84193aa2507113747d348@hygon.cn/
- 相关文章：[[sched-20260902-009]]（本系列 RFC v2 的整体讨论）、[[sched-20260903-011]]（11/23 helper 的下游使用方）。

---
id: sched-20260903-012
date: '2026-09-03'
subject: 'sched/cache: Introduce helpers for task migration decisions'
subsystem: sched
type: discussion
status: rfc
severity: medium
thread_root_msgid: '<20260827122816.756234-1-wujianyong@hygon.cn>'
lore_url: https://lore.kernel.org/all/20260827122816.756234-12-wujianyong@hygon.cn/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Jianyong Wu
maintainers_involved:
- Tim Chen
- Peter Zijlstra
patch_series:
- "sched/cache: Introduce helpers for task migration decisions (RFC v2 11/23)"
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - "patch 11 单独编译不过（dst_pre 作用域），修复留在 patch 20，系列不满足逐 commit 可二分"
  - "与 can_migrate_llc() 的行为差异（!get_llc_stats 提前返回、src_util 扣截断）与 !p 合法性未获 PZ 认可"
  - "跳过 target 与 src 之间 locality 最优节点只有作者单方解释"
  - "23 补丁 RFC 无任何 tag，本缓存中看不到效果数据"
  next_action: "等 v3：squash dst_pre 修复并逐 commit 编译，同时回应 PZ 的语义与风格意见"
contribution_opportunities:
- "对 23 补丁逐 commit 做编译验证并回帖失败清单"
- "对比 can_migrate_llc() 与新 helper 在 p==NULL/统计缺失/利用率扣减上的行为矩阵"
- "在 4 节点以上拓扑验证亲和节点序列跳过中间节点的正确性"
- "评估 util_greater/llc_imb_pct 阈值抽象在 OLK-6.6 自研 LLC 均衡中的单独移植价值"
source_email_count: 2
related_articles:
- sched-20260902-009
tags:
- sched/cache
- load_balance
- numa_balancing
---
