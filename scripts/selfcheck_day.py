import re, yaml, json, glob, os, sys

TARGET = sys.argv[1] if len(sys.argv) > 1 else '20260909'
SECTIONS = ["TL;DR", "背景与问题", "技术方案", "版本演进与当前进展",
            "Maintainer 意见与讨论焦点", "合入评估", "效果评估", "我可以参与的点", "参考链接"]
VOCAB = {
    'likelihood': {'merged', 'high', 'medium', 'low', 'rejected', 'unknown'},
    'status': {'rfc', 'under_review', 'merged_tip', 'merged_stable', 'superseded', 'stalled'},
    'type': {'bug', 'feature', 'fix', 'discussion', 'regression'},
    'severity': {'critical', 'high', 'medium', 'low', 'none'},
    'kind': {'testing', 'review', 'extend', 'new_patch', 'discussion'},
}
TAGS_OK = set("""sched_ext cfs eevdf rt deadline load_balance numa_balancing cgroup psi cpufreq idle
core_sched preempt topology uclamp dl_server nohz affinity thermal autogroup rt_bandwidth sched_debug
sched_clock regression hang crash syzbot perf arm64 x86 riscv hyperthreading""".split())

# article_template.md specifies thread_root_msgid / patch_series msgid as "<xxxxx@xxxxx>"
MSGID_SHAPE = re.compile(r'^<[^<>@\s]+@[^<>@\s]+>$')


def lore_msgid(url):
    """msgid == the path component that carries '@'.

    lore URLs come in several shapes (``all/<id>``, ``all/<id>/T/#u``,
    ``r/<id>``, ``lkml/<id>/patch/...``); the last path component is only
    the Message-ID for the first one, so the '@'-bearing segment is used.
    """
    path = re.sub(r'^https?://lore\.kernel\.org/', '', url)
    for seg in path.split('/'):
        if '@' in seg:
            return seg
    return ''


def strip_tags(s):
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r'^\s*Re:\s*', '', s)
        s = re.sub(r'^\s*\[[^\]]*\]\s*', '', s)
    return s.strip()


known_msgid = set()
all_subjects = set()
files_cache = glob.glob('sched/.state/emails/**/*.json', recursive=True)
for f in files_cache:
    if f.endswith('fetch_failures.json'):
        continue
    try:
        d = json.load(open(f))
    except Exception:
        continue
    for e in (d if isinstance(d, list) else [d]):
        if not isinstance(e, dict):
            continue
        for k in ('msgid', 'in_reply_to'):
            if e.get(k):
                known_msgid.add(str(e[k]).strip('<>'))
        for v in (e.get('references') or []):
            if v:
                known_msgid.add(str(v).strip('<>'))
        if e.get('subject'):
            all_subjects.add(e['subject'])
            all_subjects.add(strip_tags(e['subject']))
        blob = (e.get('body_stripped') or '') + '\n' + (e.get('body') or '')
        # msgids quoted verbatim inside email bodies are legitimate evidence
        for m in re.finditer(r'https?://lore\.kernel\.org/[^\s>)"\']+', blob):
            known_msgid.add(lore_msgid(m.group(0)))
        for m in re.finditer(r'<([A-Za-z0-9._%+\-=]+@[A-Za-z0-9.\-]+)>', blob):
            known_msgid.add(m.group(1))

files = sorted(glob.glob('sched/2026/09/sched-%s-*.md' % TARGET))
fails = []


def chk(cond, msg):
    if not cond:
        fails.append(msg)


for f in files:
    b = os.path.basename(f)
    t = open(f).read()
    L = t.split('\n')
    chk(L[0].startswith('# '), '%s: 首行不是 "# " 标题' % b)
    chk(L[0] != '---', '%s: frontmatter 在文件开头（应在底部）' % b)
    fence = [i for i, l in enumerate(L) if l.strip() == '---']
    chk(len(fence) >= 2, '%s: 底部缺少 --- 围栏' % b)
    if len(fence) < 2:
        continue
    a, z = fence[-2], fence[-1]
    chk(a > 3, '%s: frontmatter 围栏出现在文件开头附近（应在底部）' % b)
    try:
        y = yaml.safe_load('\n'.join(L[a + 1:z]))
    except Exception as e:
        fails.append('%s: YAML 解析失败 %s' % (b, e))
        continue
    chk(isinstance(y, dict) and 'id' in y, '%s: frontmatter 无 id' % b)
    subj = y.get('subject', '')
    chk(L[0] == '# ' + subj, '%s: 首行标题与 frontmatter subject 不一致' % b)
    chk(strip_tags(L[0][2:]) in all_subjects, '%s: 标题不在邮件缓存 subject 集合中: %r' % (b, subj))
    chk(b.startswith('sched-%s-%s-' % (TARGET, str(y.get('id', '').rsplit('-', 1)[-1]))),
        '%s: 文件名与 id 不一致 (id=%s)' % (b, y.get('id')))
    hs = re.findall(r'^## (.+)$', t, re.M)
    chk(hs == SECTIONS, '%s: 小节数/顺序不符（%d 个）: %s' % (b, len(hs), hs))
    chk('待补' not in t, '%s: 含「待补」占位' % b)
    chk('?q=' not in t, '%s: 含 ?q= 搜索页链接' % b)
    chk(not re.search(r'x{4,}', t), '%s: 含 xxxxx 占位串' % b)
    chk('uid-' not in t and 'qq-imap' not in t, '%s: 含合成 uid msgid' % b)
    ma = y.get('merge_assessment') or {}
    chk(ma.get('likelihood') in VOCAB['likelihood'], '%s: likelihood=%r 非法' % (b, ma.get('likelihood')))
    chk(y.get('status') in VOCAB['status'], '%s: status=%r 非法' % (b, y.get('status')))
    chk(y.get('type') in VOCAB['type'], '%s: type=%r 非法' % (b, y.get('type')))
    chk(y.get('severity') in VOCAB['severity'], '%s: severity=%r 非法' % (b, y.get('severity')))
    for c in (y.get('contribution_opportunities') or []):
        chk(c.get('kind') in VOCAB['kind'], '%s: kind=%r 非法' % (b, c.get('kind')))
    for tg in (y.get('tags') or []):
        chk(tg in TAGS_OK, '%s: 词表外标签 %r' % (b, tg))
    for ps in (y.get('patch_series') or []):
        v = ps.get('msgid')
        if v in (None, 'null'):
            continue
        chk(MSGID_SHAPE.match(str(v)), '%s: patch_series msgid 应为 <local@domain> 形式: %s' % (b, v))
        chk(str(v).strip('<>') in known_msgid, '%s: patch_series msgid 查无出处: %s' % (b, v))
    for fld in ('thread_root_msgid', 'lore_url'):
        v = y.get(fld)
        if v in (None, 'null'):
            continue
        s = str(v)
        if s.startswith('http'):
            chk(fld != 'thread_root_msgid', '%s: thread_root_msgid 应为 msgid 而非 URL: %s' % (b, s))
        else:
            chk(MSGID_SHAPE.match(s), '%s: %s 应为 <local@domain> 形式: %s' % (b, fld, s))
        idv = lore_msgid(s) if s.startswith('http') else s.strip('<>')
        chk(idv in known_msgid, '%s: %s 的 msgid 查无出处: %s' % (b, fld, idv))
    for url in set(re.findall(r'https?://lore\.kernel\.org/[^\s)\]">]+', t)):
        mid = lore_msgid(url)
        chk(bool(mid), '%s: lore 链接形状异常 %s' % (b, url))
        chk(mid in known_msgid, '%s: lore 链接 msgid 查无出处: %s' % (b, url))

print('检查 %d 篇' % len(files))
if fails:
    print('FAIL %d 项:' % len(fails))
    for x in fails:
        print('  -', x)
    sys.exit(1)
print('全部自查通过')
