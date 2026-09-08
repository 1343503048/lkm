# sched/cache: Estimate utilization of the whole thread group

## TL;DR

本文为增量更新，20/23 的算法本身（线程组整体利用率的非对称 EWMA 估算）与前因见 [[sched-20260828-010]]，Peter 那条建议的出处见 [[sched-20260901-006]]，整套 RFC 的方案背景见 [[sched-20260827-002]]。09-08 本线程只有一封新邮件，内容是一处代码生成层面的小收尾：作者 Jianyong Wu 在 15:43 回复 Peter Zijlstra 09-01 的意见，接受把 20/23 里的 `mul_u64_u32_div()` 换成 `mul_u64_u32_shr(..., NICE_0_LOAD_SHIFT)`，并为一周未回道歉（「Sorry for the late reply. Good point, will fix.」）。这不改变系列任何争议——20/23 的参数取值、以及 RFC v2 整体被 Peter 否掉的方向性问题依旧挂着。

## 背景与问题

摘要（详见前文）：Jianyong Wu（Hygon）的 23 补丁 RFC v2 给 cache-aware scheduling 做「按 LLC 粒度有序扩张」。其中 20/23 负责估算一个线程组（mm）的整体利用率，作为 21/23 决定「允许扩散到多少个 LLC」的输入：

```c
					mm_util = mul_u64_u32_div(cpu_util,
							min_t(unsigned long, occ, NICE_0_LOAD),
							NICE_0_LOAD);
```

即以 `occ`（线程组占用量，封顶 `NICE_0_LOAD`）对单 CPU 利用率做比例缩放。Peter 09-01 对本补丁唯一的意见就是这一行——不是算法，而是实现：他判断 `mul_u64_u32_div()` 最终会走 inline asm，因而无法把这次「除以 2 的幂」优化掉，建议改用 `mul_u64_u32_shr(..., NICE_0_LOAD_SHIFT)`。

## 技术方案

本日无新代码发出，只有作者对上述建议的接受表态。落到 v3 的改动预期是那一行换成 `mul_u64_u32_shr(cpu_util, min_t(unsigned long, occ, NICE_0_LOAD), NICE_0_LOAD_SHIFT)` 形式（具体写法待作者提交，本批邮件未给出）。

需要说明这条改写的两个语义前提，我都按本地主线核对了：一是 `NICE_0_LOAD` 必须是 2 的幂，`div` 与 `shr` 才等价——`kernel/sched/sched.h:175` 写的是 `#define NICE_0_LOAD (1L << NICE_0_LOAD_SHIFT)`，其中 64 位下 `NICE_0_LOAD_SHIFT = 2 * SCHED_FIXEDPOINT_SHIFT`（即 20），成立；二是 `mul_u64_u32_shr()` 的第二个形参是 `u32 mul`（`include/linux/math64.h:175`，语义 `(a * mul) >> shift`），而这里传入的 `min_t(unsigned long, occ, NICE_0_LOAD)` 已被封顶在 2^20，正好落在 `u32` 内，不会因为截断而失真。

## 版本演进与当前进展

- 09-08 15:43 Jianyong Wu 回复（`<3994638d89da4fd58365cefe62ff94ed@hygon.cn>`，`References` 链上带 cover `<20260827122816.756234-1-wujianyong@hygon.cn>`、20/23 `<20260828021156.785662-1-wujianyong@hygon.cn>` 与 Peter 的 `<20260901144449.GJ776954@noisy.programming.kicks-ass.net>`）：「Hi Peter, Sorry for the late reply. Good point, will fix.」
- 版本仍是 v2，v3 未出现。本批邮件里没有 20/23 的 diff 变化，也没有其它补丁的新回复。
- 从时间线看这是一个纯粹的执行进度：意见 09-01 提出，09-08 被接受，中间作者未回应。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（09-01 提出，本日被关闭）**：`mul_u64_u32_shr()` 会生成更好的代码。作者接受，无往返争议。
- **本日无新增分歧**，但 RFC v2 的实质争议一条都没被处理，仍处悬空状态：Peter 在 09-01 对 17/23 的方向性反对（「At every point NUMA migration should take precedence over LLC」「Disabling page-migration or numa task-migration separately completely wrecks things」）、对 per-task `numa_preferred_nid` 与 per-process `mm->sc_stat.cpu` 粒度冲突的追问、以及「注释不得引用已不存在的旧代码」这类要求，本日都无进展。
- 20/23 自身最难论证的部分依旧没人碰：非对称 EWMA 的上升 1/2、下降 1/8 两个权重是纯经验值，邮件里没有敏感性分析。

## 合入评估

`likelihood=unknown`，与 09-01 的判断一致——本日这封邮件不改变任何评级依据：它关闭的是一个代码生成细节，而整个 RFC 的卡点在架构层面（NUMA 与 LLC 的优先级次序、per-task 与 per-process 状态粒度），那些问题仍无解。`blocking_issues`：

1. 整套 RFC v2 的方向性异议（17/23 与 NUMA 硬优先）未回应。
2. v3 尚未发出；本日接受的这条 `mul_u64_u32_shr` 也只是「will fix」，没有 diff 落地。
3. 20/23 的 EWMA 权重缺敏感性数据，21/23（全系列最重的一封，+325/-25）依赖这个估算。

`next_action`：等 v3 一次性带上这条修正与 Peter 其它意见的处理结果。

## 效果评估

本邮件不涉及效果。20/23 的估算方式与 21/23 的扩张策略在整个 RFC 里都没有 benchmark 数字，本日这封「will fix」同样只是代码风格/代码生成层面的确认，无任何量化证据。

## 我可以参与的点

- **验证改写的代码生成收益（testing）**：`mul_u64_u32_div()` → `mul_u64_u32_shr()` 的实际效果是可以直接量出来的——在同一台机器上对改动前后 `mm_util` 所在函数做反汇编对比，看是否真的从 `div` 指令/`__aeabi_uldivmod` 退路变成移位，回帖附上结论能帮 Peter 省一次复核。这类「意见已接受、证据没人补」的空档成本很低。
- **补 EWMA 参数敏感性（testing）**：这是 20/23 从 8/28 至今一直没人回答的问题。给出同一负载下上升/下降权重取三档（如 1/2·1/8、1/4·1/16、1/1·1/4）时扩张 LLC 数量的时间序列，比任何代码风格意见都更有推动力。
- **别急着铺新补丁（讨论）**：v3 之前提扩展属于添乱，此处如实标注为「当前阶段无明显参与空间」的选项之一。

## 参考链接

- 本日回帖（作者接受 mul_u64_u32_shr）: https://lore.kernel.org/all/3994638d89da4fd58365cefe62ff94ed@hygon.cn/
- Peter Zijlstra 09-01 的意见: https://lore.kernel.org/all/20260901144449.GJ776954@noisy.programming.kicks-ass.net/
- RFC v2 20/23: https://lore.kernel.org/all/20260828021156.785662-1-wujianyong@hygon.cn/
- RFC v2 cover: https://lore.kernel.org/all/20260827122816.756234-1-wujianyong@hygon.cn/
- tip-bot commit: 未获取到
- stable backport: 未获取到
---
id: sched-20260908-010
date: '2026-09-08'
subject: "sched/cache: Estimate utilization of the whole thread group"
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260828021156.785662-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/3994638d89da4fd58365cefe62ff94ed@hygon.cn/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-08'
authors:
- Jianyong Wu
maintainers_involved:
- Peter Zijlstra
patch_series:
- version: v2
  msgid: <20260828021156.785662-1-wujianyong@hygon.cn>
  date: '2026-08-28'
  summary: 'RFC v2 的第 20 片（2 文件 +43/-2）：以非对称 EWMA（上升 1/2、下降 1/8）跟踪线程组整体利用率，并按 mm_util = mul_u64_u32_div(cpu_util, min(occ, NICE_0_LOAD), NICE_0_LOAD) 缩放，供 21/23 决定扩张到多少个 LLC。本日无新版本、无 diff 变化。'
  review_outcome: '作者 09-08 接受 Peter 09-01 的 mul_u64_u32_shr(..., NICE_0_LOAD_SHIFT) 建议并为一周未回道歉（"Sorry for the late reply. Good point, will fix."）。EWMA 权重取值与 RFC 的方向性异议本日仍无进展。'
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 本邮件只关闭一个代码生成细节，RFC v2 的方向性异议（17/23 与 NUMA 迁移应始终优先于 LLC）仍未回应
  - v3 尚未发出，mul_u64_u32_shr 的修正目前只是口头 will fix
  - 非对称 EWMA 的 1/2 与 1/8 权重缺敏感性分析，而 21/23 的扩张决策直接依赖该估算
  next_action: 等 v3 一次性带上本条修正与 Peter 其余意见的处理结果
contribution_opportunities:
- kind: testing
  description: 对 mul_u64_u32_div 与 mul_u64_u32_shr 两版做反汇编对比，确认是否真从除法退路变为移位，回帖附证据
- kind: testing
  description: 给出同一负载下 EWMA 上升/下降权重三档取值时扩张 LLC 数量的时间序列，补上 20/23 至今缺失的敏感性分析
source_email_count: 1
related_articles:
- sched-20260901-006
- sched-20260828-010
- sched-20260827-002
tags:
- cfs
- numa_balancing
---
