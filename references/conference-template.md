# 论文笔记：新增会议分析的操作说明（本文件不会被发布，references/ 已在 _config.yml 的 exclude 中）

## 目录与 URL 规则

```
_conferences/<会议小写>-<年份>/index.md    →  /lkm/conferences/<会议小写>-<年份>/   （届级总览）
_conferences/<会议小写>-<年份>/<slug>.md  →  /lkm/conferences/<会议小写>-<年份>/<slug>.html（单篇分析）
```

- 每届会议一个目录；跨届总览用区间年份命名目录，如 `osdi-2016-2026/`、`lpc-2020-2025/`。
- 新会议零代码改动：`conf` 填什么，落地页筛选器就自动出现什么（未知会议徽章用默认配色；
  想要专属配色在 assets/css/main.css 加一行 `.conf-<小写> { ... }`）。

## front-matter 模板

```yaml
---
title: "文章标题（英文原题或中文整理标题）"
conf: LPC              # 会议名：LPC / OSDI / SOSP / CKC（中国内核开发者大会）/ OSPM / LSFMM / ...，自由填写
year: "2025"           # 必须加引号，保持字符串；跨届总览用 "2016-2026"
direction: sched       # sched / mm / perf / android / arch / mixed；也可自定义新值（自动进筛选器）
overview: true         # 仅届级总览页填写；单篇分析省略此字段
track: Scheduler & Real-Time MC   # 可选，会议内的 track/MC 名
speakers: [John Stultz, Qais Yousef]   # 单篇分析填写；总览省略
source_url: https://...            # 可选，论文 PDF / 会议视频 / 官方议程页
source_type: talk      # paper / talk / video，可选
permalink: /conferences/lpc-2025/  # 仅总览页需要；单篇分析由目录自动生成 URL，无需填写
date: 2026-09-22       # 分析发布日期
tags: [sched qos]      # 复用日报标签词表（eevdf、proxy execution、cpuset...），自动进标签页
tldr: "一句话摘要，进全局搜索索引"
related_daily:         # 可选，相关日报文章 ID，页面侧栏会渲染成链接
  - sched-20260909-010
---
```

## 正文约定

- 正文从 H2（`##`）开始写，H1 由布局渲染；TOC、阅读进度条自动生成。
- 单篇分析建议结构：背景 → 技术方案 → 与主线/日报的关联（可引用 related_daily）。
- 标题里的链接、表格均支持（kramdown）。

## 上传即生效

push 到 master 后 GitHub Actions 会自动跑 `scripts/build_site.py`（会议文章进
assets/search.json 与 pages/tags/ 标签页）再做 Jekyll 构建部署，无需手动跑脚本。
