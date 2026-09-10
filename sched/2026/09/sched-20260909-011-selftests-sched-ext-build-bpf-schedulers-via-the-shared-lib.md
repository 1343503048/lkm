# selftests/sched_ext: build BPF schedulers via the shared lib.bpf.mk

## TL;DR

本文为增量更新，重构动机与 skeleton API 等价性的完整分析见 related_articles 中的 sched-20260814-010。Ziyang Men 在 09-09 07:55 发出 v4 的 4/4：把 `tools/testing/selftests/sched_ext/Makefile` 自带的约 130 行 libbpf/bpftool/vmlinux.h/BPF object/skeleton 构建机器换成 `include ../lib.bpf.mk`，让 sched_ext 成为继 `selftests/cgroup`、`selftests/hid` 之后第三个树内消费者——净删 97 行（+26/-123）。注意：v4 相对 v3 改了什么**未获取到**（当天邮箱里只有 4/4，封面不在缓存内）。

## 背景与问题

sched_ext 的 selftests 需要构建大量 BPF 程序（每个被测调度器一个 skeleton，另有 subskeleton），这套流程——构建 libbpf、构建 host bpftool、从 vmlinux BTF 生成 `vmlinux.h`、用 clang 编 `.bpf.o`、再用 bpftool 生成 skeleton——在每个需要 BPF 的 selftests 目录里都要重写一遍。tools/testing 下已经存在一份共享片段 `lib.bpf.mk`（`selftests/cgroup` 与 `selftests/hid` 在用），sched_ext 只是没接进来。重复维护的直接代价是这套片段每次演进（比如 clang 版本适配）都得手工同步三处。

## 技术方案

删掉本地那 130 行，改为 `include ../lib.bpf.mk`，然后把 sched_ext 特有的东西作为变量喂给共享规则：

```make
# Build scheduler skeletons and subskeletons with the shared BPF rules.
BPF_SRCS        := $(wildcard *.bpf.c)
BPF_SKEL_EXT    := .bpf.skel.h
BPF_GEN_SUBSKEL := 1
# Preserve the existing build/ layout.
BPF_OBJ_DIR  := $(OUTPUT)/build/obj/sched_ext
BPF_SKEL_DIR := $(OUTPUT)/build/include
SCXOBJ_DIR   := $(BPF_OBJ_DIR)
```

`BPF_GEN_SUBSKEL := 1` 是这个补丁最关键的一行——sched_ext 用的是 subskeleton（多个 BPF 对象合并成一个 skeleton），共享片段此前只有 cgroup/hid 两个消费者，不一定已支持；作者同时保留 `build/` 输出布局不变，避免 `clean` 与既有文档/脚本路径失配。本地 `CFLAGS` 与 `LDFLAGS` 保持原样（`-lelf -lz -lpthread -lzstd` 等），只把不再需要的 include 目录（`$(INCLUDE_DIR)`、`$(APIDIR)`、`$(BPFDIR)` 等）交给共享片段提供。

作者声明「所有生成的 skeleton 与 subskeleton 保持同样的公开 API，runner 的构建与链接方式不变」。补丁带 `Suggested-by: Eduard Zingerman` 与 `Suggested-by: Mykola Lysenko`（两位都是 BPF/selftests 侧的建议者）以及 `Assisted-by: Claude:claude-opus-5`。

## 版本演进与当前进展

- v3：08-14 发出（`<20260814075054.507089-5-ziyang.meme@gmail.com>`），当时 Makefile 减 116 行。
- v4 4/4：09-09 07:55（`<20260908235552.2610256-5-ziyang.meme@gmail.com>`），改为 +26/-123。相比 v3 少删了几行、多了一些显式的目录保留设置，但**v3→v4 的 changelog 未获取到**（封面 `<20260908235552.2610256-1-ziyang.meme@gmail.com>` 不在当天邮件缓存里），因此不能确认这次迭代是为回应谁的哪条意见。
- 4/4 发出当天无人回帖；1/4..3/4 也不在当天缓存内。

## Maintainer 意见与讨论焦点

本日没有 review。可以确认为「悬着」的是我在 08-14 那篇里提过的那个问题——本地 `BPF_CFLAGS` 的覆盖是否改变了构建严格性。v4 里这一点反而更值得问：与 v3 一样，`BPF_CFLAGS` 被重新赋值给共享片段，而 diff 显示原来本地的 `-O2 -mcpu=v3` 这一对**从 sched_ext 的 BPF_CFLAGS 里直接消失了**（共享片段是否等价补回，本封邮件里没说明），同时原先手写的 `IS_LITTLE_ENDIAN` 推导被换成共享片段提供的 `$(MENDIAN)`。`-mcpu=v3` 影响生成 BPF 指令集（例如是否可用 32-bit atomic / jump-offset 优化），在旧内核或不同 clang 版本上产物会不一样；这类差异在 selftests 里通常表现为「编不过」或「verifier 拒绝」，而不是行为错误，因此很容易在自测中被忽略。Eduard Zingerman 与 Mykola Lysenko 作为建议者，目前也还没表态。

## 合入评估

`likelihood=medium`。方向上无人反对（两票 `Suggested-by` 就是 BPF selftests 侧主动要求的收敛），改动局限在 `tools/testing/selftests/sched_ext/Makefile`，且作者承诺 skeleton 公开 API 不变。卡点有三：一是 `BPF_GEN_SUBSKEL` 这条能力共享片段是否真的支持、还是需要同时改 `lib.bpf.mk`（若需要，本系列只有 4/4 改了 sched_ext，那另一半在哪）当天无证据；二是 `-O2 -mcpu=v3` 消失后产物是否等价；三是这是第 4 版但当天连一次 `Tested-by`/`Reviewed-by` 都没有。

`next_action`：作者补上 v4 的 changelog（封面未收到，社区可能同样没看到 v3→v4 的差异说明），并由 sched_ext/BPF 侧确认共享片段对 subskeleton 的支持与编译选项默认值。

## 效果评估

无任何数据。这类构建系统重构的效果体现在维护成本上：净删 97 行，sched_ext 从此不需要单独跟随 libbpf/bpftool 的构建约定变化。属结构性收益，作者与社区都没有（也不需要）给出性能数字。

## 我可以参与的点

- `testing`：这是能立刻产生价值的动作——在 `make -C tools/testing/selftests/sched_ext` 下确认全部 skeleton 与 subskeleton 仍能生成、runner 能链接，并在至少两个不同 clang 版本上各跑一遍。这类 Makefile 重构最容易在「作者的 clang 版本」以外的组合上碎掉。
- `review`：直接问清 `-O2 -mcpu=v3` 从本地 `BPF_CFLAGS` 去掉之后，共享片段给的默认值是什么；如果不同，`bpftool prog dump xlated` 对比一两个调度器的产物即可确认指令集差异。
- `review`：确认 `BPF_GEN_SUBSKEL` 是否已在 `tools/testing/selftests/lib.bpf.mk` 中存在——若不存在，说明本系列还缺一片（改共享片段），而当天缓存里看不到。
- `new_patch`：cgroup、hid、sched_ext 三个消费者的 Makefile 现在都往 `lib.bpf.mk` 收敛，自家分支若同步了这类目录，可以顺着检查自己的 `tools/testing/selftests/` 里还有哪些重复的 BPF 构建机器。

## 参考链接

- v4 4/4: https://lore.kernel.org/all/20260908235552.2610256-5-ziyang.meme@gmail.com/
- v3 线程根: https://lore.kernel.org/all/20260814075054.507089-5-ziyang.meme@gmail.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: "sched-20260909-011"
date: "2026-09-09"
subject: "selftests/sched_ext: build BPF schedulers via the shared lib.bpf.mk"
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "20260908235552.2610256-5-ziyang.meme@gmail.com"
lore_url: "https://lore.kernel.org/all/20260908235552.2610256-5-ziyang.meme@gmail.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v4
generated_at: "2026-09-10T01:00:00"
authors:
  - "Ziyang Men"
maintainers_involved: []
patch_series:
  - version: v3
    msgid: "20260814075054.507089-5-ziyang.meme@gmail.com"
    date: "2026-08-14"
    summary: "用共享的 tools/testing/selftests/lib.bpf.mk 取代 sched_ext 自带约 130 行 BPF 构建机器，Makefile 减 116 行；声明 28 个 skeleton/subskeleton 公开 API 不变。"
    review_outcome: "Suggested-by Eduard Zingerman 与 Mykola Lysenko；当日无进一步 review。"
  - version: v4
    msgid: "20260908235552.2610256-5-ziyang.meme@gmail.com"
    date: "2026-09-09"
    summary: "同上方向，实测 +26/-123；以 BPF_SRCS/BPF_SKEL_EXT/BPF_GEN_SUBSKEL=1 与显式 BPF_OBJ_DIR/BPF_SKEL_DIR 接入共享规则并保留既有 build/ 布局，本地 IS_LITTLE_ENDIAN 推导改用共享片段的 $(MENDIAN)。v3→v4 的 changelog 未获取到（封面不在当天缓存）。"
    review_outcome: "4/4 发出当天无人回帖；1/4..3/4 亦不在当天缓存内。"
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "v4 封面未收到，v3→v4 改了什么、回应了谁的意见对社区不可见"
    - "本地 BPF_CFLAGS 中的 -O2 -mcpu=v3 在新版本里消失，共享片段是否等价补回未在邮件中说明"
    - "BPF_GEN_SUBSKEL 这一能力是否已存在于 lib.bpf.mk 无证据；若不存在则本系列缺改共享片段的那一半"
    - "已到第 4 版但当天无任何 Reviewed-by/Tested-by"
  next_action: "作者补发或说明 v4 changelog；确认共享片段对 subskeleton 与编译选项默认值的处理；请 sched_ext/BPF 侧至少给一次跨 clang 版本的构建验证"
contribution_opportunities:
  - kind: testing
    description: "在两个以上不同 clang 版本下构建 tools/testing/selftests/sched_ext，确认全部 skeleton/subskeleton 生成、runner 链接且用例可运行，这类 Makefile 重构最易在作者之外的工具链组合上碎掉"
  - kind: review
    description: "追问 -O2 -mcpu=v3 被去掉后共享片段给的默认值，并用 bpftool prog dump xlated 比对一两个调度器产物是否有指令集差异"
  - kind: review
    description: "确认 tools/testing/selftests/lib.bpf.mk 是否已支持 BPF_GEN_SUBSKEL，若无需补上改共享片段的那一半补丁"
source_email_count: 1
related_articles:
  - "sched-20260814-010"
tags:
  - "sched_ext"
---
