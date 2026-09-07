---
id: sched-20260828-002
date: '2026-08-28'
subject: '[BUG] general protection fault in cpuset_cpus_allowed'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <CA+0ovChh3VjsKN1g+ZGjwwY2fGTpP7uD+aCCByLj5Qbymw=bfQ@mail.gmail.com>
lore_url: https://lore.kernel.org/all/CA+0ovChh3VjsKN1g+ZGjwwY2fGTpP7uD+aCCByLj5Qbymw=bfQ@mail.gmail.com/
authors:
- Farhad Alemi
maintainers_involved:
- Ridong Chen
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 作者未随邮件提供 reproducer.c，Ridong Chen 两次回帖索要
  - 报告缺少内核版本、.config 与是否伴随 CPU hotplug
  - cpuset_fork(PID 1) 路径与热插拔竞态解释不吻合，根因未定
  - 当日无修复补丁、无 Fixes 标签
  next_action: 公开复现器并由 cpuset 维护者定位 effective_cpus 滞后窗口，随后出硬化补丁
contribution_opportunities:
- kind: testing
  description: 在 OLK-6.6 的 guarantee_online_cpus() 上复现同一无上界循环（逐字相同，用 cpu_online_mask）
- kind: discussion
  description: 回帖提供 cpuset_fork 路径为何命中同一处，或提供带 cpuset 分区 + CPU 热插拔的复现数据
- kind: new_patch
  description: 确认根因后提交 guarantee_active_cpus() 遍历上界/退回 top_cpuset.effective_cpus 的硬化补丁
generated_at: '2026-09-07T22:08:24'
source_email_count: 3
related_articles:
- sched-20260829-001
tags:
- cgroup
- affinity
- crash
title: '[BUG] general protection fault in cpuset_cpus_allowed'
layout: article
---

## TL;DR

ASU SEFCOM 实验室的 Farhad Alemi 报告 `cpuset_cpus_allowed()` 里一次 general protection fault：`guarantee_active_cpus()` 沿 cpuset 层级向上走的 `while` 循环没有终止保护，越过了顶层 cpuset，在 NULL 上读 `cs->effective_cpus`。两条触发路径分别是 `sched_setaffinity()` 和 `cpuset_fork()`→`cgroup_post_fork()`→`copy_process()`（后者崩溃任务是 PID 1 systemd）。Ridong Chen 当天两次回帖索要 reproducer，并直接贴出那段可疑循环。当日**没有任何修复补丁**，也没有内核版本/配置信息。对用户主线（cpuset）是必读级别：OLK-6.6 的 `guarantee_online_cpus()` 是同一个无上界循环，同样缺保护。

## 背景与问题

报告给出的崩溃现场：

```
Oops: general protection fault, probably for non-canonical address 0xdffffc000000001d: 0000 [#1] SMP KASAN NOPTI
KASAN: null-ptr-deref in range [0x00000000000000e8-0x00000000000000ef]
RIP: 0010:bitmap_intersects include/linux/bitmap.h:440 [inline]
RIP: 0010:cpumask_intersects include/linux/cpumask.h:822 [inline]
RIP: 0010:guarantee_active_cpus kernel/cgroup/cpuset.c:481 [inline]
RIP: 0010:__cpuset_cpus_allowed_locked kernel/cgroup/cpuset.c:4022 [inline]
RIP: 0010:cpuset_cpus_allowed+0x14a/0x2f0 kernel/cgroup/cpuset.c:4071
```

作者补充：第二份抓取以**完全相同的地址、相同 KASAN 区间、相同 RIP** 命中在 `cpuset_fork <- cgroup_post_fork <- copy_process <- kernel_clone <- clone3`，崩溃任务是 PID 1。崩溃报告放在 GitHub（见参考链接），`reproducer.c` 邮件里说"available upon request"，**没有随邮件提供**；报告也**没有给出内核版本、`.config`、是否做过 CPU 热插拔**。

## 技术方案

本邮件无补丁，只有崩溃分析。落到当前主线代码上，`kernel/cgroup/cpuset.c` 的 `guarantee_active_cpus()` 是：

```
if (WARN_ON(!cpumask_and(pmask, possible_mask, cpu_active_mask)))
        cpumask_copy(pmask, cpu_active_mask);

rcu_read_lock();
cs = task_cs(tsk);

while (!cpumask_intersects(cs->effective_cpus, pmask))   /* 主线 cpuset.c:481 */
        cs = parent_cs(cs);                              /* 主线 cpuset.c:482 */
```

而 `parent_cs()`（`kernel/cgroup/cpuset-internal.h`）就是 `css_cs(cs->css.parent)`——**顶层 cpuset 的 `css.parent` 为 NULL**。因此该循环唯一的 NULL 来源就是"链条走到顶仍未与 `pmask` 相交"：一旦 `top_cpuset.effective_cpus` 与 `possible_mask & cpu_active_mask` 无交集，循环就会把 NULL 赋给 `cs` 并在下一轮解引用。KASAN 报的空指针区间是 8 字节（`0xe8..0xef`），与在 NULL 基址上读 `effective_cpus` 这一个字段一致。

这与函数自身的契约注释直接冲突——它的 kernel-doc 写着 "**One way or another, we guarantee to return some non-empty subset of cpu_active_mask**"，而 `cpuset_cpus_allowed()` 的注释也保证"Guaranteed to return some non-empty subset of cpu_active_mask"。能违反这个保证的窗口，只可能在 `effective_cpus` 相对 `cpu_active_mask` 滞后的时刻（热插拔/partition 重建路径更新 `top_cpuset.effective_cpus`，而本函数只在 `callback_lock` 下读）。以上是按代码结构收敛出的唯一 NULL 路径，**尚未经邮件里的复现验证**，不要当既定结论。

另外注意调用侧：`__cpuset_cpus_allowed_locked()` 对 `cs == &top_cpuset` 的任务是**跳过** `guarantee_active_cpus()` 的，只有非顶层 cpuset 里的任务才会走进这个循环。

## 版本演进与当前进展

- 8/28 13:43 报告发出。
- 8/28 17:21 Ridong Chen 回帖只要一件事："Could you please share the reproducer.c with us?"
- 8/28 17:54 Ridong Chen 再回帖，直接把 `guarantee_active_cpus()` 里那句 `while (!cpumask_intersects(cs->effective_cpus, pmask)) cs = parent_cs(cs);` 引出来，附言 "Having the reproducer would help me debug how this situation could occur."
- 本系列缓存内当日无第三人之外的响应；8/29 02:07 Waiman Long 也有回帖，但不在本日报道范围内。
- 无人发修复补丁，无 `Reported-by`/`Tested-by` 交换，无 `Fixes:` 标签。

## Maintainer 意见与讨论焦点

当日唯一的社区声音是 Ridong Chen（`ridong.chen@linux.dev`），他的态度是**先要复现器、不做无根据猜测**——两次回帖都在强调需要 `reproducer.c` 才能定位"这种情况怎么发生"，并且已经用引用代码的方式把嫌疑点锁定在无上界的向上遍历循环。他没有给出自己的根因判断，也没有认可任何修复方向。

未解决问题（三个都卡着后续判断）：复现器未公开；报告未给内核版本与配置（无法判断是否已受近期 `cpu_online_mask`→`cpu_active_mask` 改动影响）；`cpuset_fork`（PID 1）这条路径为什么也会命中同一处，说明可能不存在单一"热插拔竞态"解释——fork 路径与 CPU 上下线关系更弱，这反而是最值得追问的点。

## 合入评估

**likelihood: unlikely**（当日无补丁可评，进展只到"社区认可可疑代码位置"）。

- `blocking_issues`：作者未提供 reproducer.c；缺内核版本/`.config`/是否伴随 CPU hotplug；无人给出 `Fixes:` 指向。
- `next_action`：作者公开复现器 → 由 Ridong Chen 一类 cpuset 活跃贡献者定位窗口 → 出修复补丁。若最终定性为"越界走到根"，最可能的修复形式是给循环加上界（走不到 `&top_cpuset` 之上）并在无交集时退回 `top_cpuset.effective_cpus`/`cpu_active_mask`。

## 效果评估

无效果数据。本邮件只给出崩溃现场（同一 `RIP`、同一 KASAN 区间、两条不同调用链）这一定性证据，没有性能影响、没有触发概率、没有可复现负载描述。

## 我可以参与的点

- **自查 OLK-6.6 是否同病**（对用户最直接）：OLK-6.6 的 `kernel/cgroup/cpuset.c` 里 `guarantee_online_cpus()` 是**逐字相同**的无上界循环，且用的是 `cpu_online_mask`：

  ```
  if (WARN_ON(!cpumask_and(pmask, possible_mask, cpu_online_mask)))
          cpumask_copy(pmask, cpu_online_mask);
  ...
  while (!cpumask_intersects(cs->effective_cpus, pmask))
          cs = parent_cs(cs);
  ```

  已核对：OLK-6.6 的 `cpuset_cpus_allowed()`（`kernel/cgroup/cpuset.c:4907`）与主线同构——同样有 `if (cs != &top_cpuset) guarantee_online_cpus(tsk, pmask);` 的特判、同样在 `callback_lock` 下调用，唯一区别就是判据用 `cpu_online_mask` 而非 `cpu_active_mask`。也就是说这个无上界遍历在 6.6 上一字不差地存在，若内部有频繁 CPU 上下线 + cpuset 分区的场景，可以直接在 6.6 上做压力复现。
- **提供复现数据**：如果能在自家机器上构造出"沿链到根 `effective_cpus` 都不含任何 active CPU"的场景（例如 partition root 把 CPU 全部分走后热插拔，或 `cpuset.cpus` 被写空与 hot-remove 交叠），回帖给这个线程就是上游此刻最缺的信息，Ridong Chen 已经公开索要。
- **补 fork 路径的分析**：`cpuset_fork`→`copy_process` 这条链为什么也会踩到同一处，是线程里目前没人回答的问题；读一下 `cpuset_fork()` 里 `task_css_set` 的挂载时机即可给出有价值的判断。
- **硬化补丁**：`guard against walking past the top cpuset` 这类小补丁风险低、易被接受，但建议先在线程里确认根因再发，避免与 Ridong Chen 正在做的定位重复。

## 参考链接

- 报告（线程根）: https://lore.kernel.org/all/CA+0ovChh3VjsKN1g+ZGjwwY2fGTpP7uD+aCCByLj5Qbymw=bfQ@mail.gmail.com/
- Ridong Chen 索要复现器: https://lore.kernel.org/all/dc5ce72e-b835-4ae2-b4c9-e96dc6d48eba@linux.dev/
- Ridong Chen 指出可疑循环: https://lore.kernel.org/all/15c4ce09-ae6f-477e-a400-6b61fe81b477@linux.dev/
- 报告作者的崩溃样本仓库（邮件原文给出）: https://github.com/farhad-alemi/public_bug_reports/tree/main/166-general-protection-fault-in-cpuset-cpus-allowed/
- 相关代码: `kernel/cgroup/cpuset.c` `guarantee_active_cpus()` / `__cpuset_cpus_allowed_locked()` / `cpuset_fork()`，`kernel/cgroup/cpuset-internal.h` `parent_cs()`
- tip-bot commit: 未获取到
- stable backport: 未获取到
