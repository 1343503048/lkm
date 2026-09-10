---
id: sched-20260910-001
date: 2026-09-10
subject: 'sched/fair: A series of load balance patches to improve real-time performance
  of CFS tasks'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260910042950.1619727-1-jackzxcui1989@163.com>
lore_url: https://lore.kernel.org/all/20260910042950.1619727-1-jackzxcui1989@163.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-11T09:40:00'
authors:
- Xin Zhao
maintainers_involved:
- Vincent Guittot
- K Prateek Nayak
patch_series:
- version: v1
  msgid: null
  date: '2026-08-15'
  summary: 首发 10 补丁 RFC（当时仅 patch 09/10 被单独记录，真实 msgid 未获取到）。
  review_outcome: 首发时无 review 意见。
- version: v1-resend
  msgid: <20260910042950.1619727-1-jackzxcui1989@163.com>
  date: '2026-09-10'
  summary: RESEND 全部 10 补丁：1 通用修复，2/3 前置，4 定义 LB_PROMOTE feature，5 select_task_rq_fair_thin，6/7
    抢占式 active balance，8 去 avg_idle 检查，9/10 newly idle 尽力迁移。
  review_outcome: Vincent 拒绝 05/10 的新选核函数、指出应查 nr_idle_scan 并认可小 LLC 放宽扫描；Prateek
    质疑 01/10 的 overload 语义并给 rq->flag 替代、否定 03/10 的 commit message 论证（作者接受把清 flag
    移到开中断前）；Kayra 质疑 02/10 的 smp_processor_id 冗余论证并追问测试方法。
merge_assessment:
  likelihood: low
  blocking_issues:
  - 05/10 被 Vincent 明确拒绝：主线不接受再增加一个 select idle cpu 函数
  - 01/10、03/10 的 commit message 论证被 Prateek 指出不准确，需要重写方案或说明
  - 02/10 的冗余检查结论被 Kayra 质疑后作者尚未正面回应，且该补丁 subject 有 scbed/fair 笔误
  - 全部效果数据来自作者单一嵌入式平台，无第三方复现
  next_action: 作者按 Vincent 方向改做 nr_idle_scan 的小 LLC 自适应（或 want_affine 慢路径方案）、修正 01/10-03/10
    论证后发正式 v2，并考虑把前置修复 1/2/3/9 拆出独立推进
contribution_opportunities:
- kind: new_patch
  description: 实现 nr_idle_scan 按 LLC 规模放宽扫描上限的补丁——Vincent 明确说小核数场景可以放松，但无人认领
- kind: testing
  description: 在小 CPU 数嵌入式 arm64（CONFIG_HZ_250）平台复现不合理 CPU 空闲事件，独立验证 LB_PROMOTE 的事件消除与
    sys% 代价数据
- kind: review
  description: 分析 active_load_balance_cpu_stop() 中 smp_processor_id() 与 busiest_cpu
    的等价性，把 Kayra 质疑的结论写成可进 commit message 的论证
source_email_count: 22
related_articles:
- sched-20260815-001
tags:
- cfs
- load_balance
- topology
title: 'sched/fair: A series of load balance patches to improve real-time performance
  of CFS tasks'
layout: article
---

## TL;DR
Xin Zhao 重发（RESEND）了 10 补丁的 RFC 系列，引入 LB_PROMOTE 特性以消除低 HZ（CONFIG_HZ_250）嵌入式平台上 CFS 任务的「不合理 CPU 空闲」事件（>4ms 的调度延迟可完全消除），本次收到了 Vincent Guittot 与 K Prateek Nayak 的实质性评审：核心补丁 05/10（select_task_rq_fair_thin）被 Vincent 明确拒绝思路，03/10 的 commit message 论证被 Prateek 质疑，但讨论给出了可落地的替代方向（放宽小 LLC 场景的 nr_idle_scan），值得跟进。

## 背景与问题
嵌入式平台常用 CONFIG_HZ_250，测试发现大量「不合理 CPU 空闲」事件：CPU 进入 idle 持续时长 t 期间，存在可运行、不受 cgroup 限制的任务却超过 t 未被调度（t > 2.5ms）。作者测试显示 95% 以上此类事件短于 4ms，但仍有 4-5ms 甚至偶发 5-10ms 的实例；对实时系统而言，超过 4ms 的调度延迟会造成性能尖刺。所有补丁均来自对每个捕获到的不合理空闲事件的 ftrace 与负载均衡代码流日志分析。

## 技术方案
10 个补丁分层组织（引自封面信）：patch 1 解决与 LB_PROMOTE 无关的通用问题；patch 2、3 是独立的前置补丁，主要支撑 patch 6、7；patch 4 定义新 sched_feat `LB_PROMOTE`（features.h +24 行）；patch 5 引入面向嵌入式平台的 `select_task_rq_fair_thin()`；patch 6 改造 `active_load_balance_cpu_stop()` 使其可复用于抢占式 active balance；patch 7 实现 CFS 任务被抢占时触发 active balance；patch 8 移除 newly idle 路径的 avg_idle 提前退出检查；patch 9 是小优化、作为 patch 10 的前导；patch 10 让 newly idle 时尽力找到可迁移任务。总 diffstat：4 files changed, 224 insertions(+), 25 deletions(-)（core.c +3、fair.c +220/-25、features.h +24、sched.h +2）。该特性只影响 fair 任务，代价是 sys% 上升——用本会 idle 的 CPU 时间加速任务调度。

讨论中暴露的关键设计点：
- 05/10 的动机是 wake 路径快速路径只在 LLC 内选 idle CPU，对 CPU 数少的嵌入式机器不友好（难以跨 LLC 绑任务）。Vincent 指出主线已有 `sched_balance_find_dst_cpu()` 看得更宽，但需要拓扑设置 SD_BALANCE_WAKE；作者回应其 18 CPU、按 cluster 划分 LLC 的平台上该 flag 默认为 0，嵌入式项目一般不改。作者提出的折中：`want_affine = !wake_wide(p) && cpumask_test_cpu(cpu, p->cpus_ptr) && !sched_feat(LB_PROMOTE)`，LB_PROMOTE 开启时强制走慢路径。
- 01/10（rd->online != env->cpus 时不置 set_rd_overloaded）引出 Prateek 对 env.cpus 两种清空场景（LBF_DST_PINNED / LBF_ALL_PINNED）的完整梳理，他建议改为在 busiest 的 rq_lock 内置 rq->flag、由 add_nr_running() 选择性消费；Vincent 解释了 dest_cpu 被清空是防 can_migrate 失败时在少数 dst cpu 间 ping-pong，并认可 redo 时「busiest 保持清空、dst_cpu 可以加回」。
- 03/10（在 active_load_balance_cpu_stop() 末尾清 active_balance）：Prateek 指出 detach_one_task 后 TASK_ON_RQ_MIGRATING 已立即摘除 busiest 的 PELT 信号，commit message 论证不准确；作者补充真实动机是目的端负载在 attach 前未更新，若提前清 flag，另一 CPU C 可能对同一目的地重复触发 active balance，并接受「清 flag 应放在开中断之前」的批评。

## 版本演进与当前进展
- v1（2026-08-15 首发）：当时仅以单补丁形式被记录（见 sched-20260815-001），无 review 意见。
- v1 RESEND（2026-09-10，msgid `<20260910042950.1619727-1-jackzxcui1989@163.com>`）：内容同上，本次引发 Vincent、Prateek、Kayra Cizmeci 三人共 11 封讨论，作者当天逐条回应。当前进展：05/10 方案需推倒重来（转向 nr_idle_scan/慢路径思路），03/10 需改写 commit message 并把清 flag 移到开中断前，02/10 的 smp_processor_id() 冗余论证被 Kayra 质疑、尚未见作者正面回答（当天作者未回 02/10 的第二问）。

## Maintainer 意见与讨论焦点
- Vincent Guittot（05/10）："We don't want yet another select idle cpu function." 唯一合理解释是 nr_idle_scan 提前中止扫描，应去查为什么小规模场景下 nr_idle_scan 不能保留所有 CPU；后续补充：nr_idle_scan 是为数百 CPU 的大 LLC 设计的，「当只有几个核时，扫描数量可以放得更宽」——这实际上指出了一条可被主线接受的替代路径。
- K Prateek Nayak（01/10）：质疑对无法被帮助的 CPU 置 rd->overload 如何让 newidle balance 更高效；给出 rq->flag 替代方案；并向 Vincent 追问 LBF_DST_PINNED 清 dest_cpu 的原因（Vincent 已答复）。
- K Prateek Nayak（03/10）："I'm not convinced by the justification for this in the commit message"，至少应在开中断前清 flag。作者已接受。
- Kayra Cizmeci（02/10）：质疑 smp_processor_id() 检查冗余的结论——cpu_active(busiest_cpu) 与 smp_processor_id() 并非等价检查，要求在 commit message 中补充论证；（05/10）追问测试方法，作者给出了内核模块计时法。
- 注意：02/10 的 subject 存在笔误 "scbed/fair"（应为 sched/fair），尚无人指出。

## 合入评估
likelihood: low。RFC 阶段即遭两位核心维护者对关键补丁的方向性否定：05/10 被 Vincent 明确不要（yet another select idle cpu function），01/10、03/10 的论证被 Prateek 质疑。但讨论并未关门——Vincent 主动给出 nr_idle_scan 小 LLC 放宽的口子，01/10 的 rq->flag 方案与 redo 时加回 dst_cpu 的语义也形成了新共识。下一步需要作者按这些方向重构后发正式 v2（去 RFC），且 10 补丁应拆分推进：1/2/3/9 这类前置修复可独立先行。

## 效果评估
封面信给出两组数据（fillback 场景）：
- 60 秒事件分布对比：LB_PROMOTE 开启时三组测试 2.5-3ms/3-4ms/4ms+ 事件全部为 0；关闭时分别为 4/13/1、6/3/0、1/1/0。
- 25 分钟 × 15 轮端到端延迟：max 172（on）vs 180（off），median of avg 166 vs 167.68；代价是 sys%：max 9.68 vs 9.35，median of avg 8.81 vs 8.55。
- 05/10 讨论中作者补充的 select_task_rq_fair() 耗时测量（内核模块累计进出口时间差）：打补丁后 avg 460ns → 328ns（count 179226 vs 180836）。测量脚本存在 insmod 报错输出，数据可信度一般，仅供参考。
平台拓扑：18 CPU、多个 cluster（0-1、2-5、6-9、10-13、14-17），每 cluster 一个 LLC、无更细层级（作者原话如此，cluster 数与列举不完全一致）。

## 我可以参与的点
- 顺着 Vincent 给出的方向做 nr_idle_scan 的 LLC 规模自适应（小 LLC 放宽扫描上限）并发补丁，这是讨论中明确「可以被接受」但目前无人认领的改动（new_patch）。
- 在小 CPU 数嵌入式 arm64 板（CONFIG_HZ_250）上复现「不合理 CPU 空闲」事件并验证 LB_PROMOTE 数据，当前所有数据均来自作者单一平台（testing）。
- 回答/分析 Kayra 对 02/10 的质疑：active_load_balance_cpu_stop() 运行在 busiest CPU 的 stopper 上时 smp_processor_id() 与 busiest_cpu 是否恒等，把结论写成可进 commit message 的论证（review）。

## 参考链接
- lore thread（RESEND 封面）: https://lore.kernel.org/all/20260910042950.1619727-1-jackzxcui1989@163.com/
- Vincent 对 05/10 的否定与 nr_idle_scan 方向: https://lore.kernel.org/all/CAKfTPtAmB8pQms38CWoXPmG7bL64mY8L7Gyd=_LvNoM7wvEgdA@mail.gmail.com/
- Prateek 对 01/10 的分析: https://lore.kernel.org/all/7735bbdb-2465-4ed3-9486-be9b82f3f42a@amd.com/
- Prateek 对 03/10 的质疑: https://lore.kernel.org/all/f771bdd6-3e4b-47db-bfa9-b04bd58b9a06@amd.com/
- 作者拓扑与 SD_BALANCE_WAKE 说明: https://lore.kernel.org/all/20260910155635.2101399-1-jackzxcui1989@163.com/
- 首发 v1（08-15）记录: 见 related_articles sched-20260815-001（当时 lore 链接未获取到）
