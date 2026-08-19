#!/usr/bin/env python3
"""build_site.py — 将 sched/ 原始文章预处理为 Jekyll 可用的页面。

职责:
1. 读取 sched/ 下所有文章，将底部 frontmatter 移到顶部
2. 生成 Jekyll posts（posts/_posts/）
3. 生成每日索引页（posts/_daily/）
4. 生成标签索引页（pages/tags/）
5. 生成搜索索引 JSON（assets/search.json）
6. 生成首页数据（pages/home_data.json）
"""

import json
import os
import re
import shutil
import sys
import yaml
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHED_DIR = REPO_ROOT / "sched"
POSTS_DIR = REPO_ROOT / "_posts"
DAILY_DIR = REPO_ROOT / "_daily"
TAGS_DIR = REPO_ROOT / "pages" / "tags"
ASSETS_DIR = REPO_ROOT / "assets"

# ── Frontmatter 解析 ──────────────────────────────────────────

def extract_bottom_frontmatter(content: str):
    """从文件末尾提取 ---...--- 包裹的 YAML frontmatter。"""
    # 从末尾向前查找
    pattern = r'\n---\n(.*?)\n---\s*$'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        yaml_str = match.group(1)
        body = content[:match.start()]
        try:
            fm = yaml.safe_load(yaml_str) or {}
        except yaml.YAMLError:
            fm = {}
        return fm, body.rstrip()
    return None, content


def extract_title(body: str):
    """从正文第一行提取 # 标题。"""
    for line in body.strip().split('\n'):
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
    return None


# ── 单篇文章处理 ──────────────────────────────────────────────

def process_article(src_path: Path, dest_dir: Path):
    """处理单篇文章：底部 frontmatter → 顶部，生成 Jekyll 文章。"""
    content = src_path.read_text(encoding='utf-8')
    fm, body = extract_bottom_frontmatter(content)

    if fm is None:
        return None  # 非标准文章，跳过

    # 标题：优先用 frontmatter 的 subject，否则用正文第一行 #
    title = fm.get('subject') or extract_title(body) or src_path.stem
    date = str(fm.get('date', ''))
    if not date:
        # 从文件名提取日期
        m = re.search(r'sched-(\d{8})', src_path.name)
        if m:
            d = m.group(1)
            date = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        else:
            return None

    article_id = fm.get('id', src_path.stem)
    slug = src_path.stem

    # Jekyll 文件名: YYYY-MM-DD-original-slug.md
    jekyll_filename = f"{date}-{slug}.md"

    # 构造顶部 frontmatter
    fm_out = dict(fm)
    fm_out['title'] = title
    fm_out['layout'] = 'article'
    fm_out.pop('subject', None)

    # 确保 tags 是列表
    if isinstance(fm_out.get('tags'), str):
        fm_out['tags'] = [t.strip() for t in fm_out['tags'].split(',')]

    # 确保 authors 是列表
    if isinstance(fm_out.get('authors'), str):
        fm_out['authors'] = [a.strip() for a in fm_out['authors'].split(',')]

    # 移除 body 中的第一行 # 标题（layout 会渲染标题）
    lines = body.strip().split('\n')
    if lines and lines[0].startswith('# '):
        body = '\n'.join(lines[1:]).strip()

    # 提取 TL;DR 用于搜索索引
    tldr = ''
    in_tldr = False
    for line in body.split('\n'):
        if line.strip() == '## TL;DR':
            in_tldr = True
            continue
        if in_tldr:
            if line.startswith('## '):
                break
            tldr += line.strip() + ' '
    tldr = tldr.strip()[:300]

    # 计算 URL
    url = f"/lkm/{date.replace('-', '/')}/{slug}.html"

    # 组装输出
    yaml_str = yaml.dump(fm_out, allow_unicode=True, default_flow_style=False, sort_keys=False)
    output = f"---\n{yaml_str}---\n\n{body}\n"

    dest_path = dest_dir / jekyll_filename
    dest_path.write_text(output, encoding='utf-8')

    return {
        'title': title,
        'id': article_id,
        'date': date,
        'type': fm.get('type', 'unknown'),
        'status': fm.get('status', 'unknown'),
        'severity': fm.get('severity', 'none'),
        'tags': fm_out.get('tags', []),
        'authors': fm_out.get('authors', []),
        'maintainers_involved': fm.get('maintainers_involved', []),
        'current_version': fm.get('current_version', ''),
        'url': url,
        'tldr': tldr,
        'slug': slug,
        'merge_assessment': fm.get('merge_assessment', {}),
        'source_email_count': fm.get('source_email_count', 0),
    }


# ── 每日索引处理 ──────────────────────────────────────────────

def process_daily_index(src_path: Path, dest_dir: Path):
    """处理每日索引文件。"""
    content = src_path.read_text(encoding='utf-8')
    m = re.search(r'index-(\d{8})\.md', src_path.name)
    if not m:
        return None

    date_str = m.group(1)
    date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

    # 统计文章数
    month_dir = src_path.parent
    articles = list(month_dir.glob(f"sched-{date_str}-*.md"))

    # 提取第一行标题
    first_line = content.strip().split('\n')[0] if content.strip() else ''

    # 将 .md 链接替换为 .html
    content_html = re.sub(r'\(([^)]*)\.md\)', r'(\1.html)', content)

    fm_out = {
        'layout': 'daily_index',
        'title': first_line.lstrip('# ').strip(),
        'date': date,
        'article_count': len(articles),
    }

    yaml_str = yaml.dump(fm_out, allow_unicode=True, default_flow_style=False)
    output = f"---\n{yaml_str}---\n\n{content_html}\n"

    dest_path = dest_dir / f"{date}-index.md"
    dest_path.write_text(output, encoding='utf-8')
    return {'date': date, 'count': len(articles)}


# ── 标签索引生成 ──────────────────────────────────────────────

def generate_tag_pages(tag_index: dict):
    """为每个标签生成索引页。"""
    TAGS_DIR.mkdir(parents=True, exist_ok=True)

    for tag, articles in sorted(tag_index.items()):
        articles.sort(key=lambda a: a.get('date', ''), reverse=True)

        # 安全的 YAML tag 名（处理 sched/core 等含 / 的标签）
        safe_tag = tag.replace('/', '_')

        lines = [
            '---',
            f'layout: tag',
            f'tag: "{tag}"',
            f'title: "标签: {tag}"',
            f'article_count: {len(articles)}',
            '---',
            '',
        ]

        for a in articles:
            type_str = a.get('type', 'unknown')
            status = a.get('status', 'unknown')
            severity = a.get('severity', 'none')
            title = a.get('title', a.get('id', ''))
            # 使用相对路径（从 pages/tags/ 到 posts/_posts/）
            date_parts = a['date'].replace('-', '/')
            url = f"../../posts/_posts/{a['date']}-{a['slug']}.html"
            lines.append(
                f'- [{a["id"]}]({url}) `{type_str}/{severity}/{status}` — {title}'
            )

        content = '\n'.join(lines) + '\n'
        (TAGS_DIR / f"{safe_tag}.md").write_text(content, encoding='utf-8')


# ── 搜索索引 ──────────────────────────────────────────────────

def generate_search_index(all_articles: list):
    """生成客户端搜索索引 JSON。"""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    search_data = []
    for a in all_articles:
        search_data.append({
            'title': a['title'],
            'id': a['id'],
            'date': a['date'],
            'type': a['type'],
            'status': a['status'],
            'severity': a['severity'],
            'tags': a['tags'],
            'authors': a['authors'],
            'url': a['url'],
            'tldr': a['tldr'],
        })

    (ASSETS_DIR / "search.json").write_text(
        json.dumps(search_data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )


# ── 主流程 ────────────────────────────────────────────────────

def main():
    dry_run = '--dry-run' in sys.argv

    # 清理输出目录
    for d in [POSTS_DIR, DAILY_DIR, TAGS_DIR]:
        if d.exists():
            shutil.rmtree(d)
        if not dry_run:
            d.mkdir(parents=True, exist_ok=True)

    tag_index = defaultdict(list)
    all_articles = []
    daily_indices = []
    skipped = []

    # 处理所有文章
    for md_file in sorted(SCHED_DIR.rglob("sched-*.md")):
        # 跳过 .state 目录（备份等）和 index 文件
        if '.state' in md_file.parts:
            continue
        if 'index' in md_file.name:
            continue
        if dry_run:
            continue

        result = process_article(md_file, POSTS_DIR)
        if result:
            for tag in result.get('tags', []):
                tag_index[tag].append(result)
            all_articles.append(result)
        else:
            skipped.append(str(md_file))

    # 处理每日索引
    for idx_file in sorted(SCHED_DIR.rglob("index-*.md")):
        if '.state' in idx_file.parts:
            continue
        if dry_run:
            continue
        result = process_daily_index(idx_file, DAILY_DIR)
        if result:
            daily_indices.append(result)

    # 生成标签页
    if not dry_run:
        generate_tag_pages(tag_index)
        generate_search_index(all_articles)

    # 输出统计
    print(f"✅ 构建完成:")
    print(f"   文章: {len(all_articles)} 篇")
    print(f"   每日索引: {len(daily_indices)} 天")
    print(f"   标签页: {len(tag_index)} 个")
    if skipped:
        print(f"   ⚠ 跳过 {len(skipped)} 个非标准文件:")
        for s in skipped[:5]:
            print(f"     - {os.path.basename(s)}")

    # 标签分布 top 10
    top_tags = sorted(tag_index.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    print(f"   📊 Top 标签: {', '.join(f'{t}({len(arts)})' for t, arts in top_tags)}")


if __name__ == "__main__":
    main()
