# sched/cache: Check reduced capacity before alb_break_llc()

## TL;DR
Zhan Xusheng 发单补丁修 cache-aware 调度的一个放置缺陷：当源 CPU 的容量被外部因素（如 hrtimer 抢占、IRQ 记账）压减后，仍会被 `alb_break_llc()` 以「LLC 优先」为由拦下来不被迁移，任务长期滞留在低容量 CPU 上。补丁把「reduced capacity」检查挪到 `alb_break_llc()` 之前，让容量降低先于 LLC 偏好生效。作者用 QEMU（IRQ_TIME_ACCOUNTING + hrtimer 抢占）复现：任务 20s 内停在 CPU0 只能跑 1.8e7 iters/s，关闭 cache-aware 后 4.6e7 iters/s。Chen Yu（Intel）认可方向但要求补 benchmark、并考虑「调 `alb_break_llc()` 本身」的更小改动方案；Kayra Cizmeci 已给 **Reviewed-by**。

## 背景与问题
cache-aware 调度器在 `CONFIG_SCHED_CACHE` 下会把任务聚到 preferred LLC；`alb_break_llc()` 在 `env->src_rq->nr_running <= 1` 时直接 `return true`，声称「不需要 break」。问题在于：这个判断**不看容量**——若源 CPU 因 hrtimer 高频抢占（配 IRQ_TIME_ACCOUNTING 时的贬值）或热管理而 `capacity` 被压减（`reduced_cap_alb()` 才命中），LLC 偏好仍把任务钉在己方 LLC 上，宁可跨 LLC 也不迁移，造成负载失衡。作者读代码发现该路径，并在 QEMU `-smp 4,sockets=2,cores=2` + IRQ_TIME_ACCOUNTING 下复现：一个模块每 1ms 在 CPU0 的 hrtimer 栈里耗 600us，CPU1 跑钉死的忙循环，测试进程（一忙一睡两线程）初始钉 CPU0、随后放开到全部 CPU，结果 20s 内任务一直留在 CPU0。

## 技术方案
把 reduced-capacity 检查提前：在 `alb_break_llc()` 之前先判断源 CPU 容量是否被压减（`reduced_cap_alb()` 语义），命中则先于 LLC 偏好触发迁移。作者澄清了顺序细节：只有 `alb_break_llc()` 返回 0（会拦下迁移），`asym_active_balance()`/`imbalanced_active_balance()` 都只返回 1，所以只需把 `alb_break_llc()` 挪到 capacity 检查之后即可。补丁基于 `ee92b7ef4c1e`（"sched/cache: Honor asym packing over cache aware scheduling on hybrid systems"），应用于 tip/master。

被考虑的备选（Chen Yu 提出）：与其挪检查，不如直接「调 `alb_break_llc()` 本身的 `nr_running <= 1` 判断」更安全；Chen Yu 还提供了「引入 helper 比较 src/dst 容量、无功能变更」的两片补丁作对照。作者实测 Chen Yu 的两片补丁后，任务仍被 `alb_break_llc()` 后半段的 `can_migrate_llc()` 禁止离开 preferred LLC，说明仅调 `nr_running` 判断不足以解决问题。

## 版本演进与当前进展
*current_version: v1*（2026-10-29，`<20261029023650.3404429-1-zhanxusheng1024@gmail.com>`）。单补丁首帖当日即获多轮 review：Chen Yu 追问复现手段并给出替代方案，作者逐个回应，Kayra 最终 `Reviewed-by`。尚无 v2。

## Maintainer 意见与讨论焦点
- **Chen Yu（Intel，非 maintainer）**：主要顾虑是「把容量检查提前，会完全无视任务的 LLC 偏好」，这是「CPU 容量 vs 远端 LLC 缓存重建 / 跨 LLC 访问延迟」的权衡，可能 workload 相关；要求作者给出找到问题的 benchmark/平台，他好跑 hackbench/tbench/schbench/netperf 评估；并建议「调 `alb_break_llc()` 的 `nr_running <= 1` 分支」可能是更安全的最小改动。
- **Kayra Cizmeci（reviewer）**：先误会了补丁所基于的树，作者澄清后给了 `Reviewed-by: Kayra Cizmeci`。
- **Zhan Xusheng**：说明复现基于读代码 + QEMU，且试过 Chen Yu 的两片补丁仍不能解决（`can_migrate_llc()` 仍禁止迁移），论证「仅调 nr_running 不够」。
- 未解决焦点：Chen Yu 要的「真实 workload 上的 benchmark 数据」还没给出；「容量优先 vs LLC 优先」的取舍仍需数据佐证。

## 合入评估
*likelihood=medium*。补丁方向获 Kayra `Reviewed-by`，作者对 Chen Yu 的技术质疑给出了可复现的回应，是壁垒。但 Chen Yu 明确要 benchmark 数据佐证「容量优先」相对「LLC 优先」的收益，且尚未有人（含维护者）直接拍板。*blocking_issues*：缺真实 workload benchmark；`nr_running<=1` 分支是否应当一并修正仍待定。*next_action*：作者补 hackbench/tbench/schbench/netperf 数据，说明容量优先 vs LLC 优先的权衡结论。

## 效果评估
作者 QEMU 复现：任务在 cache-aware 调度下 20s 停在 CPU0，约 1.8e7 iterations/s，关闭 cache-aware 后 4.6e7 iterations/s（约 -61% 的吞吐损失）。这是作者自己搭的微型复现（hrtimer + IRQ_TIME_ACCOUNTING），非标准 benchmark；Chen Yu 点名要的 hackbench/tbench/schbench/netperf 数据尚未提供。

## 我可以参与的点
- **testing**：跑 Chen Yu 点名的 hackbench/tbench/schbench/netperf（或带上 IRQ_TIME_ACCOUNTING / hrtimer 抢占扰动的扩展场景），对比补丁前后，为「容量优先 vs LLC 优先」提供真实数据。
- **review**：核对 `alb_break_llc()` / `can_migrate_llc()` 的返回路径，确认「只有 alb_break_llc() 返回 0」的判断、以及把容量检查提前是否遗漏了 `asym`/`imbalanced` 分支的交互。

## 参考链接
- lore thread（补丁）: https://lore.kernel.org/all/20261029023650.3404429-1-zhanxusheng1024@gmail.com/
- Chen Yu 的质疑: https://lore.kernel.org/all/auMBWAGx04w5h80o@chenyu-dev/
- Kayra 的 Reviewed-by: https://lore.kernel.org/all/auL_-u5bHv-Tp6hh@scheduler.schedules/

---
id: sched-20261029-007
date: 2026-10-29
subject: "sched/cache: Check reduced capacity before alb_break_llc()"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261029023650.3404429-1-zhanxusheng1024@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261029023650.3404429-1-zhanxusheng1024@gmail.com/"
authors: [Zhan Xusheng]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261029023650.3404429-1-zhanxusheng1024@gmail.com>"
    date: 2026-10-29
    summary: "把 reduced-capacity 检查挪到 alb_break_llc() 之前，让容量降低先于 LLC 偏好触发迁移"
    review_outcome: "Kayra Reviewed-by；Chen Yu 要求补 benchmark 并评估调 nr_running 分支的替代方案"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "缺真实 workload 的 benchmark 数据佐证容量优先 vs LLC 优先的取舍"
    - "nr_running <= 1 分支是否应一并修正待定"
  next_action: "作者补 hackbench/tbench/schbench/netperf 数据并回应权衡结论"
contribution_opportunities:
  - kind: testing
    description: "跑 hackbench/tbench/schbench/netperf（可加 IRQ_TIME_ACCOUNTING 扰动）对比补丁前后"
  - kind: review
    description: "核对 alb_break_llc()/can_migrate_llc() 返回路径与容量检查提前后与 asym/imbalanced 分支的交互"
generated_at: "2026-10-30T09:30:00"
source_email_count: 7
related_articles: []
tags: [load_balance]
---