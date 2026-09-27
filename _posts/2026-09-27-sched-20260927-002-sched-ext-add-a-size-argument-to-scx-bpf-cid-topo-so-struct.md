---
id: sched-20260927-002
date: 2026-09-27
subject: 'sched_ext: Add a size argument to scx_bpf_cid_topo() so struct scx_cid_topo
  can grow'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <fa6479d36b528573565ca22914451317@kernel.org>
lore_url: https://lore.kernel.org/all/fa6479d36b528573565ca22914451317@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <fa6479d36b528573565ca22914451317@kernel.org>
  date: 2026-09-27
  summary: 给 scx_bpf_cid_topo() 加 out__sz 参数，拷贝 min(程序大小, 内核 sizeof) 并置余 -1，使 struct
    scx_cid_topo 可追加字段增长；Fixes e9b55af47edf，Cc stable v7.2+。
  review_outcome: Andrea Righi Reviewed-by；Tejun applied 到 sched_ext/for-7.3-fixes，并作为
    tags/sched_ext-for-7.3-rc4-fixes-2 唯一 commit 发 GIT PULL。
upstream_commit: 94480606a677deb68d5622cf0ded88626514b3f2
fixes_commit: e9b55af47edf
merged_branch: sched_ext/for-7.3-fixes（tags/sched_ext-for-7.3-rc4-fixes-2）
merge_assessment:
  likelihood: merged
  blocking_issues:
  - 进 Linus 树的合并 commit 与 -rc 归属未获取到（无 pr-tracker-bot 回执）
  - stable 回合（Cc v7.2+）是否已 pick 未获取到
  next_action: 跟踪 pr-tracker-bot 合并回执；与内部分支比对 scx_bpf_cid_topo() 是否已带 size 参数形态
contribution_opportunities:
- kind: new_patch
  description: 回合自查：本修复 Cc stable v7.2+，比对内部分支/OLK 的 scx_bpf_cid_topo() 是否已带 size
    参数，未带则按 commit 94480606 回合
- kind: testing
  description: 用旧 vmlinux.h 构建的 BPF 调度器在新内核验证加载不被拒、CO-RE 访问新字段生效
generated_at: '2026-09-28T09:00:00'
source_email_count: 4
related_articles: []
tags:
- sched_ext
- topology
title: 'sched_ext: Add a size argument to scx_bpf_cid_topo() so struct scx_cid_topo
  can grow'
layout: article
---

## TL;DR

Tejun Heo 为 sched_ext 发的一枚 ABI 前向兼容修复：给 `scx_bpf_cid_topo()` kfunc 增加 buffer size 参数，拷贝「程序大小与内核结构大小中较小者」并把剩余部分置 -1，使 `struct scx_cid_topo` 以后能通过追加字段安全增长、不再破坏按旧 vmlinux.h 构建的 BPF 调度器。已获 Andrea Righi Reviewed-by，当日即 applied 到 sched_ext/for-7.3-fixes，并作为 `tags/sched_ext-for-7.3-rc4-fixes-2` 的唯一 commit 由 Tejun 向 Linus 发出 GIT PULL（目标 v7.3-rc4）。

## 背景与问题

`scx_bpf_cid_topo()` 把 `struct scx_cid_topo` 拷进一个由 BPF 程序按其**自身 vmlinux.h** 定大小的缓冲区，而 verifier 按**运行内核 BTF** 的 sizeof 来核验写大小。一旦该结构在内核里增长（比如新增 cluster 字段），每个按旧布局构建的调度器都会在加载时被拒、或写越界。这是「把手握结构交给 BPF」这类接口的常见坑，其他接口都已用 size 参数封住，唯独这里漏了。

## 技术方案

给 kfunc 加 `out__sz` 参数（程序的 `sizeof(struct scx_cid_topo)`），拷贝 `min(out__sz, 内核 sizeof)` 字节，其余字节置 -1。对拷贝的访问经 CO-RE 重定位，因此结构可安全地**在末尾追加**字段（kerneldoc 已注明）。kfunc 原地修改而不做版本分叉，理由是 cid 接口仍在定型期、尚无已发布的调度器使用现有形态。落点：`kernel/sched/ext/cid.c` +26/-…、`types.h` +4、`tools/sched_ext/include/scx/common.bpf.h` +2/-1，共 21 insertions(+), 11 deletions(-)。

## 版本演进与当前进展

- v1（2026-09-27 03:23，`<fa6479d36b528573565ca22914451317@kernel.org>`）：首发，带 `Fixes: e9b55af47edf ("sched_ext: Add topological CPU IDs (cids)")` 与 `Cc: stable@vger.kernel.org # v7.2+`。
- 09-27 03:42：Andrea Righi 回复「Makes sense to me」，给出 Reviewed-by。
- 09-27 04:15：Tejun applied 到 sched_ext/for-7.3-fixes，补上 Righi 的 Reviewed-by 标签。
- 09-27 16:49：Tejun 向 Linus 发 GIT PULL（`tags/sched_ext-for-7.3-rc4-fixes-2`，顶端 94480606a677deb68d5622cf0ded88626514b3f2），本 commit 是其中唯一改动。

## Maintainer 意见与讨论焦点

无分歧：作者即 sched_ext 维护者 Tejun Heo，另获同为 sched_ext 维护者的 Andrea Righi Reviewed-by 后即合入。讨论仅在「是否原地改 kfunc 而非新增带 size 的变体」——Tejun 在 commit message 里给出理由（cid 接口未定型、无已发布调度器使用），无人反对。

## 合入评估

*likelihood=merged*：`status=merged_tip`，已 applied 到 sched_ext/for-7.3-fixes，并作为 `tags/sched_ext-for-7.3-rc4-fixes-2` 通过 GIT PULL 走向 v7.3-rc4。*blocking_issues*：进 Linus 树的确切合并 commit 与 -rc 归属尚未见 pr-tracker-bot 回执（未获取到）；stable 回合（Cc v7.2+）是否已被 pick 未获取到。*next_action*：跟踪 pr-tracker-bot 合并回执确认进主线时点；与内部分支/OLK 分支比对是否已带此 size 参数 kfunc。

## 效果评估

无 benchmark。收益属 ABI 正确性一类：`struct scx_cid_topo` 此后可安全追加字段，旧调度器二进制加载不再被拒或写越界。规模 21 insertions(+)/11 deletions(-)。

## 我可以参与的点

- `new_patch`：回合自查——本修复带 `Cc: stable # v7.2+`，与内部分支/OLK 分支比对 `scx_bpf_cid_topo()` 是否已带 size 参数形态，未带则按 commit 94480606a677deb68d5622cf0ded88626514b3f2 回合。
- `testing`：用旧版 vmlinux.h 构建的 BPF 调度器在新内核上验证加载不再被拒、且访问新追加字段时按 CO-RE 语义生效。

## 参考链接

- 补丁: https://lore.kernel.org/all/fa6479d36b528573565ca22914451317@kernel.org/
- Righi Reviewed-by: https://lore.kernel.org/all/arggKqtys5jxn47h@gpd4/
- Tejun applied 回执: https://lore.kernel.org/all/91086617198af8f4ca532252cc80b8cd@kernel.org/
- GIT PULL（Another fix for v7.3-rc4）: https://lore.kernel.org/all/b633964a6f8f06d64bee4227394d6218@kernel.org/
