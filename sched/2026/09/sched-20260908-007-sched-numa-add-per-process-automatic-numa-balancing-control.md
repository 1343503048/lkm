# sched/numa: Add per-process automatic NUMA balancing control

## TL;DR

Li Zhe（ByteDance）在 09-08 20:24 发出 4 补丁（无 v 前缀，即 v1）：给自动 NUMA 平衡加一个 **prctl 级别的 per-process 开关**，让个别进程能整体退出 NUMA 扫描与调度侧 locality 统计，同时把 `kernel.numa_balancing` 保留为管理员的硬总闸。设计上刻意选了「弱且可预测」的形状：两态、无 default 态、`PR_GET_*` 只回配置值不回生效值、模式存进 `signal_struct`（线程组语义），热路径读的是 `task_struct` 上的一份调度快照。作者还明确对比并放弃了 2023 年两版 prctl 提案（per-mm + 三态 + 允许 per-process 覆盖全局 static key）与 Chen Yu 的 per-cgroup 提案。本日向无人回帖，属于「新增 uAPI、动机叙述充分但零 review」的早期状态。

## 背景与问题

cover 第一段就给出用例形状：

> Automatic NUMA balancing is controlled globally through the kernel.numa_balancing sysctl and can be influenced indirectly through memory policy. That works well as a system default, but it is too coarse for workloads where a launcher wants most processes to use the default policy while a selected process opts out because it already manages NUMA placement or cannot afford the sampling overhead.

也就是「launcher 拉起大多数进程用默认策略，但选中的某个进程自己管 NUMA 放置、或吃不起采样开销」。现状只有两个粒度可选：全局 sysctl（一关全关）与 memory policy（间接、且语义不是「关掉自动平衡」）。

作者列了三条前案并说明为什么不照抄（这一段的诚实程度是本系列最大的优点，链接都在 cover 里）：

- **[1] Chen Yu 的 per-cgroup 提案**（`20250625102337.3128193-1-yu.c.chen@intel.com`）：加 cgroup-local enable 旋钮 + `NUMA_BALANCING_CGROUP` 模式（默认关闭、按 cgroup 打开）。cover 转述当时的讨论共识：自动 NUMA 平衡本来就是 task/process 粒度工作的、这个旋钮不是资源控制属性、`sched_setattr()` 或 `prctl()` 这类 per-task 接口更合适，cgroup/cpuset 应该继续只描述分组与放置域。
- **[2][3] 2023 年的两版 prctl 提案**（`20230412140701.58337-1-ligang.bdlg@bytedance.com`、`20230412141127.59741-1-ligang.bdlg@bytedance.com`）：per-mm 模式 + disabled/enabled/default 三态 + `/proc/<pid>/status` 里的 `NumaB_mode`，并且改了全局 static key 处理，使 per-process enable 能覆盖全局 sysctl。

本系列被作者称为「a more conservative variant to preserve existing administrator and workload expectations」，四条取舍逐条给了理由：保留 sysctl 作 hard off switch；两态而不是三态，避免暴露一个含义依赖全局策略、容易被误读的 "default"；配置存 `signal_struct` 以获得显式线程组语义，同时不让更多无谓共享 mm 的非 `CLONE_THREAD` 用户被绑上同一策略。

## 技术方案

**patch 1/4（内部机制，7 files，+134/-4）**

状态分两处放，是本系列最关键的设计取舍：

- `struct signal_struct` 新增 `bool numa_balancing_enabled;`（`CONFIG_NUMA_BALANCING` 下）——**用户可见的配置值**。
- `struct task_struct` 新增 `bool numa_balancing_sched_enabled;`——注释写明是「Scheduler snapshot of signal_struct::numa_balancing_enabled … not part of the userspace-visible process mode」。快照的用意是热路径零额外开销地读取，并让 runqueue 计数保持一致。

继承语义：fork 继承父进程模式、`CLONE_THREAD` 共享、exec 保留；`copy_process()` 在 `p` 发布之前于 `current->sighand->siglock` 下初始化两处状态（非 `CLONE_THREAD` 时才写新 `p->signal`）。

设置路径 `task_numa_balancing_set_current()`（`kernel/sched/core.c`，紧跟 `sched_setnuma()`）：

```c
+static void sched_numa_balancing_change_task(struct task_struct *p, bool enabled)
+{
+	guard(task_rq_lock)(p);
+	scoped_guard (sched_change, p, DEQUEUE_SAVE)
+		WRITE_ONCE(p->numa_balancing_sched_enabled, enabled);
+}
+
+int task_numa_balancing_set_current(bool enabled)
+{
+	static DEFINE_MUTEX(task_numa_balancing_mutex);
+	...
+	guard(mutex)(&task_numa_balancing_mutex);
+	if (WARN_ON_ONCE(!lock_task_sighand(current, &flags)))
+		return -ESRCH;
+	old_enabled = current->signal->numa_balancing_enabled;
+	if (old_enabled != enabled)
+		WRITE_ONCE(current->signal->numa_balancing_enabled, enabled);
+	unlock_task_sighand(current, &flags);
+	if (old_enabled != enabled) {
+		sched_numa_balancing_change_task(current, enabled);
+		read_lock(&tasklist_lock);
+		for_other_threads(current, t)
+			sched_numa_balancing_change_task(t, enabled);
+		read_unlock(&tasklist_lock);
+	}
+	return 0;
+}
```

作者的理由：串行化并发更新，先改 signal 模式，立即更新调用线程，再在 `tasklist_lock` 读侧走其余线程用 `sched_change` 更新，「This keeps `rq->nr_numa_running` and `rq->nr_preferred_running` in sync without adding extra hot-path locking.」另外 `kernel/sched/core.c` 中 `__sched_setscheduler` 上方的字段变更注释清单里补了 `task_numa_balancing_set_current()` 一行，把它归入「会改任务字段并需要 dequeue/enqueue 的接口」。

热路径一共 9 处接入点，全部是 `task_numa_sched_snapshot_enabled()` 早退（fair.c +36/-4）：`get_pref_llc()`、`get_scan_cpumasks()`、`task_numa_fault()`、`task_tick_numa()`、`update_scan_period()`、`migrate_degrades_locality()`、`task_numa_compare()`（跳过 swap 候选），以及 `account_numa_enqueue()/account_numa_dequeue()` 把 `nr_numa_running`/`nr_preferred_running` 的累加条件与 enabled 相与。

语义边界作者写得很明确，也是最容易被 review 挑的一句：

> Already-installed NUMA hinting PTEs, queued scan work, and other NUMA state are not actively cleared; they drain or age out naturally as the disabled state takes effect. This keeps the slow-path ABI simple and avoids expensive address-space surgery.

**patch 2/4（uAPI，2 files，+24）**：`PR_SET_NUMA_BALANCING = 82` / `PR_GET_NUMA_BALANCING = 83`，取值为 `PR_NUMA_BALANCING_DISABLE = 0` / `PR_NUMA_BALANCING_ENABLE = 1`，`kernel/sys.c` 里做常规参数校验后转发到 `task_numa_balancing_set_current()`。ABI 说明照抄了上面的取舍：

> PR_GET_NUMA_BALANCING returns the configured process mode, not the effective state after combining the global sysctl/static key and memory policy restrictions. This keeps the ABI weak and predictable: a process can observe and restore the value it configured, while administrators retain kernel.numa_balancing as the top-level hard-off switch.

**patch 3/4 / 4/4 正文未收到本批缓存**，从 cover 得知标题为 `proc: Report process NUMA balancing mode`（`fs/proc/array.c | 16 ++`，即在 `/proc/<pid>/status` 暴露模式）与 `Documentation: Describe per-process NUMA balancing control`（`sysctl/kernel.rst | 16 ++`、`proc.rst | 6 ++`），具体实现与文案未获取到。整系列 diffstat：12 files changed, 201 insertions(+), 4 deletions(-)。

我按主线核对了编号前提：本地 `include/uapi/linux/prctl.h` 里已用最大编号是 81（`PR_SET_CFI`），82/83 正好接上、与补丁上下文（`PR_CFI_DISABLE`/`PR_CFI_LOCK` 之后）一致，本批邮件里没有出现编号冲突。

## 版本演进与当前进展

- 09-08 20:24:42/43/44 Li Zhe 连发 cover（`<20260908122446.56708-1-lizhe.67@bytedance.com>`）、1/4、2/4；3/4、4/4 未进本批缓存。
- 标题无版本前缀，即 v1；无 `Changes in vN`，因为本系列自身无前版。cover 讨论的是**别人**的前案（[1][2][3]），不是自己的历史版本。
- 本日向无人回帖，无 review、无 Ack、无 NAK，未见 tip/stable 收录。

## Maintainer 意见与讨论焦点

未获取到——本批只有作者自己的 cover + 2 个补丁，没有任何维护者或同事回应，讨论焦点尚未形成。以下是我按补丁本身读出的、几乎一定会被问到的点（属我的判断，不是邮件里的分歧）：

- **新 uAPI 的准入**：prctl 一直是「加进去就永久背住」的接口。作者用「weak and predictable」自辩（`PR_GET_*` 只回配置值、不回生效值），但「get 到的值与实际行为不一致」本身也可能被要求改成显式三态或至少在文档里写清判定式。这与 2023 版选择 `default` 态的理由恰好相反，两个方向谁对，需要调度维护者表态。
- **与 `numa_group` 的粒度错配**：自动 NUMA 平衡的决策单位实际是 `numa_group`（共享 mm 的线程组会被合并），而本系列的开关单位是线程组。cover 声称「automatic NUMA balancing already operates at task/process granularity」是引用 [1] 的讨论结论，但补丁里没有任何一处处理同 mm 的**其他**线程组仍继续扫描、从而通过 `numa_group` 把统计与迁移决策带回本进程的情况。这一层是本系列语义上最大的未论证处。
- **`tasklist_lock` 读侧 + 逐线程 `guard(task_rq_lock)` 的锁序**：作者在 `read_lock(&tasklist_lock)` 下依次为每个线程取 `task_rq_lock`，而主线 `task_rq_lock()` 会先拿 `pi_lock` 再拿 rq 锁；一次性遍历整棵线程链表并逐个串行化，慢路径代价与「持锁遍历」的合理性大概率会被 Peter 或 Neeraj 追问（对照主线更常见的 `rcu_read_lock()` + `for_other_threads` 或先收集再逐个 `sched_change`）。
- **`WARN_ON_ONCE(!lock_task_sighand(...))`**：`lock_task_sighand()` 失败在 exit race 下是正常路径，主线多数写法是直接 `return -ESRCH`，加 WARN 会造噪音，属易被挑的细节。
- **`account_numa_*` 的快照一致性**：注释说快照在「任务进入 runqueue 时」生效、通过正常 dequeue/update/enqueue 路径生效，但已排在 rq 上的任务的计数是在下一次 enqueue 才纠正，作者没有说明这期间的 `nr_numa_running` 偏差是否可接受。

没有已知的反对意见；也没有已知的、被作者承认的未解决问题。

## 合入评估

`likelihood=medium`。依据：动机叙述完整、边界条件写得克制（明确不主动清理 hinting PTE、保留 sysctl 硬闸、编号无冲突），且直面了两条前案而不是无视它们——这些都是「作者知道自己在做什么」的信号；但本日零 review，且新增 uAPI + 跨 sched/proc/docs 三个域，天然需要更长的共识过程。`blocking_issues`：

1. 无任何维护者回应，尤其缺调度侧（Peter Zijlstra / Chen Yu / Greg Thelen 这类会关心 ABI 的人）对 prctl 形态的首肯。
2. 未论证与 `numa_group`（跨线程组、按 mm 聚合）粒度不一致时会发生什么，即「一个线程组关掉、同 mm 另一个还开着」的实际效果。
3. 3/4、4/4（`/proc` 暴露与文档）正文未送达收件端，本批邮件无法完整评审 ABI 的全貌。
4. 前案 [2][3] 与 [1] 都停在讨论阶段没落地，本系列需要回答「为什么这次不同」，而 cover 目前的回答是设计取向更保守，没有回答社区层面的推进障碍。

`next_action`：等首轮 review；作者侧最有价值的补充是 `numa_group` 交互的说明 + 一组真实开销数据（关掉扫描省下多少，见下节）。

## 效果评估

暂无效果数据。本批邮件里没有任何 benchmark、没有开销数字、也没有「关掉某进程后整机 NUMA 扫描采样次数下降多少」的测量。cover 只给了定性动机（「cannot afford the sampling overhead」），属于作者主观判断，未见测试数据。

## 我可以参与的点

- **补开销数据（testing）**：这是本系列目前最缺、门槛最低的一块。在自家 2-socket 机器上用带 `numa_balancing=1` 的内核跑一个自管 NUMA 的负载（`numactl --cpunodebind/--membind` 绑死的常驻服务即可），对比 `PR_SET_NUMA_BALANCING` 前后的 `/proc/vmstat` NUMA hint 相关计数、`perf stat -e ...` 或 ftrace 的 `update_numa_stats`/`task_numa_migrate` 事件量，量化「省下的开销」，直接回贴。作者与维护者都需要这个数字来判断值不值得新增 uAPI。
- **验证 `numa_group` 交互（testing/review）**：同 mm、多进程（不 `CLONE_THREAD`）场景下，只关掉其中一个进程的模式，观察 `task_numa_group_id()` 聚合后的 preferred node 与迁移决策是否仍把该进程拖回去。若确实会，这是可以带复现步骤回贴的实质意见。
- **锁与慢路径（review）**：`read_lock(&tasklist_lock)` 下逐线程 `task_rq_lock` 这条路径，我可以在本地主线核对既有同类写法的惯例并给出对照，或至少给出「线程数很多时（数千线程的 Java 进程）一次 prctl 的耗时」量级。
- **接口一致性讨论（discussion）**：与本日/近日另一个走 prctl 的系列（`sched/cache: Per-task control of cache aware scheduling via prctl`，Chen Yu/Tim Chen）在争同一批 prctl 编号与同一类 per-task 控制形态。把两次的 ABI 形状（两态 vs 分组对象）摆在一起谈，对社区判断「per-task 控制该怎么加」有帮助。
- **自家分支（new_patch）**：OLK 若有进程级 NUMA 干扰投诉，本系列的 1/4 机制部分是可独立评估的（快照 + 9 处早退），但它带 uAPI，回合时要考虑自家是否要暴露同一接口。

## 参考链接

- v1 cover: https://lore.kernel.org/all/20260908122446.56708-1-lizhe.67@bytedance.com/
- v1 1/4 `sched/numa: Track per-process automatic NUMA balancing mode`: https://lore.kernel.org/all/20260908122446.56708-2-lizhe.67@bytedance.com/
- v1 2/4 `sched/numa: Add prctl controls for process mode`: https://lore.kernel.org/all/20260908122446.56708-3-lizhe.67@bytedance.com/
- v1 3/4 / 4/4: 未获取到（本批缓存无这两封邮件，故无 Message-ID）
- 前案 [1] Chen Yu per-cgroup 提案、[2][3] 2023 prctl 提案：三个链接均出自本批 cover 原文，见正文
- tip-bot commit: 未获取到
- stable backport: 未获取到
---
id: sched-20260908-007
date: '2026-09-08'
subject: "sched/numa: Add per-process automatic NUMA balancing control"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260908122446.56708-1-lizhe.67@bytedance.com>
lore_url: https://lore.kernel.org/all/20260908122446.56708-1-lizhe.67@bytedance.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-08'
authors:
- Li Zhe
maintainers_involved: []
patch_series:
- version: v1
  msgid: <20260908122446.56708-1-lizhe.67@bytedance.com>
  date: '2026-09-08'
  summary: '4 补丁，12 files changed 201 insertions(+) 4 deletions(-)。1/4 在 signal_struct 存用户可见的 numa_balancing_enabled、在 task_struct 存调度快照 numa_balancing_sched_enabled，新增 task_numa_balancing_set_current()（mutex 串行 + siglock 改 signal + for_other_threads 下逐个 sched_change 更新快照）并在 fair.c 9 处热路径按快照早退、account_numa_enqueue/dequeue 与 enabled 相与；2/4 新增 PR_SET/GET_NUMA_BALANCING 82/83 与两态取值，GET 只回配置值；3/4 在 /proc/<pid>/status 暴露模式，4/4 补文档（这两封正文未收到）。不主动清理已装 hinting PTE 与排队 scan work，任其自然排空。'
  review_outcome: '本日无人回帖，无 Ack 无 NAK，也未见 tip 收录。'
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 新增 prctl uAPI，本日向零 review，缺调度侧维护者对接口形态的首肯
  - 未论证与 numa_group（按 mm 跨线程组聚合）粒度不一致时的实际效果，即同 mm 其他线程组仍在扫描时会否把本进程拖回迁移
  - 3/4 /proc 与 4/4 文档正文未送达收件端，本批邮件无法评审 ABI 全貌
  - 前案（Chen Yu per-cgroup、2023 两版 prctl）均未落地，社区层面的推进障碍未回答
  next_action: 等首轮 review；作者补 numa_group 交互说明与关闭扫描的开销量化数据
contribution_opportunities:
- kind: testing
  description: 在 2 路机器上用自管 NUMA 的常驻负载量化 PR_SET_NUMA_BALANCING 前后 NUMA hint 扫描/迁移事件量的差异，回帖提供开销数据
- kind: testing
  description: 同 mm 多进程（非 CLONE_THREAD）下只关一个进程，验证 numa_group 聚合是否仍把该进程拉回迁移决策
- kind: review
  description: 核对 read_lock(tasklist_lock) 下逐线程 task_rq_lock 的锁序与慢路径代价是否符合主线惯例，并量一下数千线程进程一次 prctl 的耗时
- kind: discussion
  description: 与同期同样走 prctl 的 sched/cache per-task 控制系列对照接口形态与编号占用
- kind: new_patch
  description: 评估 1/4 的快照+热路径早退机制在自家分支的可用性（是否暴露同一 uAPI 需另行决定）
source_email_count: 3
related_articles:
- sched-20260803-006
- sched-20260829-002
tags:
- numa_balancing
- cfs
---
