# sched/cache: Avoid cache-aware scheduling for memory-heavy processes

## TL;DR

Chen Yu（Intel）在 cache-aware scheduling v4（22 补丁）系列中提出 patch 17/22：对 RSS 超过 LLC（last-level cache）容量的 memory-heavy 进程暂停 cache-aware 聚合，改用 RSS/足迹门控 + 迟滞避免「先聚合再被 wake_affine 锁死在本地 LLC」的回归。Red Hat 的 Jirka Hladky 与 Phil Auld 复测确认：RSS 门控修复了 VM 用例 20% 打包收益的回归（默认容差 22.47s vs 21.81s），代价是聚合前约 16s 的启动延迟（非永久）。属对已合入 cache-aware 特性的修正，方向获各方认可。

## 背景与问题

cache-aware scheduling 把任务按 LLC 聚合以提升缓存局部性，但对「内存占用超 LLC」的进程会产生回归：这些进程先被聚合到同一 LLC，随后 wake_affine 把 wakee 反复放到 waker 所在的同一 LLC；而负载均衡跨 LLC 扩散太慢（active load balance 需超 `cache_nice_tries+2=4` 次失败、min_interval 192ms，288 核 2 node 约 1.4s 才拉走一个任务）。Red Hat（Phil Auld）在 288-CPU 机器上报告：VM 用例丢失 20% 打包收益。根因是对 memory-heavy 进程不该做聚合。

## 技术方案

- **patch 17/22（Chen Yu）**：RSS 超过 LLC 的进程不再聚合；RSS 门控只在首次 address-space sweep 完成（约 16s）前生效，之后由 fault-based 足迹估计接管、可重新分组，故最坏只是有界启动延迟。
- **配套（Tim Chen，第二补丁）**：当足迹历史为 0 时回退到 RSS 判定。
- **迟滞（hysteresis）**：Chen Yu 认同「对 RSS/足迹应用迟滞」以避免阈值附近抖动；并指出「大 RSS 但不共享数据的进程」是 cache-aware 不应干预的信号，可由用户态 prctl 或 NUMA balancing 的 numa_group 提供。

## 版本演进与当前进展

*current_version: v4（cache-aware scheduling 系列，22 补丁；本 patch 为 17/22）*。当日无新版本；为 Red Hat 复测 + 设计讨论（4 封）。

## Maintainer 意见与讨论焦点

- **Chen Yu（作者，Intel）**：自建 SRF 复现用例（64 spinning 线程绑 LLC0 后释放 affinity，采样放置速率），确认根因是「聚合后被 wake_affine 留 + 负载均衡扩散太慢」而非 wakeup 本身；确认 RSS 门控即可消除回归、accumulation 只决定之后决策正确性。
- **Jirka Hladky（Red Hat tester）**：给出完整对照数据（见下），确认补丁在 CAS off 时与 stock 一致（惰性），CAS on 时行为变化仅限「RSS 超 LLC 的进程」。
- **Phil Auld（Red Hat 报告者）**：感谢测试、认可两个修复都有价值，追问「其它测试是否回归」。
- 无 NAK；方向获认可。

## 合入评估

*likelihood=medium*。针对已合入 feature 的回归修正、有 Red Hat 独立复测背书，方向收敛；但属 22 补丁 v4 系列的一环，需随整个系列迭代/评审。*blocking_issues*：① 累积（accumulation）与迟滞策略待落地；② 系列整体尚未合入。*next_action*：作者按「RSS 门控 + 迟滞 + 共享检测」方向出 v5，Red Hat 继续全量回测。

## 效果评估

Jirka Hladky 在 288-CPU（2 node）机器上，n=5 中位数：

- VM：补丁内核默认容差丢失 20% 打包收益（22.47s vs 21.81s CAS off），`aggr_tolerance=4` 后回到 17.70s；门控在 ~0.1s 内拒绝、~16s 首扫后解除（非永久）。
- NAS MG D 1x64：stock OFF 26.45s / stock ON 41.78s / patched OFF 26.38s / patched ON 26.47s（RSS 回退消除回归）。
- NAS MG C 1x4：9.34 / 11.99 / 9.38 / 9.36s；CAS off 时补丁与 stock 在全部用例上 within noise。
- 复现 Chen Yu 模型：LLC0→LLC1 扩散间隔实测 1.59s vs 模型 1.44s（<10%）。

## 我可以参与的点

- **testing**：在 Intel SRF/AMD 多 LLC 平台上跑 memory-heavy 进程（RSS>LLC）的 wake_affine 场景，验证 RSS 门控 + 迟滞的组合不引入新的聚合饥饿。
- **review**：就「大 RSS 不共享进程 → 应跳过 cache-aware」这一信号的来源（prctl vs numa_group）给出取舍意见。

## 参考链接

- lore（patch 17/22 与讨论）: 未获取到（patch 正文不在此前拉取窗口，仅回帖在缓存）
- Jirka 的复测报告: https://lore.kernel.org/all/CAE4VaGBf__ktY48MbL3FkG4TvQaAQDUdhRKphjivPuou_MmhRA@mail.gmail.com/
- Chen Yu 的复现与回应: https://lore.kernel.org/all/av2tdXOhCjMgLHsq@chenyu-dev/

---
id: sched-20261118-018
date: '2026-11-18'
subject: "sched/cache: Avoid cache-aware scheduling for memory-heavy processes"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: null
authors: [Chen Yu]
maintainers_involved: []
current_version: v4
patch_series:
  - version: v4
    msgid: null
    date: null
    summary: "RSS 超 LLC 的进程暂停 cache-aware 聚合（系列 patch 17/22）"
    review_outcome: "Red Hat 复测确认修复回归，方向获认可"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["accumulation 与迟滞策略待落地", "系列整体未合入"]
  next_action: "作者按 RSS 门控 + 迟滞 + 共享检测出 v5"
contribution_opportunities:
  - kind: testing
    description: "多 LLC 平台跑 memory-heavy 进程验证 RSS 门控 + 迟滞"
  - kind: review
    description: "就大 RSS 不共享进程的跳过信号来源（prctl vs numa_group）取舍"
generated_at: "2026-11-19T09:00:00+08:00"
source_email_count: 4
related_articles: []
tags: [load_balance, numa_balancing, cgroup]
---
