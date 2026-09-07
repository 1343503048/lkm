---
id: sched-20260830-005
date: '2026-08-30'
subject: 'cpufreq: initialize policy rwsem before sysfs publication'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260830155301.2713780-1-runyu.xiao@seu.edu.cn>
lore_url: https://lore.kernel.org/all/20260830155301.2713780-1-runyu.xiao@seu.edu.cn/
authors:
- Runyu Xiao
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260830155301.2713780-1-runyu.xiao@seu.edu.cn>
  date: 2026-08-30
  summary: 把 init_rwsem(&policy->rwsem) 提前到 kobject_init_and_add() 之前，消除用户态在 policy
    半初始化时进入 sysfs 属性回调的窗口
  review_outcome: v1 当日无人回复；次日 Viresh Kumar Acked-by、Zhongqiu Han 认为 Fixes 应指向 2fc3384dc75b
    并报出同一窗口的第二个漏洞
upstream_commit: null
fixes_commit: ad7722dab729
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Fixes 标签指向可能被维护者要求改写（次日社区认为应指 2fc3384dc75b）
  - 同一发布窗口内其它字段的初始化顺序未审，可能还有同类问题
  next_action: 作者按 review 修正 Fixes 目标后由 cpufreq 维护者收取，并推进同型审计
contribution_opportunities:
- kind: review
  description: 逐个核对 cpufreq_policy_alloc() 中在 kobject 发布之后才初始化的成员，找出同型的第二、第三个窗口
- kind: testing
  description: 在 cpufreq 驱动延迟注册/热插拔重建 policy 的场景下用 lockdep 抓取半初始化访问证据
generated_at: '2026-09-07T22:06:23'
source_email_count: 1
related_articles:
- sched-20260831-012
tags:
- cpufreq
- crash
title: 'cpufreq: initialize policy rwsem before sysfs publication'
layout: article
---

## TL;DR

Runyu Xiao（东南大学）单补丁：`cpufreq_policy_alloc()` 里 `init_rwsem(&policy->rwsem)` 排在 `kobject_init_and_add()` **之后**，也就是 policy 的 sysfs 目录和默认属性已经对外可见、rwsem 还没初始化——用户态只要在这个窗口里打开并读写属性，就会去取一把未初始化的信号量。补丁只是把那行提前到 kobject 发布之前（2 行改动），带 `Fixes: ad7722dab729` 与 `Cc: stable`。当天无人回复；次日 cpufreq 维护者 Viresh Kumar 直接 `Acked-by`，并有人报出同一窗口的第二个问题（见 sched-20260831-012）。

## 背景与问题

- **窗口**：`cpufreq_policy_alloc()` 创建 policy → `kobject_init_and_add(&policy->kobj, &ktype_cpufreq, cpufreq_global_kobject, "policy%u", cpu)` 把 `/sys/devices/system/cpu/cpuN/cpufreq/` 一类属性挂出来 → 之后才 `init_rwsem(&policy->rwsem)`。从 kobject 发布到 rwsem 初始化之间，属性回调完全可被用户态进入。
- **谁能撞上**：任何监听 `change` uevent 并随即读取属性的用户态——`udev`、频率/性能守护进程、容器运行时的常规扫描。启动期通常被内核自身顺序掩盖，**延迟注册 cpufreq policy（驱动后注册/模块加载）时最容易出现**。
- **症状**：属性回调里 `down_read/down_write` 一把未初始化的 rwsem。开 `CONFIG_DEBUG_MUTEXES`/lockdep 时会先报警；不开调试选项时属于未定义行为。
- **本邮件未给出**：具体内核版本、lockdep 报警原文、复现步骤（未获取到）。

## 技术方案

纯顺序调整，`drivers/cpufreq/cpufreq.c` 中 +2/−2：

```c
 	if (!zalloc_cpumask_var(&policy->real_cpus, GFP_KERNEL))
 		goto err_free_rcpumask;
 
+	init_rwsem(&policy->rwsem);
+
 	init_completion(&policy->kobj_unregister);
 	ret = kobject_init_and_add(&policy->kobj, &ktype_cpufreq,
 				   cpufreq_global_kobject, "policy%u", cpu);
...
-	init_rwsem(&policy->rwsem);
-
 	freq_constraints_init(&policy->constraints);
```

设计取舍：选择"把初始化提前"而不是"给属性回调加 `if (!rwsem_initialized())` 之类的防御"，理由很直接——**发布顺序正确性是 sysfs 的常规契约**（先初始化完对象再 publish），提前一行即可根治，而加判空只是把同一个窗口以另一种方式暴露出来。

`Fixes: ad7722dab729`（"cpufreq: create per policy rwsem instead of per CPU cpu_policy_rwsem"）——即把 per-CPU 锁换成 per-policy 锁、从而引入这个窗口的那个提交。作者另加 `Cc: stable@vger.kernel.org`，并在 commit message 尾部标了 `Assisted-by: Codex:GPT-5`。

## 版本演进与当前进展

- 8/30 23:53（北京时间）v1 发出，当日**无人回复**。
- 本地主线树核对（`/home/zq/code/linux`，树时间 2026-08-31）：`init_rwsem(&policy->rwsem)` 仍在 `kobject_init_and_add()` 之后（`drivers/cpufreq/cpufreq.c:1275` vs `1262`），即该问题当时未修。
- 次日线程推进：Viresh Kumar `Acked-by`；Zhongqiu Han 指出 `Fixes:` 应指向 `2fc3384dc75b`，并顺手报出**同一窗口的第二个漏洞**（`policy->cpus` 用不带 `__GFP_ZERO` 的 `alloc_cpumask_var()` 分配，kobject 一发布 `policy_is_inactive()` 就可能读到垃圾 mask），表示会另发修复。详见 sched-20260831-012。

## Maintainer 意见与讨论焦点

- 本日内**没有任何表态**，所以当日不存在争议。
- 值得注意的一点（当时无人提，次日才被提出）：**`Fixes:` 标签指向是否正确**。补丁选了引入 per-policy rwsem 的 `ad7722dab729`，而次日社区认为应指 `2fc3384dc75b`——这类元数据错误在 stable 自动回合阶段会被拦下。
- 另一处未被讨论的问题：这次只把 **rwsem** 提前，`policy_alloc()` 里还有其它成员（cpumask、约束、notifier block 等）同样在 kobject 发布之后才初始化；"提前一行"是否够，取决于是否有人把整个 publish 顺序审一遍。这后来确实被 Zhongqiu Han 以 `policy->cpus` 垃圾 mask 的形式坐实为**同一类第二个 bug**。

## 合入评估

**likely**。改动 2 行、无接口变化、无语义争议、`Fixes:` + `Cc: stable` 齐备，属于 cpufreq 维护者最容易直接收走的一类顺序修复；唯一的实际障碍是 `Fixes:` 目标要不要改（元数据层面，不影响方案）。截至本日尚未进 tip/stable（未获取到）。

## 效果评估

暂无效果数据。本邮件未附带 lockdep 报警、复现程序或触发概率的量化，"存在窗口"是从代码顺序直接可读的事实，但"实际有多少用户态会撞上"没有数据支撑；对性能也没有任何影响，属于纯正确性修复。

## 我可以参与的点

- **同类审计（最省事也最可能被引用）**：`cpufreq_policy_alloc()` 里在 `kobject_init_and_add()` 之后才被填的字段还有哪些？把 `policy->cpus`、`real_cpus`/`loaded_cpus` 的分配零初始化、`policy->isset` 等逐个核对，能直接产出一批同型修复补丁——次日的 `policy->cpus` 已经证明这条路有效，还有没有第三处目前没人查。
- **给出真实触发案例**：线上/CI 里 `udev` 或频率守护进程在 cpufreq 驱动延迟注册（模块加载、CPU 热插拔后重建 policy）时读到半初始化 policy 的证据，如果有 lockdep 记录，回帖会直接被引用为该补丁的 `Reported-by` 材料。
- **回合判断**：本条与 cpufreq 交互但机制简单（初始化顺序），若 OLK-6.6 的 cpufreq policy 注册路径同形（`ad7722dab729` 之后），属于低风险可回合候选；注意 `Fixes:` 需改写指向 OLK-6.6 自己的 commit。

## 参考链接

- lore thread（v1，当日唯一邮件）: https://lore.kernel.org/all/20260830155301.2713780-1-runyu.xiao@seu.edu.cn/
- 本补丁 `Fixes:` 目标: `ad7722dab729` ("cpufreq: create per policy rwsem instead of per CPU cpu_policy_rwsem")
- tip-bot commit: 未获取到
- stable backport: 未获取到（仅 `Cc: stable@vger.kernel.org`）
