---
id: sched-20260801-004
date: 2026-08-01
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<uid-14197@qq-imap>"
lore_url: unknown
authors: [Shubhang Kaushik]
maintainers_involved: [K Prateek Nayak, Chris Mason, Madadi Vineeth Reddy]
current_version: v3
patch_series:
  - version: v1
    msgid: unknown
    date: unknown
    summary: "利用已有的 last_wakee / wake_wide() 状态识别窄范围的互惠 WF_SYNC 唤醒（A 唤醒 B、B 唤醒 A 交替），对这类 handoff 直接偏好 waker CPU"
    review_outcome: "未获取到 v1 的具体 review 内容"
  - version: v2
    msgid: unknown
    date: unknown
    summary: "在 v1 基础上迭代"
    review_outcome: "Chris Mason 建议把 SMT 系统也纳入考虑；Madadi Vineeth Reddy 指出应从 SMT 侧同样处理该问题"
  - version: v3
    msgid: unknown
    date: 2026-07-28
    summary: "把直接偏好 waker CPU 的行为限定在 !sched_smt_active()；SMT 系统继续走原有 wake_affine() 与 select_idle_sibling() 路径。仅在 waker CPU 上没有其他可运行 fair 任务、且在非对称算力系统上 wakee 能放得下时才生效"
    review_outcome: "K Prateek Nayak 认为不应按 SMT 与否二分，应把判断下推进 select_idle_sibling()、在已知 test_idle_core() 结果处统一决策，并给出了完整的替代 diff（SMT-2 上轻度测试，perf bench sched pipe 平均约 10% 提升）"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["K Prateek Nayak 提出了结构不同的替代实现并已有可用 diff，作者的 !sched_smt_active() 二分法未获认可", "同期存在 Madadi Vineeth Reddy 的 SMT 侧独立 patch，三条路径需要收敛", "Prateek 的替代实现自称仅在 SMT-2 上轻度测试，两套方案都缺少充分的跨平台数据"]
  next_action: "作者需要在『维持 v3 的 non-SMT 限定』与『采纳 Prateek 下推进 select_idle_sibling() 的统一实现』之间做出选择并发 v4；社区需要先就这三条路径的边界达成一致"
contribution_opportunities:
  - kind: testing
    description: "对比测试三套实现（v3 的 non-SMT 限定、Prateek 的 select_idle_sibling 下推版、Vineeth 的 select_idle_core 版）在同一批机器上的表现，这是当前 thread 最缺、也最能推动收敛的输入"
  - kind: review
    description: "审阅 Prateek diff 中 select_idle_smt() 从 sched_domain_span(sd) 改为 rd->span 的语义变化——从 LLC 域放宽到 root domain 是否会在 isolcpus / cpuset 隔离场景下引入越界选择"
generated_at: "2026-08-02T00:55:00"
source_email_count: 1
related_articles: []
tags: [cfs, load_balance, perf, arm64, hyperthreading]
---

## TL;DR

Shubhang Kaushik (Ampere) 试图让 pipe 式乒乓负载的互惠同步唤醒直接留在 waker CPU 上，在 80 核非 SMT Ampere Altra 上 `perf bench sched pipe` 提升约 30%。但 v3 采用的「非 SMT 才生效」二分法遭到 K Prateek Nayak 的结构性异议，后者给出了一份下推进 `select_idle_sibling()` 的替代实现——方案路线尚未收敛，v4 走向未定。

## 背景与问题

pipe 式的乒乓（ping-pong）负载中，整体开销可能被 handoff 成本主导。这类场景下把 wakee 放到一个空闲 CPU 上，反而比让这对任务共用同一个 runqueue 更慢——因为迁移带来的 cache miss 和 IPI 开销超过了并行执行的收益。

现有的 `wake_affine()` + `select_idle_sibling()` 路径没有识别这种模式的能力：它倾向于找一个真正空闲的 CPU，而不会意识到「waker 马上就要睡了，让 wakee 就地接手反而更划算」。

## 技术方案

利用调度器**已有**的 `last_wakee` 与 `wake_wide()` 状态来识别「窄范围的互惠 WF_SYNC 唤醒」，即如下交替模式：

```
A 唤醒 B
B 唤醒 A
A 唤醒 B
...
```

当 wake-affine 域允许 `SD_WAKE_AFFINE` 时，对这类窄互惠 handoff 直接偏好 waker CPU。生效条件有两个约束：waker CPU 上没有其他可运行的 fair 任务；在非对称算力系统上 wakee 必须能放得下（`task_fits_cpu`）。

不复用新状态、直接借助已有的 `last_wakee` 是这个方案的优点——零额外内存开销。

**核心争议在于作用范围的划定方式**。v3 选择用 `!sched_smt_active()` 做二分：非 SMT 系统走新路径，SMT 系统原样走老路径。K Prateek Nayak 认为这个切分维度不对，他给出的替代 diff 把判断下推进 `select_idle_sibling()`，在**已经知道 `test_idle_core()` 结果之后**再决策：

- 若 `has_idle_core` 为真，说明有完全空闲的 core 可用，正常走 SIS；
- 若为假，才考虑两件事：先尝试在 prev 所在 core 上找空闲 SMT 兄弟（cache 热）；再判断是否是通过了 WA_IDLE 的同步唤醒对，若 `target == this_cpu && p->last_wakee == current && (target_rq->nr_running - cfs_h_nr_delayed(target_rq)) <= 1 && asym_fits_cpu(...)`，则直接返回 target，把两者临时叠在同一 CPU 上。

这个改法的理由是：「没有空闲 core」本身才是「叠在一起更划算」的真正判据，而不是「有没有 SMT」。Prateek 的 diff 还顺带把 `select_idle_smt()` 的入参从 `struct sched_domain *sd` 改为 `struct root_domain *rd`（span 检查从 `sched_domain_span(sd)` 改为 `rd->span`），并在其中加入 `sched_asym_cpucap_active() && !task_fits_cpu(p, cpu)` 的过滤。

## 版本演进与当前进展

- **v1 / v2**：基于 `last_wakee` / `wake_wide()` 识别互惠同步唤醒并偏好 waker CPU。v2 阶段 Chris Mason 提出 SMT 系统的处理建议，Madadi Vineeth Reddy 也指出应从 SMT 侧同样解决该问题。
- **v3**（2026-07-28 发出，baseline v7.2-rc5）：唯一的 changelog 条目是把直接偏好 waker CPU 的行为限定在 `!sched_smt_active()`，SMT 系统继续走原有路径。
- **2026-07-30**：K Prateek Nayak 回复，提出下推进 `select_idle_sibling()` 的替代方案并附完整 diff。
- **2026-08-01 12:03**：Madadi Vineeth Reddy 在此 thread 中说明他已就 SMT 侧单独发出 patch（见本日 003 号文章），并给出链接。

当前 thread 的状态是：作者尚未对 Prateek 的替代方案表态，v4 未发。

## Maintainer 意见与讨论焦点

**K Prateek Nayak（AMD，CFS 唤醒路径的活跃 reviewer）**是本轮的关键异议方。他没有 NAK，措辞也很建设性（"Building on top of Chris' suggestion on v2..."），但实质上提出了一个**结构不同的实现**，而不是对 v3 的增量修改建议。这一点很重要：他不是在要求作者补数据或改细节，而是认为切分维度本身选错了。他还给出了自己的测试结果：在 SMT-2 系统上轻度测试，`perf bench sched pipe -l 1000000` 平均约 **10%** 提升——但他自己标注了 "Lightly tested"。

**Madadi Vineeth Reddy（IBM）**从 v2 起就主张 SMT 侧也需要处理，并已于 08-01 独立发出 `select_idle_core()` 侧的 patch。他在本 thread 中的回复本质上是在说明「你限定 non-SMT 之后留下的那半边，我用另一个 patch 补上了」。

**Chris Mason** 在 v2 中的建议是 Prateek 方案的起点，但本日邮件中未见其直接发言。

需要如实指出的分歧状态：**同一个问题现在有三条技术路径在并行推进**（v3 的 non-SMT 限定、Prateek 的 SIS 下推、Vineeth 的 select_idle_core 改造），彼此在功能上有重叠。社区尚未就「哪一条是主线」达成一致，这是比任何单个技术细节都更实质的阻碍。

## 合入评估

合入可能性 **medium**。方案要解决的问题是真实的、收益数字也不小（30%），但当前卡在路线选择上：

1. **v3 的形态大概率不会原样合入**。Prateek 已经给出了他认为更合理的实现并附可用 diff，作者要么采纳、要么给出坚持二分法的充分理由。
2. **三条路径必须收敛**。在 Vineeth 的 SMT 侧 patch 与 Prateek 的统一改法都在桌面上的情况下，maintainer 不太可能分别接受三个部分重叠的改动。
3. **两套方案的测试都不充分**。作者只有 Ampere Altra 非 SMT 的数据，Prateek 只在 SMT-2 上"轻度测试"，都缺少跨平台横向对比。

下一步是作者发 v4 明确路线选择，或者三方在 thread 中先就边界划分达成共识。

## 效果评估

**作者数据（v3）**：80 核非 SMT Ampere Altra，`perf bench sched pipe -l 1000000` 提升约 **30%**，40 轮平均。Hackbench、schbench、SPECjBB 未见实质回退。baseline 为 v7.2-rc5。这批数据的样本量（40 轮）比较扎实，但**仅覆盖单一非 SMT 平台**。

**Prateek 数据（替代实现）**：SMT-2 系统上 `perf bench sched pipe -l 1000000` 平均约 **10%** 提升，他自己标注为 "Lightly tested"，未给出轮数与机器细节。

两组数字来自不同实现、不同平台，**不能直接比较**。目前没有任何一方在同一批机器上跑过两套实现的横向对比。

## 我可以参与的点

- **测试（当前最有价值的贡献）**：在同一批机器上横向对比三套实现——v3 的 non-SMT 限定、Prateek 的 `select_idle_sibling()` 下推版、Vineeth 的 `select_idle_core()` 版。覆盖非 SMT（Ampere Altra 类）、SMT-2（x86 / arm64）、SMT-8（POWER）三种布局，跑 `perf bench sched pipe`、hackbench、schbench。这正是 thread 目前最缺、也最能推动路线收敛的输入。
- **Review**：Prateek diff 中 `select_idle_smt()` 的 span 检查从 `sched_domain_span(sd)` 放宽到 `rd->span`，这是从 LLC 域扩大到 root domain 的语义变化。在 isolcpus / cpuset 隔离场景下，这是否会选到本不该被选的 CPU，值得核对——原注释明确提到 isolcpus 会导致兄弟线程不全在域内，改成 root domain span 之后这个约束的强度发生了变化。

## 参考链接

- lore thread (v3): 未获取到
- Vineeth 的 SMT 侧 patch: https://lore.kernel.org/lkml/20260801035532.260625-1-vineethr@linux.ibm.com/
- Vineeth 在 v2 中提出 SMT 侧思路: https://lore.kernel.org/all/60a584c5-25ac-4077-a725-a2f9ee74318d@linux.ibm.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
