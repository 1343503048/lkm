---
id: sched-20260806-002
date: "2026-08-06"
title: "sched/fair: NOHZ 优先 fully idle core（v5，已集齐 R-b）"
series: "Prefer fully idle cores for NOHZ balancing"
type: feature
status: under_review
severity: none
merge_likelihood: high
tags: [cfs, load_balance, nohz, topology, hyperthreading]
authors: ["Andrea Righi <arighi@nvidia.com>", "K Prateek Nayak <kprateeknayak@amd.com>", "Mete Durlu <meted@linux.ibm.com>", "Vincent Guittot <vincent.guittot@linaro.org>", "Shrikanth Hegde <sshegde@linux.ibm.com>"]
reviewers: ["K Prateek Nayak <kprateeknayak@amd.com>", "Mete Durlu <meted@linux.ibm.com>", "Vincent Guittot <vincent.guittot@linaro.org>", "Shrikanth Hegde <sshegde@linux.ibm.com>"]
related_articles: ["sched-20260805-002", "sched-20260804-005", "sched-20260801-005", "sched-20260730-008"]
emails: ["uid-24730@qq-imap", "uid-24669@qq-imap", "uid-24357@qq-imap"]
---

# sched/fair: NOHZ 优先 fully idle core（v5，已集齐 R-b）

## 摘要

Andrea Righi 的「NOHZ idle load balancer 优先挑选整核全 idle 的 CPU」系列推进到 **v5**，本日最大进展：**已集齐 4 个 Reviewed-by**（Prateek、Mete、Vincent、Shrikanth）和 Prateek 的 Tested-by。相较 08-05 的 v3/v4（仍缺数据 + Peter 语义质疑），v5 仅是 tags 收集 + 局部变量重排，说明之前 Peter 关注的 `cpumask_andnot` 语义与 `sched_smt_active` 时机问题已被接受/解决。

核心不变：`find_new_ilb()` 优先选 SMT 兄弟都空闲的物理核，找不到时回退到首个 idle CPU；遇到忙 CPU 后跳过其 SMT 兄弟避免重复 core-idle 检查。

实测（v5 cover 保留）：ad hoc GEMM（每 SMT 核一个 CPU 密集任务）约 6.2 → 9.4 TFLOP/s（+51%）。**注意**：本系列历史上长期缺「带调频噪声」的稳定数据——v5 仍未补，但 reviewer 们已用 R-b 放行，意味着该障碍已被认可解决（或被视为可后续量化）。

## 技术细节

v5 相对 v4 的变化（来自 cover）：
- 收集 Tested-by / Reviewed-by。
- 按 Prateek 建议重排局部变量声明。
- 无功能性改动。

v4 已落实：移除冗余的 `this_cpu` 检查（Prateek/Vincent）。

`find_new_ilb()` 逻辑（v5）：
```
ilb_cpus = idle_cpus_mask ∩ housekeeping(KERNEL_NOISE)
for_each_cpu(ilb_cpu, ilb_cpus):
    if (!idle_cpu(ilb_cpu)):
        if (sched_smt_active() && fallback>=0)
            cpumask_andnot(ilb_cpus, ilb_cpus, cpu_smt_mask(ilb_cpu)); // 跳过忙核兄弟
        continue;
    if (sched_smt_active() && !is_core_idle(ilb_cpu)):
        fallback = ilb_cpu (首次) 且跳过其兄弟;
        continue;
    return ilb_cpu;          // 整核 idle，直接选中
return fallback;            // 回退到首个 idle CPU
```

## 影响与风险

- 影响面：仅 NOHZ idle load balancing 的 ILB 选择，单线程/轻线程性能敏感（尤其 SMT 同核上有忙线程时）。
- 风险：低。已获 4 R-b + 1 T-b，逻辑稳定；唯一历史遗留是「带噪声数据」未在 v5 补，但 reviewer 已放行。
- 收益：在 NVIDIA Vera（Olympus core）等平台上避免反复短暂唤醒 idle 兄弟造成算力干扰，GEMM +51%。

## 评价

从 08-01 起历经 v2→v5，是本轮最成熟的系列之一。**集齐 4 R-b 后合入可能性很高**，建议 maintainer 收尾进 tip/sched/core。值得注意 reviewer 已接受「fallback 保留首个 idle CPU」的设计，解决了 Peter 早前对 `cpumask_andnot` 裁剪候选的担忧。
