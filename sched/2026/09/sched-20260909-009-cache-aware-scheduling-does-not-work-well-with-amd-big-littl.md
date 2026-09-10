# Cache-aware scheduling does not work well with amd big/little cores

## TL;DR

本文为增量更新，问题背景与前几轮的参数/拓扑讨论见 related_articles 中的 sched-20260905-007 / sched-20260831-006 / sched-20260829-003。09-09 这个线程没有推进结论，只澄清了两件事：报告者 Klaus Kusche 说明他对比的「with/without patch」指的是 Tim Chen 08-31 那枚补丁而**不是** Mario 的那枚；以及 Tim Chen 主动透露 CAS 的主动负载均衡路径还有两个已知问题需要修，并给出了补丁链接。Klaus 表明自己在休假（Linz 的 Ars Electronica Festival），未来几天不会有新数据。

## 背景与问题

在 AMD 的大小核（HX 370：4 个大核独占 16MB L3、8 个小核共享 8MB L3）上，cache-aware scheduling（CAS）的表现不符合预期。报告者此前对比了若干配置：(a) 关掉 CAS、(b) CAS 开、(c) CAS 开 + 某些补丁。当天的混乱就出在「(b)/(c) 里那个 patch 到底是谁的哪一枚」。

## 技术方案

本日没有新代码，只有两条指向既有补丁的链接，值得单独记下来因为它们是 Tim Chen 主动给出的、尚未在本线程内展开的修复：

- `20260903020656.3793626-1-wanglu.priv@gmail.com`（Lu Wang 的 active load balance guard）
- `2b0a35122ee615c6fa51076e5d79330e633755ac.camel@linux.intel.com`（本线程另一条 ALB 讨论线，见 sched-20260909-015）

Tim 的原话："we have also found two issues with the active load balance paths for CAS that need fixes. You may want to add those patches and see if they are helpful to improve things."

## 版本演进与当前进展

- 09-09 05:54 Tim Chen 提出两点澄清请求：他理解 Mario 提到的那枚（`c1e7fe5e75ed11fa85368e5a186472afd3858f3a`，主线中该 commit 的标题是 `sched/cache: Add user control to adjust the aggressiveness of cache-aware scheduling`）只是把默认的 cache-aware 参数**通过 debugfs 暴露出来**、并不改动取值，因此他「不认为 (b) 和 (c) 会有差别」——但报告者前面又说没有 Mario 补丁时结果明显更差，两处矛盾。他也确认了自己需要去找与 HX-370 相近的机器复现。
- 09-09 16:59 Klaus Kusche 澄清：(b)/(c) 里的 with/without patch 指的是 **Tim 08-31/25 发的那枚**（`20260825174112.2580942-1-tim.c.chen@linux.intel.com`），不是 Mario 的；并确认拓扑是大核 16MB L3、小核 8MB L3。同时表明短期内（"Most likely not within the next few days"）不会有进一步动作，因为在休假。
- 09-09 21:19 Mario Limonciello 回帖，正文只有一串 40 位哈希 `eaece4849991d62fcd6f46637c55dcce00e25d70`，没有任何解释。该哈希不在我本地的主线树里，因此它指向什么（某个 for-next 提交？某个自建树的提交？某个补丁文件？）**未获取到**，不做猜测。

## Maintainer 意见与讨论焦点

维护者侧本日没有新的判断，只有一个方法论上的纠正：Tim Chen 强调「按我的理解那枚补丁只暴露参数、不改取值，所以我不预期有差异」——这实际上是在质疑对方实验分组是否有效。Klaus 的澄清把矛盾解开了（是两组不同的补丁被混称为 "patch"），但这轮对比的可解释性仍然受损：**到目前为止，线程里没有出现一个明确标注了「内核基线 + 逐条补丁 + 是否含 debugfs 暴露」的对照组表**。这也是本线程从 08-29 起反复出现的同一个问题。

拓扑方面，Klaus 给出的 4 大核/16MB + 8 小核/8MB 是当天唯一确定的新事实，而 Tim 先前推测的是「4 个大核在一个 L3、8 个小核在另一个 L3」——两者一致，说明大小核共享域划分本身就是 CAS 需要正确处理的异构 L3 层级。

## 合入评估

不适用：这是一份问题报告而非 patch 系列，没有可评估的合入对象。相关修复目前散在别处：Tim 提到的两枚 ALB 补丁在另一条线上推进（见 sched-20260909-015 与 Lu Wang 的链接），它们能否解释 HX-370 上的现象尚未验证。

## 效果评估

本日**没有任何新数据**，只有对既有数据的归因纠正。这一点值得强调：从 08-29 至今，这个线程里出现的数字一直没能形成一个可复现、可归因的对照，而当天唯一能确认的量化信息是拓扑（16MB/8MB L3、4+8 核）。Klaus 的「带补丁 vs 不带补丁差异很大」这句结论，因为 patch 归属被纠正，目前需要重新对应到 `20260825174112.2580942-1` 那枚补丁上，而不是 Mario 的参数暴露补丁。

## 我可以参与的点

- `testing`：这是当前最有价值也最缺的一件事——手上有 AMD Strix/HX 系列大小核机器的话，按明确表格复现一遍：基线内核、+Tim 的 `20260825174112.2580942-1`、+Mario 的 `c1e7fe5e75ed`（仅暴露参数）、+Lu Wang 的 ALB guard，逐个给出吞吐与 `perf` 侧的迁移/L3 命中数据。当天 Tim 自己说需要去找类似 HX-370 的机器，说明连 Intel 侧也缺复现平台。
- `discussion`：直接把这些补丁链接回给 Klaus，并给出一份「他应该按什么顺序、在什么负载上试」的最小清单——他 09-09 之后要休假几天，这正是可以趁空档把实验设计定下来的窗口。
- `review`：跟进 Tim 提到的「CAS 的主动负载均衡路径有两个问题需要修」这一说法——当天他没有在本线程里描述这两个问题分别是什么，只是丢了链接。把它们与 `nr_pref_llc_running` 那条讨论线（sched-20260909-015）对照，很可能能确认这两枚补丁是否就是同一件事。

## 参考链接

- 本日 Tim Chen 的澄清与两枚 ALB 补丁指引: https://lore.kernel.org/all/3cb5cbdb227bee0b822f1550e10659faadd77a3d.camel@linux.intel.com/
- 本日 Klaus Kusche 的澄清与休假说明: https://lore.kernel.org/all/e17ef3af-c1cd-4360-ba4b-9900ccc36ef6@computerix.info/
- Mario Limonciello 的裸哈希回帖: https://lore.kernel.org/all/76dba935-1052-4fa9-a70c-16cecdfd12c8@amd.com/
- Tim Chen 那枚被对比的补丁: https://lore.kernel.org/all/20260825174112.2580942-1-tim.c.chen@linux.intel.com/
- Lu Wang 的 ALB guard: https://lore.kernel.org/all/20260903020656.3793626-1-wanglu.priv@gmail.com/
- Mario 的参数暴露补丁（主线 c1e7fe5e75ed，标题 sched/cache: Add user control to adjust the aggressiveness of cache-aware scheduling）: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=c1e7fe5e75ed
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: "sched-20260909-009"
date: "2026-09-09"
subject: "Cache-aware scheduling does not work well with amd big/little cores"
subsystem: sched
type: bug
status: stalled
severity: medium
thread_root_msgid: "2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info"
lore_url: "https://lore.kernel.org/all/e17ef3af-c1cd-4360-ba4b-9900ccc36ef6@computerix.info/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: "2026-09-10T00:50:00"
authors:
  - "Klaus Kusche"
maintainers_involved:
  - "Tim Chen"
  - "Mario Limonciello"
patch_series:
  - version: v1
    msgid: "2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info"
    date: "2026-09-09"
    summary: "问题报告线程（非 patch 系列）。本日无新代码；澄清 (b)/(c) 对照组里被简称 patch 的是 Tim Chen 的 20260825174112.2580942-1 而非 Mario 的 c1e7fe5e75ed（后者只把默认 cache-aware 参数经 debugfs 暴露、不改取值），并确认 HX-370 拓扑为大核 16MB L3、小核 8MB L3。"
    review_outcome: "Tim Chen 指出原表述自相矛盾并要求澄清；报告者答复后表明数日内不会有新数据（休假）。Mario Limonciello 仅回一串未解释的 40 位哈希。"
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "报告方进入休假，未来数日无新数据"
    - "至今没有一份明确标注内核基线与逐条补丁的对照组表，既有数字无法可靠归因"
    - "Tim Chen 提到 CAS 的主动负载均衡路径有两个问题需修，但未在本线程描述具体是哪两个"
  next_action: "等待报告者回归，或由其他人按（基线 / +Tim 的补丁 / +Mario 的参数暴露 / +Lu Wang 的 ALB guard）矩阵在同类大小核机器上复现并回帖"
contribution_opportunities:
  - kind: testing
    description: "在 AMD Strix/HX 类大小核机器上按逐补丁矩阵复现并给出吞吐与迁移/L3 命中数据，Tim Chen 自陈也需要找类似 HX-370 的平台"
  - kind: discussion
    description: "把 Tim 给出的两枚 ALB 补丁与线程里既有的对照结果对应起来，给报告者一份明确的复现清单，趁其休假的空档把实验设计定下来"
  - kind: review
    description: "跟进 CAS active load balance 路径那两个尚未描述的问题，确认它们与 nr_pref_llc_running 讨论线中的修复是否为同一件事"
source_email_count: 3
related_articles:
  - "sched-20260905-007"
  - "sched-20260831-006"
  - "sched-20260829-003"
tags:
  - "load_balance"
  - "topology"
  - "x86"
---
