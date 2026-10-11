# sched/eevdf: Fix vprot across reweighting

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261003-007：Kayra 发出重组后的独立补丁「Fix vprot across reweighting」——以她为作者、Christian 为 Co-developed-by。实现 `rel_vprot` 标志（类比 `rel_deadline`）：reweight dequeue 时把 `vprot` 减 `avruntime` 转为相对值并置 `se->rel_vprot`，re-enqueue 时再加回；区别是 `rel_vprot` 不依赖 `PLACE_REL_DEADLINE`（vprot 无重算机制、需携带）。自带「pin 两任务到同一 CPU、改 nice 3000 次、校验 weight×(vprot−vruntime) 不变性」的测试：Base 下 Normal 6002/6002、NRTP 53/53 全错，加补丁后 0/6003、0/55 全对。Kayra 注明与 Christian 原版差异很大，请其确认 trailer。
- sched-20261011-004（今天）：Christian Loehle 给出 `Tested-by`（「nice find」），但指出「我的 SOB 不应再保留」（Signed-off-by 应移除），并表示还要再细看这是否是最佳实现方式；Kayra 回复会连同 Co-developed-by 一起在 v2 移除 SOB。

## 背景与问题

（承接 sched-20261003-007）EEVDF 的 slice protection 是绝对 vruntime 边界。reweight（nice 变更/cgroup 权重变化）时 `reweight_eevdf()` 缩放存活 protection，但移动 vruntime 时「已过期」的 vprot 原样不动，旧 vprot 可重新复活（dead protection 变活、或存活 protection 大小无规律涨落），current 越过有更早 deadline 的 eligible 实体被保护性选中。此问题即 Christian v2 4/5 所修、也是 Kayra 9-30 反例的延续；`Fixes:` 同时指向 `80390ead2080`（"Separate se->vlag from se->vprot"）与 `bcd74b2ffdd0`（"Only set slice protection at pick time"）。今日无新代码，增量是 Christian 的 `Tested-by` 与其 SOB 移除意见。

## 技术方案

（承接 sched-20261003-007）单补丁（`include/linux/sched.h` +1、`kernel/sched/core.c` +1、`kernel/sched/fair.c` +25/−10）：

- `struct sched_entity` 新增 `unsigned char rel_vprot`（与 `rel_deadline` 并列，填入既有 hole）。
- `rescale_entity()` 的 `rel_vprot` 参数改为读 `se->rel_vprot` 成员（原来是函数参数传递）。
- `reweight_eevdf()`：dequeue 侧（`curr && protect_slice(se)`）把 `se->vprot -= avruntime` 同时置 `se->rel_vprot = 1`——protection 转为相对 avruntime 的量；re-enqueue 侧 `se->vprot += avruntime` 恢复绝对值（对称于 `rel_deadline`）。
- **与 rel_deadline 的关键差异**：`rel_vprot` 不依赖 `PLACE_REL_DEADLINE`——deadline 有 place 时的重算机制，vprot 没有，「So it gets carried」（相对态须跨 enqueue 携带）。

测试方法（作者自述，双嵌套 VM）：两任务 pin 同一 CPU，TA 的 nice 在 0/10 间切换 3000 次，在 `__dequeue_task()` 与 `enqueue_task_fair()` 两侧记录 weight 与 `rem = (s64)(se->vprot - se->vruntime)`，校验两侧 `weight×rem` 比值在 0.95–1.05 内。今日无新代码。

## 版本演进与当前进展

- v1（10-03，`<20261003114656.105721-1-kayracizmeci@gmail.com>`）：Christian v2 4/5 折入 Kayra 署名的独立补丁落地。
- 10-11：Christian 回帖给 `Tested-by`（「Ah nice find」），但表示「FWIW my SOB shouldn't be there anymore」（Signed-off-by 应移除）；Kayra 回复「会在 v2 连同 Co-developed-by 一起移除 SOB」。
- 待 Kayra 发 v2（移除 SOB 与 Co-developed-by trailer）；Christian 尚未最终确认实现是否为其认可的最佳方式。

## Maintainer 意见与讨论焦点

- **Christian Loehle**（Co-developed-by / 维护者）：给出 `Tested-by` 表示认可方向，但要求移除其 Signed-off-by（「my SOB shouldn't be there anymore」）；还需进一步确认实现是否为最佳方式（「allow me to look at this code for a bit」），尚未最终拍板。
- **Peter Zijlstra**：仍未表态（此前他对 v2 4/5 前身的反对已因系列解体消化）。

## 合入评估

*likelihood=medium*。问题真实（两作者独立验证）、Christian 已 `Tested-by`；但作者需发 v2 清理 trailer（移除 SOB/Co-developed-by），Peter 仍未 review。*blocking_issues*：v2 清理 trailer；Christian 确认实现方式；Peter review。*next_action*：Kayra 发 v2 移除 SOB/Co-developed-by，等 Christian 确认后交 Peter 收取。

## 效果评估

今日无新 benchmark。Christian 的 `Tested-by` 是对原作者自测（Base 下 Normal 6002/6002 错、NRTP 53/53 错 → 加补丁 0/6003、0/55 对）的认可，未见额外数字；「dead protection 复活」路径仍缺覆盖（作者此前自述未测）。

## 我可以参与的点

- `testing`：补「dead protection 复活」路径的测试——构造过期 protection 在 reweight 后复活的场景验证补丁，回帖补数据（作者此前明说未覆盖）。
- `review`：核对 `rel_vprot` 在 fork/exit/wake 路径是否需要清理（`__sched_fork()` 已初始化为 0，但 cgroup reweight 之外的路径可再核对）。

## 参考链接

- lore（本补丁 v1）: https://lore.kernel.org/all/20261003114656.105721-1-kayracizmeci@gmail.com/
- lore（Christian Tested-by，10-11）: https://lore.kernel.org/all/ed2c3c89-f556-4fad-b17b-cc08f2eab84a@arm.com/
- lore（Kayra 回复，10-11）: https://lore.kernel.org/all/20261011100637.60790-1-kayracizmeci@gmail.com/

---
id: sched-20261011-004
date: '2026-10-11'
subject: 'sched/eevdf: Fix vprot across reweighting'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20261003114656.105721-1-kayracizmeci@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20261003114656.105721-1-kayracizmeci@gmail.com/'
authors:
  - 'Kayra Cizmeci'
maintainers_involved:
  - 'Christian Loehle'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261003114656.105721-1-kayracizmeci@gmail.com>'
    date: '2026-10-03'
    summary: 'rel_vprot 标志：reweight 时 protection 转/恢复相对量（Christian 4/5 折入版）'
    review_outcome: '10-11 Christian 给 Tested-by，但要求移除其 SOB；待发 v2 清理 trailer'
upstream_commit: null
fixes_commit: '80390ead2080'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'v2 需清理 trailer（移除 SOB/Co-developed-by）'
    - 'Christian 尚未确认实现是否为最佳方式'
    - 'Peter 未表态'
  next_action: 'Kayra 发 v2 移除 SOB/Co-developed-by，等 Christian 确认后交 Peter 收取'
contribution_opportunities:
  - kind: testing
    description: '补 dead protection 复活路径测试（作者明说未覆盖）'
  - kind: review
    description: '核对 rel_vprot 在 fork/exit/wake 路径的清理完整性'
generated_at: '2026-10-12T01:00:00'
source_email_count: 2
related_articles:
  - sched-20261003-007
tags:
  - eevdf
---