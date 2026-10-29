# cpufreq: add an Amlogic speed-bin driver

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261027-017：Christian Köver-Draxl 提交的 Amlogic speed-bin cpufreq 驱动（系列 4/4，为 Amlogic SoC 增加 speed-bin 分档感知的频率/电压设置）讨论继续——Christian Hewitt 提醒其 S4 工作（ramp-delay 是 OPP 切换稳定关键），Amlogic 厂商侧 Chuan Liu 当众要求「先 hold off 不要在 S4 上提 cpufreq 驱动」，因 S4 的 clock 驱动尚不能设 CPU 时钟、regulator 缺电压稳定等待逻辑。
- sched-20261029-016（今天）：Chuan Liu（Amlogic）发长文澄清立场并细化诉求——重新审了 2/4（功能完整，是否放 `s4-pll.c` 请 Jerome Brunet 评估）、说明其邮箱问题致漏收系列其它 patch、解释「统一 amlogic-cpufreq.c 覆盖 S4/C3/T7…A9」的规划（不同硬件架构共享 regulator/DSU/clk、transition latency、bl31.bin 的 SMC→SCMI 差异），并明确希望先做整体评估再定。**关键张力**：cpufreq 维护者 Viresh Kumar 已表示「可经 PM tree 单独收 4/4」，但厂商希望暂缓、先做统一方案评估。

## 背景与问题
（承接 20261027-017）为 Amlogic SoC 增加 speed-bin 感知的 cpufreq 驱动。厂商侧（Chuan Liu）今日补充的关键约束：S4/C3/T7 的 bl31.bin 已发布、多数客户固件仍走 SMC 设置 CPU 时钟，频繁 `set_rate()/set_parent()` 会产生较大 clock latency、拖累 sugov 线程；电压缩放又是 transition latency 大头；而后续 SoC（S7/S7D/S6 共享单 regulator、A9 两 cluster 共享 dsu_clk）资源耦合更复杂，现有 `amlogic-cpufreq.c` 难以直接扩展。因此厂商希望上游驱动尽量覆盖这些优化，并保留与已发布固件的兼容。

## 技术方案
今日无补丁代码变更，是厂商对**驱动架构方向**的长文回应：倾向做「统一 `amlogic-cpufreq.c`」而非逐 SoC 驱动，但承认对多 cluster 共享资源（CPU/DSU 共享 rail、CPU/DSU 频率按 80% 联动等）尚无定论；对 transition latency 优化（离散 clock 走 SMC vs SCMI、电压 step 的 200us/30mV 等待）还需与已发布 bl31.bin 权衡。Christian Loehle（Arm，reviewer）的此前提问（clock 与电压稳定逻辑）今日被 Chuan Liu 间接回应但仍未闭环。

## 版本演进与当前进展
*current_version: v1*（2026-10-25 首发，线程根 `<20261025192219.209137-1-christian.koever-draxl@student.uibk.ac.at>`，4 片）。今日主要进展是厂商 Asmlogic 的系统性立场声明 + 请求更多时间做整体评估；驱动代码本身无新版本。

## Maintainer 意见与讨论焦点
- **Viresh Kumar（cpufreq 维护者，20261026）**：「Is it safe to apply just this one? I can take this via the PM tree then.」——表达愿意经 PM tree 收取 4/4。
- **Christian Loehle（Arm，reviewer）**：持续就 clock 支持与电压稳定逻辑提问（今日被 Chuan Liu 间接回应）。
- **Chuan Liu（Amlogic 厂商，今天）**：与其说是 review，不如说是「请暂缓 + 统一方案再评估」的请求；并请 Jerome Brunet 评估 2/4 的挂载位置。
- 未解决焦点：厂商「暂缓」与 Viresh「可收取」之间的张力——社区侧要看作者（学生）能否给出不依赖厂商整体评估的最小可用版本，或等厂商统一方案。

## 合入评估
*likelihood=medium*。Viresh 已释放「可经 PM tree 收 4/4」的信号是合入抓手，但厂商明确希望先做跨 SoC 整体评估、且 4/4 是否可独立于 1–3 收取尚未确认。*blocking_issues*：厂商要求 hold off 并先评估统一方案；4/4 单独收取的安全性（依赖 1–3？）待澄清。*next_action*：作者与厂商/Viresh 确认 4/4 是否可独立收取并回应 transition latency / 电压稳定等 review 问题。

## 效果评估
无性能数据。厂商提到「电压缩放占 transition latency 大头、SMC 频繁 set_rate 拖累 sugov 线程」等均为定性描述，未给数字。驱动正确性/稳定性（resume、ramp-delay）是当前讨论主线。

## 我可以参与的点
- **review**：结合 Christian Hewitt 的 S4 分支与 Chuan Liu 的统一方案诉求，评估 2/4 放 `s4-pll.c` 是否合理、4/4 能否独立收取。
- **discussion**：就「逐 SoC 驱动 vs 统一 amlogic-cpufreq.c」的取舍（共享 regulator/DSU、transition latency、固件兼容）给出建议，推动厂商与社区收敛。

## 参考链接
- lore thread（系列 cover）: https://lore.kernel.org/all/20261025192219.209137-1-christian.koever-draxl@student.uibk.ac.at/
- Chuan Liu 今日的长文: https://lore.kernel.org/all/4a51e879-708c-49dc-a08a-3f64eeec8bbf@amlogic.com/
- Viresh Kumar 的「可经 PM tree 收」: https://lore.kernel.org/all/at7lXEqds7ukoR2V@vireshk-B250M-D3H/

---
id: sched-20261029-016
date: 2026-10-29
subject: "cpufreq: add an Amlogic speed-bin driver"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261025192219.209137-1-christian.koever-draxl@student.uibk.ac.at>"
lore_url: "https://lore.kernel.org/all/20261025192219.209137-1-christian.koever-draxl@student.uibk.ac.at/"
authors: [Christian Köver-Draxl]
maintainers_involved: [Viresh Kumar]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261025192219.209137-1-christian.koever-draxl@student.uibk.ac.at>"
    date: 2026-10-25
    summary: "4 片：Amlogic speed-bin 感知的 cpufreq 驱动"
    review_outcome: "Viresh 愿经 PM tree 收 4/4；厂商 Chuan Liu 要求暂缓、先做统一方案评估"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "厂商要求 hold off 并先评估跨 SoC 统一方案"
    - "4/4 单独收取是否依赖 1–3 待澄清"
  next_action: "作者与厂商/Viresh 确认 4/4 可否独立收取，并回应 transition latency 与电压稳定问题"
contribution_opportunities:
  - kind: review
    description: "评估 2/4 放 s4-pll.c 是否合理、4/4 能否独立收取"
  - kind: discussion
    description: "就逐 SoC 驱动 vs 统一 amlogic-cpufreq.c 的取舍给出建议，推动收敛"
generated_at: "2026-10-30T09:30:00"
source_email_count: 1
related_articles: [sched-20261027-017]
tags: [cpufreq]
---