---
id: sched-20260911-015
subject: 'sched/fair: avoid recalculating curr status in place_entity() and requeue_delayed_entity()'
date: '2026-09-11'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260824125223.508178-1-kayracizmeci@gmail.com>
lore_url: https://lore.kernel.org/all/60fd4fc5d17b706766a428b63760d1f69e6d11bb.1787737648.git.kayracizmeci@gmail.com/
authors:
- Kayra Cizmeci
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
current_version: v2
patch_series:
- version: v1
  msgid: <20260824125223.508178-1-kayracizmeci@gmail.com>
  date: 2026-08-24
  summary: 2 补丁系列：减少 place_entity()/requeue_delayed_entity() 的 curr 状态重复计算。
  review_outcome: 发出后无人回复。
- version: v2
  msgid: <60fd4fc5d17b706766a428b63760d1f69e6d11bb.1787737648.git.kayracizmeci@gmail.com>
  date: 2026-08-25
  summary: 继续 curr 状态下沉方向（2/2 正文未入缓存）。
  review_outcome: 09-11 ping 后：Vincent 否定（可读性+无收益）；PeterZ 判定 curr==se 不可达、整补丁为 no-op，给出删除死代码的
    diff；作者接受并承诺 v3。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v3（删除死代码版）未发出
  - curr == se 不可达的论证需在 v3 中闭环（测试证据/入口核查）
  next_action: 作者发 v3 删除 curr 分支并附断言测试结果
contribution_opportunities:
- kind: testing
  description: core-sched 等异常 enqueue 路径下长跑 WARN_ON_ONCE(cfs_rq->curr == se) 验证不可达
- kind: review
  description: v3 发出后核对删除完整性与 enqueue_hierarchy 后的新路径
generated_at: '2026-09-14T11:35:00'
source_email_count: 5
related_articles: []
tags:
- cfs
- eevdf
title: 'sched/fair: avoid recalculating curr status in place_entity() and requeue_delayed_entity()'
layout: article
---

## TL;DR
Kayra Cizmeci 的系列（让 place_entity()/requeue_delayed_entity() 不必重复计算 curr 状态）在 ping 后当日获得两位维护者表态：Vincent 认为「降低可读性且无可测收益」，Peter Zijlstra 则给出更彻底的判断——curr == se 分支根本不可达，整补丁等价于 no-op，不如把死代码整个删掉；作者当场接受 PeterZ 方向并承诺发 v3。本文为增量更新，v1 背景承前（v1 cover 08-24 发出，未见于此前日报）。

## 背景与问题
enqueue_task_fair() 里 `curr = (cfs_rq->curr == se)` 为真时走 place_entity(cfs_rq, se, flags) 的独立分支，否则走 reweight_eevdf + place_entity(ENQUEUE_QUEUED) + __enqueue_entity() 的常规路径。作者认为该判定可下沉/简化，减少 place_entity() 与 requeue_delayed_entity() 中重复的 curr 状态计算（少一次 avg_vruntime_weight()）。系列共 2 补丁，本文讨论聚焦 2/2。

## 技术方案
- 作者 v2 思路：调整 curr 状态的传递方式，避免重复计算（v2 2/2 正文未入缓存，效果为每次 enqueue 少一次 avg_vruntime_weight()）；
- PeterZ 的替代方案：引用自己 08-13 的论证（patch.msgid.link/20260813103155.GC1246887），指出 `cfs_rq->curr == se` 在 enqueue 时不可能为真——该分支是不可达死代码，正确做法是整个删掉（bool curr 变量、place_entity(curr) 调用、if (!curr) 包裹全部移除，-13/+3 行）；
- 作者验证：此前在 v1/v2 上做过 WARN_ON_ONCE 测试，该情况从未命中（自述测试量有限）；接受 PeterZ 方向，v3 将直接删除死代码。

## 版本演进与当前进展
current_version: v2（v1 cover msgid `<20260824125223.508178-1-kayracizmeci@gmail.com>`、v2 2/2 msgid `<60fd4fc5d17b706766a428b63760d1f69e6d11bb.1787737648.git.kayracizmeci@gmail.com>`，均 08-24 前后发出；当日入缓存 5 封均为讨论）。

- v1/v2（08-24 前后）：发出后无人回复，直至 09-11 作者 gentle ping；
- 09-11：Vincent 与 PeterZ 相继表态，作者接受 PeterZ 的删除方向，承诺「今天或明天发 v3」。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**："This makes the code less readable and I don't think it gives any measurable benefit"——对 v2 优化方向直接否定；
- **Peter Zijlstra**：认为 curr == se 不可达、v2 实质是 no-op，给出删除死代码的完整 diff（与其后 Kayra 独立投递的 dead-code 补丁完全一致，见 sched-20260911-020）；
- **作者**：接受 PeterZ 方向，v3 = 删除 curr 分支；Vincent 对「删除」本身的意见未发表（其否定的可读性论据针对的是 v2 的下沉方案）；
- 分歧焦点已从「怎么优化」转为「删多少」：PeterZ 主张全删，v3 形态待验证。

## 合入评估
likelihood=medium：PeterZ 给出了明确方向（删除不可达分支）且作者接受；但「分支不可达」的论证尚需 PeterZ 08-13 邮件的完整推理获得认可，v3 未发出。blocking_issues：v3 未投递；删除后 place_entity 的 curr 分支语义（注释里遗留的 "XXX comment on the curr thing"）如何处理未说明；需要确认 enqueue 路径确无 curr == se 的隐藏入口（如 core-sched/force 组合）。next_action：作者发 v3（删除死代码），附 WARN_ON_ONCE 断言版测试结果佐证不可达。

## 效果评估
作者自评收益为「1 次 avg_vruntime_weight() 的增减，不可测量」（"not measurable in any means"）；PeterZ 视整补丁为 no-op。无任何 benchmark 数字；效果评估应视为可忽略的性能影响 + 死代码清理。

## 我可以参与的点
- kind=testing：在带 core-sched/异常 enqueue 路径的配置下跑 WARN_ON_ONCE(cfs_rq->curr == se) 长测，为「不可达」论证提供作者之外的证据。
- kind=review：v3 发出后对照 PeterZ 的 diff 核对是否完整删除（含 curr 变量与 XXX 注释残留），并检查 enqueue_hierarchy() 引入后 enqueue 路径是否产生新的 curr == se 可能。

## 参考链接
- v1 cover：https://lore.kernel.org/all/20260824125223.508178-1-kayracizmeci@gmail.com/
- v2 2/2：https://lore.kernel.org/all/60fd4fc5d17b706766a428b63760d1f69e6d11bb.1787737648.git.kayracizmeci@gmail.com/
- 作者 ping：https://lore.kernel.org/all/20260911105704.1220164-1-kayracizmeci@gmail.com/
- PeterZ 的不可达论证与删除 diff：https://lore.kernel.org/all/20260911124256.GZ776954@noisy.programming.kicks-ass.net/
- PeterZ 引用的 08-13 论证：https://patch.msgid.link/20260813103155.GC1246887%40noisy.programming.kicks-ass.net
