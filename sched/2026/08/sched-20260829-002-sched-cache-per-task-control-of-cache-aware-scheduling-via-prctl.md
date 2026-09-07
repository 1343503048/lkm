# sched/cache: Per-task control of cache aware scheduling via prctl

## TL;DR

Tim Chen + Chen Yu（Intel）发出 7 补丁 RFC（base v7.2-rc6），把 cache-aware scheduling（CAS）的分组单位从"mm"解绑成独立的引用计数对象 `sched_cache_group`，并给出一套照抄 core scheduling 形状的 `prctl(PR_SCHED_CACHE, ...)` 接口（GET/CREATE/SHARE_FROM/DISABLE/ENABLE），同时把 debugfs 的 `enabled` 布尔扩成 THP 式 `always/advise/never`。8/29 Peter Zijlstra 的唯一回复是一句要动机："Who would be using this -- what workload prompted you do do this etc."——接口很大、用例还没交代，这是当前最需要补的东西。与 sched QoS（Qais Yousef）和 cgroup 两条既有路线直接重叠，本文明确写了"要做 per-cgroup 得先问 cgroup 维护者"。

## 背景与问题

CAS 现在按 **mm** 分组：LLC 聚合目标存在 `mm_struct` 里（`mm->sc_stat.cpu`），于是一个地址空间内的线程被拉往同一 LLC。作者指出这个粒度两头都不对：

- **太粗**：很多负载是跨**进程**协作而非跨线程——每连接一进程的数据库、每站点一个 renderer 的浏览器、server + worker 组合。它们通过 shm/pipe 传数据，本应聚到同一 LLC，但因为不共享 mm，今天完全做不到。
- **太细/太急**：一个进程内互不共享数据的线程，仅仅因为同处一个地址空间就被强行聚合。
- **只有一个全局旋钮**：整件事的开关是 debugfs 里一个系统级布尔，无法按任务/进程表达意图。

## 技术方案

**Patches 1–3 是纯准备，无行为变化**：

1. `sched_cache_stat` → `sched_cache_group`，变成 `refcount_t` + `call_rcu()` 释放的独立对象；`mm_struct` 从内嵌改为持有指针 `mm->sched_cache_grp`；新建 `kernel/sched/cache_sched.c` 承载 `sched_cache_group_put()` 等 helper；同时让 `account_mm_sched()` 与 `task_tick_cache()` 一致地跳过 kthread。
2. 给 `task_struct` 加 `struct sched_cache_group __rcu *sched_cache_grp`，让调度器热路径不再经 `p->mm` 取组；每个任务持有自己的一份引用（`copy_mm()`/`exec_mmap()` 取、`exit_mm()` 放）。
3. 抽出 `sched_cache_alloc_group()` helper，为 prctl CREATE 这个第二个调用者铺路。

**Patch 4 是接口本体**：

```
int prctl(PR_SCHED_CACHE, subop, pid, arg4, pid_type);
```

- `pid` 为操作对象（0 = 调用者），`pid_type` 选 `PIDTYPE_PID`/`TGID`/`PGID`（GET 只接受 `PIDTYPE_PID`）。
- `GET` 把 cookie 写到 `arg4`（`u64 __user *`，必须 8 字节对齐，否则 `-EINVAL`）；`SHARE_FROM` 把 `arg4` 那个 pid 的组复制给 `pid`；`CREATE` **刻意不做幂等**，总是新建组，所以要多任务同组就 CREATE 一次 + 其余 SHARE_FROM。
- 权限模型完全跟随 core scheduling：每个被触碰的任务都要过 `ptrace_may_access(PTRACE_MODE_READ_REALCREDS)`，且组粒度操作是**先全体验证再一次性修改**（all-or-nothing）。
- 与 `PR_SCHED_CORE_SHARE_FROM/SHARE_TO` 的差异：不需要把中介任务（如 schedqos 守护进程）拉进组里，避免污染该组的 per-LLC 占用统计。

**两个有意的设计取舍**（作者自己列出的）：

- **cookie 归内核所有**：用户态永不构造/传入 cookie，只报 pid；下发的是内核对象的 obfuscated hash（同 core scheduling）。理由是省掉用户态的 cookie 生命周期管理与不同实体间 cookie 撞号，作者认为这会让 schedqos 更好实现。
- **选 prctl 而不是 sched_setattr**：理由是"组成员关系不是一个属性值"，且 core scheduling 已立了 prctl 的先例（连 subop 布局、`pid_type` 作用域、权限模型都复用）。备选方案 `sched_setattr`（Qais Yousef 的 sched QoS 路线）被明确写成"被比较后放弃"，这是判断合入方向的关键信息。

**Patch 5–7**：`ENABLE/DISABLE` 子操作（组内 `enabled` 字段）；Chen Yu 写的 `enabled` 三态化——设计矩阵 `always` 忽略 per-task hint、`advise` 尊重、`never` 全关，默认 `always`，写侧仍接受 `1/0`、`y/n`、`on/off` 以兼容既有脚本，读侧变成 `[always] advise never`，并可由新的 `sched_cache=` 启动参数选择；Patch 7 新增 `Documentation/scheduler/sched-cache.rst`（175 行，该 patch 带 `Assisted-by: Claude:claude-opus-4.8`）。

作者还点名 Yangyu Chen 之前"用 prctl 暴露 per-process 参数"的提案可以自然叠在本系列之上，并主动写下：**理论上 cgroup 也能用同一机制提供 per-cgroup CAS，但要先拿到 cgroup 维护者的意见**。明确 TODO：prctl(2) man page、`tools/testing/selftests` 下的子操作与权限测试。

## 版本演进与当前进展

- 本系列为**首个版本（无版本号的 RFC，7/7）**，8/28 15:29（PT）/ 8/29 06:29（北京时间）发出，作者署名 "Tim Chen and Chen Yu"，cover 里直接标 RFC。
- 8/29 17:27 Peter Zijlstra 回 cover 一帖，只要动机，未评论接口。
- 当日无 v2，也无其他维护者表态。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（唯一维护者回复）**：`Who would be using this -- what workload prompted you do do this etc.` —— 这是对"先给 UAPI、后找用例"的常见质疑。UAPI 一旦落地就不可回收，没有明确用户之前 PZ 不会接受形状。
- **作者侧的自我定位**：把本系列归到 sched QoS 的延长线上（"inspired by Qais' sched QoS tool"），并主动区分两处设计（内核持有 cookie、prctl 而非 sched_setattr），说明接口形态之争他们预期会发生。
- **未被回答的问题（本日的争议空白）**：① 谁用、什么负载逼出来的（PZ 的问题，无人应答）；② 与 Qais Yousef 的 `sched_setattr`-based QoS 是竞争还是分工，cover 只给了作者单方理由；③ per-task 粒度是否真够——cover 里"这些组在实践中往往是 cgroup"的暗示（"in theory cgroup could offer..."）与本系列的 per-task 设计之间存在张力，而这恰恰是需要 cgroup 维护者表态却还没表态的部分；④ `ptrace_may_access(READ_REALCREDS)` 在容器/多租户下是否足够（可以让非本组任务 SHARE_FROM 进别人的组）。

## 合入评估

**possible**。有利面：作者就是 CAS 的两位核心维护者，1–3 的解耦部分本身是有价值的清理（把 CAS 状态从 mm 生命周期里拿出来，也顺带消掉一类 mm 生命周期耦合问题），这部分即使接口被否也可能单独留下；向后兼容与启动参数都考虑到了。不利面：这是 RFC 且 PZ 只问了动机，接口形状（prctl 命名空间、cookie 语义、THP 三态）没有任何人 ack；新增 UAPI 需要 man-page + selftest 两项 TODO 完成；per-cgroup 变体还需要 cgroup 维护者输入。最可能的走向是 1–3 先行、4–6 在用例与接口形状上多轮往返。

## 效果评估

暂无效果数据。cover 与 7 个补丁全部在讲机制与接口，没有任何 benchmark、也没有给出"跨进程共享工作负载在 CAS 下损失多少"的量化动机——这与 PZ 索要动机的点是同一个缺口。THP 式三态的取舍也只是类比，没有数据支撑。

## 我可以参与的点

- **回答 PZ 的问题（最容易产生影响力的一帖）**：社区现在缺的就是用例。你在华为侧如果有真实的跨进程共享负载（同机多进程协同、shm/pipe 密集）能给出"按 mm 分组导致聚合失效/误伤"的量化例子，直接回帖就是本系列最缺的材料。
- **cgroup 粒度这条线可以主动推**：作者已明说"要做 per-cgroup 需要 cgroup 维护者意见"，而这是 cpuset/cgroup 主线的地盘——可以就"组语义放在 cpuset/cgroup 还是 prctl cookie 上"给出立场与 patch 方向（例如复用 cpuset 层级表达 LLC 聚合域）。
- **接口形状的表态**：prctl vs `sched_setattr`、内核持有 cookie vs 用户态 cookie，这两处是作者点名征求反馈的地方（"especially on the interface shape, the kernel-owned-cookie choice, and whether always/advise/never is the right model"）。
- **selftest / man page**：作者列了两个明确 TODO，`tools/testing/selftests` 下覆盖 5 个子操作与 `ptrace_may_access` 权限矩阵的测试是低门槛、会被直接引用的贡献。
- **回合判断**：1–3 属于纯重构（`sched_cache_group` 解耦），对 OLK-6.6 若已有 CAS 的话是干净的可回合候选；4–6 引入 UAPI，短期不建议跟进。

## 参考链接

- lore cover: https://lore.kernel.org/all/cover.1787955777.git.tim.c.chen@linux.intel.com/
- lore 1/7（Decouple sched_cache_group from mm）: https://lore.kernel.org/all/4f82fe28ecdda1728e3ad29bd44f5287226a8d73.1787955777.git.tim.c.chen@linux.intel.com/
- lore 2/7（task_struct->sched_cache_grp）: https://lore.kernel.org/all/865e1e28ee8325d481c681a43401edd34e9a4141.1787955777.git.tim.c.chen@linux.intel.com/
- lore 3/7（sched_cache_alloc_group helper）: https://lore.kernel.org/all/d6cd97ac68c817576d57658c2ebcffdbd3ac0341.1787955777.git.tim.c.chen@linux.intel.com/
- lore 4/7（prctl 接口）: https://lore.kernel.org/all/50fe2db1a62ea2376a87d0c14778b1ff456d11ec.1787955777.git.tim.c.chen@linux.intel.com/
- lore 5/7（ENABLE/DISABLE）: https://lore.kernel.org/all/14772dcf31c7eae3cec060fd6884579ed1c0f03b.1787955777.git.tim.c.chen@linux.intel.com/
- lore 6/7（debugfs 三态，Chen Yu）: https://lore.kernel.org/all/fd341106e7e6cbd2f047656650f43ee87c6633c1.1787955777.git.tim.c.chen@linux.intel.com/
- lore 7/7（sched-cache.rst 文档）: https://lore.kernel.org/all/86909723689d9c496b5a67ee2a0ecfd0d63e8712.1787955777.git.tim.c.chen@linux.intel.com/
- lore Peter Zijlstra 索要动机: https://lore.kernel.org/all/20260829092721.GB776954@noisy.programming.kicks-ass.net/
- tip-bot commit / stable backport: 未获取到（RFC，未进 tip）

---
id: sched-20260829-002
date: '2026-08-29'
subject: "sched/cache: Per-task control of cache aware scheduling via prctl"
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<cover.1787955777.git.tim.c.chen@linux.intel.com>"
lore_url: "https://lore.kernel.org/all/cover.1787955777.git.tim.c.chen@linux.intel.com/"
authors: [Tim Chen, Chen Yu]
maintainers_involved: [Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<cover.1787955777.git.tim.c.chen@linux.intel.com>"
    date: 2026-08-29
    summary: "7 补丁 RFC：把 CAS 分组从 mm 解耦为引用计数的 sched_cache_group，新增 PR_SCHED_CACHE prctl（GET/CREATE/SHARE_FROM/DISABLE/ENABLE）与 THP 式 always/advise/never debugfs 三态"
    review_outcome: "Peter Zijlstra 仅问用途与触发该设计的工作负载；无人 ack 接口形状，无 v2"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "维护者索要具体工作负载动机，作者尚未回答"
    - "新增 UAPI 缺 prctl(2) man page 与 selftests（作者列为 TODO）"
    - "与 sched_setattr 路线的 sched QoS 接口之争未解决"
    - "per-cgroup 变体需 cgroup 维护者表态"
  next_action: "补充真实用例与量化动机，完成 man page/selftest，就 prctl 与 sched_setattr 的取舍与 Qais Yousef 达成一致"
contribution_opportunities:
  - kind: discussion
    description: "回帖回答 Peter Zijlstra 的动机问题，给出跨进程共享负载下按 mm 分组失效的量化例子"
  - kind: extend
    description: "推进 per-cgroup 的 CAS 表达（cpuset 层级 vs prctl cookie），作者明确邀请 cgroup 侧输入"
  - kind: new_patch
    description: "补 tools/testing/selftests 覆盖 5 个子操作与 ptrace_may_access 权限矩阵"
generated_at: "2026-09-07T22:06:23"
source_email_count: 8
related_articles: [sched-20260831-008]
tags: [load_balance, cgroup]
---
