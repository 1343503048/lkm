# sched: fix typos and repeated words in comments

## TL;DR

Hemanth Selam 在 09-07 14:49 发出一个 2 补丁的注释修正系列：`kernel/sched/ext/ext.c` 里两处 `upto` → `up to`（`bypass_lb_node()` 的负载均衡注释、`scx_bpf_dispatch` kfunc 注释），以及 `tools/sched_ext/include/scx/common.bpf.h` 里重复的 `be`。作者自陈「Nothing outside comments changes」，给出的验证方法是把注释删掉、字符串字面量替换成占位符、压缩空白后比较前后编译产物；来源是 `scripts/checkpatch.pl` 对 `scripts/spelling.txt`；并明确标注 `Assisted-by: Cursor:claude-opus-5`，在 cover 里说明扫描、编辑、changelog 都由该模型完成、之后按上述方法复核。构建基线是 `v7.3-rc1-269-gbc35965f6940` 的 x86_64 defconfig。同作者当天还发了 sched 注释拼写的 14 补丁系列与一个 cpuidle 系列。本日无任何维护者回帖。

## 背景与问题

这类「全树注释拼写」系列是内核里的常客，工具链也是现成的：`scripts/checkpatch.pl` 会按 `scripts/spelling.txt` 的漏拼表报 hit，重复词（"repeated word"）也在它的检查范围内。作者把自己的做法拆成三个明确声明，正好对应这类补丁最容易招致质疑的三处：

- **每处独立成补丁**，理由是「any one of them can be dropped without touching the rest」，即任一处被维护者否掉不牵连其余。
- **不动标识符相关词**：原文说法是「Words that name an identifier were left alone deliberately, even when they read as typos」，因为改了散文会让注释与它描述的代码不一致。
- **AI 参与方式公开**：补丁带 `Assisted-by: Cursor:claude-opus-5`，cover 写明扫描/编辑/changelog 出自该模型、人工按上述等价性方法复核。

## 技术方案

纯注释，无代码变化，2 补丁合计 2 files changed, 3 insertions(+), 3 deletions(-)。

- 1/2 `sched: fix typo "upto" in comments`：`kernel/sched/ext/ext.c` 两处，一处是 `bypass_lb_node()` 里「balancing to fill donee CPUs upto $nr_target」，另一处是 `__bpf_kfunc_start_defs()` 之后 `scx_bpf_dispatch` 的注释「this function can be called upto ops.dispatch_max_batch times」。
- 2/2 `tools/sched_ext: fix repeated word 'be' in comment`：`ARRAY members` 相关宏注释里「is intended to be be resized before loading the BPF program」去掉第二个 `be`。

按本地主线源码核对，这几处漏拼确实仍在（`kernel/sched/ext/ext.c` 的 `upto` 两处、`tools/sched_ext/include/scx/common.bpf.h` 的 `be be` 一处），不是已被修过的重复劳动。

作者的等价性验证值得单独记一笔：不是「只改了注释所以肯定安全」的说法，而是把每个被改的 C 文件做「删注释 + 字符串字面量替换成占位符 + 压缩空白」后比较前后剩余内容一致，从而论证编译产物不可能不同。同时他诚实标了覆盖缺口：只构建了 x86_64 defconfig，其他没被 defconfig 编到的代码「只读没编」。

## 版本演进与当前进展

- 09-07 14:47 `Hemanth Selam` 发 `[PATCH 4/5] cpuidle: fix repeated word 'that' in comment`（`drivers/cpuidle/cpuidle-tegra.c`，属于另一个 5 补丁系列，本批缓存里没有它的 cover）。
- 09-07 14:49 本系列的 cover + 1/2 + 2/2（msgid 尾号 `-1/-2/-3`，是正常成套发送）。
- 09-07 14:54 与 14:57 又单独发出 `[PATCH 05/14] sched: fix typos in comments` 与 `[PATCH 11/14] sched: fix repeated word 'into' in comment`——这两封在本批缓存里 `in_reply_to` 为空、msgid 尾号都是 `-1`，即各自单独成封发出，对应的 14 补丁系列 cover 没有进入缓存，因此无法给出该系列的完整清单。就已取到的正文看，05/14 触及 `include/linux/sched.h` 与 `kernel/sched/{core,cputime,fair,sched.h,topology,wait_bit}.c`（例如把 dlserver 注释里的 `atleast` 改成 `at least`、RT 注释里的 `compability`、cputime 里的 `substract`、fair.c 里的 `faireness`、sched.h 里的 `actualy`、topology.c 里的 `avaialable`、wait_bit.c 里的 `condtion`），11/14 改的是 `kernel/sched/sched.h` 里 `rq_order_less()` 在 `CONFIG_SCHED_CORE` 下那段注释中的重复词 `into`。
- 本日截至邮件结束，这三个系列都没有任何维护者或第三方回帖。

## Maintainer 意见与讨论焦点

**本日无 review 意见**——三个系列加起来零回帖，因此没有任何来自维护者的真实争议记录。

需要说明但不宜当作本线程事实的背景是：AI 辅助生成的大规模注释/风格补丁在社区里接受度并不统一，有的维护者直接收、有的明确要求这类补丁不要占他的收件箱。本系列作者在 cover 里主动交代工具与复核方法，正是针对这种质疑的预防性写法；这一天没有人就此表态。

从补丁本身能挑、也最可能被挑的具体问题是**修得不彻底**：05/14 在 `kernel/sched/cputime.c` 那个注释块里只把 `Don't substract the steal time from` 改成 `subtract`，而紧邻的上一行 `Record the idle time after substracting ...` 保持原样（主线该注释块两处拼写都在），同一个补丁对同一词形做了不一致处理。类似地，`kernel/sched/sched.h` 的 05/14 那一行上下还有 `exhaused`（在同一注释段里）未见处理。这类残留是纯注释系列最容易让 reviewer 顺手回一句「一并检查下同文件其他处」的地方。

## 合入评估

`likelihood=medium`。有利因素：改动全在注释、风险接近零，作者给出了可复核的等价性验证方法，且每处单独成补丁方便维护者按需丢弃；`kernel/sched/ext/ext.c` 属于 sched_ext，`tools/sched_ext/` 属于 sched_ext 工具侧，这两处的收件人集中。卡点：无人表态；纯注释补丁通常不会被视为需要立即收取的工作项，往往要等维护者在 `next` 分支顺手带；跨 `kernel/` 与 `tools/` 两侧可能需要分别收；另外这类同一天连发多个大系列（2 + 14 + 5 补丁）的做法，可能让维护者倾向要求作者合并、精简说明而不是逐封审。没有 `Fixes`、不涉及 stable。

## 效果评估

无数据，也不需要数据：这是纯注释改动，作者自陈「Nothing outside comments changes」并以「删注释 + 字符串占位 + 压缩空白后剩余内容逐字节一致」的对比论证编译产物等价，未提供任何运行时或性能测量。功能层面的唯一可验证事实是：`v7.3-rc1-269-gbc35965f6940` 上 x86_64 defconfig 构建干净通过，其他架构与配置未构建。

## 我可以参与的点

- **最低成本的一次实质参与**：把 05/14 里的不一致点回给作者——`kernel/sched/cputime.c` 同一注释块中 `substracting` 未改、`kernel/sched/sched.h` 注释里 `exhaused` 等仍在——并附一句建议他把 `scripts/spelling.txt` 的检查按文件一次性收敛，而不是同文件里改一处漏一处。这类反馈对维护者是减负，也是新参与者最容易落地的 review。
- **帮跑等价性验证**：作者的验证只覆盖 x86_64 defconfig。可以在 arm64 或其他 arch 上对 05/14 涉及的文件做前后编译产物对比（他给的方法本身就是可复用的脚本思路），把「未构建」这个缺口补掉。
- **自家分支的同步取舍**：OLK 分支若与上游 `kernel/sched/*` 注释保持接近，这类补丁回合价值在于避免后续 rebase 时的注释冲突，但也要注意别把自家已改过的注释又覆盖回去；建议在自己分支上单独一个 commit 收取，方便日后与上游对齐时丢弃。
- 若打算跟进这类系列，值得先观察 Tejun/sched_ext 侧对 `Assisted-by: Cursor:claude-opus-5` 标注的态度——本线程零回帖本身就是信息，等第一篇被明确接受或被拒的回复出现，再决定要不要投入同类工作。

## 参考链接

- 本系列 cover（验证方法、AI 参与声明、构建基线）: https://lore.kernel.org/all/20260907064943.25304-1-hemanth.selam@gmail.com/
- 1/2 `sched: fix typo "upto" in comments`: https://lore.kernel.org/all/20260907064943.25304-2-hemanth.selam@gmail.com/
- 2/2 `tools/sched_ext: fix repeated word 'be' in comment`: https://lore.kernel.org/all/20260907064943.25304-3-hemanth.selam@gmail.com/
- 同作者当天单独发出的 `[PATCH 05/14] sched: fix typos in comments`: https://lore.kernel.org/all/20260907065448.17762-1-hemanth.selam@gmail.com/
- 同作者当天单独发出的 `[PATCH 11/14] sched: fix repeated word 'into' in comment`: https://lore.kernel.org/all/20260907065725.17876-1-hemanth.selam@gmail.com/
- 同作者当天 cpuidle 系列的 `[PATCH 4/5] cpuidle: fix repeated word 'that' in comment`: https://lore.kernel.org/all/20260907064725.10686-5-hemanth.selam@gmail.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260907-016
date: '2026-09-07'
subject: 'sched: fix typos and repeated words in comments'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260907064943.25304-1-hemanth.selam@gmail.com>
lore_url: https://lore.kernel.org/all/20260907064943.25304-1-hemanth.selam@gmail.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-07'
authors:
- Hemanth Selam
maintainers_involved: []
patch_series:
- version: v1
  msgid: <20260907064943.25304-1-hemanth.selam@gmail.com>
  date: '2026-09-07'
  summary: '2 补丁纯注释修正。1/2 改 kernel/sched/ext/ext.c 两处 upto 为 up to（bypass_lb_node() 注释与 scx_bpf_dispatch kfunc 注释），2/2 改 tools/sched_ext/include/scx/common.bpf.h 中重复的 be。作者以 checkpatch.pl + scripts/spelling.txt 发现，每处独立成补丁便于单独丢弃，标识符相关词故意不改，自陈注释之外无改动并给出「删注释 + 字符串占位 + 压缩空白后比对」的等价性验证方法，带 Assisted-by: Cursor:claude-opus-5，构建基线 v7.3-rc1-269-gbc35965f6940 的 x86_64 defconfig。2 files changed, 3 insertions(+), 3 deletions(-)。'
  review_outcome: 截至本日无回帖、无 Acked-by/Reviewed-by。
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 本日内零 review，纯注释补丁通常不是维护者优先收取的工作项
  - 作者只构建了 x86_64 defconfig，其他架构与配置未构建（其自述）
  - 同日该作者另有 14 补丁与 5 补丁的同类型系列，维护者可能要求合并或精简说明
  next_action: 观察 sched_ext 侧（Tejun Heo 等）是否表态以及对 Assisted-by 标注的接受度；必要时向作者指出同文件内漏改的不一致处
contribution_opportunities:
- kind: review
  description: 指出 05/14 修得不彻底的地方（kernel/sched/cputime.c 同一注释块中 substracting 未改、kernel/sched/sched.h 注释里 exhaused 仍在），建议按文件一次性收敛
- kind: testing
  description: 在非 x86_64 架构上对涉及文件做修改前后编译产物对比，补上作者只构建 x86_64 defconfig 的覆盖缺口
- kind: new_patch
  description: 自家分支按单 commit 收取这类注释修正，便于后续与上游 rebase 时减少注释冲突且可随时丢弃
source_email_count: 3
related_articles: []
tags:
- sched_ext
---
