# cpufreq: initialize policy rwsem before sysfs publication

## TL;DR

Runyu Xiao（东南大学）8/30 的单补丁把 cpufreq policy 的 rwsem 初始化提前到 sysfs kobject 发布之前，避免用户态在 policy 半初始化时进入属性回调。8/31 cpufreq 维护者 Viresh Kumar 直接给 `Acked-by`；随后 Zhongqiu Han（Qualcomm）指出一处**必须改的元数据错误**（`Fixes:` 应指向 `2fc3384dc75b`）并顺手报出**同一窗口的第二个漏洞**：`policy->cpus` 用不带 `__GFP_ZERO` 的 `alloc_cpumask_var()` 分配，kobject 一发布 `policy_is_inactive()` 就可能读到垃圾 mask 从而放行 `show()/store()`——他表示会另发修复。这是当天 cpufreq 侧最有信息量的一条。

## 背景与问题

cpufreq 在注册 policy 时会创建一个 kobject 并挂出 sysfs 属性；如果 rwsem 的初始化排在 kobject 发布**之后**，就存在一个窗口：用户态（`udev`、性能守护进程、容器运行时的常规扫描）可以在 policy 尚未完成初始化时打开并读写这些属性，属性回调会去取一把还没初始化的 rwsem。

- **触发条件**：模块/驱动延迟注册 cpufreq policy 时最容易出现（启动期由内核顺序掩盖）；任何在 policy 注册路径上监听 `change` uevent 的用户态都是潜在触发者。
- **症状**：依赖 `CONFIG_DEBUG_MUTEXES`/lockdep 时会先报警，未开调试选项时属于未定义行为。
- **补丁本体不在当日缓存中**（8/30 发出，缓存缺 8/27–8/30），上述判断依据来自 subject、两位回帖人对代码位置的描述。

## 技术方案

把 policy rwsem 的 init 移到 sysfs 发布之前，使"可被用户态看到"一定晚于"锁已就绪"。这是顺序修复，不引入新状态、不改数据结构。

讨论中浮现的第二处同源问题（Zhongqiu Han）：同一发布窗口里 `policy->cpus` 仍是未清零的垃圾——`alloc_cpumask_var()` 默认不带 `__GFP_ZERO`，而 `policy_is_inactive()` 会读这个 mask，于是半初始化的 policy 仍可能被判定为"不活跃"并让 `show()/store()` 进到回调里。他选择**另发一个补丁**而不是把本系列扩大，这是本线程里唯一的方案分歧（也是常规做法：一个可 `Fixes:` 的问题一个补丁）。

## 版本演进与当前进展

- 8/30：v1（`<20260830155301.2713780-1-runyu.xiao@seu.edu.cn>`）。
- 8/31 13:29：Viresh Kumar `Acked-by`（`<apURJD6v92pMNKbJ@vireshk-B250M-D3H>`）。
- 8/31 20:13：Zhongqiu Han 提出 `Fixes:` 标签指向错误 + 报告 `policy->cpus` 的相邻问题（`<83f87db8-fa13-41d0-ae52-544d22e228e6@oss.qualcomm.com>`）。
- 当日仍是 v1；`Acked-by` 已到手，作者尚未发出带更正的版本。

## Maintainer 意见与讨论焦点

- **Viresh Kumar（cpufreq 维护者）**：无异议，直接 `Acked-by: Viresh Kumar`。方案本身没有任何反对意见。
- **Zhongqiu Han（Qualcomm）**：两条实质意见。① "The tag should be `2fc3384dc75b` ("cpufreq: Initialize policy->kobj while allocating policy")."——即当前 `Fixes:` 指向的 commit 不对，正确的引入点是那次"在分配 policy 时初始化 kobj"的改动（也正是它把 kobject 发布时机提前、从而暴露了窗口）。② 报告 `policy->cpus` 未清零的相邻缺陷并承诺另发修复。
- 未解决：本补丁的 `Fixes:` 需要在合入前更正（这直接影响 stable 是否会自动捡它、以及捡错 commit 的风险）；`policy->cpus` 那个问题还没有补丁。

## 合入评估

**likely**。维护者已 `Acked-by`，改动是纯粹的初始化顺序修正、不涉及行为变更，唯一条件是换掉 `Fixes:` 标签。这类修复通常直接进 cpufreq fixes 并请求 stable 回合——`Fixes:` 标签正确与否在这里是实质性的，因为回合目标分支完全由它决定。`next_action`：作者（或代为 apply 的维护者）把 `Fixes:` 改成 `2fc3384dc75b`；`policy->cpus` 缺 `__GFP_ZERO` 的修复单独跟进。

## 效果评估

暂无效果数据。线程内没有 Oops/lockdep 报告、没有复现日志，也没有任何量化描述——两位回帖人都只做了代码语义论证。"用户可以读到半初始化 policy"这一点目前是推理而非实测。

## 我可以参与的点

- **可直接接手的后续 patch**：Zhongqiu Han 说要另发的 `policy->cpus` 清零问题（改用 `alloc_cpumask_var_gfp(..., __GFP_ZERO)` 或在发布前显式 `cpumask_clear()`），目前无人发帖；如果先做出来并在该线程里说明，是一笔干净的贡献。
- **复现与验证**：给这个窗口做一个可复现路径（延迟注册的 cpufreq 驱动 + 在 policy 注册瞬间轮询 `/sys/devices/system/cpu/cpu*/cpufreq/` 的用户态），带 lockdep 输出回帖，能把"推理成立"变成"实测成立"。
- **回合核对**：内部分支若把 cpufreq policy 注册改过顺序（不少下游会做），需要按 `2fc3384dc75b` 是否存在来判断这个窗口在自己分支上是否成立。

## 参考链接

- lore thread（v1）: https://lore.kernel.org/all/20260830155301.2713780-1-runyu.xiao@seu.edu.cn/
- Viresh Kumar 的 Acked-by: https://lore.kernel.org/all/apURJD6v92pMNKbJ@vireshk-B250M-D3H/
- Zhongqiu Han 的 Fixes 更正与相邻问题: https://lore.kernel.org/all/83f87db8-fa13-41d0-ae52-544d22e228e6@oss.qualcomm.com/
- 应作为 Fixes 目标的 commit: `2fc3384dc75b` ("cpufreq: Initialize policy->kobj while allocating policy")
- tip-bot commit: 未获取到（尚未见合入记录）
- stable backport: 未获取到

---
id: sched-20260831-012
date: '2026-08-31'
subject: "cpufreq: initialize policy rwsem before sysfs publication"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260830155301.2713780-1-runyu.xiao@seu.edu.cn>"
lore_url: "https://lore.kernel.org/all/83f87db8-fa13-41d0-ae52-544d22e228e6@oss.qualcomm.com/"
authors: [Runyu Xiao, Viresh Kumar, Zhongqiu Han]
maintainers_involved: [Viresh Kumar]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260830155301.2713780-1-runyu.xiao@seu.edu.cn>"
    date: 2026-08-30
    summary: "把 policy rwsem 初始化提前到 sysfs kobject 发布之前，避免用户态在半初始化 policy 上进入属性回调"
    review_outcome: "Viresh Kumar 给 Acked-by；Zhongqiu Han 指出 Fixes 标签应改为 2fc3384dc75b，并报出同窗口的 policy->cpus 未清零问题（将另发）"
upstream_commit: null
fixes_commit: "2fc3384dc75b"
merged_branch: null
merge_assessment:
  likelihood: likely
  blocking_issues:
    - "Fixes: 标签当前指向错误 commit，需改为 2fc3384dc75b 后合入（直接影响 stable 回合目标）"
    - "无复现证据，仅有代码语义论证"
  next_action: "作者更正 Fixes 标签；policy->cpus 缺 __GFP_ZERO 的问题由另一补丁跟进"
contribution_opportunities:
  - kind: new_patch
    description: "先人一步修 policy->cpus 未清零（Zhongqiu Han 声称会另发但线程内尚无补丁），使 sysfs 发布窗口彻底关闭"
  - kind: testing
    description: "用延迟注册的 cpufreq 驱动 + policy 注册瞬间轮询 sysfs 的方式给出 lockdep/Oops 复现"
  - kind: review
    description: "核对内部分支是否含 2fc3384dc75b，据此判断该窗口是否存在并决定是否回合"
generated_at: "2026-09-07T21:16:22"
source_email_count: 2
related_articles: []
tags: [cpufreq, crash]
---
