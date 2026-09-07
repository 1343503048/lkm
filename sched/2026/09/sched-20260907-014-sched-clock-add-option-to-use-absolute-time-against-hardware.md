# sched_clock: Add option to use absolute time against hardware clock reset

## TL;DR

本文为增量更新，完整背景见 sched-20260906-005（Thomas Gleixner 09-06 的明确 NAK）与 sched-20260903-015（Marc Zyngier 的三条反对）。本日是这条线程的**收尾**：Feng Tang 09-07 17:05 接受「补丁 hacky」的判断，放弃改 epoch 的原方案，转而按 Marc 的建议拿出一个形状完全不同的 diff——不新增 cmdline 开关、不动 epoch，只在 `sched_clock_register()` 已有的那行 `pr_info` 里多打一个「计数器自复位以来已运行多少 ns」的字段；Marc 17:37 回：这正是大家历来在本地做的事，而且只在 bring-up 新硬件/新固件且它是坏的时候才有意义，kernel 不是这类东西的落脚点（他 09-02 就已表态 `reluctant to burden the kernel with something that is, by definition, unreliable`）；Feng 18:57 回「I see your point now, thanks!」。线程到此终止，**没有 v2、没有新版本号**，方向彻底关闭。

## 背景与问题

需求本身（把 kernel / SCP firmware / ATF 的日志对到同一条以硬件计数器复位为原点的时间线上追 RAS 问题）、原方案（`abs_sched_clock` core_param 直接把新计数器的绝对值当作 epoch）、以及三层反对（EL2 可任意 offset 使「绝对」不成立、破坏 `sched_clock()` handover、boot 期 panic 时 debugfs 不可用）都已在前两篇记录，此处不重复。

本日的关键是**讨论对象换了**：争的不再是「要不要一个改变 `sched_clock()` 语义的开关」，而是「能不能只在注册日志里多打一个换算量」。这个降级恰好绕开了前两条反对——不动 epoch 就不存在 handover 连续性问题，不宣称「绝对时钟」也就不存在 EL2 offset 的可靠性质疑。

## 技术方案

Feng Tang 本日贴出的 diff（以引用块形式出现在回帖里，不是正式发送的 patch：无 `--- /` 分隔、无 diffstat、无 sign-off）：

```
--- a/kernel/time/sched_clock.c
+++ b/kernel/time/sched_clock.c
@@ -176,7 +176,7 @@ static enum hrtimer_restart sched_clock_poll(struct hrtimer *hrt)
 void sched_clock_register(u64 (*read)(void), int bits, unsigned long rate)
 {
-	u64 res, wrap, new_mask, new_epoch, cyc, ns;
+	u64 res, wrap, new_mask, new_epoch, cyc, ns, reset_ns;
 	...
@@ -235,8 +235,11 @@ void sched_clock_register(u64 (*read)(void), int bits, unsigned long rate)
 	/* Calculate the ns resolution of this counter */
 	res = cyc_to_ns(1ULL, new_mult, new_shift);
 
-	pr_info("sched_clock: %u bits at %lu%cHz, resolution %lluns, wraps every %lluns\n",
-		bits, r, r_unit, res, wrap);
+	/* Calculate the time since last counter resetting to 0 */
+	reset_ns = mul_u64_u64_div_u64(new_epoch, NSEC_PER_SEC, rate);
+
+	pr_info("sched_clock: %u bits at %lu%cHz, resolution %lluns, wraps every %lluns, has run %lluns since counter reset\n",
+		bits, r, r_unit, res, wrap, reset_ns);
```

与原提案的三点差别值得逐条对照：

1. **不再修改 epoch**：`epoch_ns` 的累加路径一字未动，`sched_clock()` 的取值语义与 handover 连续性完全不受影响，只增加一行输出。
2. **不再需要 `core_param`**：diff 里既没有 `abs_sched_clock` 变量也没有参数注册，也就是说这行信息是无条件打印的——顺带把「boot 期 panic 时 debugfs 不可用」这一条也解决了（dmesg 一定有）。
3. **精度/溢出改用 `mul_u64_u64_div_u64(new_epoch, NSEC_PER_SEC, rate)`**，而不是原方案里的 `cyc_to_ns()`。这正好是 09-03 那轮自动评审（Sashiko）指出应改用的换算方式——原方案里只是一处顺带的正确性修补，在本日这个形状里它成了唯一的技术实现点。

## 版本演进与当前进展

- 09-02 v1（无版本号单发）→ 09-02/09-03 Marc Zyngier、Yao Yuan 的质疑与作者让步 → 09-06 04:39 Thomas Gleixner NAK。
- **09-07 17:05 Feng Tang**：承认 hacky，转述 Marc 的建议原文（`why isn't this just a one-off sampling of the counter, kept in some user accessible location (debugfs or something else), and ultimately post-processed to align your logs?`），给出上面这个「把 reset 以来的偏移打进注册日志」的新形状。
- 09-07 17:37 **Marc Zyngier** 再次反对（见下节）。
- **09-07 18:57 Feng Tang**：`I see your point now, thanks!` ——线程最后一条，无后续。
- 版本号仍为 v1（原提案那一份）；本日既没有 v2，也没有把新 diff 正式投递。

## Maintainer 意见与讨论焦点

- **Marc Zyngier（本日）**：三句递进的拒绝，原文如下——
  - `Which is what people have done locally since the beginning of times. And the only time this is actually useful is when bringing up new HW/FW that is broken.`
  - `So why the need to put that in an upstream kernel, instead of being as part of your debug toolbox? I don't think the kernel shouldn't be the recipient of this sort of stuff.`（原文双重否定，字面读是「我不认为 kernel 不该收这类东西」，但结合上一句「大家历来在本地做」以及他 09-02 的 `I'm somewhat reluctant to burden the kernel with something that is, by definition, unreliable`，实际语义按反对理解。）
  - 他这次反对的**不是技术形态而是归属权**：新形状已经不破坏任何语义，他的立场是这个信息本身属于本地调试工具箱，与是否优雅无关。这一点比 09-06 tglx 的情绪化 NAK 更难绕——因为它没有可修复的技术项。
- **Feng Tang（本日）**：策略从「辩护」转成「按建议改形状再试一次」，被再次拒绝后直接接受（`I see your point now`），没有留下 handover、能力检查等任何未答的技术债——因为新方案本就不碰这些。
- 焦点最终收敛为一个纯定位问题：**上游接受什么**。本线程给出的答案是——连「注册时无条件多打一个 ns 数」这种零语义风险的改法都不被接受，说明反对方认为这条信息的所有者应是厂商自己的 bootloader/固件日志或 out-of-tree 补丁，而不是通用 timekeeping 代码。

## 合入评估

`likelihood=low`（实质为零）。原 `abs_sched_clock` 方案：timekeeping 维护者 NAK、arm64 时间源维护者两条实质反对、作者本人承认 hacky，本日已自行放弃；本日的新形状：唯一在场的相关维护者（Marc）再次反对，作者当场收手。`status=stalled`，且是「作者已认同不该继续」这种最彻底的停滞——不会有 v2。

`severity=none`：既没有回归被引入，也没有既有 bug 被修复；线程从头到尾只是提案被拒。

## 效果评估

无数据，本日三份邮件都不含性能或时间线对齐的实测（原方案的两条证据是「本地靠它追过需要 kernel/SCP/ATF 协作的 RAS 问题」这一主观陈述，前作已记录）。值得记录的「效果」只有讨论结果本身：一个新形状从提出到被否只用了 32 分钟（17:05 → 17:37），作者 1 小时 20 分后认账。

从工程角度可以给这条一个客观评价：本日的 diff 若真被接受，收益是「任何平台启动日志里都能读到计数器已运行时长」，代价是一行 permanent dmesg 输出与一次启动期 64 位乘除。反对意见里并未主张这个代价过高，主张的是**这类知识不该由通用内核持有**——所以这不是一次能量化的失败，而是一次归属判定。

## 我可以参与的点

- **结论先行：这条线程不需要再跟进，也不建议按调度器补丁的路子去 review**。真正的语义风险都在 timekeeping 侧，而该侧维护者已明确不接收。若内部有同样的「跨 kernel/BMC/SCP 日志对齐」需求，成本最低的做法就是本日和前作都指向的那条：自家 bootloader 或早期 init 阶段采样一次硬件计数器、连同换算关系打进日志、事后脚本对齐；本日的 diff 甚至可以原样拿去当 out-of-tree 调试补丁用（它不改语义，维护负担几乎为零）。
- **可以替这个需求往上追一层的地方**：真正的痛点是「boot 期 panic 时 debugfs 不可用」，而这是 pstore/ramoops 与 early console 的范畴。如果有兴趣推上游能接受的方案，值得调研的方向是把这类启动期一次性采样数据放进 `printk` 结构化的 reserved 区或 pstore console/ramoops，让 crash 后仍可读——这与「调度器时间基准」无关，但决定了这类需求能否在不碰 timekeeping 的前提下闭环。邮件中无人提出这一层，属于可以我们补的方向。
- **可复用为团队内部案例**：这条线程是一个完整且便宜的「上游边界」教材——先给语义开关（被 NAK）、再退到只加一行日志（仍被否）、期间还顺手修对了 `mul_u64_u64_div_u64()` 的精度问题，最后照样不通过。可以拿它说明：**技术正确性不是合入的充分条件，功能归属才是**；内部提上游需求前先问「这是不是 debug toolbox 该干的事」。
- **精度点仍然值得抄**：`new_epoch → ns` 这类高频计数器到纳秒的换算必须走 `mul_u64_u64_div_u64()` 而不是先乘后除的 `cyc_to_ns()`（后者在 bits 大、rate 高的计数器上会溢出）。自家分支里凡有 counter→ns 换算（调度统计、cgroup CPU 记账、驱动时间戳）都可以照此对照检查一遍。

## 参考链接

- 相关文章/系列：
  - [[sched-20260906-005]] 前作：Thomas Gleixner 的 NAK 与线程整体判断。
  - [[sched-20260903-015]] 更早一篇：Marc Zyngier 的 EL2 / handover 两条实质反对与作者的让步过程。
  - [[sched-20260902-013]] v1 首发记录。
- 本日 Feng Tang 的新形状 diff: https://lore.kernel.org/all/ap5-ZM-2RMih3iQ7@U-2FWC9VHC-2323.local/
- 本日 Marc Zyngier 的再次反对: https://lore.kernel.org/all/86h5k14d34.wl-maz@kernel.org/
- 本日 Feng Tang 的收尾: https://lore.kernel.org/all/ap6Ypbz4wkftPgBa@U-2FWC9VHC-2323.local/
- 原提案 v1: https://lore.kernel.org/all/20260902082123.95770-1-feng.tang@linux.alibaba.com/
- Thomas Gleixner 的 NAK（09-06）: https://lore.kernel.org/all/8733vn5t6p.ffs@fw13/
- tip-bot commit: 未获取到（无 commit）
- stable backport: 未获取到

---
id: sched-20260907-014
date: '2026-09-07'
subject: 'sched_clock: Add option to use absolute time against hardware clock reset'
subsystem: sched
type: discussion
status: stalled
severity: none
thread_root_msgid: '<20260902082123.95770-1-feng.tang@linux.alibaba.com>'
lore_url: https://lore.kernel.org/all/ap5-ZM-2RMih3iQ7@U-2FWC9VHC-2323.local/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Feng Tang
maintainers_involved:
- Marc Zyngier
- Thomas Gleixner
- Feng Tang
patch_series:
- version: v1
  msgid: <20260902082123.95770-1-feng.tang@linux.alibaba.com>
  date: '2026-09-02'
  summary: '原提案：kernel/time/sched_clock.c 新增 abs_sched_clock core_param，开启后 sched_clock_register() 用计数器绝对值直接作为 epoch，以对齐 kernel/SCP/ATF 日志。09-06 Thomas Gleixner NAK。本日 Feng Tang 放弃该形状，改贴一个只扩展 pr_info 输出（新增 has run %lluns since counter reset，用 mul_u64_u64_div_u64 换算）、不改 epoch 也不加参数的 diff；Marc Zyngier 再次反对，认为这属于本地 debug toolbox。'
  review_outcome: 'Marc Zyngier 09-07 17:37 反对（一次性采样大家历来在本地做、只在 bring-up 坏硬件/固件时有用、kernel 不该收这类东西）；Feng Tang 18:57 回 I see your point now, thanks!。线程终止，未投递 v2。'
merge_assessment:
  likelihood: low
  blocking_issues:
  - 原方案被 timekeeping 维护者 NAK，作者本日自行放弃
  - 降级后的「只多打一行日志」形状同样被 Marc Zyngier 反对，争点已从技术正确性转为功能归属
  - 作者已认同不该继续（I see your point now），不会有 v2
  next_action: 停止跟进该线程；内部同类需求按 out-of-tree 调试补丁或 bootloader 期一次性采样 + 日志后处理自行实现；若要闭环 boot 期 panic 可读性，调研 pstore/ramoops 方向
contribution_opportunities:
- kind: new_patch
  description: 在自家平台实现「启动早期一次性采样硬件计数器 + 打印换算关系 + 事后脚本对齐 kernel/SCP/ATF 日志」，可作为 out-of-tree 补丁直接复用本日 Feng Tang 贴出的 diff 形状
- kind: discussion
  description: 针对该场景的真实约束（boot 期 panic 时 debugfs 不可用）调研 pstore/ramoops 等上游已接收的机制，替代往通用 timekeeping 里塞调试用途
source_email_count: 3
related_articles:
- sched-20260906-005
- sched-20260903-015
- sched-20260902-013
tags:
- sched_clock
---
