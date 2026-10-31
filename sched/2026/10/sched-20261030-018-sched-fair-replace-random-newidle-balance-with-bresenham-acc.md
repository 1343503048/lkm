# sched/fair: Replace random newidle_balance with Bresenham accumulator

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261029-006（v3）：Qing Wang 把 `newidle_balance` 的随机掷骰换成 Bresenham 累加器以消除方差；Kayra 要求先给「突发是否有实际影响」的数据，并指出 v3 移除 `sched_rng()` 会在 Linus/tip 树上编译报错；作者承诺 v4 删掉有 bug 的 reset 行。
- sched-20261030-018（今天）：作者发 **v4**（恢复被误删的 `sched_rnd_state`/`sched_rng()`，保留 Bresenham）。Peter 两天内三度质疑：随机数本就「修复」了 slope 变化的独立性问题；整数除法向下取整不具分配律（`(3/2+3/2)=2 ≠ (3+3)/2=3`），Bresenham 会**少做 newidle 均衡**；且「均匀」本身不是优点——两 CPU 若同步成固定 pattern 反而增加争用。Kayra 给出 Zen 3 tbench 实测（1 client +0.72%、8 +0.73%、16 -1.29%、32 -1.62%）：**看不出 Bresenham 有收益**。

## 背景与问题
（承接 v3）`newidle_balance` 在 CPU 进入 idle 时以一定概率尝试负载均衡，现行实现用 `sched_rng()` 掷骰；作者主张用确定性方法消除随机方差以利调试/追踪。今日 Peter 从更根本处反驳该动机：把均衡与否当作**独立随机变量**反而能「修复」ratio 斜率变化带来的问题（各次调用互不关联，避免固定 pattern 的共振）；且作者声称的「均匀性」在双 CPU 同步场景下可能放大锁争用。

## 技术方案
（承接 v3，v4 细节）v4 恢复 `sched_rnd_state`/`sched_rng()`（v2 曾误删导致 Linus/tip 编译失败），并把累加器描述改为 Bresenham 式：每次 `pos += (1 + newidle_ratio)`，`pos >= 1024` 时允许均衡并 `pos -= 1024`。作者给出「Bresenham 最大 per-window 误差 0.5 次 vs 随机 41 次」的仿真对比。今日技术争议聚焦两点：

- **初始值**（K Prateek）：建议 `newidle_window_pos` 初始设 512，让首次就能均衡然后稳定；作者回应初始值只影响首次允许均衡的时机、不影响后续间隔，[0,1023) 皆可。
- **向下取整损失**（Peter）：累加器在 slope 变化（ratio 更新）丢弃的分数会累积损失一次均衡，结论是「Bresenham 实际做得**更少** newidle 均衡」，不能断言与随机等价。

## 版本演进与当前进展
*current_version: v4*（2026-10-30 发出）。v4 相对 v3：恢复被误删的 `sched_rnd_state`/`sched_rng()`，修掉 `update_newidle_stats()` 里错误的 `newidle_window_pos = 0` reset。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（maintainer）**：明确不认可「均匀优于随机」——三点：① 独立随机变量可修复 slope 变化问题；② 向下取整不分配 → 少做均衡；③ 均匀触发在双 CPU 同步 pattern 下增加争用。语气明显偏否定（"so far you seem unable to see this distinction :-("）。
- **K Prateek Nayak**：初始值取 512 的 nit。
- **Kayra Cizmeci**：tbench 实测无收益、甚至 16/32 client 小幅回退。
- **未解决**：作者尚未回应「向下取整损失」与「均匀性非优点」两个核心质疑；缺乏「去掉随机化」的真实收益证据。

## 合入评估
*likelihood=low*。维护者态度偏否定，且实测数据显示无收益甚至微回退；作者需要回答「为什么要做这个改动」的根本问题，否则难以合入。*blocking_issues*：缺「突发/方差有实际影响」的真机证据；向下取整损失与均匀性非优点的质疑未回应。*next_action*：作者给出能证明「确定性优于随机」的实测数据，或回应 Peter 的两点数学/争用质疑。

## 效果评估
Kayra 的 Zen 3 tbench（8 核 16 线程，5 次取均值，MB/s）：1 client 313.42 vs 311.19（+0.72%）、8 2113.36 vs 2097.95（+0.73%）、16 3229.59 vs 3271.83（-1.29%）、32 3286.98 vs 3341.13（-1.62%）。结论：低 client 微涨、高 client 微跌，整体无收益。作者的理论对比（Bresenham 0.5 vs 随机 41 次 per-window 误差）为仿真数字，非真机。

## 我可以参与的点
- **testing**：在负载突变的场景（newidle_ratio 频繁变化）对比 Bresenham vs 随机掷骰的均衡次数与尾延迟，回答「方差是否真有影响」。
- **discussion**：分析 Peter 提出的「双 CPU 同步 pattern 争用」与「向下取整损失」在真实调度中的量级，评估均匀性的利弊。

## 参考链接
- lore thread（v4）: https://lore.kernel.org/all/20261030091946.2498870-1-wangqing7171@gmail.com/

---
id: sched-20261030-018
date: 2026-10-30
subject: "sched/fair: Replace random newidle_balance with Bresenham accumulator"
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: "<20261030091946.2498870-1-wangqing7171@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261030091946.2498870-1-wangqing7171@gmail.com/"
authors: [Qing Wang]
maintainers_involved: [Peter Zijlstra]
current_version: v4
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - "缺「突发/方差有实际影响」的真机数据"
    - "向下取整损失与均匀性非优点两点质疑未回应"
  next_action: "作者给出确定性优于随机的实测数据，或回应 Peter 的数学/争用质疑"
contribution_opportunities:
  - kind: testing
    description: "在 newidle_ratio 频繁变化场景对比 Bresenham vs 随机的均衡次数与尾延迟"
  - kind: discussion
    description: "分析双 CPU 同步 pattern 争用与向下取整损失在实际调度中的量级"
generated_at: "2026-10-31T09:00:00"
source_email_count: 7
related_articles: [sched-20261029-006]
tags: [load_balance]
---