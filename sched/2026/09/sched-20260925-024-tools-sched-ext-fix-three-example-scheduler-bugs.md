# tools/sched_ext: Fix three example scheduler bugs

## TL;DR

Wanwu Li（kylinos.cn）发了一组修复 sched_ext 三个示例调度器 bug 的补丁（PATCH 0/3），但 Tejun Heo 复审发现 3/3 一出场就会触发运行时错误——作者根本没有跑过这些补丁，直接打回要求「先复现每个 bug、验证修复再发」。作者道歉并承诺重做。这是一次「未测试就投稿」被当场拦下的典型案例。

## 背景与问题

`sched_ext` 在 `tools/sched_ext` 下提供一批示例调度器，供开发者和用户学习/参考。这组 patch 声称修复其中的三个 bug。问题不在修复意图，而在**提交质量**：Tejun 发现 3/3 在 `bpf_task_from_pid()` 拿到的任务上调用了 `scx_bpf_task_cgroup()`，而该 kfunc 只接受「传给当前 op 的任务」，于是在首次 dispatch 就被禁用：

```
sched_ext: BPF scheduler "pair" enabled
sched_ext: BPF scheduler "pair" disabled (runtime error)
sched_ext: pair: called on a task not being operated on
     scx_bpf_task_cgroup+0x15b/0x160
```

这说明补丁根本没被运行过。

## 技术方案

（3 枚方向）修复示例调度器的 bug（具体 bug 列表未在当日缓存逐条给出，以 0/3 封面与 Tejun 对 3/3 的 review 为限）。3/3 需重做：把 `scx_bpf_task_cgroup()` 错误地用于非当前 op 任务的问题重新设计。

## 版本演进与当前进展

- v1（2026-09-24 前后，`<...liwanwu@kylinos.cn>`，0/3）：首发。
- 09-25：Tejun 打回（`<9c8dd70b66bba55c87376f227d986945@kernel.org>`），作者回帖道歉并承诺重做（`<e29045bd-6043-4f1d-baea-7616e7090c39@kylinos.cn>`）。

## Maintainer 意见与讨论焦点

Tejun Heo 的批评直指流程而非技术细节：「This means the patches were posted without being run at all. That's not acceptable.」——要求投稿前必须复现并验证。作者承认是「serious mistake」、道歉并承诺逐 bug 复现、重做 3/3。无 NAK，但当前版本不会被接受。

## 合入评估

*likelihood=low*（当前版本）。修复意图没问题、但质量不达标被打回。*blocking_issues*：作者须复现并修复 3/3 的 kfunc 误用、跑通验证后再发 v2。*next_action*：Wanwu 复现每个 bug、验证修复、重做 3/3 后重发。

## 效果评估

暂无效果数据；3/3 的失败本身是可复现的运行时错误（首次 dispatch 即被禁用），见上文 kernel log。

## 我可以参与的点

- `testing`：复跑示例调度器（尤其 "pair"）的 dispatch 路径，验证 3/3 修复后不再触发「called on a task not being operated on」。
- `review`：审读作者 v2 里 3/3 是否正确规避了对非当前 op 任务调用 `scx_bpf_task_cgroup()` 的限制。

## 参考链接

- Tejun 打回: https://lore.kernel.org/all/9c8dd70b66bba55c87376f227d986945@kernel.org/
- 作者道歉回帖: https://lore.kernel.org/all/e29045bd-6043-4f1d-baea-7616e7090c39@kylinos.cn/

---
id: sched-20260925-024
date: 2026-09-25
subject: "tools/sched_ext: Fix three example scheduler bugs"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20260924143659.268595-1-liwanwu@kylinos.cn>"
lore_url: "https://lore.kernel.org/all/20260924143659.268595-1-liwanwu@kylinos.cn/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: "2026-09-26T01:15:00"
authors:
  - "Wanwu Li"
maintainers_involved:
  - "Tejun Heo"
patch_series:
  - version: v1
    msgid: "<20260924143659.268595-1-liwanwu@kylinos.cn>"
    date: 2026-09-24
    summary: "修复三个 sched_ext 示例调度器 bug（0/3）"
    review_outcome: "09-25 Tejun 打回：3/3 未测试即投稿，触发运行时错误，要求复现并验证后重发"
merge_assessment:
  likelihood: low
  blocking_issues:
    - "3/3 对非当前 op 任务调用 scx_bpf_task_cgroup()，首次 dispatch 即被禁用"
    - "作者须复现每个 bug、验证修复后再发 v2"
  next_action: "Wanwu 复现并修复 3/3、跑通验证后重发 v2"
contribution_opportunities:
  - kind: testing
    description: "复跑示例调度器（尤其 pair）的 dispatch 路径，验证 3/3 修复后不再触发 called on a task not being operated on"
  - kind: review
    description: "审读作者 v2 里 3/3 是否正确规避对非当前 op 任务调用 scx_bpf_task_cgroup 的限制"
source_email_count: 2
related_articles: []
tags:
  - sched_ext
---