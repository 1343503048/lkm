---
id: sched-20260905-007
date: '2026-09-05'
subject: Cache-aware scheduling does not work well with amd big/little cores
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: <2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info>
lore_url: https://lore.kernel.org/all/2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info/
upstream_commit: eaece4849991d62fcd6f46637c55dcce00e25d70
fixes_commit: d04013a4b21b
merged_branch: tip/sched/urgent
current_version: null
generated_at: '2026-09-07'
authors:
- Klaus Kusche
maintainers_involved:
- Tim Chen
- Chen Yu
- Mario Limonciello
patch_series: []
merge_assessment:
  likelihood: low
  blocking_issues:
  - 本日为纯反馈邮件，无补丁可合
  - 实测仅一台 Ryzen HX 370、两个 build 负载、time 级别方法学，作者自评精度不足
  - Intel 侧尚未表态是否据此调整 aggr_tolerance 或 CAS 与非对称调度的优先级
  next_action: 等待 Intel/AMD 是否给出调参或文档补丁；补第二平台数据
contribution_opportunities:
- 在 AMD 混合核上用规范方法复现 CAS 关/开/开+补丁三组并扫 aggr_tolerance
- 定位 CAS 覆盖 asymmetric scheduling 策略的具体代码路径并回帖
- 自查内部内核 CONFIG_DEBUG_FS=n 时 ITMT/首选核是否被静默关闭
source_email_count: 1
related_articles:
- sched-20260904-006
tags:
- sched/cache
- topology
title: Cache-aware scheduling does not work well with amd big/little cores
layout: article
---

## TL;DR

这不是一条补丁，而是 Intel 与 AMD 双方 cache-aware 调度（CAS）从业者共同参与的实测反馈线。Klaus Kusche 在 09-05 给出了他在这个线程里的**第一份量化数据**，结论与 08-31 那条「两个补丁组合看起来达到预期效果」的直觉判断并不一致：在 AMD Ryzen HX 370 上，两个 build 负载里 **完全关掉 CAS 反而可复现地比开着好 2–2.6% wallclock**，而 Tim Chen 的 misfit 补丁带来的是 ≤1% 以内的无差别。他的实测直接回应了 Tim Chen 09-01「只用 misfit 补丁、默认 `aggr_tolerance`，报个数字给我，对后续 tuning 有帮助」的请求。

## 背景与问题

线程起点是 Klaus Kusche 反馈「cache-aware 调度在 AMD big/little 核上表现不好」。08-31 Mario Limonciello（AMD）把参与过 CAS 的人都拉了进来，Chen Yu（Intel）随后给出根因判断：**当前代码里 cache-aware 调度会覆盖非对称调度（asymmetric scheduling）的策略**，Ricardo 早前就发现过并有一个针对 **misfit 任务**、在 CAS 中尊重 CPU capacity 的补丁（即 Tim Chen 的 `sched/fair: avoid creating misfits during cache-aware balancing`），请他验证是否改善。

另有一个环境前提贯穿全线程：Chen Yu 说「CAS 可以通过 debugfs 调，甚至关掉」，而 Klaus 的内核全部**不带 debugfs**，因此他连 big/little 调度都拿不到——除非打上 Mario 的 `x86/itmt: Don't make ITMT enablement depend on debugfs`（该补丁把 `sched_set_itmt_support()` 里把 debugfs 创建失败当致命错误的处理去掉，此前 `CONFIG_DEBUG_FS=n` 时 debugfs stub 返回 `-ENODEV` 会让 ITMT 被静默关闭，`Reported-by` 正是 Klaus Kusche；已在 09-02 进 `tip/sched/urgent`，committer 为 Peter Zijlstra，带 Tim Chen 与 K Prateek Nayak 的 `Reviewed-by`）。这也解释了他 08-31 时观察到的「7.2 出来时的巨大差异」——他现在怀疑那其实是旧版 Mario 补丁没正确 apply 或没起作用。

## 技术方案

- 本日邮件无代码改动，属社区反馈与调优讨论。
- 涉及的两处上游改动：Mario 的 ITMT/debugfs 解耦（已入 tip/sched/urgent，`Fixes: d04013a4b21b`）与 Tim Chen 的 CAS 避免制造 misfit（站内 sched-20260904-006 记为已进 tip/sched/urgent，但本批缓存正文里未获取到对应的 tip-bot 通知，无法独立确认）。
- Peter Zijlstra 08-31 对 Tim Chen 那份 misfit 补丁提过流程性意见（作者自己漏了 `Signed-off-by`，以及 subject 在子系统前缀后应大写），说明该补丁在讨论期间本身还在移动。

## 版本演进与当前进展

- 08-31：Chen Yu 指根因并给出 misfit 补丁链接；Klaus 当天回「两个补丁组合看起来有预期效果」，但依据只是各核负载柱状图，明说「我没有精确数字或 benchmark」，并且在休假三周。
- 09-01：Tim Chen 请求他只用 misfit 补丁、默认 `aggr_tolerance` 给数字；Klaus 说需要另外构建带 debugfs 的内核，延后。
- 09-05（本日）：Klaus 交出对照测试结果，方法是用 `time` 量 wallclock 与 CPU 消耗（自陈「不是完美的 benchmark 环境」），负载为内核构建（`-j 24` + full LTO、自带 .config）与一个高并行应用构建；big/little 调度始终开启、Mario 补丁始终打上，三组对照是 CAS 全关 / CAS 开无补丁 / CAS 开加补丁。
- 线程至此没有新补丁产出；下一步逻辑上是 Intel 侧决定是否据此调 `aggr_tolerance` 类参数或收口 CAS 与非对称调度的优先级关系。

## Maintainer 意见与讨论焦点

- **Tim Chen（Intel，CAS 主要维护者之一）**：09-01 主动索要可用于调参的数据——「If you just apply <misfit 补丁>, with default aggr_tolerance, what numbers do you see? That will be helpful for further tuning.」他接受的是「用户实测驱动调参」这种推进方式，而不是让用户接受既定默认值。
- **Chen Yu（Intel）**：08-31 的定位是这个线程里最有技术含量的一句——问题不在 CAS 的启发式本身，而在**它与非对称调度策略的优先级关系**（CAS 覆盖了 asymmetric scheduling），并把已存在的 misfit 方向补丁接上，同时点出 Ricardo 早就碰过同一问题。
- **Klaus Kusche（用户侧，09-05）**：给出对 Tim 请求的正面回答，也是最有分量的负面结论——b) 与 c) 之间「没有显著差异（≤1% wallclock），有时 b) 好、有时 c) 好，差异低于我测试的精度」；但 a)（CAS 全关）「可复现地优于 b) 和 c)，wallclock 2–2.6%」，内核态 CPU 秒也略好；用户态 CPU 秒波动太大不可用（同一负载第二遍跑都更耗 user CPU 却 wallclock 略短，他表示不理解原因）。他因此把这轮结论收得很克制：「至少在这两个 build benchmark 上，Ryzen HX 370 完全不启用 cache aware scheduling 略好，但 CAS 的损失小于 3%」。
- 关键张力：Intel 侧（Chen Yu、Tim Chen）在推 CAS 的参数化与正确性修复，AMD 用户侧的量化结果却是「这套机制在 AMD 混合核上净收益为负、修复补丁也没带来可测收益」。这属于典型的「跨厂商平台默认值需要平台相关证据」的议题，而不是某个 bug 的收尾。

## 合入评估

**likelihood: unlikely**（就本日这封邮件而言没有可合的东西：它不是补丁，也不带 `Fixes`/`Reported-by`）。

依据与后续路径：线程的可合产出早于本日且已在别处——ITMT 与 debugfs 解耦已进 `tip/sched/urgent`（`eaece4849991d62fcd6f46637c55dcce00e25d70`，带两个 `Reviewed-by` 与一个 `Tested-by`）；CAS 避免制造 misfit 的补丁在 08-31 还被 Peter Zijlstra 挑过 SoB/标题格式，说明当时未定。本日的实测数据真正的落点是**默认值/文档**：若要转化为改动，最可能是调 `aggr_tolerance` 一类参数的默认取值、或在 `Documentation/scheduler/` 与 Kconfig 帮助里明确「AMD big/LITTLE 平台上 CAS 收益未证实、可选关闭」。卡点：只有一台笔记本（Ryzen HX 370）、两个 build 负载、`time` 级别的方法学，作者自己也标注了精度不足，Intel 侧未表态是否据此调整。

## 效果评估

本日线程里的唯一实测数据（Klaus Kusche，AMD Ryzen HX 370，big/little 始终开启，Mario 的 ITMT 补丁始终打上）：

| 配置 | 相对结果 |
|---|---|
| a) CAS 完全关闭 | wallclock 可复现地优于 b) 与 c) **2–2.6%**，内核 CPU 秒也极轻微更好 |
| b) CAS 开、无 misfit 补丁 | 与 c) 无显著差异（≤1% wallclock，互有胜负，低于测试精度） |
| c) CAS 开 + misfit 补丁 | 同 b)；打开 CAS 的净代价 **< 3%** |

负载为内核构建（`-j24` + full LTO）与一个高并行应用构建。用户态 CPU 秒被作者判定不可用（第二遍运行的 user CPU 显著上升而 wallclock 略降，原因未知）。他另指出 08-31 那次「柱状图看起来对了、LTO 编译明显更快」的印象没有数字支撑，而当年 7.2 上的大幅退化很可能是旧版 Mario 补丁未正确生效所致。数据不覆盖非构建类负载，也不是控制变量的严格 benchmark。

## 我可以参与的点

- 这是当天几篇里**最容易贡献有效回帖**的一条：缺的正是「第二台机器、第二个负载」。在自家 AMD 混合核（或 Intel 异构）机器上用规范方法（固定调频/关 turbo/绑核/多轮取中位数，`perf stat` 而非 `time`）复现 a/b/c 三组，尤其把 `aggr_tolerance` 扫两个点，就是 Tim Chen 明确说「helpful for further tuning」的那类数据。
- 具体可复核代码点：CAS 与非对称调度（`asymmetric_cpu_capacity` / misfit 路径）的优先级关系在 `loadavg.c` / `fair.c` 的哪一处让前者覆盖后者——Chen Yu 的描述给了方向但没有指行；把这条链读清楚并回帖，比再报一个百分比更有价值。
- 对回合的直接影响：如果 OLK/内部内核启用了 CAS 且面向 AMD 混合核或异构大小核，本线程的结论支持**默认关闭 CAS、把开关暴露到非 debugfs 路径**（Mario 的 ITMT 补丁正说明 debugfs 缺失会静默改变调度行为，这个坑在精简 config 的产品内核里更常见）。可先自查内部内核是否也 `CONFIG_DEBUG_FS=n` 且依赖 ITMT/首选核。
- 方法学提醒（对用户自己也有用）：Klaus 这轮之所以只能得出「<3%」，就是因为他把变量绑在了 debugfs 缺失与补丁版本上。做同类对比时，把「CAS 开关」「misfit 补丁」「ITMT/debugfs 补丁」拆成正交三轴，结论才站得住。

## 参考链接

- 相关文章/系列：
  - [[sched-20260904-006]] cache-aware 均衡避免制造 misfit。
- 本日实测反馈（Klaus Kusche）：https://lore.kernel.org/all/14630984-9287-4454-b52f-3a1e526e1fdf@computerix.info/
- Tim Chen 索要调参数据：https://lore.kernel.org/all/406a5c407bbe60cafc24f715e089f5552a0791f9.camel@linux.intel.com/
- Chen Yu 的根因判断（CAS 覆盖非对称调度）：https://lore.kernel.org/all/b475039b-defe-46e7-ab85-46e3196da667@intel.com/
- 早期「看起来有效但无数字」的那封：https://lore.kernel.org/all/369d0bbb-db7a-4f86-bee2-332d5295c452@computerix.info/
- 相关代码/commit：
  - `eaece4849991d62fcd6f46637c55dcce00e25d70` "x86/itmt: Don't make ITMT enablement depend on debugfs"（tip/sched/urgent，`Fixes: d04013a4b21b`，`Reported-by: Klaus Kusche`）
  - `arch/x86/kernel/itmt.c` `sched_set_itmt_support()`
  - `kernel/sched/fair.c` cache-aware 均衡 / `aggr_tolerance` / misfit 路径
