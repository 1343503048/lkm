# sched/cpufreq: fix schedutil's boost frequency handling

## TL;DR

Ananthu C V（Qualcomm）在 09-08 16:30 发出 v2 两补丁，修 schedutil 打不到 boost 频率、以及 boost 关掉后频率上限回不来这两头问题：patch 1 在 policy 上线前用「含 boost 的最大可用频率」为 `capacity_freq_ref` 播种，patch 2 在 freq table 里额外跟踪最高非 boost 频率 `max_base_freq`，让 `policy_set_boost()` 有表时改用它/`max_table_freq` 下发 QoS 请求，从而使 `cpuinfo.max_freq` 能重新下降。作者给了完整的 `time_in_state` 前后对比（boost 关闭后不再卡在 4723200，开启后能真正驻留 569 个采样）。本日无人回帖，唯一回帖是作者自己重发被剪枝的日志。值得注意：patch 2 依赖的 `cpuinfo.max_table_freq` 在本地主线（v7.0-34367）里全树不存在，也就是说这个系列压在一个尚未落地的前置系列上。

## 背景与问题

cover 把 schedutil 能否到达 boost 频率拆成两个必须同时正确的量（原文措辞）：

> Schedutil's ability to reach boost frequencies depends on two values being correct: policy max, which caps the resolved target frequency, and the per-CPU capacity frequency reference, which anchors the utilization-to-frequency mapping.

对应两个缺陷：

1. **`capacity_freq_ref` 只锁存一次**。cover：「The per-CPU capacity frequency reference is set once at policy creation and never updated when boost is enabled afterwards, leaving schedutil unable to target boost frequencies even at full utilization.」我在本地主线核对了这条前提，成立：`drivers/base/arch_topology.c` 的 `init_cpu_capacity_callback()` 只在 `val == CPUFREQ_CREATE_POLICY` 时执行 `per_cpu(capacity_freq_ref, cpu) = policy->cpuinfo.max_freq;` 并顺带 `freq_inv_set_max_ratio()`，此后不再有任何更新路径。
2. **`cpuinfo.max_freq` 只增不减**。cover：「The generic boost callback only raises cpuinfo max, never lowers it. Once boost is enabled, disabling it leaves cpuinfo max pinned at the boost ceiling, keeping policy max stuck there too.」作者把根因归到 `538b0188da46 ("cpufreq: ACPI: Set cpuinfo.max_freq directly if max boost is known")`——该提交为保证驱动设定的值能高于频率表最大值，给 cpuinfo max 的更新加了「只允许增加」的护栏，副作用是 boost 关掉后无法回落。2/2 的 commit message 与 `Fixes:` 标签都明确指向这条。

症状层面作者给出的是可观测的 sysfs 行为：`echo 0 > boost` 之后 `policy6/scaling_max_freq` 仍停在 4723200（即 boost 上限），而期望值是回到 4454400。影响范围是所有「有频率表 + 表内标了 `CPUFREQ_BOOST_FREQ` + 支持 boost 开关」的平台。

## 技术方案

**patch 2（本批唯一有正文的补丁，+19/-1，3 个文件）** 的做法是「不清掉护栏，而是把非 boost 上限也跟踪起来」：

- `struct cpufreq_cpuinfo` 新增 `unsigned int max_base_freq; /* Highest non-boost frequency in the table */`，紧挨已有的 `max_table_freq`。
- `cpufreq_frequency_table_cpuinfo()` 里无条件统计：`if (!(pos->flags & CPUFREQ_BOOST_FREQ) && freq > max_base_freq) max_base_freq = freq;`。关键在于它不受 `cpufreq_boost_enabled()`/`policy->boost_enabled` 影响——原代码在 boost 关闭时 `continue` 跳过 boost 项，所以 `max_freq` 会随 boost 状态上下跳，而新加的这行始终得到「表内最高的非 boost 频率」。
- `policy_set_boost()` 把原先写死的 `policy->cpuinfo.max_freq` 换成按有无频率表分支：

```c
+	if (policy->freq_table) {
+		max_freq = enable ? policy->cpuinfo.max_table_freq :
+				    policy->cpuinfo.max_base_freq;
+
+		if (!max_freq)
+			/* when the freq table contains only boost frequencies */
+			max_freq = policy->cpuinfo.max_table_freq;
+	} else {
+		max_freq = policy->cpuinfo.max_freq;
+	}
+	ret = freq_qos_update_request(&policy->boost_freq_req, max_freq);
```

设计取舍很清楚：作者选择保留 `538b0188da46` 的「驱动可以设定高于表最大值」语义（cover：「In the absense of a frequency table, the handling will fall back to using cpuinfo->max_freq, preserving the current behaviour.」），代价是要新增一个跟踪量而不是直接删掉护栏。表内全是 boost 项的退化情形由 `if (!max_freq)` 兜住。

**patch 1（`arch_topology: seed capacity_freq_ref with boost-aware max freq`，`drivers/base/arch_topology.c | 3 ++-`）** 只有 cover 描述和 diffstat 进了本批缓存，正文未收到，具体写法未获取到；从 cover 可知它是在 policy 上线前把「max available（boost inclusive）频率」拿来播种 `capacity_freq_ref`。

这里有一个我认为值得追问的取舍（邮件未展开，属我按 cover 推断）：播种成含 boost 的最大频率，等于把「util → freq」的锚点永久定在 boost 顶点，而 boost 关闭时 CPU 实际最高只能跑 `max_base_freq`。09-07 Oleg Keri 的 `arm64: cpufreq: Report and track frequencies above 4.19 GHz` 系列解决同一半问题走的是另一条路——把 ref 抽成 `topology_update_freq_ref()` 并在 `policy_set_boost()` 里跟随 boost 状态更新。两种方案（一次播种 vs 随状态刷新）方向相反，最终会影响 `arch_scale_freq_ref()` 在读什么，目前两位作者各自独立发版、彼此没有引用。

## 版本演进与当前进展

- 09-08 16:30:27 Ananthu C V 发出 v2 cover（`<20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>`），16:30:29 发 2/2；1/2 正文未收到本批缓存。v2 diffstat：4 files changed, 28 insertions(+), 2 deletions(-)（`drivers/base/arch_topology.c`、`drivers/cpufreq/cpufreq.c`、`drivers/cpufreq/freq_table.c`、`include/linux/cpufreq.h`），`base-commit: 32b6ef9a5d0eca44f9cd91f52f4faa89f145a0de`。
- cover 里没有 `Changes in v2` 段落，v1 → v2 的具体差异**未获取到**；`change-id: 20260804-schedutil-boost-frequency-handling-8e6bf2387a4a` 只能说明该系列首版早至 8 月初。本地 8 月归档中有同主题的早期文章（`sched-20260806-006`、`sched-20260807-003`，当时补丁标题为 `cpufreq: allow cpuinfo max to decrease when boost is disabled` / `sched/cpufreq: Update schedutil's DVFS request to reach the boost frequencies`，作者列含 Sibi Sankar），标题与拆法与今日 v2 不同，我**无法从本日邮件确认它就是本系列的前身**，仅作线索参考。
- 09-08 18:03 作者自己回帖补发了一份干净的日志：「It seems some mangling was done and all lines starting with hashes were considered comments and ignored, malforming the logs.」原因是 cover 正文里以 `#` 开头的 shell 提示符被某些 MTA/客户端当注释剥掉了。
- 本日无任何 reviewer 回帖，无 Ack、无 NAK，未见 tip/stable 收录。
- 前置依赖状态：patch 2 的上下文与新增分支都用到 `policy->cpuinfo.max_table_freq`，而我在本地主线（`v7.0-34367-ge1ba4c925742`）全树 grep `max_table_freq` 无任何命中，`base-commit 32b6ef9a5d0e` 也不是本地已知对象——即该字段来自尚未合入主线的另一个系列（hash 与字段名取自本批补丁正文与本地 git 查询，非主线现状）。

## Maintainer 意见与讨论焦点

未获取到——本批只有作者一封自纠（补日志），Viresh Kumar、Rafael Wysocki 等 cpufreq 维护者以及调度侧维护者均未表态，讨论焦点尚未形成。目前可辨识的争议/风险点是我从补丁本身读出来的，不是邮件里的分歧：

- **依赖未合入的 `max_table_freq`**：整个「有表用表、无表回退」的分支建立在 `max_table_freq` 之上，前置系列若被改语义或被拒，本补丁的 2/2 需要重写。
- **patch 1 的锚点选择**（播种为含 boost 的最大频率 vs 随 boost 状态刷新）无人讨论，且与 09-07 Oleg Keri 系列在 `capacity_freq_ref` 上的思路存在潜在冲突，两边目前互不引用。
- **调度侧与 cpufreq 侧的合入路径**：patch 1 落在 `drivers/base/arch_topology.c`、patch 2 落在 `drivers/cpufreq/`，与 `kernel/sched/` 无直接改动，谁牵头排队（cpufreq 树 vs sched 树）邮件里没提。

没有已知的反对意见，也没有已知的未解决的技术分歧被指出。

## 合入评估

`likelihood=medium`。依据：patch 2 有完整 `Fixes:` 标签、改动小（+19/-1）、并附带前后对比的实测 sysfs 证据，方向上也与既有 `max_table_freq` 的语义自然衔接；但本日零 review，且存在硬性流程卡点。`blocking_issues`：

1. 尚无任何维护者回应（cpufreq 侧 Viresh Kumar 等未表态）。
2. 依赖尚未进入主线的 `cpuinfo.max_table_freq`，需先确认前置系列的合入状态与语义稳定性。
3. 本批邮件里看不到 patch 1 正文（收件端只收到 cover 与 2/2），reviewer 无法就地评审前半问题；`scheduleutil` 能否打到 boost 这一半的论证目前只有 cover 的两句话。

`next_action`：作者下一版把 patch 1 正文完整送出、并在 cover 里说明 `max_table_freq` 的前置系列依赖；等 cpufreq 维护者表态。

## 效果评估

邮件里有具体数字（作者自测，无第三方复现）。修复前：`cat boost` 为 0 时 `policy6/scaling_max_freq` 是 4454400，`echo 1 > boost` 后升到 4723200，但再 `echo 0 > boost` 后仍读到 4723200（回落失败）；该策略 `time_in_state` 为 `355200 36958 / 4454400 650 / 4588800 0 / 4723200 0`，即 boost 档零驻留。修复后：`echo 0 > policy6/boost` 后 `scaling_max_freq` 正确回到 4454400；`boost=0` 时 `4723200 0`，`echo 1 > policy6/boost` 后 `4723200 569`、`4588800 25`，说明 boost 频率首次被真正使用。cover 里的版本因为 `#` 开头行被剥掉而排版错乱，作者 18:03 的重发版本才是可读的原始数据。

需要标注的是：以上都是频率可达性与 sysfs 上限层面的证据，**没有性能类 benchmark 数字**（cover 提到「logs from bench runs are truncated for brevity」，但截断后的 bench 数据未随信给出），因此「schedutil 决策变好多少」目前无数据支撑。

## 我可以参与的点

- **回复补上前置依赖问题（review/discussion）**：本系列最实际的卡点是 `cpuinfo.max_table_freq` 不在主线。我可以确认自己手上树里该字段的来源（哪个系列、什么状态），并在回贴里问清「若前置被改，2/2 的 fallback 分支如何保持」，这是作者和维护者都需要答案的问题。
- **跨系列对齐（discussion）**：把这个 v2 与 09-07 Oleg Keri 的 `capacity_freq_ref` 更新方案放在一起比一次「一次播种 vs 随 boost 刷新」，尤其验证 boost 关闭时 `arch_scale_freq_ref()` 返回值是否与实际可用频率匹配。两条路线目前互不知情，先说清楚的人对社区有直接价值。
- **在我自己的 arm64 平台复测（testing）**：作者的数据是单平台（policy0/6/12 三档，最高 4723200）的产物。可在带 `CPUFREQ_BOOST_FREQ` 表项的机器上按同一手法验证 `scaling_max_freq` 能否回落，顺便验证「表内全为 boost 项」的退化分支是否真的能被触达——这个分支看起来很难在常规机器上跑到。
- **OLK 侧（new_patch）**：若自家分支存在 boost 开关 + 频率表路径，`Fixes: 538b0188da46` 这条链条值得先查一遍是否已在自家树内；按 OLK 规范回合时 `Fixes` 必须写 OLK 自己的 commit。

## 参考链接

- v2 cover: https://lore.kernel.org/all/20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com/
- v2 2/2 `cpufreq: fix schedutil not returning to non-boost freq when boost is disabled`: https://lore.kernel.org/all/20260908-schedutil-boost-frequency-handling-v2-2-25312a713699@oss.qualcomm.com/
- v2 1/2 `arch_topology: seed capacity_freq_ref with boost-aware max freq`: 未获取到（本批缓存无该邮件正文与 Message-ID）
- 作者重发日志的回帖: https://lore.kernel.org/all/ap_a2uVHgjiNtL3I@hu-anancv-blr.qualcomm.com/
- `Fixes` 目标（标题与日期取自本地 `~/code/linux` 的 git log，非本日邮件）: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=538b0188da46
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260908-006
date: '2026-09-08'
subject: "sched/cpufreq: fix schedutil's boost frequency handling"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>
lore_url: https://lore.kernel.org/all/20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com/
upstream_commit: null
fixes_commit: 538b0188da46
merged_branch: null
current_version: v2
generated_at: '2026-09-08'
authors:
- Ananthu C V
maintainers_involved: []
patch_series:
- version: v2
  msgid: <20260908-schedutil-boost-frequency-handling-v2-0-25312a713699@oss.qualcomm.com>
  date: '2026-09-08'
  summary: '2 补丁，4 files changed 28 insertions(+), 2 deletions(-)，base-commit 32b6ef9a5d0e。patch 1（arch_topology: seed capacity_freq_ref with boost-aware max freq，本批未收到正文）在 policy 上线前用含 boost 的最大可用频率为 capacity_freq_ref 播种，使 schedutil 能在 boost 打开后打到 boost 档；patch 2（cpufreq: fix schedutil not returning to non-boost freq when boost is disabled）在 cpufreq_frequency_table_cpuinfo() 无条件跟踪最高非 boost 频率并新增 struct cpufreq_cpuinfo.max_base_freq，policy_set_boost() 有频率表时改用 max_table_freq/max_base_freq 下发 freq QoS 请求、无表时回退 cpuinfo->max_freq，使 cpuinfo max 能在 boost 关闭后回落；带 Fixes: 538b0188da46。'
  review_outcome: '本日无 reviewer 回帖；作者 18:03 自己重发被 "#" 注释规则剪坏的日志。'
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 本日零 review，cpufreq 维护者未表态
  - 依赖尚未进入主线的 cpuinfo.max_table_freq（本地 v7.0-34367 全树无该字段，base-commit 32b6ef9a5d0e 亦非本地已知对象），前置系列状态未在本批邮件中说明
  - patch 1 正文未送达本批缓存，schedutil 无法触达 boost 这半问题只能靠 cover 两句话论证
  - patch 1 把 capacity_freq_ref 永久播种为含 boost 的最大频率，与 09-07 Oleg Keri 系列「随 boost 状态刷新 ref」的思路相反，两个系列互不引用
  next_action: 作者下一版补全 patch 1 正文并说明 max_table_freq 前置依赖；等 cpufreq 维护者回应
contribution_opportunities:
- kind: review
  description: 确认 cpuinfo.max_table_freq 的来源系列与合入状态，并回贴询问前置语义若变化时 2/2 的 fallback 分支如何保持
- kind: discussion
  description: 把本系列的「capacity_freq_ref 一次播种为含 boost 最大值」与 09-07 Oleg Keri 系列的「policy_set_boost() 中刷新」做对照，验证 boost 关闭时 arch_scale_freq_ref() 是否与实际可用频率匹配
- kind: testing
  description: 在带 CPUFREQ_BOOST_FREQ 表项的 arm64 平台复测 scaling_max_freq 能否随 boost 关闭回落，并尝试触达「表内全为 boost 项」的退化分支
- kind: new_patch
  description: 核查自家 OLK 分支是否存在同一 boost 开关 + 频率表路径的问题，回合时 Fixes 需引用 OLK 自身的 commit
source_email_count: 3
related_articles: []
tags:
- cpufreq
- regression
---
