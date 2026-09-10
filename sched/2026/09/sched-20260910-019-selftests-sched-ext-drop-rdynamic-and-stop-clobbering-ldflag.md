# selftests/sched_ext: Drop -rdynamic and stop clobbering LDFLAGS

## TL;DR
Tejun Heo 于 09-10 01:52 回复 "Applied to sched_ext/for-7.4."，收取了 `yphbchou0911@gmail.com` 的 v2 构建修复。**原始补丁（v1 与 v2）都不在邮箱缓存里**，缓存中只有 Tejun 的收取通知，因此补丁正文、commit message 与作者姓名均未获取到；本文的技术分析基于标题所指的两个问题在主线 Makefile 中的实际状态（我逐行核对过），并明确区分「邮件内容」与「我的代码核对」。两个缺陷都真实存在，且 `LDFLAGS =` 这一处在整个 `tools/testing/selftests` 里是**唯一一例**——修复本身没有争议，但线程内零测试反馈，且 `-rdynamic` 在 selftests/bpf 与 selftests/hid 中都还保留着，值得有人验证 sched_ext 真的不需要它。

## 背景与问题
标题点出两个 `tools/testing/selftests/sched_ext/Makefile` 的构建卫生问题。Linux 7.2-rc6 中两者都在（已用 `git diff 075b74841bd0 -- tools/testing/selftests/sched_ext/Makefile` 确认本地树该文件与 7.2-rc6 一致）：

```make
56:CFLAGS += -g -O2 -rdynamic -pthread -Wall -Werror $(GENFLAGS)			\
...
65:LDFLAGS = -lelf -lz -lpthread -lzstd
```

**问题一：`LDFLAGS =` 是覆盖式赋值。** selftests 的构建链是层层 include 的（`tools/testing/selftests/lib.mk` 及各 target Makefile），外层或命令行可能已经给 `LDFLAGS` 赋过值（例如 kselftest 统一注入的链接选项、覆盖率/静态链接标志，或用户 `make LDFLAGS=...`）。用 `=` 而不是 `+=` 会把这些值整体丢掉，属于典型的「本地能编过、换一套构建参数就链接失败」类缺陷。我核对了整个 selftests 目录：`grep -rn "^LDFLAGS *=" tools/testing/selftests/*/Makefile` 只命中 sched_ext 这一处，也就是说这是该目录里的孤例，而非普遍约定。

**问题二：`-rdynamic`。** 该选项（等价 `-export-dynamic`）把可执行文件的全部符号导出到动态符号表，典型用途是让按符号名解析自身进程偏移的测试（uprobe / USDT 一类）能成功——`tools/testing/selftests/bpf/Makefile:60` 与 `tools/testing/selftests/hid/Makefile:27` 都保留了它。sched_ext 的 runner 是通过 BPF skeleton 加载调度器的，不按符号名解析自身进程，因此该选项在这里大概率是从 selftests/bpf 抄过来的历史遗留。代价是二进制体积增大、动态符号表被无谓污染。**需要标注：作者判定它多余的具体理由未获取到（补丁正文不在缓存内），以上是我对照三处 Makefile 的分析。**

## 技术方案
补丁正文未获取到，无法给出 diff。按标题可确定的方案范围只有两点：从 `CFLAGS` 中去掉 `-rdynamic`；把 `LDFLAGS = -lelf -lz -lpthread -lzstd` 改为不覆盖既有值的形式（通常是 `LDFLAGS += ...`）。

一个**未在邮件中讨论但真实存在的相互作用**：Ziyang Men 的 `[PATCH v4 4/4] selftests/sched_ext: build BPF schedulers via the shared lib.bpf.mk`（09-09 缓存内，`<20260908235552.2610256-5-ziyang.meme@gmail.com>`）会把 sched_ext 的 Makefile 改为 `include ../lib.bpf.mk` 并删掉约 123 行自建构建逻辑，而他那一版**同样保留**了 `CFLAGS += ... -rdynamic ...` 与 `LDFLAGS = -lelf -lz -lpthread -lzstd`。主线目前尚未 include `lib.bpf.mk`（我已确认该 include 不存在），说明 Ziyang 的转换还没落地。两者改的是同一个文件的同几行：本补丁先进 `sched_ext/for-7.4`，Ziyang 的 v4 之后必须 rebase，否则 `-rdynamic` 与 `LDFLAGS =` 会被他的版本原样带回来。

## 版本演进与当前进展
- v1：存在（v2 的前缀表明有过 v1），但 msgid 与内容均未获取到，缓存内无踪迹。
- v2：`<20260909151741.24742-1-yphbchou0911@gmail.com>`，标题前缀为 `[PATCH v2 sched_ext/for-7.4]`——作者按 Tejun 对 sched_ext 补丁的惯例，把目标 topic 分支直接写进了前缀。该邮件**未投递到本邮箱**，正文未获取到。
- **09-10 01:52（本日）**：Tejun Heo 回复 "Hello, Applied to sched_ext/for-7.4."（`<178897635521.2.18013318571965009488@kernel.org>`），称呼处未写名字。
- 已进 `sched_ext/for-7.4`，缓存内无 tip-bot 回帖，主线尚未合入。
- v1→v2 改了什么、v1 是否收到过意见：均未获取到。

## Maintainer 意见与讨论焦点
- **Tejun Heo**：唯一发言者，且只有收取通知一句。无任何评审意见被缓存捕获——v2 从发出（09-09 15:17）到被收取（09-10 01:52）约 10.5 小时，中间没有可见的往返。
- 无 NAK、无争议、无未决问题。这类构建卫生修复本身就是维护者最愿意直接收的类型。
- 值得记一笔的对照：同一晚（09-10 01:52 / 01:57）Tejun 连续收取了三枚补丁——本枚、同作者的 `sched_ext: Merge adjacent ifdefs in ext.h`（见 sched-20260910-020）、以及 Tianyi Chen 的 `Validate select_cpu_and mask constraints`（见 sched-20260910-018）。说明 `sched_ext/for-7.4` 正在集中收集小修复与自测覆盖。
- 线程中**无人**提到与 Ziyang Men lib.bpf.mk 转换的相互作用，这是一个当前没人盯的协调缺口。

## 合入评估
likelihood: merged。

已进 `sched_ext/for-7.4` topic 分支，剩下只是随分支进主线的时间问题。改动限于 selftests 构建脚本，不影响内核运行时行为。

blocking_issues：无（就已收取这件事而言）。两点需要留意而非阻塞：一是 v2 是否连带处理了 `lib.bpf.mk` 相关的其他赋值方式未知；二是 Ziyang Men 的 v4 4/4 若后续被收取，需要 rebase 到本补丁之上，否则两处缺陷会被带回。

next_action：等 `sched_ext/for-7.4` 合入主线；建议有人在 Ziyang Men 的 lib.bpf.mk 线程里提一句「`-rdynamic` 与 `LDFLAGS =` 已在 for-7.4 中被修掉，v5 请基于该版本」，避免重复回退。

## 效果评估
无 benchmark（构建脚本改动）。线程内也**没有任何构建验证记录**：作者未给出 `make -C tools/testing/selftests TARGETS=sched_ext` 的结果，Tejun 未要求，缓存里没有 CI（bpf-ci bot）回帖。

我能提供的可核实证据只有 Linux 7.2-rc6 的现状（代码核对，非测试结果）：`tools/testing/selftests/sched_ext/Makefile:56` 的 `-rdynamic`、`:65` 的 `LDFLAGS =` 均仍存在；`^LDFLAGS *=` 在 selftests 各 target Makefile 中仅此一处；`-rdynamic` 另见 selftests/bpf:60 与 selftests/hid:27。

## 我可以参与的点
- **补构建与运行验证（testing）**：这是本线程唯一的实质缺口。分别在 (a) 默认构建、(b) `make LDFLAGS="-Wl,--as-needed"` 一类外层注入链接选项、(c) clang/LLVM=1 三种情形下构建 `tools/testing/selftests` 的 sched_ext target，并跑一遍 runner 的全部用例，确认去掉 `-rdynamic` 后没有用例依赖动态符号表（尤其是任何打印符号名/回溯输出的用例）。把结果回帖到已收取的线程里，作为落地前的确认。
- **协调与 lib.bpf.mk 转换的顺序（discussion）**：在 Ziyang Men 的 v4 线程指出本补丁已进 `sched_ext/for-7.4`，请其 v5 基于该版本，避免 `-rdynamic` 与 `LDFLAGS =` 被原样带回。这是一句话成本、能防止真实回退的参与点。
- **横向排查（review）**：`^LDFLAGS *=` 在 selftests 里虽是孤例，但 `tools/` 下其他子目录（如 `tools/sched_ext`、`tools/testing/selftests/*/Makefile` 之外的构建脚本）是否有同类覆盖式赋值，可以顺手扫一遍并作为独立清理发出。

## 参考链接
- Tejun Heo 的收取通知（本日邮件）: https://lore.kernel.org/all/178897635521.2.18013318571965009488@kernel.org/
- 被收取的 v2 补丁（线程根，未投递到本邮箱、正文未获取到）: https://lore.kernel.org/all/20260909151741.24742-1-yphbchou0911@gmail.com/
- 同作者同批被收取的另一枚: https://lore.kernel.org/all/20260909172740.36375-1-yphbchou0911@gmail.com/
- 存在相互作用的 lib.bpf.mk 转换 v4 4/4（Ziyang Men，09-09 缓存内）: https://lore.kernel.org/all/20260908235552.2610256-5-ziyang.meme@gmail.com/
- v1 补丁: 未获取到（缓存内无踪迹）
- upstream commit / stable backport: 未获取到（已进 topic 分支，缓存内无 tip-bot 回帖）

---
id: sched-20260910-019
date: 2026-09-10
subject: "selftests/sched_ext: Drop -rdynamic and stop clobbering LDFLAGS"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<20260909151741.24742-1-yphbchou0911@gmail.com>"
lore_url: "https://lore.kernel.org/all/178897635521.2.18013318571965009488@kernel.org/"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.4"
current_version: v2
generated_at: "2026-09-11T01:55:00"
authors:
  - "yphbchou0911@gmail.com"
maintainers_involved:
  - "Tejun Heo"
patch_series:
  - version: v1
    msgid: null
    date: null
    summary: "未获取到：v2 的前缀表明存在 v1，但缓存内无其 msgid 与内容。"
    review_outcome: "未获取到。"
  - version: v2
    msgid: "<20260909151741.24742-1-yphbchou0911@gmail.com>"
    date: "2026-09-09"
    summary: "按标题为去掉 selftests/sched_ext Makefile 中 CFLAGS 的 -rdynamic，并把覆盖式的 LDFLAGS = 改为不丢弃外层赋值的形式；该邮件未投递到本邮箱，正文与 changelog 未获取到。"
    review_outcome: "09-10 01:52 Tejun Heo: Applied to sched_ext/for-7.4，无附加意见，线程内无其他往返。"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "等 sched_ext/for-7.4 合入主线；建议在 Ziyang Men 的 lib.bpf.mk 线程提醒 v5 需基于本补丁，避免 -rdynamic 与 LDFLAGS = 被带回"
contribution_opportunities:
  - kind: testing
    description: "在默认构建、外层注入 LDFLAGS、clang/LLVM=1 三种情形下构建 selftests sched_ext 并跑完 runner 全部用例，确认去掉 -rdynamic 后无用例依赖动态符号表——线程内零构建验证记录"
  - kind: discussion
    description: "在 Ziyang Men 的 [PATCH v4 4/4] lib.bpf.mk 线程指出本补丁已进 sched_ext/for-7.4，请其 v5 基于该版本，防止两处缺陷被原样带回"
  - kind: review
    description: "横向排查 tools/ 下其他构建脚本是否存在同类覆盖式 LDFLAGS 赋值（selftests 各 target 中目前仅 sched_ext 一处），可作为独立清理发出"
source_email_count: 1
related_articles:
  - "sched-20260910-020"
  - "sched-20260909-011"
tags:
  - sched_ext
---
