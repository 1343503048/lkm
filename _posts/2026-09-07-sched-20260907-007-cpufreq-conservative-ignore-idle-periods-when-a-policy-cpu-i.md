---
id: sched-20260907-007
date: '2026-09-07'
subject: 'cpufreq: conservative: Ignore idle periods when a policy CPU is busy'
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: <2026090215474182681fN7LLOSpqIc3s3OqJaW@zte.com.cn>
lore_url: https://lore.kernel.org/all/2026090215474182681fN7LLOSpqIc3s3OqJaW@zte.com.cn/
upstream_commit: null
fixes_commit: 00bfe05889e9
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Shengming Hu
maintainers_involved:
- Zhongqiu Han
patch_series:
- version: v1
  msgid: <2026090215474182681fN7LLOSpqIc3s3OqJaW@zte.com.cn>
  date: '2026-09-02'
  summary: 'drivers/cpufreq/cpufreq_governor.c +4/-1：dbs_update() 中新增 all_cpus_idle，只有
    policy 内每个 CPU 都满足 idle_time > 2*sampling_rate 时才保留 policy_dbs->idle_periods，否则置
    UINT_MAX，避免满载 CPU 的 policy 被空闲兄弟的 deferred idle periods 拉到底。Cc: stable，Fixes:
    00bfe05889e9，两枚同域（@zte.com.cn）Reviewed-by。'
  review_outcome: Zhongqiu Han 09-06 认可问题但否定判据，给出以 measured_load > up_threshold 置
    busy_cpu_seen 的反方案；作者 09-07 接受「不满足 long-idle 不代表忙」并同意分离实测/继承负载，但反对 up_threshold，改提
    max_sample_load < down_threshold 并预告 v2；Zhongqiu 09-07 晚反驳称两门在保持区无实质差别、down_threshold
    会造成功耗回退。无 v2、无外部 tag。
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 作者计划的 v2 方向（down_threshold 门）正是评审者当日明确反对的方向，双方尚未就 requested_freq 与继承 prev_load
    的关系对齐
  - 全线程没有任何 benchmark 或功耗数字，两条路线的收益/代价均为逻辑推演
  - 评审者自己的 up_threshold 反方案也尚未正式提交，上游没有可评的成体系改法
  - cpufreq 维护者（Rafael Wysocki、Viresh Kumar）未参与；dbs_update() 为 ondemand/conservative
    共用路径
  next_action: 等 v2 或 Zhongqiu 正式发出 up_threshold 版本；关键是谁能给出两种门的频率/功耗对照数据
contribution_opportunities:
- kind: testing
  description: 分别实现 up_threshold 门与 max_sample_load < down_threshold 门，在「一 CPU 长 idle
    + 一 CPU 保持区 75%」「+ 满载」「全 idle」三种组合下采频率曲线与整机功耗，把当前的纯逻辑争论变成数据
- kind: review
  description: 补齐 per-policy 新增状态（如 max_sample_load）的复位时机与 CPU hotplug / governor
    切换时的残留问题，本线程未讨论
- kind: discussion
  description: 在 sched_ext 侧确认 update-util 回调稀疏（作者观测到 DBS interval 达 59 ms）是否本身应修，这决定该
    bug 在上游的实际触发面
- kind: new_patch
  description: 内部树若已带 00bfe05889e9 等价改动且存在共享 policy + 长 idle CPU 形态，可先在内部验证 up_threshold
    方向（改动更小、功耗回退风险更低）
source_email_count: 2
related_articles: []
tags:
- cpufreq
- idle
title: 'cpufreq: conservative: Ignore idle periods when a policy CPU is busy'
layout: article
---

## TL;DR

Shengming Hu（ZTE）的单补丁修的是一个真实的行为缺陷：共享 policy 里一个长期空闲 CPU 记录的 deferred idle periods，会把一个满载 CPU 所在的 policy 频率一路拉到最低（他实测卡在约 530 MHz，而 CPU 2 一直 100%）。做法是把 `dbs_update()` 里的 `policy_dbs->idle_periods` 改成「只有 policy 内每个 CPU 都满足 long-idle 条件才保留，否则置 `UINT_MAX`」。Zhongqiu Han（Qualcomm）09-06 认可问题但认为判据选错——「不满足 long-idle」不等于「这个 CPU 忙」，并给出以 `measured_load > up_threshold` 为准的反方案。09-07 双方完成一轮实质交锋：作者承认第一点、也接受「实测负载要与可能继承 `prev_load` 的决策负载分开记录」，但反对用 `up_threshold` 当门限（举 CPU A 长期 idle + CPU B 稳定 75%、up=80/down=20 的例子），改为在 `struct policy_dbs_info` 里单独记 `max_sample_load` 并以 `max_sample_load < down_threshold` 放行 deferred 降频；Zhongqiu 当晚反驳：`cs_dbs_update()` 里 `idle_periods` 只影响局部 `requested_freq`，而保持区根本不会用它改频，两个门限只在很窄的条件下才有差别，用 `down_threshold` 会造成功耗回退。本日无 v2、无任何性能或功耗数字。

## 背景与问题

conservative governor 与 ondemand 共用 `dbs_update()`：它遍历 policy 内所有 CPU，取最大负载作为 `max_load`，同时统计「deferred idle periods」——某个 CPU 的 `idle_time > 2 * sampling_rate` 时按 `idle_time / sampling_rate` 折算成被跳过的采样周期数，policy 级取各 CPU 的最小值写入 `policy_dbs->idle_periods`。`00bfe05889e9`（"cpufreq: conservative: Decrease frequency faster for deferred updates"）据此让下次更新一次性补扣多个降频台阶。

问题出在这两件事在共享 policy 下会同时发生：一个 CPU 长期空闲（idle_time 远超两个采样周期）与另一个 CPU 满载。作者的复现是 CPU 2 与 CPU 3 同一 policy，CPU 2 上跑一个 CPU 型 SCHED_EXT 任务保持 100%、CPU 3 空闲；由于 SCHED_EXT 产生 update-util 回调比 CFS 稀疏，DBS 更新很稀疏，trace 记录形如：

```
 load=100 idle_periods=7 interval=59 ms
 load=100 idle_periods=4 interval=39 ms
 load=100 idle_periods=2 interval=19 ms
 load=100 idle_periods=7 interval=59 ms
```

在默认 5% 步长、2.6 GHz 上限的机器上，conservative 会先减掉七个 130 MHz 台阶、再加回一个，反复之后 policy 稳定在约 530 MHz——尽管 CPU 2 始终满载。作者据此把判据改成「policy 内所有 CPU 都真的处于长 idle」。

## 技术方案

**v1（已发出）**：`drivers/cpufreq/cpufreq_governor.c` +4/-1，在 `dbs_update()` 里加 `bool all_cpus_idle = true`，凡某个 CPU 未走 `idle_time > 2 * sampling_rate` 分支就置 false，最后 `policy_dbs->idle_periods = all_cpus_idle ? idle_periods : UINT_MAX;`。带 `Cc: stable@vger.kernel.org`、`Fixes: 00bfe05889e9`，以及两枚与作者同域（@zte.com.cn）的 `Reviewed-by`（Luo Haiyang、Run Zhang）。

**Zhongqiu Han 的反方案（09-06 贴出但尚未正式提交，请求作者先在场景里试）**：不再问「这个 CPU 有没有被按时采样」，而是问「这个 CPU 在这一轮实测里忙不忙」。他在循环里先算一份不写回任何 per-CPU 状态的 `measured_load`（`!time_elapsed || idle_time >= time_elapsed` 时为 0，否则 `100 * (time_elapsed - idle_time) / time_elapsed`），把决策用的 `load` 复用同一计算，再用 `if (measured_load > dbs_data->up_threshold) busy_cpu_seen = true;`，最终 `policy_dbs->idle_periods = busy_cpu_seen ? UINT_MAX : idle_periods;`。这样「空闲但按时被采样」的兄弟不会把 deferred periods 全部丢掉，同时保留唤醒时的快速降频能力。

**作者 09-07 的第三条路（将进 v2）**：部分接受——承认 long-idle 条件基于累计 idle time、不能可靠指示该 CPU 是否该阻止 deferred 降频；也同意「本采样周期实测负载要与可能继承 `prev_load` 的决策负载分开保存」。但不同意拿 `up_threshold` 当门：他的例子是 CPU A 连续多个采样周期 idle、CPU B 稳定 75% 负载，`up_threshold=80`、`down_threshold=20` 时 policy 落在 conservative 的保持区，两边都不触发；若只以 `up_threshold` 为门，B 不会阻止 deferred 降频，A 攒下的 idle periods 仍会把 policy 频率拉下来。因此他主张以「本 policy 本周期实测最大负载」为门，并明确这份量要单独记录在 `struct policy_dbs_info`（例如 `max_sample_load`）以免与 `dbs_update()` 的返回值混淆：

```
if (policy_dbs->max_sample_load < cs_tuners->down_threshold &&
    policy_dbs->idle_periods < UINT_MAX) {
        ...
}
```

即只有整个 policy 实测负载低于 `down_threshold` 时才放行 deferred 降频。

## 版本演进与当前进展

- 09-02 15:47 v1 首发（无版本号，`<2026090215474182681fN7LLOSpqIc3s3OqJaW@zte.com.cn>`），单文件 4 增 1 删，带 `Cc: stable` 与两枚同域（@zte.com.cn）`Reviewed-by`。
- 09-06 23:13 Zhongqiu Han 唯一一份外部评审：「The problem is real, but I don't think this condition is the right one.」并给出 `measured_load` / `up_threshold` 反方案 diff，请他试跑，「Once everyone agrees I can send this formally」。
- 09-07 18:55 作者回帖：接受两点、拒绝 `up_threshold` 作为门限，提出 `max_sample_load` + `down_threshold`，明确「I'll rework the patch along these lines」并预告发 v2、给 Zhongqiu 挂 `Suggested-by`。
- 09-07 23:07 Zhongqiu Han 逐点反驳 down_threshold 方案（见下节），双方未再跟帖。
- 截至本日缓存中无 v2、无其它评审者介入，cpufreq 维护者（Rafael Wysocki、Viresh Kumar）与 sched/cpufreq 协作侧均未表态。

## Maintainer 意见与讨论焦点

- **Zhongqiu Han（本日 23:07，核心反驳）**：
  1. 事实层面不同意差别存在：`cs_dbs_update()` 里 `idle_periods` 只影响局部变量 `requested_freq`，而「该变量在 policy 保持区时根本不会真的被用来改频」。
  2. 两个门限只在「实测负载落在 `down_threshold` 与 `up_threshold` 之间、且用于决策的负载（此时是继承来的 `prev_load`）触发了某一分支」时才有区别；「若没有 CPU 走 reuse 路径，两者相等、结果相同」。
  3. 取舍：用 `up_threshold` 只在 CPU 真的忙到该升频时才放弃 deferred 降频，其余情况仍尽量降，「stays closer to the design of 00bfe05889e9」，既修掉描述的 bug 又避免明显功耗回退；用 `down_threshold` 则「只要负载不在最低降频区就跳过 deferred 降频」，会造成功耗回退。
- **Shengming Hu（作者）**：坚持 A/B 场景（75% 落在保持区）说明只看 `up_threshold` 挡不住空闲兄弟把 policy 拉下来，并强调必须把实测负载独立于继承负载记录。
- 已经收敛的部分其实不少：问题真实、`idle_time > 2 * sampling_rate` 的反面推不出「CPU 忙」、per-policy 一票否决会整体废掉 `00bfe05889e9` 在共享 policy 上的优化、实测负载与继承负载应当分离——这四点双方都同意。
- 未收敛的部分是「什么算忙到该阻止补扣降频」：`> up_threshold`（几乎升频）还是 `< down_threshold`（几乎降频），中间保持区里谁说了算。Zhongqiu 的论证依赖「保持区不改频」这一代码事实，作者的依赖是「决策负载可能来自继承的 `prev_load`，与保持区不是一回事」——两种说法其实针对的是不同变量（`requested_freq` 是否被应用 vs `max_load` 是否被继承），本线程中没有人把这条链条对齐写到彼此能反驳的程度。

## 合入评估

`likelihood=unknown`。

正向：问题真实且有 trace 佐证，属于「共享 policy 下错误压频」这类会影响性能的行为缺陷；带 `Fixes:` 与 `Cc: stable`；改动只有 4 行；评审者并未否定修复必要性，只否定判据。

卡点：一是作者已宣布要按 `max_sample_load` + `down_threshold` 出 v2，而该方向正是评审者当日明确反对的（会造成功耗回退），v2 很可能被再次退回，双方尚未在同一层次上把 `requested_freq` 与继承 `prev_load` 的关系讲清；二是全线程没有任何 benchmark 或功耗数字，两条路线的功耗/性能差全是推演；三是 Zhongqiu 自己的反方案也停在「先请你试跑」而未正式提交，上游目前没有一份可评的成体系改法；四是 cpufreq 维护者缺席，`dbs_update()` 属 ondemand/conservative 共用路径，一处判据变化会影响 ondemand 之外的 governor；五是 v1 里两枚 `Reviewed-by` 都来自与作者同一公司域名的地址，不构成上游评审背书。

## 效果评估

本线程没有任何 benchmark、功耗测量或频率曲线统计，两侧都停留在逻辑推演。可引用的量化材料只有 v1 提交说明里的复现证据：同一 SCHED_EXT 满载场景下 `load=100 idle_periods=7 interval=59 ms` 这类 trace 行，以及「5% 默认步长 + 2.6 GHz 上限时先减七个 130 MHz 台阶、只加回一个，反复之后 policy 稳定在约 530 MHz」的算例。

缺口很明确：作者没有给出修复后 policy 频率恢复到多少；Zhongqiu 的「避免明显功耗回退」与作者的「A 的 deferred idle 仍会拉低 policy 频率」都没有数字；SCHED_EXT 与 CFS 在 update-util 回调密度上的差异（这正是本 bug 触发条件）也未被量化，邮件里只给了 19/39/59 ms 的 interval 观测。未获取到：任一版本的能耗数据、`down_threshold` 与 `up_threshold` 两种门的对照实验。

## 我可以参与的点

- 最容易做出增量的一件事是把这场分歧变成实验：按 Zhongqiu 的 `up_threshold` 版与作者的 `max_sample_load < down_threshold` 版各跑一次，至少覆盖三种组合——(a) 一 CPU 持续 idle + 另一 CPU 稳定落在保持区（例如 75%，up=80/down=20）；(b) 一 CPU idle + 另一 CPU 满载；(c) 全部 CPU 长时间 idle。采 policy 频率曲线、`/cpufreq/stats` 台阶计数与整机功耗，直接回答「保持区里两种门是否真的等价」。这条数据上游目前完全没有。
- 代码层面可以补一个双方都没写的点：`max_sample_load` 这类 per-policy 状态的复位时机（policy 内 CPU 集合变化、CPU hotplug、governor 停止/切换时），以及它是否需要在 `dbs_update()` 每轮开头清零——本线程只讨论了「记什么」，没讨论「什么时候不残留」。
- 与调度器侧的耦合值得单独确认：作者的现象之所以能出现，前提是 SCHED_EXT 的 update-util 回调比 CFS 稀疏（interval 到 59 ms）。若内部要同时使用 sched_ext 类调度器与 conservative/ondemand governor，这本身就是一个独立于本补丁的可靠性问题，可以在 sched_ext 侧确认 util 更新链路是否该保证 DBS 采样节奏。
- 回合判断：只要内部树带 `00bfe05889e9` 的等价改动、且存在「多 CPU 共享一个 cpufreq policy + 有长时间空闲 CPU + 更新稀疏」的形态（绑核到同 cluster、cgroup 限流让 CPU 频繁长时间 idle 都可能凑出这个条件），这个压频问题就同样存在。在共识形成前，`up_threshold` 方向改动更小、功耗风险更低，适合先做内部验证而不是照搬 v1 的 per-policy 一票否决。

## 参考链接

- v1 补丁本体（含复现 trace、`Fixes: 00bfe05889e9`）：https://lore.kernel.org/all/2026090215474182681fN7LLOSpqIc3s3OqJaW@zte.com.cn/
- Zhongqiu Han 的评审与 `measured_load`/`up_threshold` 反方案：https://lore.kernel.org/all/f0b59964-081c-4547-8251-3e3134c4942f@oss.qualcomm.com/
- 作者 09-07 回应（承认第一点、提出 `max_sample_load` + `down_threshold`、预告 v2）：https://lore.kernel.org/all/20260907185517424rOcCTgNPmgf1i0mLqlxWN@zte.com.cn/
- Zhongqiu Han 09-07 反驳（`requested_freq` 与保持区、功耗回退）：https://lore.kernel.org/all/3c7be2f1-b1be-4f6e-948d-e1991d8afa6b@oss.qualcomm.com/
- 相关代码：`drivers/cpufreq/cpufreq_governor.c` `dbs_update()` / `cs_dbs_update()`、`struct policy_dbs_info`、`struct cpu_dbs_info`
- tip-bot commit: 未获取到
- stable backport: 未获取到
