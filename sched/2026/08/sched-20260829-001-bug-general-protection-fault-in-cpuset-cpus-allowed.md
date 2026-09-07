# [BUG] general protection fault in cpuset_cpus_allowed

## TL;DR

ASU SEFCOM 实验室报告 `cpuset_cpus_allowed()` 路径上的 GPF（KASAN 判为 null-ptr-deref，崩在 `guarantee_active_cpus()` 里的 `cpumask_intersects()`），第二次捕获甚至把 PID 1 (systemd) 打崩。8/29 cpuset 维护者 Waiman Long 首次给方向：**只在 `sched_setaffinity()` 与 CPU hotplug 竞争时才会发生**，并称"已发出一个 hopefully 修复该 bug 的补丁"，请报告者验证。该修复补丁本身不在本次邮件数据源里（未获取到），报告者对"是否确为 hotplug 竞争"也未回应。这条正好落在 cpuset/cgroup 主线上，值得盯。

## 背景与问题

- **症状**（8/28 原始报告，KASAN 内核）：
  `Oops: general protection fault, probably for non-canonical address 0xdffffc000000001d` / `KASAN: null-ptr-deref in range [0x00000000000000e8-0x00000000000000ef]`，RIP 落在 `bitmap_intersects()` → `cpumask_intersects()` → `guarantee_active_cpus()`（`kernel/cgroup/cpuset.c:481`）→ `__cpuset_cpus_allowed_locked()`（4022）→ `cpuset_cpus_allowed()`（4071），调用方是 `__sched_setaffinity()`/`sched_setaffinity()`/`__x64_sys_sched_setaffinity()`。
- **第二条复现路径**：同一地址、同一 KASAN 区间、同一 RIP，经 `cpuset_fork ← cgroup_post_fork ← copy_process ← kernel_clone ← clone3`，崩溃任务是 **PID 1 systemd**——即 fork 与改亲和性两条入口都能进同一个空指针。
- **入口性质**：`cpuset_cpus_allowed()` 是调度器在设置/收敛亲和性时向 cpuset 索取"允许集合"的接口，`guarantee_active_cpus()` 负责保证结果里至少还有活着的 CPU，其循环要一路 `parent_cs()` 上溯直到 `cs->effective_cpus` 与掩码相交。Ridong Chen 在讨论中把这段循环原文贴出来，含义是：**要么某个 `cs` 为空、要么 `effective_cpus` 未初始化/已被清掉**，而这需要复现器才能确定。
- **首报内核版本 / 具体 commit**：邮件里未给出（未获取到），报告者只给了 crash 报告仓库；`reproduced.c` 标注"available upon request"，未公开。

## 技术方案

本日没有任何可分析的补丁代码，只有一个**根因假设**：

- Waiman Long 的判断是"这个空指针只可能来自 `sched_setaffinity()` 与 CPU hotplug 的竞争"（原话以反问形式给出："This null pointer dereference should only happen if you are racing sched_setaffinity() with cpu hotplug operation. Right?"）。
- 该假设与代码结构吻合：`guarantee_active_cpus()` 依赖 cpuset 层级在 hotplug 下仍维持"每个 cs 的 `effective_cpus` 与本节点活 CPU 有交集"这一不变式；hotplug 迁移/下线 cpuset 与用户态设置亲和性并发时，上溯过程中读到的 `cpuset` 结构或其掩码可能处于中间态。
- Waiman 说已另行发出修复补丁请报告者试测，但**该补丁未进入本次分析的邮件缓存**，因此其做法（是补锁、补判空，还是调整 hotplug 与 cpuset 更新顺序）本日无法判定。

## 版本演进与当前进展

- 8/28 13:43 Farhad Alemi 发出 `[BUG]` 报告（含两份 crash 捕获）。
- 8/28 17:21、17:54 Ridong Chen 两次索取 reproducer，并贴出 `guarantee_active_cpus()` 片段说明"想知道这种情况怎么可能发生"。
- 8/29 02:07 Waiman Long 给出 hotplug 竞争假设 + "已发补丁，请试测"。
- 8/30、8/31 该线程在本地邮件缓存中**没有新邮件**——报告者是否确认竞争场景、是否贴出测试结果、补丁是否被 review，均无后续。

## Maintainer 意见与讨论焦点

- **Waiman Long（Red Hat，cpuset 侧活跃维护者）**：唯一给出技术判断的人，方向是 hotplug 并发；态度是"先让报告者验证补丁"，没有对根因下定论。
- **Ridong Chen（linux.dev）**：不接受猜测，坚持先拿到复现器再定位；这是本线程目前最大的缺口。
- **无 NAK、无 Reviewed-by、无 Fixes 认领**：报告本身也没有 `Fixes:` 标签指向具体 commit（未获取到）。
- **未解决的关键分歧/空白**：①"是否真是 hotplug 竞争"仍是问句，没有作者回答；②fork/`clone3` 那条路径同样崩溃，而 fork 路径与 `sched_setaffinity()` 并非同一个竞争窗口，单靠 hotplug 假设能否同时解释两条栈，本日无人讨论。

## 合入评估

**unclear**。卡点不在方案争议，而在**信息缺失**：修复补丁没进数据源、复现器没公开、竞争窗口没被证实或证伪。可判断的只有"维护者已接手并倾向 hotplug 并发这一类"，因此短期内出现带 `Fixes:` 的修复概率不低，但目前无法评价其正确性，也看不出是否需要 cpuset 锁序层面的改动。需要等补丁正文 + 报告者的 Tested-by。

## 效果评估

暂无效果数据。报告方只提供了 crash 现场（同址同栈两次捕获，其中一次 PID 1），未提供触发频率、负载形态或修复后的验证结果。

## 我可以参与的点

- **直接补位复现器**：这是全线程最缺的东西，且报告者明确写了 "Happy to test a patch if that helps"。可用 `sched_setaffinity()`/`clone3` 与 `echo 0 > /sys/devices/system/cpu/cpuN/online` 并发压测，配合多层 cpuset（含 `effective_cpus` 会被 hotplug 收缩的子集）尝试稳定触发，并把结果回帖。
- **在自己的分支上做静态审计**：`OLK-6.6` 若 `guarantee_active_cpus()`/`__cpuset_cpus_allowed_locked()` 与上游同形，可直接检查 hotplug 路径（`cpuset_hotplug_workfn()`）与 `cpuset_rwsem` 的取锁窗口能否让 `cs->effective_cpus` 在读侧呈现未初始化/已释放状态，把结论回帖——这类"无复现器的静态分析"社区是欢迎的。
- **追补丁**：补丁一旦贴出（本日报未捕获到），值得第一时间 review；如果它只是补判空而没有解释 fork 路径，可以提出这个未被回答的问题。

## 参考链接

- lore（原始报告，Farhad Alemi）: https://lore.kernel.org/all/CA+0ovChh3VjsKN1g+ZGjwwY2fGTpP7uD+aCCByLj5Qbymw=bfQ@mail.gmail.com/
- lore（Ridong Chen 索取复现器）: https://lore.kernel.org/all/dc5ce72e-b835-4ae2-b4c9-e96dc6d48eba@linux.dev/
- lore（Ridong Chen 贴出 guarantee_active_cpus）: https://lore.kernel.org/all/15c4ce09-ae6f-477e-a400-6b61fe81b477@linux.dev/
- lore（Waiman Long 的 hotplug 假设 + 已发补丁）: https://lore.kernel.org/all/e27ad187-7572-4999-b171-f510990d4006@redhat.com/
- 报告者的 crash 报告仓库（邮件原文给出的外部链接，非 lore）: https://github.com/farhad-alemi/public_bug_reports/tree/main/166-general-protection-fault-in-cpuset-cpus-allowed/
- Waiman Long 所称的修复补丁: 未获取到（不在本次邮件数据源中）
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260829-001
date: '2026-08-29'
subject: "[BUG] general protection fault in cpuset_cpus_allowed"
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<CA+0ovChh3VjsKN1g+ZGjwwY2fGTpP7uD+aCCByLj5Qbymw=bfQ@mail.gmail.com>"
lore_url: "https://lore.kernel.org/all/e27ad187-7572-4999-b171-f510990d4006@redhat.com/"
authors: [Farhad Alemi, Ridong Chen, Waiman Long]
maintainers_involved: [Waiman Long, Ridong Chen]
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "Waiman Long 所称的修复补丁未进入邮件数据源，无法评价方案"
    - "reproducer 未公开，hotplug 竞争假设仍停留在问句，报告者未确认"
    - "fork/clone3 第二条崩溃路径与 sched_setaffinity 假设的关系无人解释"
  next_action: "报告者确认竞争场景并测试补丁；社区需要公开复现器或给出静态审计结论"
contribution_opportunities:
  - kind: testing
    description: "构造 sched_setaffinity()/clone3 与 CPU hotplug 并发的复现器，在多层 cpuset 下压测并回帖"
  - kind: review
    description: "在 OLK-6.6 上审计 guarantee_active_cpus()/cpuset_hotplug_workfn() 的取锁窗口，判断同一空指针是否本地存在"
  - kind: discussion
    description: "回答线程里没人解释的问题：fork 路径崩溃是否也能由 hotplug 竞争解释"
generated_at: "2026-09-07T22:06:23"
source_email_count: 1
related_articles: []
tags: [cgroup, affinity, crash]
---
