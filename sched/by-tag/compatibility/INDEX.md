# tag: compatibility

共 1 篇

- [sched-20260820-002](../../2026/08/sched-20260820-002.md) `feature/low/under_review` — Daniel T. Lee 把 sched_ext ops 的几个 container 指针参数（cs/cpuc/dsq/task 的 kptr）从 `PTR_UNTRUSTED` 改为 `PTR_TRUSTED`，因为 ops 调用上下文已保证其可信。用户写 BPF 调度器时不再被迫加冗余检查。已通过 bpf CI，合入概率高。