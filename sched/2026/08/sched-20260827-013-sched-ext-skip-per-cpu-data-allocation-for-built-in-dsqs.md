# sched_ext: Skip per-CPU data allocation for built-in DSQs

## TL;DR
Qiurong Fang（KylinOS）发现内建 DSQ 的 `struct scx_dsq_pcpu` per-CPU 分配全是死内存（deferred reenqueue 只服务用户 DSQ），改为跳过分配。Zhan Xusheng 的回帖把收益放大了两个数量级——内建 DSQ 本身随 `nr_cpu_ids` 增长，省的是 **O(nr_cpu_ids²)** 条目——并完整验证了跳过条件与 `exit_dsq()` 早退的必要性，同时提出两条修正意见（Fixes 标签是否过度、作者署名不一致）。当日无维护者表态。

## 背景与问题
`sched_ext: Add per-CPU data to DSQs`（30b0515342db）给每个 DSQ `alloc_percpu(struct scx_dsq_pcpu)`；但 `schedule_dsq_reenq()` 对 local DSQ 走 `sch->pcpu->deferred_reenq_local`，并**拒绝其余全部内建 DSQ id**——即 `SCX_DSQ_GLOBAL/REJECT/BYPASS/RESCUE` 等带着 `nr_cpu_ids × sizeof(struct scx_dsq_pcpu)` 的死内存。大核数机器上这不是小数目（Zhan：只有 GLOBAL 是单实例，LOCAL/REJECT/BYPASS/RESCUE 都是 per-CPU 初始化，数量 × nr_cpu_ids）。

## 技术方案
`scx_init_dsq()` 中 `dsq_id & SCX_DSQ_FLAG_BUILTIN` 直接 return 0 跳过分配；`exit_dsq()` 加 `if (!dsq->pcpu) return;`。Zhan 验证的关键正确性链条：全树唯一读点 ext.c:1130 本来就处于 `!(dsq->id & SCX_DSQ_FLAG_BUILTIN)` 分支（1127，正好互补）；进 `scx_init_dsq()` 的五个内建 id 全部带该 flag（sched/ext.h:58-62）；且 `exit_dsq()` 的早退**不是整理性代码而是必需**——`per_cpu_ptr(NULL, cpu)` 会给出偏移指针让 `list_empty()` 去读。

## 版本演进与当前进展
v1（`<20260827082329.3368255-1-fangqiurong@kylinos.cn>`），08-27 即获 Zhan 的详细技术核对（未给 tag，附两条修改意见）。`Fixes: 30b0515342db`。

## Maintainer 意见与讨论焦点
- Zhan 的两条待决意见：(1) 带 Fixes 会把它送进 stable，而纯内存节省没有正确性收益，"除非你能说出正确性角度，否则不该带"；(2) 邮件头 `Qiurong Fang` 与正文 From:/SoB 的 `fangqiurong` 不一致，需修正署名。
- 无人 NAK；sched_ext 维护者当日未表态。

## 合入评估
**possible**。机制上已被社区同行验证安全，收益论证在 Zhan 回帖后反而更强（二次方）；卡点是作者对两条意见的回应（去掉/保留 Fixes 的取舍、署名修正），以及 Tejun 侧是否需要补性能数字（大机内存节省量）。

## 效果评估
无实测数字。节省量当前只有阶的分析（O(nr_cpu_ids²) × sizeof(scx_dsq_pcpu)）；如作者补上具体机型（如 256/512 核）的 meminfo 对比会好卖得多。

## 我可以参与的点
- 这正是大核数场景的补丁：在自家机型上算出/量出内建 DSQ per-CPU 内存的绝对值并回帖 Tested-by/数据，是对合入最直接的推动。
- 若做 sched_ext 回合评估，可顺带检查 6.6 的 DSQ per-CPU 结构差异（该分配点若同源，回合同理可行）。

## 参考链接
- lore: https://lore.kernel.org/all/20260827082329.3368255-1-fangqiurong@kylinos.cn/
- Zhan 的核对回帖: https://lore.kernel.org/all/20260827093838.532352-1-zhanxusheng1024@gmail.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260827-013
date: '2026-08-27'
subject: "sched_ext: Skip per-CPU data allocation for built-in DSQs"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20260827082329.3368255-1-fangqiurong@kylinos.cn>"
lore_url: "https://lore.kernel.org/all/20260827082329.3368255-1-fangqiurong@kylinos.cn/"
authors: [Qiurong Fang, Zhan Xusheng]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260827082329.3368255-1-fangqiurong@kylinos.cn>"
    date: 2026-08-27
    summary: "内建 DSQ 跳过 scx_dsq_pcpu per-CPU 分配，exit_dsq() 加 NULL 早退"
    review_outcome: "Zhan 验证安全性并把收益修正为 O(nr_cpu_ids²)，但质疑 Fixes→stable 与署名不一致"
upstream_commit: null
fixes_commit: "30b0515342db"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "Fixes 标签是否保留（决定进不进 stable）待作者回应"
    - "邮件头与 Signed-off-by 署名不一致需修正"
    - "sched_ext 维护者尚未表态，缺绝对收益数字"
  next_action: "作者回帖处理两条意见，最好附上大核数机型的内存节省实测"
contribution_opportunities:
  - kind: testing
    description: "在大核数机型上量化内建 DSQ 死内存的绝对值并回帖 Tested-by"
  - kind: discussion
    description: "就 Fixes/stable 取舍给出使用侧意见"
generated_at: "2026-09-07T22:05:00"
source_email_count: 2
related_articles: []
tags: [sched_ext]
---
