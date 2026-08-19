# arm64: sched/preempt: Enable HAS_SEPARATE_PREEMPT_RESCHED_BITS

## TL;DR

Boqun Feng 发出一个 24 patch 的 preempt_count 清理与重构系列，其中三个与调度核心直接相关：两个是 `kernel/sched/core.c` 中调试断言函数的参数与比较清理，一个是为 arm64 打开 `HAS_SEPARATE_PREEMPT_RESCHED_BITS`。改动本身低风险，但作为跨架构大系列，合入取决于整体协调。

## 背景与问题

系列围绕 `preempt_count` 的表示与使用做清理，本次采样到的三个 sched 相关 patch 各自解决一个独立的小问题：

**08/24 — `__cant_sleep()` 的死参数**。该函数带一个 `preempt_offset` 参数，但**所有调用点传的都是 0**（唯一的调用宏 `cant_sleep()` 硬编码传 0）。这个参数除了让代码里出现一个形如 `preempt_count() > preempt_offset` 的比较之外没有任何作用。

**09/24 — `__cant_migrate()` 中的有符号比较**。`preempt_count()` 在所有架构上都是非负 int（使用 `PREEMPT_NEED_RESCHED` 的架构会在返回时把 MSB 掩掉），但代码里仍在做有符号比较。这是语义上的冗余，也容易让读者误以为存在负值情况。

**11/24 — arm64 未启用 `HAS_SEPARATE_PREEMPT_RESCHED_BITS`**。arm64 已经使用 64 位 preempt count，且 need-resched 位维护在与 preempt count **分离的另一个 32 位字段**中。这意味着 preempt count 本身有足够位宽表示 16 级 NMI 嵌套，完全满足该 Kconfig 的前提，但一直没有 select 它。不开启的代价是：多一个 per-CPU 变量、NMI 路径上多若干条指令。

## 技术方案

三个 patch 都是最小改动：

**08/24**：删掉 `__cant_sleep()` 的第三个参数，声明与定义同步修改，`cant_sleep()` 宏相应简化；函数体内 `if (preempt_count() > preempt_offset)` 直接变成 `if (preempt_count())`。改动 2 文件各 4 行。

**09/24**：把 `__cant_migrate()` 中对 `preempt_count()` 的有符号比较改为直接的布尔判断，理由是该值恒为非负。

**11/24**：`arch/arm64/Kconfig` 中在 ARM64 的 select 列表里加一行 `select HAS_SEPARATE_PREEMPT_RESCHED_BITS`。**单文件 1 行**。这是典型的「前置条件早已满足、只差一个开关」的改动，风险集中在 NMI 嵌套深度假设是否真的成立。

需要如实说明：本次只采样到这三封邮件，系列另外 21 个 patch 的内容、以及是否存在封面信（PATCH 00/24）都不在本次数据范围内，因此**无法评估这三个 patch 在整个系列中的依赖关系**——例如 11/24 是否依赖前面某个 patch 引入的基础设施。

## 版本演进与当前进展

v1，2026-08-01 04:30 发出（三封邮件时间戳相同，为同一批投递）。当日未观察到任何 review 回复。

## Maintainer 意见与讨论焦点

**暂无相关内容**。本次采样中没有观察到任何 review 回复或 maintainer 表态。

从惯例判断，这类改动需要的确认方是：`kernel/sched/core.c` 中 preempt 相关的改动通常由 Peter Zijlstra 把关；arm64 Kconfig 的改动需要 arm64 maintainer（Catalin Marinas / Will Deacon）确认 NMI 嵌套深度假设。但这属于流程推测，当日邮件中没有任何实际证据，不应当作已发生的事实。

## 合入评估

合入可能性 **medium**，且这个判断的置信度不高，原因是信息不完整。

**就这三个 patch 本身而言**，08/24 和 09/24 是几乎无风险的清理（删死参数、改冗余比较），单独看合入门槛很低；11/24 只有一行，但涉及架构级行为假设，需要 arm64 侧确认「16 级 NMI 嵌套足够」这个前提。

**但作为 24 patch 大系列的一部分**，它们的命运取决于整体：跨越 sched、arm64、以及可能的其他架构，需要多方 maintainer 协调；大系列往往需要多轮迭代，或被拆分成若干独立小系列分批合入。在没有看到封面信与其余 patch 的情况下，无法判断整体的成熟度。

## 效果评估

**基本无量化数据**。

11/24 的 changelog 中提到开启后「节省一个 per-CPU 变量以及 NMI 路径中的额外指令」——这是**作者的机制层面判断，未给出具体节省的指令条数或任何性能测量**，不应当作已验证的收益。

08/24 与 09/24 是纯代码清理，本身不预期有性能影响，邮件中也未给出数据，这属于合理情况。

## 我可以参与的点

- **Review（门槛低、见效快）**：08/24 可以帮忙全树核对 `__cant_sleep()` 的所有调用点确实都传 0（作者声称如此，值得独立验证）；09/24 可以核对在各架构的 preempt_count 布局下，改为无符号语义后 `PREEMPT_NEED_RESCHED` 掩码处理是否在所有路径上都已生效——这是「恒为非负」这一前提能否成立的关键。
- **测试**：在 arm64 机器上验证 11/24 开启后 NMI 嵌套路径（perf NMI、SDEI、pseudo-NMI）行为正常，特别是构造较深嵌套的场景确认 16 级假设成立；同时可以实测作者声称的 NMI 路径指令节省，用具体数字替换现在的定性描述。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "arm64: sched/preempt: Enable HAS_SEPARATE_PREEMPT_RESCHED_BITS"
id: sched-20260801-007
date: 2026-08-01
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<uid-13886@qq-imap>"
lore_url: unknown
authors: [Boqun Feng]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<uid-13886@qq-imap>"
    date: 2026-08-01
    summary: "24 个 patch 的大系列，围绕 preempt_count 语义清理与 HAS_SEPARATE_PREEMPT_RESCHED_BITS 展开。当日观察到其中 3 个与 sched 直接相关：08/24 移除 __cant_sleep() 中恒为 0 的 preempt_offset 参数；09/24 消除 __cant_migrate() 中对 preempt_count() 的有符号比较；11/24 为 arm64 打开 HAS_SEPARATE_PREEMPT_RESCHED_BITS，节省一个 per-CPU 变量并减少 NMI 路径指令"
    review_outcome: "当日仅观察到系列本身发出，未见 review 回复"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["24 个 patch 的跨子系统大系列，需要 sched、arm64、以及各架构 maintainer 分别确认，协调成本高", "本次仅观察到 3 封 sched 相关邮件，系列整体状态与其余 21 个 patch 的内容不在本次采样范围内，信息不完整"]
  next_action: "等待 Peter Zijlstra（sched preempt 方向）与 arm64 maintainer 对相关 patch 的意见"
contribution_opportunities:
  - kind: review
    description: "08/24 与 09/24 是低风险清理，可以帮忙核对 __cant_sleep() 的所有调用点确实都传 0、以及 __cant_migrate() 改为无符号比较后在各架构 preempt_count 布局下语义不变"
  - kind: testing
    description: "在 arm64 机器上验证 11/24 开启 HAS_SEPARATE_PREEMPT_RESCHED_BITS 后 NMI 嵌套（perf NMI / SDEI）路径行为正常，并测量作者声称的『节省 per-CPU 变量与 NMI 路径指令』的实际效果"
generated_at: "2026-08-02T00:55:00"
source_email_count: 3
related_articles: []
tags: [preempt, arm64]
---
