# kernel/sched/ext/sub.c:288:16: sparse: sparse: incorrect type in argument 1 (different address spaces)

## TL;DR

0day 机器人在 torvalds `master` 上报告一条新增 sparse 告警：`kernel/sched/ext/sub.c:288:16` 把带 `__rcu` 标注的 `rq->curr` 直接传给期望 `struct task_struct const *p` 的 `scx_task_sched()`，属于地址空间（RCU 注解）不匹配而非编译错误。同一份报告里其余 26 处调度器告警都是存量，只有这一处被标为 `>>`（新引入），机器人要求单独出补丁并附 `Fixes:` / `Reported-by:` / `Closes:`。本日以及相邻日期缓存中没有任何人回帖，也还没有修复补丁。

## 背景与问题

报告头部字段：`tree: torvalds/linux.git master`、`head: 940de590b839f71d6dc846160534bf202401b8b7`、`commit: bb70e4fb626b70895b7917ee97c256f24d019c34 sched_ext: Eject the top rescue consumer on overload`、`date: 4 weeks ago`、`config: sparc-randconfig-r131-20260826`、`compiler: sparc-linux-gcc (GCC) 16.1.0`、`sparse: v0.6.5-rc1`，且注明 `this is a W=1 build`。触发提交在邮件列表里对应 Tejun Heo 08-01 的 `[PATCH 09/12] sched_ext: Eject the top rescue consumer on overload`。

新增告警指向 sub-scheduler 的 rescue 计费函数：

```
void scx_rescue_charge(struct rq *rq, s64 delta_exec)
{
	struct scx_sched_pcpu *pcpu;
	...
288:	pcpu = per_cpu_ptr(scx_task_sched(rq->curr)->pcpu, cpu_of(rq));
289:	pcpu->rescue_avg = scx_rescue_decay_avg(pcpu) + delta_exec;
```

问题在于 `rq->curr` 在头文件里是 `struct task_struct [noderef] __rcu *`，而 `scx_task_sched()` 的形参是普通 `const struct task_struct *p`，中间没有经过 RCU 读取原语，sparse 因此判定「different address spaces」。这不是孤立事件：proxy execution 为 `rq->curr` / `rq->donor` 加上 `__rcu` 标注后，所有未走 `rcu_dereference()` 风格读取的使用点都会被 sparse 点名，报告的存量告警清单（`deadline.c:2339/3314/3316/3578/3631`、`ext/ext.c:391/1423/1613/2370/2384/3302/4381/4382/6821/6822/8357/8391/10275`、`rt.c:1313/1676`、`sched.h:1442/2470/2481`、`syscalls.c:1343/1418`）几乎全部同因，其中 `sched.h:2470` 一条重复 33 次。`sub.c:288` 只是新代码里第一个因此被抓到的。

## 技术方案

报告本身不附带补丁，只给出告警与代码上下文，并规定修复的标签要求：

```
Fixes: bb70e4fb626b ("sched_ext: Eject the top rescue consumer on overload")
Reported-by: kernel test robot <lkp@intel.com>
Closes: https://lore.kernel.org/oe-kbuild-all/202609040234.7zfFgTWS-lkp@intel.com/
```

要消掉这条告警，需要在 `scx_rescue_charge()` 里以 RCU 语义正确的方式取到 `rq->curr`（持 RCU 读侧临界区后用 `rcu_dereference()` 取得裸指针，或按 sched_ext 现有的 curr/donor 读取封装来取），再把它交给 `scx_task_sched()`；具体写法由作者选择，缓存中未见任何人给出建议。原稿提到的 `__user` 与本次告警无关，实际只有 `__rcu` 一类问题。

## 版本演进与当前进展

- 09-04 03:04 机器人发出报告（`202609040234.7zfFgTWS-lkp@intel.com`），是独立邮件、不挂在任何系列线程下。
- 本日匹配 1 封邮件。跨 08-01 至 09-06 的全部缓存中检索 `references` / `in_reply_to`，未找到任何引用该 msgid 的回复，也没有以 `Fixes: bb70e4fb626b` 为基础的修复补丁。
- 因此当前状态是「已报告、未响应」，无版本号可言（`current_version` 保持为空）。

## Maintainer 意见与讨论焦点

**未获取到任何维护者意见**——该报告没有任何回帖，也没有人在其他邮件里引用它。

有意义的背景事实是：受影响提交 `bb70e4fb626b` 本身出自 sched_ext 维护者 Tejun Heo（08-01 的 `[PATCH 09/12]`），所以修复责任不涉第三方、不需要跨人协调，这也解释了为什么 0day 报告的直接通知对象就是维护者本人。

**讨论焦点（潜在）**：这条告警真正牵连的是 sched_ext/proxy-exec 侧的 `__rcu` 注解约定。报告里的 26 处存量告警说明该约定尚未统一——`scx_task_sched(rq->curr)` 这类「拿到 rq->curr 就当成普通 task_struct 用」的写法在 ext.c、sub.c、sched.h 中大量存在。是否应该提供统一的 curr/donor 读取 helper、让 sparse 干净成为系列的前置条件，才是这个告警值得讨论的点，而不是 `sub.c` 这一行本身。

## 合入评估

likelihood: **unclear**。

依据：单行注解级修复、不涉及行为改变、机器人已给出 `reproduce` 与 `config` 链接，修复门槛极低；提交对象（sched_ext 维护者）明确，历史上此类 0day 告警通常都会跟一个小补丁。

卡点：
- 缓存中无人回帖、无补丁，无法判断维护者是准备单独修、还是并入下一批 sched_ext fixes，或是认为这类 sparse 噪音暂不处理。
- 只在 `sparc-randconfig` + `W=1` 下复现，常规构建不受影响，缺少被立即处理的压力。
- 若顺带处理存量 `__rcu` 告警，就不是一行而是一批改动，周期会被显著拉长。

## 效果评估

邮件中未提供效果数据。这类修复属静态分析注解层面，不改变运行时行为，报告也未给出任何功能或性能影响证据。可量化的信息只有报告本身：92 条 sparse 输出行、27 个不同告警位置，其中仅 `kernel/sched/ext/sub.c:288:16` 被标为新增（同一条重复 4 次），其余 26 个位置为存量。

## 我可以参与的点

- **门槛最低的上游参与**：直接按报告要求写一个单行修复（给 `scx_rescue_charge()` 的 `rq->curr` 走正确的 RCU 读取），带上机器人指定的 `Fixes:` / `Reported-by:` / `Closes:` 三个标签发到 sched 列表。0day 报告已提供 `config` 与 `reproduce` 链接，本地验证路径清楚；这类小补丁是建立与 sched_ext 维护者通信记录的低成本方式。
- **值得追问的语义问题**：注解修好后，`scx_task_sched(rq->curr)->pcpu` 的解引用本身仍然成立吗？同日文章《sched_ext: Fix NULL sched deref in kfunc sub-sched error paths》的根因正是 `scx_task_sched()` 对不存在调度上下文的返回为空并被无条件解引用。如果那一处需要防护，本行同样直接解引用，是否存在同一类风险？这是可以在回帖里问清、且只看函数体就能回答的点。
- **系统性清理空间**：26 处存量告警集中在 `rq->curr` / `rq->donor` 的 `__rcu` 标注上（`sched.h:2470` 33 次、`sched.h:2481` 12 次、`deadline.c` 五处、`ext/ext.c` 十四处、`rt.c` 两处、`syscalls.c` 两处），说明缺少统一的 curr/donor 读取封装。如果有人愿意整理出一份约定并批量收敛，这是能一次让 sparse 干净、且明显还没人做的活儿。
- **回合视角**：单行注解修复对 OLK-6.6 无独立回合价值（除非已把 `bb70e4fb626b` 一并回合）；真正需要跟踪的是 proxy-exec 对 `rq->curr` 的 `__rcu` 语义变化——它会牵动所有直接读 `rq->curr` 的下游代码，包括 cpuset/cgroup 相关的计费路径。

## 参考链接

- 邮件线程：
  - 0day 报告本体: <https://lore.kernel.org/all/202609040234.7zfFgTWS-lkp@intel.com/>
  - 机器人给出的 Closes 链接（报告原文）: <https://lore.kernel.org/oe-kbuild-all/202609040234.7zfFgTWS-lkp@intel.com/>
  - 复现配置（报告原文）: <https://download.01.org/0day-ci/archive/20260904/202609040234.7zfFgTWS-lkp@intel.com/config>
  - 复现脚本（报告原文）: <https://download.01.org/0day-ci/archive/20260904/202609040234.7zfFgTWS-lkp@intel.com/reproduce>
- 相关代码/commit：
  - `bb70e4fb626b70895b7917ee97c256f24d019c34` "sched_ext: Eject the top rescue consumer on overload"
  - `kernel/sched/ext/sub.c:288` `scx_rescue_charge()`
  - `kernel/sched/sched.h:2470` / `:2481`（重复最多的存量告警位置）

---
id: sched-20260904-009
date: '2026-09-04'
subject: 'kernel/sched/ext/sub.c:288:16: sparse: sparse: incorrect type in argument 1 (different address spaces)'
subsystem: sched
type: bug
status: under_review
severity: low
thread_root_msgid: 202609040234.7zfFgTWS-lkp@intel.com
lore_url: https://lore.kernel.org/all/202609040234.7zfFgTWS-lkp@intel.com/
upstream_commit: null
fixes_commit: bb70e4fb626b70895b7917ee97c256f24d019c34
merged_branch: null
current_version: null
generated_at: '2026-09-07'
authors:
- kernel test robot
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 缓存中无任何回帖，无法判断维护者是否会单独出修复补丁
  - 仅 sparc-randconfig + W=1 复现，常规构建不受影响，缺少处理压力
  - 若要顺带收敛 26 处同因存量 __rcu 告警，改动规模远超单行
  next_action: 作者（提交 bb70e4fb626b 的 Tejun Heo）需在 scx_rescue_charge() 中对 rq->curr 做 RCU 语义正确的读取，并附 Fixes/Reported-by/Closes 标签。
contribution_opportunities:
- '按报告要求提交单行 __rcu 注解修复，附 Fixes: bb70e4fb626b / Reported-by / Closes 标签'
- 确认注解修复后 scx_task_sched(rq->curr)->pcpu 的解引用是否仍需防空
- 整理 rq->curr / rq->donor 的统一 RCU 读取封装，批量收敛 26 处同因存量告警
source_email_count: 1
related_articles: []
tags:
- sched_ext
---
