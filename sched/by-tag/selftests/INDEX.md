# tag: selftests

共 3 篇

- [sched-20260815-016](../../2026/08/sched-20260815-016-sched-ext-make-sched-class-ext-select-generic-allocator-2.md) `fix/low/under_review` — Xu Xuefei 修复 `sched_ext` selftest `scx_ddsp` 中"failure tests"的偶发（flaky）失败：根因是任务退出与断言检查时序竞争。v1 刚发出，等待 Tejun review。
- [sched-20260815-015](../../2026/08/sched-20260815-015-selftests-sched-ext-fix-flaky-ddsp-failure-tests-on-busy-sys.md) `feature/low/under_review` — bpf-ci 代为提交的补丁：让 `selftests/sched_ext` 通过共享的 `lib.bpf.mk` 构建 libbpf，与上游 libbpf 同步，消除版本漂移。CI 已测试通过（2026-08-15 13:55）。属 08-14 系列 010 的延续（selftests/sched_ext 构建现代化）。
- [sched-20260814-010](../../2026/08/sched-20260814-010-selftests-sched-ext-build-bpf-schedulers-via-the-shared-lib-.md) `cleanup/low/under_review` — Ziyang Men 提交 v3（4/4）「selftests/sched_ext: build BPF schedulers via the shared lib.bpf.mk」。把 sched_ext 自带的约 130 行 libbpf/bpftool/vmlinux.h/BPF object/skeleton 构建逻辑替换为共享的 `tools/testing/selftests/lib.b
