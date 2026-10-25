# Sleeping Owner Handling for Proxy Execution (v33)

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20260922-002（v32）：John Stultz 发出 proxy execution 第 5 阶段「Sleeping Owner Handling」第 32 版：任务阻塞在 owner 睡眠的 mutex 上时，把 waiter 停用并挂到 owner 的等待表，待 owner 唤醒时在同 runqueue 重新激活以提升 owner。v32 新增 K Prateek 的「无 owner 时激活 blocked donor」补丁，并在 John 与 K Prateek 两套方案间等 Peter 表态。
- sched-20261024-001（v33）：系列扩到 7 补丁，聚合 K Prateek、Shubhang、zhidao su、Hui Su、Peter 等多人修复，新增 proxy 链循环检测（Brent 算法 + 1024 深度上限）、远程 tick 改 rq->donor，以及 sleeping-owner 路径一批正确性修复。当天 Peter Zijlstra、Andrea Righi、Kayra Cizmeci 密集 review：Kayra 给 2/7、6/7 Reviewed-by，Peter 质疑 1/7 的 sched_delayed 判据，Andrea 在 3/4/7 提 cookie 校验、DL 带宽记账、offline CPU 等问题。仍属 RFC。
- sched-20261025-010（今天）：Kayra Cizmeci 继续 review，对 5/7（链循环停用）补问该补丁是否缺 `Fixes` 标签，并给出建议 commit `7de9d4f94638`。

## 背景与问题
（承接 v32/v33）proxy execution 提交路径第 5 阶段处理「任务阻塞在 mutex 上而 owner 在睡眠」：需在 owner 唤醒时重新激活挂在其上的 waiter 树，且 waiter 树可嵌套、需额外列表规避级联递归。v33 无新背景，把系列扩为 7 补丁纳入链循环检测等边界修复。今日无新背景，为 5/7 的补丁元数据 review。

## 技术方案
（承接 v32 + v33）v33 共 7 补丁，其中 5/7 **`sched/proxy: Break cyclic proxy chains by deactivating blocked tasks`**（zhidao su）：链回环时清当前 `blocked_on` 关系并停用该 blocked 任务，`MAX_PROXY_CHAIN_DEPTH 1024` 对齐 rtmutex 的 max_lock_depth。今日无代码变更。

## 版本演进与当前进展
*current_version: v33*（`<20261023220431.1106611-1-jstultz@google.com>`）。当日收到 Kayra Cizmeci 对 5/7 的回帖（`<at0fFKw8Vv1br_PZ@scheduler.schedules>`）。

## Maintainer 意见与讨论焦点
今日 Kayra Cizmeci 对 5/7 补问：`This needs a Fixes tag, no?` 并给出 `Fixes: 7de9d4f94638`（"sched: Start blocked_on chain processing in find_proxy_task()"）。此前（10-24）Peter Zijlstra 质疑 1/7 的 `sched_delayed` 判据、Andrea Righi 在 3/4/7 提 cookie 校验/DL 带宽记账/offline 隐患，均无作者回应。

## 合入评估
*likelihood=unknown*。仍属 proxy execution 的 RFC 阶段；Kayra 的 Fixes 标签属补丁元数据级意见，不改变 RFC 定性，但作者尚未回应此前 Peter/Andrea 的实质问题。*blocking_issues*：Peter 对 1/7 判据、Andrea 对 DL 记账/cookie/offline 的未解决问题；5/7 缺 Fixes 标签。*next_action*：作者回应 Peter/Andrea 意见并补 5/7 的 Fixes 标签。

## 效果评估
无性能数据，属正确性功能补丁；5/7 链回环复现器此前已示功能验证（修复前 90s 超时内无法完成，修复后打印 cycle detected 且心跳 kthread 继续运行）。

## 我可以参与的点
- *kind: review*：核对 5/7 的 `Fixes: 7de9d4f94638` 是否准确、以及链循环停用逻辑的边界。
- *kind: testing*：启用 SCHED_PROXY_EXECUTION 的构建上压测 mutex/futex 阻塞唤醒与链回环路径。
- *kind: discussion*：补 cover 提到的 sequence-marker 对比测量数据。

## 参考链接
- v33 cover: https://lore.kernel.org/all/20261023220431.1106611-1-jstultz@google.com/
- Kayra 5/7 回帖: https://lore.kernel.org/all/at0fFKw8Vv1br_PZ@scheduler.schedules/
- 前文: sched-20261024-001 / sched-20260922-002

---
id: sched-20261025-010
date: 2026-10-25
subject: 'Sleeping Owner Handling for Proxy Execution (v33)'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<20261023220431.1106611-1-jstultz@google.com>'
lore_url: 'https://lore.kernel.org/all/20261023220431.1106611-1-jstultz@google.com/'
authors:
  - 'John Stultz'
  - 'Peter Zijlstra'
  - 'K Prateek Nayak'
  - 'Shubhang Kaushik (Ampere)'
  - 'zhidao su (Xiaomi)'
  - 'Hui Su'
maintainers_involved:
  - 'Peter Zijlstra'
  - 'Andrea Righi'
current_version: v33
patch_series:
  - version: v32
    msgid: '<20260922024117.1514332-1-jstultz@google.com>'
    date: 2026-09-22
    summary: '2 补丁：加入无 owner 激活 blocked donor；采纳 Atul 与 Peter guard() 风格整理'
    review_outcome: '待 Peter 在两方案间表态'
  - version: v33
    msgid: '<20261023220431.1106611-1-jstultz@google.com>'
    date: 2026-10-24
    summary: '扩到 7 补丁：远程 tick 用 donor、无 owner/null mutex 激活、return migration 设 TASK_RUNNING、链回环+深度上限、Brent 早检测'
    review_outcome: 'Kayra 2/7+6/7 R-b、5/7 补问 Fixes；Peter 质疑 1/7；Andrea 3/4/7 提问题'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - 'Peter 对 1/7 sched_delayed 判据有取舍意见'
    - 'Andrea 指出 7/7 DL bw 记账泄漏与 offline cpu 隐患'
    - '5/7 缺 Fixes 标签'
  next_action: '作者回应 Peter/Andrea 意见并补 5/7 的 Fixes 标签'
contribution_opportunities:
  - kind: review
    description: '核对 5/7 的 Fixes commit 与链循环停用边界'
  - kind: testing
    description: '启用代理执行的构建下压测 mutex/futex 阻塞唤醒与链回环路径'
  - kind: discussion
    description: '补 cover 提到的 sequence-marker 对比测量数据'
generated_at: '2026-10-26T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260922-002
  - sched-20261024-001
tags:
  - proxy_execution
---