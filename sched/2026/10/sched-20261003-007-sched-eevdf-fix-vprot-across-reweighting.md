# sched/eevdf: Fix vprot across reweighting

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260930-008：Christian Loehle 两枚 EEVDF slice-protection 边界修复——1/2 让每次新授予的 protection 无条件下限到最小 slice，2/2 保持「已过期的 protection」在 reweight 移动 vruntime 后仍是过期态；当日 Kayra 追问 2/2 的 reweight 路径反例。
- sched-20260930-009：Christian 单片 HRTICK 修复——fair hrtick 取「虚拟 deadline 与存活 protection」较早者。
- sched-20261001-001：两轮合并扩展为 5 补丁 v2「Keep slice protection boundaries consistent」，Peter 对 1/5 明确不喜欢、对 3/5 追问动机。
- sched-20261002-002：系列解体重组——Kayra 指出 4/5 依赖的 `(!curr)` 分支已被她 9 月的补丁从 tip 删除、且其 reweight 反例证明 4/5 所修问题真实；Christian 提议把 4/5 折进 Kayra 的修复由她署名重发（自加 Co-developed-by），1/5 与 3+5/5 放弃、2/5 独立重发。
- sched-20261003-007（今天）：**Kayra 发出重组后的独立补丁**「Fix vprot across reweighting」——按 10-02 约定以她为作者、Christian Co-developed-by。实现 `rel_vprot` 标志（类比 `rel_deadline`）：reweight dequeue 时若 current 有存活 protection 则把 vprot 减去 avruntime 转为相对值、置 `se->rel_vprot`，re-enqueue 时再加回；区别是 `rel_vprot` 不依赖 `PLACE_REL_DEADLINE`（vprot 无重算机制、需携带）。自带一套「pin 两任务到同一 CPU、改 nice 3000 次、校验 weight×(vprot−vruntime) 不变性」的测试：Base 下 Normal 6002/6002、NRTP 53/53 全错，加补丁后 0/6003、0/55 全对。Kayra 注明本版与 Christian 原版差异很大，trailer 系沿用 10-02 的 squash 约定，请 Christian 确认。

## 背景与问题

（承接 sched-20261002-002）EEVDF 的 slice protection 是绝对 vruntime 边界。reweight（nice 变更/cgroup 权重变化）时 `reweight_eevdf()` 缩放存活 protection 但移动 vruntime 时「已过期」的 vprot 原样不动，旧 vprot 可重新复活（dead protection 变活、或存活 protection 的大小无规律涨落），current 越过有更早 deadline 的 eligible 实体被保护性选中。此问题即 Christian v2 4/5 所修、也是 Kayra 9-30 反例的延续；`Fixes:` 同时指向 `80390ead2080`（"Separate se->vlag from se->vprot"）与 `bcd74b2ffdd0`（"Only set slice protection at pick time"）。

## 技术方案

单补丁（`include/linux/sched.h` +1、`kernel/sched/core.c` +1、`kernel/sched/fair.c` +25/−10，base tip/sched/core @ 4a3b51aab6e2）：

- `struct sched_entity` 新增 `unsigned char rel_vprot`（与 `rel_deadline` 并列，填入既有 hole）。
- `rescale_entity()` 的 `rel_vprot` 参数改为读 `se->rel_vprot` 成员（原来作为函数参数传递）。
- `reweight_eevdf()`：dequeue 侧（`curr && protect_slice(se)`）把 `se->vprot -= avruntime` 的同时置 `se->rel_vprot = 1`——protection 转为相对 avruntime 的量；re-enqueue 侧 `se->vprot += avruntime` 恢复为绝对值（对称于 `rel_deadline` 的处理）。
- **与 rel_deadline 的关键差异**：`rel_vprot` 不依赖 `PLACE_REL_DEADLINE`——deadline 有 place 时的重算机制，vprot 没有，「So it gets carried」（相对态必须跨 enqueue 携带）。
- 测试方法（作者自述，双嵌套 VM）：两任务 pin 同一 CPU，TA 的 nice 在 0/10 间切换 3000 次；在 `__dequeue_task()` 与 `enqueue_task_fair()` 两侧记录 weight 与 `rem = (s64)(se->vprot - se->vruntime)`，校验两侧 `weight×rem` 比值在 0.95-1.05 内。

## 版本演进与当前进展

- Christian v2 4/5（10-01）→ 10-02 决定折进 Kayra 的修复 → 本补丁（10-03，`<20261003114656.105721-1-kayracizmeci@gmail.com>`）为该约定的落地，Link 指向 Kayra 10-01 的相关补丁与 Christian 的折入邮件。
- 待 Christian 对「版本差异很大但保留 trailer」表态；无其他 review。

## Maintainer 意见与讨论焦点

- **Christian Loehle**（Co-developed-by）：10-02 提议折入的当事方，本版实现与他原版差异大，需其确认 trailer 保留是否合适（Kayra 已主动提出「If it is tho, please let me know」）。
- **Peter Zijlstra**：对前作 1/5 的反对已因系列解体消化；本补丁尚未见其表态。

## 合入评估

*likelihood=medium*。问题真实（两作者独立验证）、方向是双方约定、带双 `Fixes:`；但刚发出、Christian 需确认 squash 语义、Peter 未表态，且 base 是 tip 当日 HEAD（随 tip 漂移需重定基）。*blocking_issues*：Christian 确认 Co-developed-by 语义；Peter review。*next_action*：Christian 回复确认后等 Peter 收取。

## 效果评估

作者自测（双嵌套 VM，自嘲为「war crime」环境）：Base 下 Normal 场景 6002/6002 次不变性被破坏（最大漂移 4.49x 增 / 0.17x 减、平均 1.64x）、NRTP（no-run-to-parity）场景 53/53 全错（2.27x / 0.31x、平均 1.08x）；加补丁后 Normal 0/6003、NRTP 0/55 全对。覆盖「存活 protection 的 reweight 不变性」；「复活（revived）」路径作者自述未覆盖（「my computer ate that part」）——复活路径的验证是遗留缺口。

## 我可以参与的点

- `testing`：补「dead protection 复活」路径的测试（作者明说未覆盖）——构造过期 protection 在 reweight 后复活的场景验证补丁，回帖补数据。
- `review`：核对 `rel_vprot` 在 fork/exit/wake 路径是否需要清理（`__sched_fork()` 已初始化为 0，但 cgroup reweight 之外的路径可再核对）。

## 参考链接

- lore（本补丁）: https://lore.kernel.org/all/20261003114656.105721-1-kayracizmeci@gmail.com/
- lore（Kayra 10-01 相关补丁）: https://lore.kernel.org/all/20261001164609.244156-1-kayracizmeci@gmail.com/
- lore（Christian 折入邮件）: https://lore.kernel.org/all/e4700a93-ebd5-4c7e-88b5-d606437a13c0@arm.com/

---
id: sched-20261003-007
date: '2026-10-03'
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
    review_outcome: '待 Christian 确认 trailer；待 Peter review'
upstream_commit: null
fixes_commit: '80390ead2080'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'Christian 需确认 Co-developed-by squash 语义'
    - 'Peter 未表态'
  next_action: 'Christian 确认后等 Peter 收取'
contribution_opportunities:
  - kind: testing
    description: '补 dead protection 复活路径测试（作者明说未覆盖）'
  - kind: review
    description: '核对 rel_vprot 在 fork/exit/wake 等路径的清理完整性'
generated_at: '2026-10-04T01:00:00'
source_email_count: 1
related_articles:
  - sched-20260930-008
  - sched-20260930-009
  - sched-20261001-001
  - sched-20261002-002
tags:
  - eevdf
  - fair
---
