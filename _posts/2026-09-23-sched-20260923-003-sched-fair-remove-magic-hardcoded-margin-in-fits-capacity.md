---
id: sched-20260923-003
subject: 'sched/fair: Remove magic hardcoded margin in fits_capacity()'
date: '2026-09-23'
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: <20260504020003.71306-5-qyousef@layalina.io>
lore_url: https://lore.kernel.org/all/20260504020003.71306-5-qyousef@layalina.io/
authors:
- Qais Yousef
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <20260504020003.71306-5-qyousef@layalina.io>
  date: '2026-05-04'
  summary: capacity-aware 系列 04/13：fits_capacity() 改为 per-rq 阈值，移除 1280/1024 魔数 margin
  review_outcome: Zhan Xusheng/Chen Yu 指出新签名与 invalid_llc_nr() 静默错绑，建议拆 fits_llc_nr()
    helper
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - fits_capacity() 新签名与 invalid_llc_nr() 参数错绑需先拆解
  next_action: 作者 Qais Yousef 确认是否承接 fits_llc_nr() 拆分
contribution_opportunities:
- kind: review
  description: 核查新签名下是否还有其他非容量参数调用者被静默错绑
- kind: new_patch
  description: fits_llc_nr() helper 可作为独立修复 patch（Zhan 已给草稿）
generated_at: '2026-09-24T09:00:00'
source_email_count: 2
related_articles: []
tags:
- cfs
- load_balance
title: 'sched/fair: Remove magic hardcoded margin in fits_capacity()'
layout: article
---

## TL;DR
Qais Yousef 早期 capacity-aware 系列（v2 04/13）中的清理补丁——把 `fits_capacity()` 的魔数 margin（`cap*1280 < max*1024`）换成 per-rq 的 `fits_capacity_threshold`——在今日被 Zhan Xusheng 指出一个与主线交互的隐患：`fits_capacity()` 改了签名后，新合入的 `invalid_llc_nr()` 把「LLC 内 CPU 数」当容量传给新签名，会静默绑定到错误的 `@cpu` 参数。Zhan 提出拆出 `fits_llc_nr()` 独立 helper，Chen Yu 补充可用 `x*5 < y*4`（移位）更快。

## 背景与问题
原补丁（`<20260504020003.71306-5-qyousef@layalina.io>`，capacity-aware scheduling 系列 v2 04/13）把 `fits_capacity(cap, max)` 的硬编码 1280/1024 margin 替换为 `fits_capacity(unsigned long util, int cpu)`，用 per-rq 的 `fits_capacity_threshold` 判断。这是设计层面的清理：margin 不再是全局魔数，而是按 rq 维护。但今日讨论揭示，该改动与主线后续合入的 cache-aware scheduling（`CONFIG_SCHED_CACHE`）代码发生了签名冲突。

## 技术方案
Zhan Xusheng 指出：主线 `kernel/sched/fair.c` 的 `invalid_llc_nr()` 是 `fits_capacity()` 的第二个调用者，然而它第二个参数传的不是 capacity，而是 `scale * per_cpu(sd_llc_size, cpu)`（LLC 内 CPU 数的缩放计数）。`sd_llc_size` 是 per-CPU int、`scale` 是 int，乘积会无转换、无告警地绑定到新签名 `int cpu`，测试退化为 `cpu_rq(scale * sd_llc_size)->fits_capacity_threshold`——默认配置（`llc_aggr_tolerance=1`）下 `scale=1`，即 `cpu_rq(sd_llc_size)`，在单 LLC 机器上是非法 CPU id。

他提出把二者使用拆开：新增 `fits_llc_nr(nr_threads, nr_cpus)` helper 专用于「线程数 vs LLC 内 CPU 数」的比较（默认约 80% 阈值、镜像 fits_capacity 的 ~20% margin），`invalid_llc_nr()` 改调它。并给出对 `tip/sched/urgent`（`3cb0243767fd`）的补丁：`nr_threads * 100 < (u64)nr_cpus * 80`，与旧式 `x*1280 < y*1024` 等价（无功能变化），`CONFIG_SCHED_CACHE=y`/`=n` 均编译通过无告警，可作独立 patch 单发。

Chen Yu 进一步建议把这步换成 `x * 5 < y * 4`，因为 `y * 4` 是左移，更快。

## 版本演进与当前进展
- 原 patch（v2 04/13，2026-05-04）不在本次分析窗口内，今日为其久置后的新一轮评审讨论；无新版发出。

## Maintainer 意见与讨论焦点
本日参与者为 Zhan Xusheng 与 Chen Yu（均非该 patch 作者，作者 Qais Yousef 未在本日出现），无维护者表态。讨论焦点集中在 `fits_capacity()` 新签名与 `invalid_llc_nr()` 的静默参数错绑这一正确性隐患，以及 `fits_llc_nr()` helper 的常数优化（乘 100/80 vs 乘 5/4 移位）。无争议、无 NAK。

## 合入评估
*likelihood=unknown*。原 patch 属大型 capacity-aware 系列（13 枚）的组成部分，今日讨论只是其与主线 cache-aware 代码交互的一个侧面问题，作者尚未回应，也无维护者涉入。*blocking_issues*：`fits_capacity()` 新签名与 `invalid_llc_nr()` 的参数错绑需先拆解（独立 `fits_llc_nr()` 或其它方式），否则 04/13 无法安全应用。*next_action*：Zhan/Chen 的意见需作者 Qais Yousef 确认承接（拆 helper 或并入系列拆分）。

## 效果评估
无性能数据。`fits_llc_nr()` 建议被明确标注为「no functional change」（`x*1280 < y*1024` 等价于 `x*100 < y*80`，进而等价于 `x*5 < y*4`），属正确性拆分而非性能优化；Chen Yu 的移位建议仅为更快的常数运算。

## 我可以参与的点
- kind=review：核查 `fits_capacity()` 新签名下是否还有除 `invalid_llc_nr()` 之外的第二处「非容量参数」调用者被静默错绑。
- kind=new_patch：若作者不承接，`fits_llc_nr()` helper 本身可作为独立修复 patch 提交（Zhan 已给出可编译的草稿）。

## 参考链接
- lore（Zhan Xusheng 回复）: https://lore.kernel.org/all/20260923065407.3451520-1-zhanxusheng@xiaomi.com/
- lore（原 patch v2 04/13，May）: https://lore.kernel.org/all/20260504020003.71306-5-qyousef@layalina.io/
