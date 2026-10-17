---
id: sched-20261017-008
subject: 'sched_ext: Keep proxy donors local through core-sched retries'
date: 2026-10-17
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261015101935.2844323-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20261015101935.2844323-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261015101935.2844323-1-arighi@nvidia.com>
  date: 2026-10-15
  summary: cookie 匹配才算 proxy put + SCX_TASK_DSQ_PROXY_IDLE 标记 + rq_is_open() 识别
  review_outcome: Tejun 指出 Fixes 错误、标记冗余、cookie 测试不足，建议 pick_again 处清 PROXY_PENDING
    并改标题
upstream_commit: null
fixes_commit: 67d0d8d018f3
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Fixes 标签指向不存在的 commit；SCX_TASK_DSQ_PROXY_IDLE 冗余与 cookie 测试不足需改实现；标题待调
  next_action: Andrea 按 Tejun 意见修正 Fixes、评估移除标记、在 pick_again 处清 SCX_RQ_PROXY_PENDING
    后出 v2
contribution_opportunities:
- kind: review
  description: 审视 donor idle 只看队首 cookie 的等价性与 pick_again 清 PROXY_PENDING 新 hook 的插入点
- kind: testing
  description: 复现未打 tag core-wide max + CFS 带宽控制解限时序，验证 cookie 测试不足与 v2 清理方案
generated_at: '2026-10-18T01:24:00'
source_email_count: 1
related_articles:
- sched-20261015-010
tags:
- sched_ext
- proxy_execution
title: 'sched_ext: Keep proxy donors local through core-sched retries'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-010-sched-ext-keep-proxy-donors-local-through-core-sched-retries.html">sched-20261015-010</a>：Andrea Righi 为 `sched_ext/for-7.4` 发修复——要求 donor 的 cookie 匹配才算 proxy put、引入 `SCX_TASK_DSQ_PROXY_IDLE` 标记、并让 `rq_is_open()` 识别该标记，避免 `SCX_RQ_PROXY_PENDING` 残留或 IMMED donor 被误送回 BPF。
- <a class="article-ref" href="/lkm/2026/10/17/sched-20261017-008-sched-ext-keep-proxy-donors-local-through-core-sched-retries.html">sched-20261017-008</a>（今天）：Tejun Heo 给出 review（Claude 生成式审阅，未复现、纯读码）——指出 `Fixes:` 标签的 commit `7ab553756463` 不存在（父提交实为 `67d0d8d018f3`）；`SCX_TASK_DSQ_PROXY_IDLE` 标记可能多余（donor idle 时只看队首 cookie 即可覆盖两种场景）；且未打 tag 的 core-wide max 下 forced idle 也可能 cookie 匹配、故 cookie 测试不足以判 proxy put；并建议改标题。

## 背景与问题
（承接 20261015-010）原补丁要修两条 core-sched/proxy 边界：① abandoned blocked-donor pick 让 `SCX_RQ_PROXY_PENDING` 残留、被 `put_prev_task_scx()` 误当 proxy put；② 有效的 IMMED 记账 put 触发本地 reenqueue scan，在 scan 前被唤醒的 SCX 任务使 `rq_is_open()` 判 closed，把「其实在本地 DSQ 队首」的 donor 送回 BPF。Tejun 今日 review 进一步收紧问题边界：③ 未打 tag 的 core-wide max 下，`core_cookie == 0`，`pick_next_task()` 强制不匹配 rq idle 而不调用 `sched_core_find()`，因此 **cookie 匹配的 donor 仍可能经历 forced idle**（给出 CFS 带宽控制 + tagged fair 任务解限的具体 5 步时序）——原补丁用 `sched_cpu_cookie_match()` 过滤 proxy put 并不充分。

## 技术方案
（承接 20261015-010）今日无新补丁，Tejun 给出三点修改建议：
1. `Fixes:` 标签错误：`7ab553756463` 不存在，父提交在 `sched_ext/for-7.4` 落地为 `67d0d8d018f3`。
2. `SCX_TASK_DSQ_PROXY_IDLE` 标记（及其 set/clear）可能整个不需要：donor idle 且 `next_class` 为 ext 时，下一次 pick 无论任务怎么进队都取本地 DSQ 队首，非 proxy 的 IMMED 任务今天也触发同样的误 reenq；donor idle 时只看队首的 cookie 就能同时覆盖 proxy 与非 proxy 两种情况。
3. cookie 测试不足：应在 `find_proxy_task()` 放弃 pick（pick_again）处清掉 `SCX_RQ_PROXY_PENDING`，使标志不会 stale，从而不再需要 cookie 测试；该处没有现成 hook，需新加一个小的 hook。
另建议改标题——复现的 bug 是「proxy idle 期间的 SCX wakeup」而非「core-sched retry」（后者读起来像 `SCX_RQ_PROXY_RETRY`）。

## 版本演进与当前进展
新补丁（`<20261015101935.2844323-1-arighi@nvidia.com>`，对已 applied v4 的 follow-up）→ 今天 Tejun review 指出 Fixes 错误 + 标记冗余 + cookie 测试不足 + 标题建议。尚无 v2。

## Maintainer 意见与讨论焦点
Tejun Heo（sched_ext 维护者，发现问题方）的意见集中在实现精度上，方向未否定：修正 Fixes 引用、评估移除 `SCX_TASK_DSQ_PROXY_IDLE`、把「清 `SCX_RQ_PROXY_PENDING`」移到 pick_again 的 abandon 处（替代 cookie 测试）、调整标题。无 NAK，属例行 follow-up 的收紧评审。

## 合入评估
*likelihood=medium*。方向正确（修的是维护者自己 review 出的缺陷），但 review 提出了需要 respin 的实质结构改动。*blocking_issues*：Fixes 标签指向不存在的 commit；标记冗余与 cookie 测试不足需作者回应并改实现；标题待调。*next_action*：Andrea 按 Tejun 意见修正 Fixes、论证/移除 `SCX_TASK_DSQ_PROXY_IDLE`、在 pick_again 处清 `SCX_RQ_PROXY_PENDING` 后出 v2。

## 效果评估
今日 Tejun 明确「一切来自读码、无复现」。作者在前一日（20261015-010）的基线数据（2000 次 mutex 中 174 次 blocked IMMED 误送回，修复后归零）仍有效。今日无新增数据。

## 我可以参与的点
- *review*：审视「donor idle 时只看队首 cookie 即可覆盖 proxy 与非 proxy IMMED 两种误 reenq」的等价性，以及 pick_again 处清 `SCX_RQ_PROXY_PENDING` 新 hook 的插入点。
- *testing*：复现 Tejun 描述的「未打 tag core-wide max + CFS 带宽控制解限」时序，验证 cookie 测试确实不足、并验证 v2 的清理方案。

## 参考链接
- Tejun 今日 review：https://lore.kernel.org/all/f010daaee76c0fe812d0b86d341fab14@kernel.org/
- 原补丁：https://lore.kernel.org/all/20261015101935.2844323-1-arighi@nvidia.com/
- Tejun 前一日 review（问题出处）：https://lore.kernel.org/all/1548cc9309a6e0894e358262e0b3d4ee@kernel.org/
