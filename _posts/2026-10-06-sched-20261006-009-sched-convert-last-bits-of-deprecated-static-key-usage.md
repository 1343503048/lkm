---
id: sched-20261006-009
date: '2026-10-06'
subject: 'sched: Convert last bits of deprecated static key usage'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <20260903115728.11864-1-hongyan.xia@transsion.com>
lore_url: https://lore.kernel.org/all/20260903115728.11864-1-hongyan.xia@transsion.com/
authors:
- Hongyan Xia
maintainers_involved:
- Valentin Schneider
current_version: v2
patch_series:
- version: v2
  msgid: <20260903115728.11864-1-hongyan.xia@transsion.com>
  date: '2026-09-03'
  summary: fair.c CFS bandwidth 与 core.c PREEMPT_DYNAMIC 宏迁到 static_branch_* 新 API，+8/-8，无功能变化
  review_outcome: 10-06 Valentin Schneider 给出 Reviewed-by，并建议树级 coccinelle 清理残留 static_key()
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - core.c 部分与 PREEMPT_DYNAMIC 精简系列争用同一区域，落地顺序待协调
  next_action: 等 maintainer 收入 tip；作者视情况发 v3 处理 changelog nit
generated_at: '2026-10-07T01:00:00'
contribution_opportunities:
- kind: new_patch
  detail: 发起树级 coccinelle 系列清理 sched 外残留 static_key_true/false()（Valentin 点名）
- kind: testing
  detail: 补上编译产物零差异的实测对比
source_email_count: 2
related_articles:
- sched-20260903-007
tags:
- cfs
- preempt
title: 'sched: Convert last bits of deprecated static key usage'
layout: article
---

> **subject**：`sched: Convert last bits of deprecated static key usage`
> 本文为增量更新，完整脉络见下。

## TL;DR

- <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-007-sched-convert-last-bits-of-deprecated-static-key-usage.html">sched-20260903-007</a>：Hongyan Xia 收掉调度器里最后一批已废弃的 static key 用法：`kernel/sched/fair.c` 的 CFS bandwidth `__cfs_bandwidth_used` 从 `struct static_key` + `static_key_false()` / `static_key_slow_inc_cpuslocked()` 迁到 `DEFINE_STATIC_KEY_FALSE()` + `static_branch_unlikely()` / `static_branch_inc_cpuslocked()`；`kernel/sched/core.c` 的 PREEMPT_DYNAMIC 更新宏也一并改用 `static_branch_enable/disable()`。作者称完成后调度器内废弃 static key API 归零。当日为 v2（rebase 并修掉 core.c 大冲突），无回帖。
- <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-009-sched-convert-last-bits-of-deprecated-static-key-usage.html">sched-20261006-009</a>（今天）：Valentin Schneider（SCHEDULER 子系统 reviewer）给出 **Reviewed-by**，并顺带厘清了旧写法的语义——由于静态存储零初始化，旧的 `struct static_key` 定义实际上等价于 `STATIC_KEY_INIT_FALSE`，所以 `DEFINE_STATIC_KEY_FALSE` 是忠实转换；`static_key_*()` 命名体系里 false == unlikely。他认为全是 `#define` 魔法、编译产物应当零差异（未实测）。随后追加一条：内核里其它子系统仍散落着 `static_key()` 用法，**值得用一个 coccinelle 驱动的单一系列统一收掉**——这是一个被 reviewer 点名的参与机会。

## 背景与问题

raw static key 不带类型信息，无法防止误配（例如对默认为 TRUE 的 key 使用 `static_key_false()`），而且 `static_key_{true/false}()` 这组命名本身有歧义，因此被废弃。调度器内的多数站点已在此前的补丁中转换，本补丁处理剩下的两处，其中 `sk_dynamic_*` 使用的 `static_key_{enable/disable}()` 严格说并未废弃，作者只是顺带统一到新 API。

今日增量：Valentin 在评审中坦承「likely/unlikely/true/false 的 static key 混乱」是这套 API 的老毛病——旧的裸 `struct static_key` 靠静态存储零初始化隐式得到 FALSE 默认值，语义全靠读者自己推导；迁移到 `DEFINE_STATIC_KEY_FALSE()` 后默认方向显式化，这正是本系列要消灭的歧义来源。

## 技术方案

- `kernel/sched/fair.c`（`CONFIG_CFS_BANDWIDTH` + `CONFIG_JUMP_LABEL` 分支）：`static struct static_key __cfs_bandwidth_used` -> `DEFINE_STATIC_KEY_FALSE(__cfs_bandwidth_used)`；`static_key_false()` -> `static_branch_unlikely()`；`static_key_slow_inc_cpuslocked()` / `static_key_slow_dec_cpuslocked()` -> `static_branch_inc_cpuslocked()` / `static_branch_dec_cpuslocked()`。
- `kernel/sched/core.c`（PREEMPT_DYNAMIC）：宏 `preempt_dynamic_key_enable(f)` / `preempt_dynamic_key_disable(f)` 改名为 `preempt_dynamic_branch_enable(f)` / `preempt_dynamic_branch_disable(f)`，实现从 `static_key_enable(&sk_dynamic_##f.key)` 改为 `static_branch_enable(&sk_dynamic_##f)`，调用点在 `__sched_dynamic_update()` 的 full/lazy 分支。
- 总计 8 增 8 删，作者声明 "No functional change"。

今日增量（Valentin 的语义核验）：

1. 旧定义 `static struct static_key __cfs_bandwidth_used` 因为静态存储初始化，实际上就是 `= STATIC_KEY_INIT_FALSE`——所以换 `DEFINE_STATIC_KEY_FALSE()` 不改变默认方向，转换忠实。
2. `static_key_*()` 命名体系里 **false == unlikely**，与 `static_branch_unlikely()` 对应，两端语义一致。
3. 编译产物预期零差异（「it's all #define magic」），但 Valentin 声明未验证（笔记本省电模式）。

## 版本演进与当前进展

- v1：不在缓存中（仅见于 v2 changelog 自述）。
- v2（09-03 19:57）：补充说明旧 API 为何被废弃；rebase 并修掉 `core.c` 的一个大冲突（与 <a class="article-ref" href="/lkm/2026/09/03/sched-20260903-013-sched-dynamic-simplify-preempt-dynamic.html">sched-20260903-013</a> PREEMPT_DYNAMIC 精简系列同抢 `__sched_dynamic_update()` 区域）。
- 10-06：Valentin Schneider 给出 Reviewed-by（附 changelog 措辞 nit），随后追加树级清理建议。**尚无 v3，未进任何分支。**

## Maintainer 意见与讨论焦点

Valentin Schneider 10-06 回帖两封：

1. **R-b 邮件**：确认转换语义忠实（旧定义因静态存储初始化等价于 `STATIC_KEY_INIT_FALSE`；`static_key_*()` 命名里 false == unlikely），预计编译产物零差异但未实测（笔记本省电模式没跑编译对比）。除一处 changelog 理解/措辞 nit 外整体放行。
2. **后续邮件**：「A quick search tells me there's still some static_key() usage spread through the kernel, that really should be fixed in a single series powered by coccinelle or somesuch.」——明确指出 sched 之外的残留 `static_key()` 应该用一个 coccinelle 驱动的单一系列统一清理，而不是零散补丁。

无分歧、无 NAK；焦点从「这枚补丁对不对」转向「树级清理怎么组织」。

## 合入评估

*likelihood=high*（从 medium 上调）。

- 上调依据：拿到 Valentin Schneider（SCHEDULER 子系统 reviewer）的 Reviewed-by；纯清理、声明无功能变化、8 行改动，是既有迁移序列的收尾。
- 残留风险：`core.c` 半部分与 Mark Rutland 的 PREEMPT_DYNAMIC 精简系列（<a class="article-ref" href="/lkm/2026/09/03/sched-20260903-013-sched-dynamic-simplify-preempt-dynamic.html">sched-20260903-013</a>）仍争用同一代码区域，最终形态取决于两者落地顺序，可能合入前还要再 rebase 一次；changelog nit 也可能催生 v3。
- *blocking_issues*：与 PREEMPT_DYNAMIC 精简系列的落地顺序协调。
- *next_action*：等 maintainer 收进 tip；作者视情况发 v3 处理 changelog nit。

## 效果评估

补丁声明 "No functional change"，Valentin 从 `#define` 展开推断编译产物零差异，但**未实测**（其原话：笔记本省电模式，没动力跑对比）——这一断言仍属「推断，未见数据」。可核实收益：调度器代码内废弃 static key API 归零（作者原话），`fair.c` 侧默认方向由 `DEFINE_STATIC_KEY_FALSE` 显式表达。

## 我可以参与的点

1. `new_patch`（Valentin 点名的机会）：发起**树级 coccinelle 系列**，统一收掉 sched 之外残留的 `static_key_true/false()` 用法。reviewer 明确说 "should be fixed in a single series powered by coccinelle"——这是被点名的空白，先跑 `grep -r 'static_key_true\|static_key_false'` 摸清存量，写 coccinelle 脚本 + 按子系统分 patch，容易被接受。
2. `testing`：补上 Valentin 没做的编译产物对比（`DEFINE_STATIC_KEY_FALSE` 前后 objdump diff），验证「零差异」推断。
3. 回合视角：OLK-6.6 里若 6.6 的 `cpufreq_schedutil`/`fair.c` 仍用旧 API，`fair.c` 半部分（CFS bandwidth）可独立回合；`core.c` 的 PREEMPT_DYNAMIC 宏在 6.6 形态不同，需手工适配。

## 参考链接

- lore（v2 补丁）: https://lore.kernel.org/all/20260903115728.11864-1-hongyan.xia@transsion.com/
- lore（Valentin 的 R-b）: https://lore.kernel.org/all/xhsmhh5izyufq.mognet@vschneid-thinkpadt14sgen2i.remote.csb/
- lore（Valentin 的 coccinelle 建议）: https://lore.kernel.org/all/xhsmhece3ytx9.mognet@vschneid-thinkpadt14sgen2i.remote.csb/
- 相关文章：<a class="article-ref" href="/lkm/2026/09/03/sched-20260903-007-sched-convert-last-bits-of-deprecated-static-key-usage.html">sched-20260903-007</a>（v2 首发）、<a class="article-ref" href="/lkm/2026/09/03/sched-20260903-013-sched-dynamic-simplify-preempt-dynamic.html">sched-20260903-013</a>（同区域并行的 PREEMPT_DYNAMIC 精简系列）
