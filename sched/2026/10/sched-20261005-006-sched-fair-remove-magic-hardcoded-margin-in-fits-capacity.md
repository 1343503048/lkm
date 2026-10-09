# sched/fair: Remove magic hardcoded margin in fits_capacity()

> **subject**：`sched/fair: Remove magic hardcoded margin in fits_capacity()`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260923-003：Qais Yousef capacity-aware 系列 v2 04/13（把 `fits_capacity()` 的 1280/1024 魔数 margin 换成 per-rq 阈值）被 Zhan Xusheng 指出与主线交互的隐患：新签名下 `invalid_llc_nr()` 把「LLC 内 CPU 数」当容量传参、静默绑定到错误的 `@cpu`；Zhan 提出拆 `fits_llc_nr()` 独立 helper（`nr_threads * 100 < (u64)nr_cpus * 80`，与旧式 `x*1280 < y*1024` 等价），Chen Yu 建议改用 `x*5 < y*4`（移位更快）。
- sched-20261005-006（今天）：Zhan Xusheng 回复 Tim Chen，**采纳其乘法形式并给出完整的溢出论证**——`1280/256=5`、`1024/256=4`，`x*5 < y*4` 与旧比较严格等价（同 `x*100 < y*80`）；溢出不构成选型理由：左侧 `nr_running_avg` 是 u64、任一乘子都在 64 位求值，右侧 `get_sched_cache_scale()` 在 `llc_aggr_tolerance>=100` 时返回 INT_MAX 而 `invalid_llc_nr()` 对此提前 bail，故 `scale ≤ 99`、`scale * sd_llc_size * 1024` 两种写法都远离 INT_MAX。**发帖策略**：压后到 04/13 排队之后——在那之前该 helper 只是把一个整数比较挪出宏、不修任何东西。

## 背景与问题

（承接 sched-20260923-003）Qais Yousef 的 capacity-aware 系列 v2 04/13（2026-05-04）把 `fits_capacity(cap, max)` 的硬编码 1280/1024 margin 替换为 `fits_capacity(unsigned long util, int cpu)`（per-rq 的 `fits_capacity_threshold`）。主线后续合入的 cache-aware scheduling（`CONFIG_SCHED_CACHE`）里 `invalid_llc_nr()` 成为新签名的第二个调用者，但它传的第二个参数是 `scale * per_cpu(sd_llc_size, cpu)`（LLC 内 CPU 数的缩放计数）而非容量——int 乘积无告警地绑定到 `int cpu` 参数，测试退化为 `cpu_rq(scale * sd_llc_size)->fits_capacity_threshold`，默认配置下即非法 CPU id。修复方向：拆出 `fits_llc_nr(nr_threads, nr_cpus)` 专管「线程数 vs LLC 内 CPU 数」比较（默认约 80% 阈值，镜像 fits_capacity 的 ~20% margin）。今天的讨论把常数形式（乘 100/80 还是乘 5/4）与溢出安全性论证收尾。

## 技术方案

（承接）拆 `fits_llc_nr()` helper、`invalid_llc_nr()` 改调它，比较式与旧式严格等价。

今天的收尾论证（Zhan Xusheng，回复 Tim Chen `<ac8a6383-3a8d-4fcd-bad1-dbb8dd6cc742@intel.com>`）：

- **等价性**：`1280/256 = 5`、`1024/256 = 4`，故 `x * 5 < y * 4` 恰为旧比较 `x*1280 < y*1024`，同 `x*100 < y*80`——Tim Chen 建议的形式成立且是最小整数对。
- **溢出分析（排除选型顾虑）**：
  - 左侧：`nr_running_avg` 是 u64，无论乘 5 还是 100 都在 64 位求值——乘子大小不影响溢出。
  - 右侧：`get_sched_cache_scale()` 在 `llc_aggr_tolerance >= 100` 时返回 INT_MAX，而 `invalid_llc_nr()` 对该值提前 bail，所以实际 `scale ≤ 99`；`scale * sd_llc_size * 1024` 在两种乘法形式下都远低于 INT_MAX。
- **发帖策略**：将采用 Tim 的形式发帖，但**压后**——等 04/13（Qais 系列）排队之后；在此之前该 helper 只是把整数比较挪出 `fits_capacity()` 宏、不修复任何东西，单独发没有价值。

## 版本演进与当前进展

- 原 patch（v2 04/13，2026-05-04，Qais Yousef）：长期久置。
- 09-23：Zhan 指出 `invalid_llc_nr()` 参数错绑 + 拆 helper 提案；Chen Yu 建议移位形式（sched-20260923-003）。
- 10-05（今天）：Zhan 采纳 Tim Chen 的 `x*5 < y*4` 形式，附完整溢出论证；宣布发帖压后至 04/13 排队。无维护者表态。

## Maintainer 意见与讨论焦点

- **Tim Chen**（Intel，资深 sched 开发者）：此前提出 `1280/256=5、1024/256=4` 的最小乘法对（其邮件为本日回复的 In-Reply-To 目标，不在当日缓存）。
- **Zhan Xusheng**：接受形式 + 补齐溢出安全论证 + 明确发帖时机。
- **Chen Yu**（fair 侧维护者之一）：当日未再发言。
- **Qais Yousef**（04/13 作者）：持续缺席，系列命运仍是最大变量。
- 焦点已收敛：常数形式（`x*5 < y*4`）、溢出安全（两侧均无风险）、发帖时机（04/13 排队后）三点全部落定；剩余唯一不确定性是 Qais 系列本身是否继续推进。

## 合入评估

*likelihood=unknown*。讨论质量高但全部发生在评论者之间，系列作者 Qais Yousef 缺席、无维护者拍板；`fits_llc_nr()` 独立补丁的合入路径明确（`invalid_llc_nr()` 参数错绑是真实正确性问题），但被作者刻意压后。*blocking_issues*：Qais 的 13 补丁 capacity-aware 系列状态不明（5 月至今久置）；Zhan 的独立补丁等 04/13 排队。*next_action*：Qais 回归系列并排队 04/13 → Zhan 发 `fits_llc_nr()`（`x*5 < y*4` 形式）；或维护者直接采纳「先修 `invalid_llc_nr()` 错绑」的独立路径。

## 效果评估

无性能数据。`x*5 < y*4` 被明确论证为与旧式 `x*1280 < y*1024` **严格等价**（no functional change）；Chen Yu 的移位更快说法属常数运算优化。溢出论证为静态类型/取值域分析，无运行时验证。

## 我可以参与的点

- `review`：Zhan 发独立补丁时核对 `get_sched_cache_scale()` 返回 INT_MAX 的 bail 路径是否覆盖所有调用者（论证依赖「scale ≤ 99」在所有路径成立）。
- `discussion`：向 Qais Yousef 询问 v2 系列计划（是否重发/拆分）——整个 fits_capacity 讨论被其系列状态卡住，一个直接询问可能解锁后续。

## 参考链接

- Zhan Xusheng 回复（溢出论证）: https://lore.kernel.org/all/20261005141200.1392044-1-zhanxusheng@xiaomi.com/
- Zhan 首次指出错绑（09-23）: https://lore.kernel.org/all/20260923065407.3451520-1-zhanxusheng@xiaomi.com/
- 原 patch v2 04/13（May）: https://lore.kernel.org/all/20260504020003.71306-5-qyousef@layalina.io/

---
id: sched-20261005-006
date: '2026-10-05'
subject: 'sched/fair: Remove magic hardcoded margin in fits_capacity()'
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: '<20260504020003.71306-5-qyousef@layalina.io>'
lore_url: 'https://lore.kernel.org/all/20261005141200.1392044-1-zhanxusheng@xiaomi.com/'
authors:
  - 'Qais Yousef'
maintainers_involved:
  - 'Tim Chen'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260504020003.71306-5-qyousef@layalina.io>'
    date: '2026-05-04'
    summary: 'capacity-aware 系列 04/13：fits_capacity() 改为 per-rq 阈值'
    review_outcome: '10-05 Zhan 采纳 Tim Chen 的 x*5<y*4 形式并附溢出论证；独立补丁压后至 04/13 排队'
related_articles:
  - sched-20260923-003
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: 'Qais 系列 5 月至今久置、作者缺席；Zhan 补丁等 04/13 排队'
  next_action: 'Qais 回归系列后 Zhan 发 fits_llc_nr() 独立补丁'
generated_at: '2026-10-06T01:00:00'
---
