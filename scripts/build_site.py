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
CONFERENCES_DIR = REPO_ROOT / "_conferences"

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

def build_id_url_map():
    """扫描全部文章，建立 文章ID → 站点URL 映射，供正文引用链接化使用。"""
    id_map = {}
    for md_file in sorted(SCHED_DIR.rglob("sched-*.md")):
        if '.state' in md_file.parts or 'index' in md_file.name:
            continue
        content = md_file.read_text(encoding='utf-8')
        m = re.search(r'\n---\n(.*?)\n---\s*$', content, re.DOTALL)
        if not m:
            continue
        idm = re.search(r"^id:\s*['\"]?(sched-\d{8}-\d{3})['\"]?\s*$", m.group(1), re.M)
        if not idm:
            continue
        stem = md_file.stem
        dm = re.match(r'sched-(\d{8})-', stem)
        if not dm:
            continue
        d = dm.group(1)
        id_map[idm.group(1)] = f"/lkm/{d[:4]}/{d[4:6]}/{d[6:]}/{stem}.html"
    return id_map


ARTICLE_ID_RE = re.compile(r'\[\[(sched-\d{8}-\d{3})\]\]|\b(sched-\d{8}-\d{3})(?![\w-])')


def linkify_article_refs(body: str, id_map: dict) -> str:
    """把正文中的文章 ID 引用转成可点击链接（class=article-ref）。

    处理 [[sched-YYYYMMDD-NNN]] 与裸 sched-YYYYMMDD-NNN 两种形式；
    跳过代码块、行内代码、markdown 链接文本与 URL 内的命中。
    """
    if not id_map or 'sched-' not in body:
        return body
    out_lines = []
    fence_open = False
    for line in body.split('\n'):
        if line.strip().startswith('```'):
            fence_open = not fence_open
            out_lines.append(line)
            continue
        if fence_open:
            out_lines.append(line)
            continue
        seg = []
        lpos = 0
        for m in ARTICLE_ID_RE.finditer(line):
            token = m.group(1) or m.group(2)
            url = id_map.get(token)
            if not url:
                continue
            if line[:m.start()].count('`') % 2 == 1:
                continue
            if m.group(1) is None:
                prev_ch = line[m.start() - 1] if m.start() > 0 else ''
                if prev_ch in ('[', '"', '/', '>') or line[m.end():m.end() + 1] == '<':
                    continue
            seg.append(line[lpos:m.start()])
            seg.append(f'<a class="article-ref" href="{url}">{token}</a>')
            lpos = m.end()
        seg.append(line[lpos:])
        out_lines.append(''.join(seg))
    return '\n'.join(out_lines)


def process_article(src_path: Path, dest_dir: Path, id_map=None):
    """处理单篇文章：底部 frontmatter → 顶部，生成 Jekyll 文章。"""
    content = src_path.read_text(encoding='utf-8')
    fm, body = extract_bottom_frontmatter(content)

    if fm is None:
        return None  # 非标准文章，跳过

    # 标题：优先用正文第一行 # 标题，否则用文件名 slug（打警告：标题应为邮件真实 subject）
    title = extract_title(body)
    if title is None:
        print(f"[warn] 缺少 `# 标题` 行，回退为文件名：{src_path.name}", file=sys.stderr)
        title = src_path.stem
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
    # Keep subject for article layout display (readable title)

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

    # 正文中的文章 ID 引用链接化（在 TL;DR 提取之后，避免污染搜索索引）
    body = linkify_article_refs(body, id_map or {})

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
            f'layout: default',
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
            url = a.get('url') or f"/lkm/{a['date'].replace('-', '/')}/{a['slug']}.html"
            lines.append(
                f'- [{a["id"]}]({url}) `{type_str}/{severity}/{status}` — {title}'
            )

        content = '\n'.join(lines) + '\n'
        (TAGS_DIR / f"{safe_tag}.md").write_text(content, encoding='utf-8')


# ── 会议文章处理（论文笔记）─────────────────────────────────────

def process_conferences():
    """扫描 _conferences/ 集合，返回用于搜索索引与标签页的元数据。

    URL 规则须与 _config.yml 中 conferences collection 的 permalink 保持一致：
    - 有显式 permalink（如届级总览 index.md）→ /lkm + permalink
    - 其余 → /lkm/conferences/<相对路径>.html
    """
    if not CONFERENCES_DIR.exists():
        return []

    articles = []
    for md_file in sorted(CONFERENCES_DIR.rglob("*.md")):
        content = md_file.read_text(encoding='utf-8')
        m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not m:
            print(f"[warn] 会议文章缺少顶部 frontmatter，跳过：{md_file.name}", file=sys.stderr)
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            print(f"[warn] 会议文章 frontmatter 解析失败，跳过：{md_file.name}", file=sys.stderr)
            continue

        if fm.get('published') is False:
            continue

        conf = str(fm.get('conf', '')).strip()
        year = str(fm.get('year', '')).strip()
        if not conf or not year:
            print(f"[warn] 会议文章缺少 conf/year，跳过：{md_file.name}", file=sys.stderr)
            continue

        title = fm.get('title')
        if not title:
            title = extract_title(content[m.end():]) or md_file.stem

        tags = fm.get('tags', []) or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]
        speakers = fm.get('speakers', []) or []
        if isinstance(speakers, str):
            speakers = [s.strip() for s in speakers.split(',')]

        date = str(fm.get('date', '') or f"{year[:4]}-01-01")[:10]
        if fm.get('permalink'):
            url = "/lkm" + str(fm['permalink'])
        else:
            rel = md_file.relative_to(CONFERENCES_DIR).with_suffix('')
            url = f"/lkm/conferences/{rel.as_posix()}.html"

        status = fm.get('source_type') or ('overview' if fm.get('overview') else '')
        articles.append({
            'title': str(title),
            'id': f"{conf.lower()}-{year}-{md_file.stem}",
            'date': date,
            'type': f"{conf} {year}",
            'status': status,
            'severity': fm.get('direction', ''),
            'tags': tags,
            'authors': speakers,
            'url': url,
            'tldr': str(fm.get('tldr', ''))[:300],
            'slug': md_file.stem,
        })
    return articles


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

    id_url_map = build_id_url_map()

    # 处理所有文章
    for md_file in sorted(SCHED_DIR.rglob("sched-*.md")):
        # 跳过 .state 目录（备份等）和 index 文件
        if '.state' in md_file.parts:
            continue
        if 'index' in md_file.name:
            continue
        if dry_run:
            continue

        result = process_article(md_file, POSTS_DIR, id_url_map)
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

    # 处理论文笔记（_conferences/）
    conf_articles = []
    if not dry_run:
        conf_articles = process_conferences()
        for result in conf_articles:
            for tag in result.get('tags', []):
                tag_index[tag].append(result)
            all_articles.append(result)

    # 生成标签页
    if not dry_run:
        generate_tag_pages(tag_index)
        generate_search_index(all_articles)

    # 输出统计
    print(f"✅ 构建完成:")
    print(f"   文章: {len(all_articles) - len(conf_articles)} 篇")
    print(f"   每日索引: {len(daily_indices)} 天")
    print(f"   标签页: {len(tag_index)} 个")
    print(f"   会议分析: {len(conf_articles)} 篇")
    if skipped:
        print(f"   ⚠ 跳过 {len(skipped)} 个非标准文件:")
        for s in skipped[:5]:
            print(f"     - {os.path.basename(s)}")

    # 标签分布 top 10
    top_tags = sorted(tag_index.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    print(f"   📊 Top 标签: {', '.join(f'{t}({len(arts)})' for t, arts in top_tags)}")


if __name__ == "__main__":
    main()
