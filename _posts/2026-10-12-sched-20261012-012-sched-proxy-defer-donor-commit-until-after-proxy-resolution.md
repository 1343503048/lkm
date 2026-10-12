---
id: sched-20261012-012
date: '2026-10-12'
subject: 'sched/proxy: Defer donor commit until after proxy resolution'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260827-sched-proxy-v3-1-1af63ac5ae56@zohomail.com>
lore_url: https://lore.kernel.org/all/20260827-sched-proxy-v3-1-1af63ac5ae56@zohomail.com/
authors:
- Xukai Wang
maintainers_involved:
- K Prateek Nayak
current_version: v3
patch_series:
- version: v3
  msgid: <20260827-sched-proxy-v3-1-1af63ac5ae56@zohomail.com>
  date: '2026-08-27'
  summary: 把 donor commit 推迟到 proxy 解析完成后
  review_outcome: Prateek 建议把 dl_server 复位放进 proxy_resched_idle()，作者吸收并重基到 tip + Andrea
    的 scx proxy 改动
merge_assessment:
  likelihood: low
  blocking_issues:
  - Prateek 直言可见收益不大（8ms 量级），复杂度 vs 收益存疑
  - Peter 偏好把 sched_proxy 逻辑集中在一处，需其与 John 表态
  next_action: 作者已按 Prateek 意见移除 save/clear/restore，等 Peter/John 对复杂度表态后发 v4
contribution_opportunities:
- kind: review
  description: 评估 rq->donor 保持「已提交调度上下文」这一不变量与 scx do_pick_task_scx 的 retry 语义是否自洽
generated_at: '2026-10-13T01:40:00'
source_email_count: 4
related_articles:
- sched-20261010-005
tags:
- proxy_execution
title: 'sched/proxy: Defer donor commit until after proxy resolution'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-005-sched-proxy-defer-donor-commit-until-after-proxy-resolution.html">sched-20261010-005</a>（及更早 20260810/20260827）：Xukai Wang 的 RFC v3「sched/proxy: Defer donor commit until after proxy resolution」——把 donor 的 commit 推迟到 proxy 解析完成后，避免中途状态被负载均衡/统计看到。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-012-sched-proxy-defer-donor-commit-until-after-proxy-resolution.html">sched-20261012-012</a>（今天）：Prateek 表示「唯一关注是重基到 tip + 处理 scx 改动」，并质疑 v3 里 dl_server 的 save/clear/restore；Xukai 接受建议，移除 save/clear/restore、改在 `proxy_resched_idle()` 里复位 `rq->dl_server`，重基到 tip + Andrea 的 sched_ext proxy-exec 改动后详述 retry 语义，等 Peter/John 表态后发 v4。

## 背景与问题

（承接 20261010-005）proxy execution 下 `__schedule()` 现在的顺序是「先 commit donor/调度类状态、再解析 proxy 链（可能失败/迁移而 retry）」。作者想改为「先 pick、再解析 proxy、最后 commit」，让 `rq->donor` 始终描述「已通过 proxy 解析存活下来的调度上下文」，而非「可能被丢弃的临时候选」。

## 技术方案

（承接 20261010-005）今日收敛：作者按 Prateek 建议删掉 v3 里围绕 `find_proxy_task()` 的 save/clear/restore，改为在 `proxy_resched_idle()` 内先 `rq->dl_server = NULL` 再 commit idle——成功解析路径保持不变，NULL retry 由下一次 `pick_next_task()` 重算 `rq->dl_server`。作者把改动重基到最新 tip 并叠加 Andrea 的 sched_ext proxy-exec 改动（curr/donor 拆分），给出调整后的 `__schedule()` 骨架与 `do_pick_task_scx()` 的 retry 序列分析：deferred 顺序下 retry 从「committed A + queued D」重新走到本地 DSQ 选 D（`SCX_DSP_LOCAL`），而不改候选；并澄清主收益是「调度状态语义」而非性能（自测端到端性能影响确实很小）。

## 版本演进与当前进展

v3（08-27）→ 今日（10-12）吸收 Prateek 意见移除 save/clear/restore、重基 tip + scx；作者明说等 Peter/John 表态再发 v4。

## Maintainer 意见与讨论焦点

- **K Prateek Nayak**：无实质反对，但认为 `proxy_resched_idle()` 是复位 dl_server 更集中的位置；提醒 8ms 量级开销在真实负载里未必可见（尤其 SCHED_PROXY_EXEC 收益更大）；并转述 Peter 此前偏好「把 sched_proxy 相关位集中在一处」，请 John/Peter/Andrea 继续评论。
- **Xukai Wang**：采纳 Prateek 意见；论证 deferred 顺序不引入额外 sched_ext 复杂度。

## 合入评估

*likelihood=low*。RFC 阶段、可见收益小（作者自认）、复杂度高，且需 Peter/John 拍板。*blocking_issues*：收益 vs 复杂度、Peter 的架构偏好未定。*next_action*：等 Peter/John 表态，若认可再发 v4。

## 效果评估

作者自述「端到端性能影响实测很小」（未见具体数字），主卖点是调度状态语义而非性能；Prateek 也认为 8ms 开销在真实负载不显著。属主观判断，未见对比数据。

## 我可以参与的点

- `review`：核对 `rq->donor` 在 deferred 顺序下「描述已提交上下文」这一不变量，在 `find_proxy_task()` 停用/迁移候选、SCX 掉 rq 锁等分支上是否始终成立。

## 参考链接

- lore（v3）: https://lore.kernel.org/all/20260827-sched-proxy-v3-1-1af63ac5ae56@zohomail.com/
- lore（Prateek 意见）: https://lore.kernel.org/all/832e9395-49e9-40dd-a4db-1c1bf9753100@amd.com/
- lore（Xukai 采纳并重基）: https://lore.kernel.org/all/ab001a53-e2d2-42e9-ba40-8b43a71a7d64@zohomail.com/
