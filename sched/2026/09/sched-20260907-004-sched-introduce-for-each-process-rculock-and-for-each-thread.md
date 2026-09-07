# sched: introduce for_each_process_rculock and for_each_thread_rculock

## TL;DR

Ye Liu 在 09-07 16:13 发出 v2（8 补丁）：在 `include/linux/sched/signal.h` 新增 `for_each_process_rculock()` / `for_each_thread_rculock()` / `for_each_process_thread_rculock()`，用 `scoped_guard(rcu)` 把 RCU 读锁作用域绑到循环本身，`break`/`goto`/`return` 退出都自动释放；其余 7 个补丁把 mm/、kernel/、fs/、lib/、security/ 里手写的 `rcu_read_lock()`/`rcu_read_unlock()` 与 `guard(rcu)()` 配对换成新宏（17 files changed, 54 insertions(+), 81 deletions(-)）。v2 的关键变化是改名 `*_rcu` → `*_rculock`（避开与「假定调用者已持锁」的既有 `*_rcu()` 迭代器混淆）。当天 Lorenzo Stoakes 给了 1/8 的 `Reviewed-by`（要求缩进）、Oleg Nesterov 也给 `Reviewed-by` 并明确表态更喜欢 `_rculock` 后缀，加上已有的 `Acked-by: Michal Hocko`，剩下的基本只是缩进与 commit message 的收尾。

## 背景与问题

问题很朴素：全树大量地方在为「遍历进程/线程」这件事手工配对 RCU 读锁——`rcu_read_lock(); for_each_process_thread(g, p) {...} rcu_read_unlock();`，一旦循环里有 `break`、`goto` 或提前 `return`，解锁点就得靠人脑穷举；`guard(rcu)()` + 花括号则是把作用域写成一个大块，锁的范围比循环大。新宏把锁的作用域收敛到循环本体，退出路径自动释放。

命名是这个系列反复讨论的点。v1 用的是 `*_rcu` 后缀，但内核里 `*_rcu()` 这一族（`list_for_each_entry_rcu()` 等）的既有约定是「假定调用者已经持有 RCU 读锁」，正好相反，于是 Steven Rostedt 建议改成 `*_rculock`、Thomas Gleixner ack；今天 Oleg Nesterov 回帖进一步确认（原文：「I personally like the new _rculock suffix more ;)」）。宏放在 `include/linux/sched/signal.h` 而不是 mm 头文件，因此 v2 也按 Michal Hocko 意见去掉了 `mm:` 前缀。动机方面，cover 写明「Suggested by Michal Hocko for the oom_kill path」，并链接了 08-13 的一支补丁（该邮件不在本批缓存中）。

## 技术方案

patch 1 只改 `include/linux/sched/signal.h`（+25 行，含 `#include <linux/cleanup.h>`），三个宏的形态都是 `scoped_guard(rcu)` 后面直接跟原迭代器：

- `for_each_process_rculock(p)` → `scoped_guard(rcu)` + `for (p = &init_task ; (p = next_task(p)) != &init_task ; )`
- `for_each_thread_rculock(p, t)` → `scoped_guard(rcu)` + `__for_each_thread((p)->signal, t)`
- `for_each_process_thread_rculock(p, t)` → `scoped_guard(rcu)` + `for_each_process(p) for_each_thread(p, t)`

因为第三个是双层循环，v2 按 Thomas Gleixner 的意见专门补了注释：`break` 只退出内层 `for_each_thread()`，要一次退出两层必须用 `goto`，RCU 读锁在离开 `scoped_guard` 作用域时自动释放。主线该处原本就有一句 `/* Careful: this is a double loop, 'break' won't work as expected. */`，新宏把这个陷阱从「语义上容易踩」变成「写在注释里且解锁不再依赖 goto 位置」。

其余 7 个补丁是纯机械替换，v2 diffstat 覆盖 `fs/proc/base.c`、`fs/resctrl/rdtgroup.c`、`kernel/cpu.c`、`kernel/freezer.c`、`kernel/hung_task.c`、`kernel/locking/lockdep.c`、`kernel/rcu/update.c`、`kernel/sched/core.c`、`kernel/sched/debug.c`、`kernel/trace/fgraph.c`、`kernel/unwind/deferred.c`、`lib/is_single_threaded.c`、`mm/ksm.c`、`mm/memory-failure.c`、`mm/oom_kill.c`、`security/landlock/tsync.c`。调度器侧的两处在 v2 只出现在 cover 的 diffstat 里（补丁正文未取到）；按本地主线源码，对应的应该就是 `kernel/sched/debug.c` 里 `print_rq()` 的 `rcu_read_lock()` + `for_each_process_thread()` 配对，以及 `kernel/sched/core.c` 里 `show_state_filter()` 的同一形态。

v2 相对 v1 的完整改动（cover 自述）：宏改名（Rostedt 建议、Gleixner ack）；补双层循环 `break`/`goto` 注释（Gleixner）；`hung_task.c` 里过时的 `unlock:` 标签改名 `out:`（Günther Noack）；在 patch 4 说明 `page_pgoff()` 在 RCU 读临界区外是安全的（SJ Park）；每个补丁 CC 全部相关维护者（Lorenzo Stoakes）；去掉 `mm:` 前缀（Hocko）。

## 版本演进与当前进展

- 08-13：一支 oom_kill 路径的补丁被 Michal Hocko 建议改成通用迭代器形式（cover 里以链接给出，本批缓存无该邮件）。
- 09-04：v1 发出，宏名用 `*_rcu`（本批缓存中无 v1 邮件，逐条差异只能依据 v2 cover 的自述）。
- 09-07 16:13：v2 发出 8 补丁，patch 1 带 `Acked-by: Michal Hocko`。
- 09-07 16:26 / 16:30：Lorenzo Stoakes 分别回 cover 与 1/8，后者给 `Reviewed-by`，条件是若干 nit（缩进）。
- 09-07 17:35：Oleg Nesterov 回 1/8，给 `Reviewed-by`。
- 本日尚无 mm/、fs/、security/ 各子系统维护者对相应补丁表态；转换范围预计还会继续扩。

## Maintainer 意见与讨论焦点

- **Lorenzo Stoakes（ARM，`ljs@kernel.org`）**：对 cover 的意见是「这些说明别进 commit message」（大意：假定 Ye Liu 同意，下面那些内容都应从进入 commit message 的 cover 文本里排除，包括 checkpatch 那段；他的原话是 checkpatch 一般要「拿盐水冲一冲」——"it's a master of false positives so usually no need to say this :)"）。这条针对的是 cover 里那段「patch 1 会触发 checkpatch 的 `Macros with complex values should be enclosed in parentheses`，属于误报，因为 `scoped_guard()` 是控制流构造而非多语句宏」的辩解。对 1/8 他给 `Reviewed-by: Lorenzo Stoakes (ARM)`，前提 nit 是把 `for` 循环体再缩进一个 tab——理由是 `for` 实际在 `scoped_guard()` 作用域里，现在的写法看不出来；双层循环那条他直言「更糟」（"this is even worse for clarity :)"），并直接给出他认可的写法：三行分别缩进（`#define ...` / `scoped_guard(rcu)` / `for_each_process(p)` / `for_each_thread(p, t)` 逐行递进）。注意他回 cover 时是称呼「Andrew」开口的，说明他默认这套改动随 mm 树走。
- **Oleg Nesterov（任务/信号侧）**：两条都表态支持，「我个人更喜欢新的 `_rculock` 后缀」（原文带 `;)`）；对 Lorenzo 的缩进意见表示「我两种写法都行」（"I am fine either way"），给 `Reviewed-by: Oleg Nesterov`。也就是说命名争议已经收敛，剩下的只是风格分歧。
- **未出现的声音**：Peter Zijlstra / Thomas Gleixner 本日没有回帖（Gleixner 的意见只以 v2 cover 转述的形式存在）；mm 之外的站点（fs/、lib/、security/landlock、kernel/trace/、kernel/locking/）维护者本日也无人表态。

## 合入评估

`likelihood=high`。理由：patch 1（唯一的非机械补丁）已同时拿到 `Acked-by: Michal Hocko`、`Reviewed-by: Lorenzo Stoakes (ARM)`、`Reviewed-by: Oleg Nesterov`，且两位 reviewer 的分歧只落在缩进这种一次重发即可消掉的事情上；其余 7 个补丁是删锁配对、净减 27 行，语义上是纯收敛。卡点：(1) 需要一次 v3 落实缩进与 commit message 精简；(2) 收树路径未定——Lorenzo 对着 akpm 说话暗示走 mm 树，但 `include/linux/sched/signal.h` 的改动和 `kernel/sched/*` 两处通常需要 sched 侧点头，跨树依赖最容易让系列停在「都认可但没人收」的状态；(3) mm/ 之外各子系统补丁仍缺各自维护者的 ack。没有 `Fixes`、没有行为变化，也不涉及 stable。

## 效果评估

无性能数据，作者也没提供这类补丁通常该给的等价性证据（例如逐站点 `objdiff` 或反汇编对比）。可量化的只有形态收益：v2 diffstat 17 files changed, 54 insertions(+), 81 deletions(-)，即 27 处净减，全部是锁配对与花括号样板；patch 1 自身 +25/-0。风险面同样只能从宏语义推断：`scoped_guard(rcu)` 的作用域只覆盖那条 `for` 语句，因此凡「循环结束后继续使用 `p`/`t`，或在循环里取得指针、在原本更宽的临界区内解引用」的站点，替换后 RCU 保护范围会静默缩小——这类站点的逐一确认在邮件中没有任何记录。

## 我可以参与的点

- **调度器侧那两处的 review 最有发言权**：`print_rq()` 与 `show_state_filter()` 都是 sysrq/debug 输出路径，循环体是全任务遍历（`show_state_filter()` 里还在逐个 `touch_nmi_watchdog()`/`touch_all_softlockup_watchdogs()` 并可能打印到慢速控制台）。替换成宏后临界区范围是否与原 `rcu_read_unlock()` 位置严格等价、这两个函数是否有循环外继续使用 `p` 的写法，是 sched 维护者会问的问题，可以提前替他核对并回帖。
- **继续扩转换范围**：`for_each_process_thread()` 在主线约有 40 处调用，本系列只覆盖了其中一部分；我在本地树里 grep 到尚未进入本系列的站点包括 `kernel/livepatch/transition.c`、`kernel/tracepoint.c`、`kernel/sys.c`、`kernel/power/process.c`、`kernel/events/core.c`、`kernel/debug/kdb/*`、`drivers/tty/tty_io.c`、`fs/fs_struct.c`、`mm/kmemleak.c` 等，按各自子系统维护者要求做机械替换并 CC 全维护者（v2 已按 Lorenzo 意见这么做）是门槛最低的参与方式。
- **替作者把验证补齐**：对每个被改写的站点确认 `break`/`continue`/`goto` 下的解锁点与原代码一致（尤其双层循环里原本用 `goto` 跳出两层的写法），并跑一遍 `objdiff`/编译矩阵（含 `CONFIG_PREEMPT_NONE`/`PREEMPT_RCU` 两种 RCU 配置）后再回贴，这比再多加一个 `Reviewed-by` 更有价值。
- 自家分支如果带着这些文件，这个系列属于「越早回合越省事」的类型：它只减少锁样板，回合冲突集中在 `hung_task.c` 的 `unlock:` → `out:` 标签改名与 mm/ 侧改动上，可以先在内部验证。

## 参考链接

- v2 cover letter（含 v1→v2 逐条改动与 diffstat）: https://lore.kernel.org/all/20260907081334.1152889-1-ye.liu@linux.dev/
- v2 1/8 补丁本体（三个宏的实现 + Acked-by: Michal Hocko）: https://lore.kernel.org/all/20260907081334.1152889-2-ye.liu@linux.dev/
- Lorenzo Stoakes 回 cover（commit message 与 checkpatch 段）: https://lore.kernel.org/all/ap5yw-Cwb41FymNd@gremlin/
- Lorenzo Stoakes 回 1/8（Reviewed-by + 缩进 nit）: https://lore.kernel.org/all/ap51Mj0cqvAYb31k@gremlin/
- Oleg Nesterov 回 1/8（Reviewed-by，支持 _rculock 命名）: https://lore.kernel.org/all/ap6FWZ9FYjkFKoH_@redhat.com/
- v1 与 08-13 的 oom_kill 原始链接只在 v2 cover 中以脚注给出，对应邮件不在本批缓存中，故不列 URL
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260907-004
date: '2026-09-07'
subject: 'sched: introduce for_each_process_rculock and for_each_thread_rculock'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260907081334.1152889-1-ye.liu@linux.dev>
lore_url: https://lore.kernel.org/all/20260907081334.1152889-1-ye.liu@linux.dev/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Ye Liu
maintainers_involved:
- Lorenzo Stoakes
- Oleg Nesterov
patch_series:
- version: v1
  msgid: <20260904083001.553587-1-ye.liu@linux.dev>
  date: '2026-09-04'
  summary: 首次引入宏（当时命名后缀为 *_rcu）并转换 mm/、kernel/、fs/、lib/、security/ 中的手写 rcu_read_lock()/rcu_read_unlock() 与 guard(rcu)() 配对。该版本邮件不在本批缓存中，以下差异均依据 v2 cover 的自述。
  review_outcome: '按 v2 cover 转述：Steven Rostedt 建议改名为 *_rculock、Thomas Gleixner ack 并要求补双层循环 break/goto 注释、Günther Noack 指出 hung_task.c 的 unlock: 标签过时、SJ Park 要求说明 page_pgoff() 的 RCU 安全性、Lorenzo Stoakes 要求 CC 全维护者、Michal Hocko 要求去掉 mm: 前缀。'
- version: v2
  msgid: <20260907081334.1152889-1-ye.liu@linux.dev>
  date: '2026-09-07'
  summary: '8 补丁。include/linux/sched/signal.h 新增 for_each_process_rculock()/for_each_thread_rculock()/for_each_process_thread_rculock()，以 scoped_guard(rcu) 把 RCU 读锁作用域绑定到循环，break/goto/return 自动释放；其余 7 个补丁为机械替换。17 files changed, 54 insertions(+), 81 deletions(-)，含 kernel/sched/core.c 与 kernel/sched/debug.c。宏名由 *_rcu 改为 *_rculock，补双层循环注释，hung_task.c 的 unlock: 改名 out:。'
  review_outcome: 'patch 1 带 Acked-by: Michal Hocko；Lorenzo Stoakes 给 Reviewed-by 并要求把 for 循环体缩进一个 tab（双层循环那条给了逐行缩进的示范），另要求把 cover 中的说明（含 checkpatch 误报那段）从 commit message 里删掉；Oleg Nesterov 给 Reviewed-by 并表示更喜欢 _rculock 后缀、对缩进无所谓。本日无其他子系统维护者表态。'
merge_assessment:
  likelihood: high
  blocking_issues:
  - 等待一次 v3 落实缩进与 commit message 精简（Lorenzo 的 Reviewed-by 以此为前提）
  - 收树路径未定，Lorenzo 回 cover 时称呼 Andrew 暗示走 mm 树，但 signal.h 与 kernel/sched 两处需要 sched 侧点头，跨树依赖容易停滞
  - mm 之外的补丁（fs/、lib/、security/landlock、kernel/trace、kernel/locking）仍缺各自维护者 ack
  next_action: 跟进是否发出 v3 及其缩进/commit message 处理方式；确认最终由哪棵树收取
contribution_opportunities:
- kind: review
  description: 核对 kernel/sched/debug.c 的 print_rq() 与 kernel/sched/core.c 的 show_state_filter() 两处替换后 RCU 临界区范围是否与原 rcu_read_unlock() 位置严格等价，是否存在循环外继续使用 p/t 的写法
- kind: extend
  description: 主线 for_each_process_thread() 约 40 处调用中仍有未覆盖站点（kernel/tracepoint.c、kernel/sys.c、kernel/power/process.c、kernel/events/core.c、kernel/livepatch/transition.c、drivers/tty/tty_io.c、fs/fs_struct.c、mm/kmemleak.c 等），可按各子系统惯例做机械替换并 CC 维护者
- kind: testing
  description: 逐站点确认 break/continue/goto 下的解锁语义，并跑 objdiff 与不同 RCU 配置（PREEMPT_NONE 与 PREEMPT_RCU）的编译验证，作者目前未提供这类证据
source_email_count: 5
related_articles: []
tags:
- sched_debug
---
