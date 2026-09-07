# sched_ext: Fix timer pinning and return value in scx_central

## TL;DR
Wanwu Li（KylinOS）发出的 3 补丁小系列，统一修复 sched_ext 示例调度器里 `bpf_timer_start()` 的三类错误用法：scx_central 重挂定时器时硬编码 `BPF_F_TIMER_CPU_PIN` 且忽略返回值（旧内核上第一次 tick 就把心跳永久打死且无诊断）、scx_flatcg 迁移 cgroup 时 `time_delta()` 把负增量钳 0 导致 vtime 信用丢失、scx_qmap 三处定时器重挂不检查返回值。当日无人回复；这类 selftest/示例修复对 sched_ext 测试生态有实际价值。

## 背景与问题
1. **scx_central**：`central_init()` 对不支持 `BPF_F_TIMER_CPU_PIN`（<6.7）的内核有 -EINVAL 回退（`timer_pinned=0`），但 `central_timerfn()` 重挂时硬编码该 flag 且不查返回值——在不支持的内核上第一个 tick 定时器就静默死掉，central 心跳消失。`Fixes: 22a920209ab6`（"sched_ext: Implement tickless support"）。
2. **scx_flatcg**：`fcg_cgroup_move()` 在向 time helper 机械转换时把 `p->scx.dsq_vtime - from_cgc->tvtime_now` 换成了 `time_delta()`，而后者把负增量钳到 0——排队任务的 dsq_vtime 通常落后于源 cgroup 前沿，钳 0 使其迁移后恰好落在目标前沿，丢失相对位置信用。`Fixes: 62addc6dbf36`（"sched_ext: Use time helpers in BPF schedulers"）。
3. **scx_qmap**：monitor/lowpri/round_robin 三个 timerfn 忽略重挂返回值，失败即静默停摆（LOWPRI_DSQ 任务饿死、cid 轮转冻结）。

## 技术方案
按 init 路径对齐：flag 改为 `timer_pinned ? BPF_F_TIMER_CPU_PIN : 0`；所有重挂点检查返回值并 `scx_bpf_error()`；flatcg 恢复环绕式有符号减法 `(s64)(a - b)`。全部改动在 `tools/sched_ext/*.bpf.c`，不触碰内核侧。

## 版本演进与当前进展
v1 一次性 3 封（以 `20260827080738.829103-1..3-liwanwu@kylinos.cn` 为系列），当日无 review。3 补丁均带/应带 Fixes，其中两封有 `Fixes:` 标签。

## Maintainer 意见与讨论焦点
无人表态。潜在讨论点：flatcg 那封实质是修 62addc6dbf36 转换引入的语义回归，属于该转换的系统性问题，值得提醒作者 grep 其他 scheduler 是否有同类钳位（当日无人提到，可视为待议）。

## 合入评估
**likely**。改动小、方向明确、带 Fixes 且全在 tools/ 示例代码，sched_ext 维护者（Tejun/DFC 侧）对示例正确性修复历来收得快；卡点仅是排队。`next_action`：等 review 或被 sched_ext tree 收走。

## 效果评估
无 benchmark；问题机理描述具体（负增量钳 0、旧内核 flag 失败路径），属可信的代码级论证，未见运行前后对比数据。

## 我可以参与的点
- **顺手可做**：全仓 grep `time_delta(` 的其它使用点，确认没有同类有/无符号回归，回帖或另发 patch——线程里没人做这件事。
- 在 <6.7 内核上跑一次 scx_central 验证修复的 flag 回退路径，Tested-by 很缺。

## 参考链接
- patch 1/3 (scx_central): https://lore.kernel.org/all/20260827080738.829103-1-liwanwu@kylinos.cn/
- patch 2/3 (scx_flatcg): https://lore.kernel.org/all/20260827080738.829103-2-liwanwu@kylinos.cn/
- patch 3/3 (scx_qmap): https://lore.kernel.org/all/20260827080738.829103-3-liwanwu@kylinos.cn/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260827-011
date: '2026-08-27'
subject: "sched_ext: Fix timer pinning and return value in scx_central"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260827080738.829103-1-liwanwu@kylinos.cn>"
lore_url: "https://lore.kernel.org/all/20260827080738.829103-1-liwanwu@kylinos.cn/"
authors: [Wanwu Li]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260827080738.829103-1-liwanwu@kylinos.cn>"
    date: 2026-08-27
    summary: "3 补丁修 sched_ext 示例调度器的 timer flag 回退、返回值检查与 vtime 负增量钳位"
    review_outcome: "暂无 review"
upstream_commit: null
fixes_commit: "22a920209ab6"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 sched_ext 维护者 review"
contribution_opportunities:
  - kind: review
    description: "全仓 grep time_delta() 其它调用点排查同类钳位回归"
  - kind: testing
    description: "在 <6.7 内核验证 scx_central 的 timer_pinned 回退路径并回帖 Tested-by"
generated_at: "2026-09-07T22:05:00"
source_email_count: 3
related_articles: []
tags: [sched_ext, cgroup]
---
