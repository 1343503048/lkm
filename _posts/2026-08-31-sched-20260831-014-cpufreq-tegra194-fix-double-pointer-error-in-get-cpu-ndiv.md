---
id: sched-20260831-014
date: '2026-08-31'
subject: 'cpufreq: tegra194: fix double-pointer error in get_cpu_ndiv'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20260831073009.3772408-1-luoxueqin@kylinos.cn>
lore_url: https://lore.kernel.org/all/20260831073009.3772408-1-luoxueqin@kylinos.cn/
authors:
- Xueqin Luo
- Viresh Kumar
- Sumit Gupta
maintainers_involved:
- Viresh Kumar
- Sumit Gupta
current_version: v1
patch_series:
- version: v1
  msgid: <20260831073009.3772408-1-luoxueqin@kylinos.cn>
  date: 2026-08-31
  summary: 去掉 smp_call_function_single() 传参中多余的 &：ndiv 已是 u64 *，传 &ndiv 使回调写指针自身栈槽（u64**），调用方永远读到未初始化
    ndiv；1 行修复
  review_outcome: 'Viresh Kumar 当日回复 Applied. Thanks. 直接合入，无改动要求；Sumit Gupta 9/1 补
    Reviewed-by；无人要求 Cc: stable'
upstream_commit: null
fixes_commit: 0839ed1fd7ac
merged_branch: cpufreq（Viresh 树；Applied 回复未说明具体分支）
merge_assessment:
  likelihood: merged
  blocking_issues:
  - 无技术阻力，维护者已 apply；仅剩随 pull 进入主线的时序
  - '是否回合 stable 未定：补丁带 Fixes: 但线程内无人显式 Cc: stable，当日也无 AUTOSEL 通知'
  next_action: 等待 cpufreq 修复分支 pull；确认 stable 回合意向；下游核对是否含 0839ed1fd7ac 之后的 tegra194
    代码
contribution_opportunities:
- kind: review
  description: 在内部分支批量审查 smp_call_function_single() 一类 void *info 调用中'形参已是指针却又传 &ptr'的同型错误，调度与
    arch 侧使用点很多
- kind: new_patch
  description: 把该排查写成 coccinelle semantic patch（匹配 smp_call_function_single(cpu, fn,
    &p, ...) 且 p 为指针），作为检查项提给社区或内部 CI
- kind: discussion
  description: '在原线程追问是否期望 Cc: stable，以及 Fixes: 目标 0839ed1fd7ac 覆盖哪些分支，据此决定下游是否跟进'
generated_at: '2026-09-07T21:36:15'
source_email_count: 2
related_articles: []
tags:
- cpufreq
- arm64
title: 'cpufreq: tegra194: fix double-pointer error in get_cpu_ndiv'
layout: article
---

## TL;DR

Xueqin Luo（Kylinos）8/31 的一行补丁修掉 `tegra194_get_cpu_ndiv()` 里 `smp_call_function_single()` 传参的**双重指针错误**：形参 `ndiv` 本身已经是 `u64 *`，却又传了 `&ndiv`，于是被调回调写的是"指针变量自己的栈槽"，调用方的 `u64` 永远读到未初始化值。维护者 Viresh Kumar 在补丁发出 26 分钟后直接回复 "Applied. Thanks." 合入，NVIDIA 的 Sumit Gupta 9/1 补上 `Reviewed-by`。文章价值不在难度，而在它揭示的一类可批量排查的模式：`void *info` 让编译器完全不检查类型。

## 背景与问题

tegra194 的 cpufreq 驱动要在**目标 CPU 自己**的上下文里读它的 NDIV（feedback divider）值，所以用 `smp_call_function_single(cpu, tegra194_get_cpu_ndiv_sysreg, info, true)` 发一个同步 IPI，回调签名是 `static void tegra194_get_cpu_ndiv_sysreg(void *ndiv)` —— 约定 `info` 是一个 `u64` 目的地址，回调把读到的值写进去。

封装函数却长这样：

```c
static int tegra194_get_cpu_ndiv(u32 cpu, u32 cpuid, u32 clusterid, u64 *ndiv)
{
-	return smp_call_function_single(cpu, tegra194_get_cpu_ndiv_sysreg, &ndiv, true);
+	return smp_call_function_single(cpu, tegra194_get_cpu_ndiv_sysreg, ndiv, true);
}
```

- **错误性质**：`&ndiv` 的类型是 `u64 **`。C 允许任意对象指针隐式转成 `void *`，所以 `smp_call_function_single()` 的原型不会给出任何警告；结果回调按 `u64 *` 去写这块地址，写的实际是**栈上那个指针变量自身**（在小端 64 位机上等于用除数值覆写了指针的低 8 字节），而调用方传进来的那个 `u64` 变量从未被赋值。
- **症状**：调用方 `tegra194_get_cpu_ndiv()` 返回 0（IPI 本身成功），看起来一切正常，但 `*ndiv` 的内容是栈上的陈旧/未初始化数据。是否表现为可观察的频率计算异常，取决于栈上恰好残留什么——**补丁和回帖都没有讨论这一点**，也没人报告过实际故障。
- **作者给出的引入点**：`Fixes: 0839ed1fd7ac ("cpufreq: tegra194: add soc data to support multiple soc")`，即 tegra194 为支持多 SoC 而引入 soc data 的那次改造是这个带 `u64 *ndiv` 形参写法的来源（补丁只给标签、未展开说明该改造前后的差异）。
- **影响范围**：仅 `drivers/cpufreq/tegra194-cpufreq.c`（1 行，`1 file changed, 1 insertion(+), 1 deletion(-)`），不涉及 sched core、不涉及 cpufreq core。

## 技术方案

去掉多余的 `&`。没有备选方案讨论——这类修复没有取舍空间。

真正值得记住的是机制层面的教训：`smp_call_function_single()` 用 `void *info` 传参，把类型检查完全交给了人，回调一侧的解引用约定与调用一侧的传参约定没有任何编译期约束。同类错误（多写一个 `&`、或回调按另一种宽度解引用）在这个 API 的所有使用者里都可能存在，编译器与 sparse 都不一定会报。当日 cpufreq 侧另一条线程（policy rwsem 初始化顺序）也是同一个大主题——**在无人工审查约束下读到未初始化数据**。

## 版本演进与当前进展

- 8/31 15:30 v1（`<20260831073009.3772408-1-luoxueqin@kylinos.cn>`），单补丁，无版本前缀，带 `Fixes:` 与作者 `Signed-off-by`。
- 8/31 15:56 Viresh Kumar 回复 "Applied. Thanks."（`<apUzriIXGmxf-PLc@vireshk-B250M-D3H>`）——已 apply，无需 v2。
- 9/1 18:03 Sumit Gupta（NVIDIA，tegra194 侧）回复 `Reviewed-by: Sumit Gupta <sumitg@nvidia.com>`（`<35c658a3-63ba-4664-ba8a-598ce6121430@nvidia.com>`）。注意这条 review 是在补丁已被 apply **之后**才到达的，属于事后确认而非合入前置条件。
- 当日缓存里没有 tip-bot / -stable 的合入通知，因此**最终 commit hash 未获取到**。

## Maintainer 意见与讨论焦点

- **Viresh Kumar（cpufreq 维护者）**：零意见，直接 apply。既没有要求补充影响分析、也没有要求补 `Cc: stable@vger.kernel.org`，更没问是否有实际故障报告。对 1 行、带 `Fixes:`、语义无歧义的驱动修复，这是他的一贯处理方式。
- **Sumit Gupta（NVIDIA）**：仅给 `Reviewed-by`，无技术评论。
- **未解决的疑点**：① 这个未初始化读是否曾在真机上造成过可观察的 NDIV/频率异常，线程里没人回答；② 是否应当进 stable——补丁有 `Fixes:` 标签（通常足以被 stable 流程识别），但没人显式 `Cc: stable`，当日也没有 AUTOSEL 通知，所以回合意向实际上悬空。

## 合入评估

**已合入**（`status: merged_tip`）。Viresh 8/31 即回复 Applied，剩余只是随 cpufreq 修复分支进入主线的时序问题；`likelihood` 取 `likely` 仅表示"进入下一个 pull"这一形式步骤，不存在技术阻力。Viresh 的回复未说明目标分支名，因此 `merged_branch` 只能记为 cpufreq（Viresh 树）。合入后唯一需要跟进的是 stable 回合是否会实际发生。

## 效果评估

暂无效果数据。补丁是纯静态阅读发现：没有 Oops、没有 dmesg 片段、没有"某平台上 NDIV 读到 X 导致频率档位错"的实测描述，也没有修复前后的对比。"调用方总是读到未初始化的 ndiv"这一结论本身是代码语义推理，作者与维护者都未验证它在真实硬件上是否曾经显形。

## 我可以参与的点

- **同类模式批量排查（最有价值的一条）**：在内部分支里对所有 `smp_call_function_single()` / `scall` 风格 `void *info` 调用做一次审查，专挑"形参已是指针却又传 `&ptr`"的组合。调度与 arch 侧同样大量使用这个 API（如 tick/nohz、tlb、cache 相关回调），这类 bug 一旦命中就是读到未初始化数据。
- **写成 coccinelle 规则发到社区**：把上面的排查做成一个 semantic patch（匹配 `smp_call_function_single(cpu, fn, &p, ...)` 且 `p` 为指针类型），作为脚本/检查项提给 checkpatch 或内核自建 CI 都有讨论空间——比逐个手工 grep 更有复用价值，也能自然带出 `Reviewed-by`。
- **补一句 stable 意向**：在该线程里问清"是否期望回合到 stable"（`Fixes:` 目标 `0839ed1fd7ac` 存在于哪些分支），对下游分支是否要跟进是决定性信息。
- **下游核对**：若内部分支（arm64 服务器方向）确实带了 `0839ed1fd7ac` 之后的 tegra194 代码，就需要同步这一行；反之若根本没引入该驱动，可以直接排除，省一次无谓回合。

## 参考链接

- lore thread（v1）: https://lore.kernel.org/all/20260831073009.3772408-1-luoxueqin@kylinos.cn/
- Viresh Kumar 的 Applied 回复: https://lore.kernel.org/all/apUzriIXGmxf-PLc@vireshk-B250M-D3H/
- Sumit Gupta 的 Reviewed-by（9/1）: https://lore.kernel.org/all/35c658a3-63ba-4664-ba8a-598ce6121430@nvidia.com/
- 被指为引入点的 commit: `0839ed1fd7ac` ("cpufreq: tegra194: add soc data to support multiple soc")
- tip-bot commit: 未获取到（当日缓存无合入通知）
- stable backport: 未获取到
