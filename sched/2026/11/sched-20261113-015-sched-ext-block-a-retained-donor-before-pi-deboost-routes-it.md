# sched_ext: Block a retained donor before PI deboost routes it back to sched_ext

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20261112-001：Tao Cui 发两补丁修复 sched_ext 在 core.c 的「进入路径契约」破坏——fork 路径 `wake_up_new_task()` 不带 `ENQUEUE_RQ_SELECTED` 致 fork 侧 fallback 永不计数；`rt_mutex_setprio()` 是唯一不先 `sched_proxy_block_task()` 就进入 sched_ext 的路径，PI deboost 会把 ext 任务以「queued+blocked」非法状态交回 BPF 调度器。Peter Zijlstra 对 patch 2 明确 NAK（"sprinkling magic hooks... So no"），认为真正该修的是 `__setscheduler_class()`。
- sched-20261113-015（今天）：**Peter 与 Andrea Righi 密集讨论替代方案**——Peter 提议让现有 `switching_to()` 回调返回 bool 表示类是否接受 blocked 任务（附 `sched_change_end()` 的示意 diff）；Andrea 同意该方向并主动接手测试 ext 边缘 case，同时指出 sub-scheduler 路径与 `update_rq_clock()`/`DEQUEUE_NOCLOCK` 的处理细节；**bpf-ci bot 列出三点疑虑**（double rq clock 更新触 WARN、changelog「唯一入口」说法不准、Peter 已否该 hook 是否仍坚持）。

## 背景与问题
（承接 20261112-001）proxy-exec 开发中暴露出：`rt_mutex_setprio()` 是唯一进入 sched_ext 却未先 `sched_proxy_block_task()` 的路径。一个被 rt waiter PI 提升的 ext 任务，被提升期间阻塞在第二个内核 mutex 上，deboost 时被路由回 sched_ext 并携带「queued+blocked」状态——正是 `scx_prepare_setscheduler()` 承诺绝不会发生的状态。今日收口在「用哪种泛化机制」而非打补丁到特定调用点。

## 技术方案
今日为设计讨论，两个方向：
- **Peter 方向**：让现有 `sched_class::switching_to()` 回调返回 bool（类是否愿意接受 blocked 任务），在 `sched_change_end()` 里若返回「需要 block」且 `p->is_blocked && ctx->queued` 则 `block_task()` 并清 `ctx->queued`；否则 `enqueue_task()`。附示意 diff，并认为「比其它 `__sched_setscheduler()` 的 magic hook 好」。
- **Andrea 方向（补充）**：即便 `switching_to()` 方向更好，仍需处理 sub-scheduler 路径（任务在 BPF 调度器间迁移时 `p->sched_class` 不变、`switching_to()` 不会跑），且 `block_task()` 在 `sched_change_begin()` 已 dequeue 之后会再次经新类 dequeue、重复通用 dequeue 记账；`p == rq->donor` 时清 `ctx->queued` 不够，还要 reset donor 并清 `ctx->running`；`scx_prepare_task_sched_change()` 里的 `update_rq_clock()` 移除后需放弃 `DEQUEUE_NOCLOCK` 让 `sched_change_begin()` 更新时钟。
- **Peter 补充**：顺带指出若 sub-scheduler proxy 支持不一致会很麻烦，建议强制执行 primary scheduler 的 proxy 立场（load sub-sched 时校验，或取所有 sub-sched 支持的逻辑与）。

## 版本演进与当前进展
v1（20261112，patch 2 被 NAK）→ 今日方案收敛到「`switching_to()` 返回 bool + `sched_change_end()` 泛化处理」，Andrea 接手实现与测试。无新补丁版本。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：否定 v1 的 magic hook，提出 `switching_to()` 返回 bool 的泛化方案，并要求 proxy 支持在 sub-scheduler 间保持一致（强制 primary 立场或逻辑与）。
- **Andrea Righi**：同意该方向并主动接手测试，同时把 sub-scheduler、donor 复位、时钟更新的细节一一列出。
- **bpf-ci bot**：列三点疑虑——double rq clock 更新（`WARN_DOUBLE_CLOCK` 下 rt/dl→ext PI deboost 触发 WARN_ON_ONCE）、changelog「唯一入口」说法不准（`__sched_setscheduler()` 在 `!SCX_OPS_SWITCH_PARTIAL` 时对任意 policy 走 ext）、Peter 已否该 hook 是否仍坚持。
- 无 NAK（方向已获认同）。

## 合入评估
方向明确且 Andrea 接手实现，合入概率中等；当前卡在「`switching_to()` 返回 bool」的实现与边界（sub-scheduler、donor、时钟）落地，以及 bpf-ci 三点疑虑需在新版说明。

## 效果评估
无 benchmark；属正确性修复（proxy-exec 的 PI deboost 状态契约）。

## 我可以参与的点
- **review**：核对 `switching_to()` 返回 bool 方案在 `sched_change_end()` 里的 `block_task()` 与 `ctx->queued`/donor/时钟处理是否完整。
- **testing**：跑 ext 的 PI deboost 边缘 case（rt/dl→ext、sub-scheduler 间迁移）验证修复。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261112144935.583937-1-cui.tao@linux.dev/
- Peter 的 switching_to() 示意: https://lore.kernel.org/all/20261112160136.GF1922751@noisy.programming.kicks-ass.net/
- bpf-ci 疑虑: https://lore.kernel.org/all/89f7ed00d7373ea7389e563810fbcd7ae775858e7fb592ad6e12cc1d1aee2565@mail.kernel.org/

---
id: sched-20261113-015
subject: "sched_ext: Block a retained donor before PI deboost routes it back to sched_ext"
date: 2026-11-13
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261112144935.583937-1-cui.tao@linux.dev>"
lore_url: "https://lore.kernel.org/all/20261112144935.583937-1-cui.tao@linux.dev/"
authors: [Tao Cui]
maintainers_involved: [Peter Zijlstra, Andrea Righi]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261112144935.583937-1-cui.tao@linux.dev>"
    date: 2026-11-12
    summary: "两补丁修 fork 进入路径与 PI deboost 进入路径契约破坏"
    review_outcome: "Peter NAK patch 2 hook；今日收敛到 switching_to() 返回 bool 的泛化方案"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "switching_to() 返回 bool 方案的实现与边界（sub-scheduler、donor、时钟）待落地"
    - "bpf-ci bot 的三点疑虑需在新版说明"
  next_action: "Andrea 实现 switching_to() 方案并测试 ext 边缘 case"
contribution_opportunities:
  - kind: review
    description: "核对 switching_to() 方案中 block_task/ctx->queued/donor/时钟处理完整性"
  - kind: testing
    description: "跑 ext 的 PI deboost 与 sub-scheduler 间迁移边缘 case"
generated_at: "2026-11-14T01:30:00"
source_email_count: 8
related_articles: [sched-20261112-001]
tags: [sched_ext, bpf]
---