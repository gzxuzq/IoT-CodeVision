#!/usr/bin/env python3
"""
码视野 IoT 官网 - 静态页全量编译脚本
1. 将 posts_index.json 中的文章编译为 posts/post_*.html
2. 将 solutions_index.json 中的解决方案编译为 solutions/sol_*.html
"""
import html
import json
import re
from collections import Counter
from pathlib import Path

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

ORIGIN = 'https://iot-showcase.hei-ai.com'


class _DemoteH1(Treeprocessor):
    def run(self, root):
        for el in root.iter():
            if el.tag == 'h1':
                el.tag = 'h2'
        return root


class DemoteH1Extension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(_DemoteH1(md), 'demote_h1', 15)


def attr(value):
    return html.escape(value or '', quote=True)


def text(value):
    return html.escape(value or '', quote=False)


def article_slug(item, is_solution):
    raw = str(item.get('id', ''))
    if is_solution:
        return raw if raw.startswith('sol_') else f'sol_{raw}'
    return raw if raw.startswith('post_') else f'post_{raw}'


def article_path(item, is_solution):
    slug = article_slug(item, is_solution)
    folder = 'solutions' if is_solution else 'posts'
    return f'/{folder}/{slug}.html'


def iso_date(value):
    raw = (value or '').strip()
    day = raw.split(' ')[0]
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day):
        return ''
    clock = raw.split(' ')[1] if ' ' in raw else ''
    if re.fullmatch(r'\d{2}:\d{2}', clock):
        return f'{day}T{clock}:00+08:00'
    return day


_META_LINE = re.compile(
    r'^(版本|编制|日期|保密等级|作者|首发|方案版本|编制单位|行业|适用规模|关键词|阅读时长)\s*[:：]'
)
_HR_LINE = re.compile(r'^[-*_]{3,}$')


def _clean_inline(stripped):
    cleaned = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', stripped)
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', cleaned)
    cleaned = cleaned.replace('**', '').replace('__', '').replace('`', '').replace('*', '')
    return re.sub(r'\s+', ' ', cleaned).strip()


def first_prose(md_text, limit=140):
    paragraphs = []
    buf = []
    in_code = False

    def flush():
        if buf:
            paragraphs.append(re.sub(r'\s+', ' ', ' '.join(buf)).strip())
            buf.clear()

    for line in (md_text or '').splitlines():
        stripped = line.strip()
        if stripped.startswith('```'):
            in_code = not in_code
            flush()
            continue
        if in_code:
            continue
        skip = (
            not stripped
            or stripped.startswith('#')
            or stripped.startswith('>')
            or stripped.startswith('|')
            or stripped.startswith(('- ', '* '))
            or bool(re.match(r'^\d+\.\s', stripped))
            or bool(_HR_LINE.match(stripped))
        )
        if skip:
            flush()
            continue
        cleaned = _clean_inline(stripped)
        if not cleaned or _META_LINE.match(cleaned) or cleaned in {'目录'}:
            flush()
            continue
        buf.append(cleaned)
        if len(' '.join(buf)) >= limit:
            flush()
            break
    flush()
    for para in paragraphs:
        if len(para) >= 40:
            return para[:limit].rstrip('，。；、 ,.;') 
    return paragraphs[0][:limit].rstrip('，。；、 ,.;') if paragraphs else ''


def meta_description(title, summary, md_text, date, item_id, seen):
    prose = first_prose(md_text)
    summary = (summary or '').strip()
    title = (title or '').strip()
    if prose and len(prose) >= 40:
        desc = prose
    elif prose and title and title not in prose:
        desc = f'{title}：{prose}'
    elif summary and title and title not in summary and not summary.startswith('针对') and not summary.startswith('面向'):
        desc = summary
    else:
        desc = title or summary or prose
    desc = re.sub(r'\s+', ' ', desc).strip(' -—')
    if len(desc) > 150:
        desc = desc[:148].rstrip('，。；、 ,.;') + '…'
    if desc in seen:
        stamp = (date or item_id or '').strip()
        desc = f'{desc.rstrip("…")}（{stamp}）'
        if len(desc) > 160:
            desc = desc[:158] + '…'
    seen.add(desc)
    return desc


def document_title(title, date, item_id, title_counts, seen):
    base = (title or '码视野物联网').strip()
    candidate = f'{base}（{date or item_id}）' if title_counts[base] > 1 else base
    if candidate in seen:
        candidate = f'{base}（{item_id}）'
    seen.add(candidate)
    return candidate


def render_markdown(md_text):
    body = markdown.markdown(
        md_text or '',
        extensions=['fenced_code', 'tables', DemoteH1Extension()],
        output_format='html',
    )
    return re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        lambda match: f'<div class="mermaid">{match.group(1)}</div>',
        body,
        flags=re.S,
    )


def related_markup(items, index, is_solution):
    current = items[index]
    key = 'industry' if is_solution else 'category'
    current_key = current.get(key)
    same = [item for i, item in enumerate(items) if i != index and item.get(key) == current_key]
    others = [item for i, item in enumerate(items) if i != index and item.get(key) != current_key]
    chosen = (same + others)[:3]
    lines = []
    for item in chosen:
        href = article_path(item, is_solution)
        label = text(item.get('title') or '相关内容')
        lines.append(f'<li><a href="{attr(href)}">{label}</a></li>')
    return '\n        '.join(lines)


def structured_data(title, description, canonical, cover, published, crumb_name, crumb_path):
    graph = [
        {
            '@type': 'TechArticle',
            'headline': title,
            'description': description,
            'image': cover,
            'author': {'@type': 'Organization', 'name': '码视野', 'url': f'{ORIGIN}/'},
            'publisher': {
                '@type': 'Organization',
                'name': '码视野',
                'url': f'{ORIGIN}/',
                'logo': {'@type': 'ImageObject', 'url': f'{ORIGIN}/images/logo.png'},
            },
            'mainEntityOfPage': canonical,
            'inLanguage': 'zh-CN',
        },
        {
            '@type': 'BreadcrumbList',
            'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': '首页', 'item': f'{ORIGIN}/'},
                {'@type': 'ListItem', 'position': 2, 'name': crumb_name, 'item': f'{ORIGIN}{crumb_path}'},
                {'@type': 'ListItem', 'position': 3, 'name': title, 'item': canonical},
            ],
        },
    ]
    if published:
        graph[0]['datePublished'] = published
    payload = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False)
    return payload.replace('<', '\\u003c')

BASE_DIR = Path(__file__).parent
POSTS_DIR = BASE_DIR / "posts"
SOLUTIONS_DIR = BASE_DIR / "solutions"
POSTS_DIR.mkdir(exist_ok=True)
SOLUTIONS_DIR.mkdir(exist_ok=True)

def get_nav_html(is_solution=False):
    sol_class = "text-brand-600 border-b-2 border-brand-500 pb-0.5 font-bold" if is_solution else "hover:text-brand-600 transition-colors"
    blog_class = "text-brand-600 border-b-2 border-brand-500 pb-0.5 font-bold" if not is_solution else "hover:text-brand-600 transition-colors"
    m_sol_class = "text-brand-600 font-bold" if is_solution else "text-slate-600"
    m_blog_class = "text-brand-600 font-bold" if not is_solution else "text-slate-600"

    return f"""
<nav class="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur border-b border-slate-100 shadow-sm">
  <div class="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
    <a href="/" class="flex items-center gap-2 font-bold text-slate-900 text-lg">
      <img src="/images/logo.png" alt="码视野" class="w-8 h-8 rounded-lg shadow-sm object-cover">
      <span>码视野</span>
      <span class="hidden sm:inline text-xs font-normal text-slate-400 ml-1">IoT Solutions Lab</span>
    </a>
    <div class="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
      <a href="/" class="hover:text-brand-600 transition-colors">官网首页</a>
      <a href="/solutions.html" class="{sol_class}">行业解决方案</a>
      <a href="/#services" class="hover:text-brand-600 transition-colors">服务能力</a>
      <a href="/#cases" class="hover:text-brand-600 transition-colors">项目案例</a>
      <a href="/#tech" class="hover:text-brand-600 transition-colors">技术栈</a>
      <a href="/blog.html" class="{blog_class}">技术博文</a>
      <!-- 顶部右上角电话（微信同号） -->
      <a href="tel:19168817431" class="inline-flex items-center gap-1.5 text-xs font-bold text-slate-800 bg-slate-100 hover:bg-brand-50 hover:text-brand-700 px-3 py-1.5 rounded-full transition-colors border border-slate-200 shadow-sm" title="点击一键拨号，微信同号">
        <span class="text-brand-600 text-sm">📞</span>
        <span class="tracking-wide">19168817431</span>
        <span class="text-[11px] text-brand-600 font-medium">（微信同号）</span>
      </a>
      <a href="/contact.html" class="bg-brand-600 text-white px-4 py-1.5 rounded-full hover:bg-brand-700 transition-colors shadow-sm">免费咨询</a>
    </div>
    <!-- 移动端右上角直拨电话与菜单按钮 -->
    <div class="flex items-center gap-2 md:hidden">
      <a href="tel:19168817431" class="inline-flex items-center gap-1 bg-brand-50 text-brand-700 text-xs px-2.5 py-1 rounded-full border border-brand-200 font-bold" title="微信同号">
        <span>📞</span>
        <span>19168817431</span>
      </a>
      <button id="menu-btn" class="p-2 text-slate-600" aria-label="切换菜单">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
      </button>
    </div>
  </div>
  <div id="mobile-menu" class="hidden md:hidden bg-white border-t border-slate-100 px-4 pb-4">
    <div class="flex flex-col gap-3 pt-3 text-sm font-medium">
      <a href="tel:19168817431" class="flex items-center justify-between bg-blue-50 border border-blue-200 text-brand-700 px-3 py-2 rounded-xl text-xs font-bold">
        <span>📞 19168817431（微信同号）</span>
        <span>点击一键拨打 →</span>
      </a>
      <a href="/" class="text-slate-600">官网首页</a>
      <a href="/solutions.html" class="{m_sol_class}">行业解决方案</a>
      <a href="/#services" class="text-slate-600">服务能力</a>
      <a href="/#cases" class="text-slate-600">项目案例</a>
      <a href="/#tech" class="text-slate-600">技术栈</a>
      <a href="/blog.html" class="{m_blog_class}">技术博文</a>
      <a href="/contact.html" class="bg-brand-600 text-white px-4 py-2 rounded-lg text-center font-bold">免费咨询</a>
    </div>
  </div>
</nav>
""".strip()

POST_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__DOC_TITLE__ · 码视野</title>
  <meta name="description" content="__DESC__">
  <link rel="canonical" href="__CANONICAL__">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="码视野">
  <meta property="og:locale" content="zh_CN">
  <meta property="og:title" content="__DOC_TITLE__">
  <meta property="og:description" content="__DESC__">
  <meta property="og:url" content="__CANONICAL__">
  <meta property="og:image" content="__COVER_IMAGE__">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="__DOC_TITLE__">
  <meta name="twitter:description" content="__DESC__">
  <meta name="twitter:image" content="__COVER_IMAGE__">
  <meta property="article:published_time" content="__PUBLISHED__">
  <meta name="baidu-site-verification" content="codeva-qFRgW9V0Kz" />
  <meta name="msvalidate.01" content="F3C35A8C570163FEFCE56F09F70A0042" />
  <!-- 百度统计 -->
  <script>
  var _hmt = _hmt || [];
  (function() {
    var hm = document.createElement("script");
    hm.src = "https://hm.baidu.com/hm.js?7f5628b9a83545683f5eb2a9df2a559c";
    var s = document.getElementsByTagName("script")[0]; 
    s.parentNode.insertBefore(hm, s);
  })();
  </script>
  <link rel="icon" type="image/png" href="/images/logo.png">
  <link rel="shortcut icon" href="/favicon.ico">
  <link rel="apple-touch-icon" href="/images/logo.png">
  <script type="application/ld+json">
  __LD_JSON__
  </script>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>tailwind.config={theme:{extend:{colors:{brand:{50:'#eff6ff',100:'#dbeafe',200:'#bfdbfe',300:'#93c5fd',400:'#60a5fa',500:'#3b82f6',600:'#2563eb',700:'#1d4ed8',800:'#1e40af',900:'#1e3a8a'}}}}}</script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;}
    .prose h2{font-size:1.35rem;font-weight:700;margin:1.8rem 0 0.8rem;color:#1e293b;border-left:4px solid #2563eb;padding-left:12px;}
    .prose h3{font-size:1.15rem;font-weight:600;margin:1.4rem 0 0.6rem;color:#334155;}
    .prose p{margin:0.8rem 0;line-height:1.8;color:#475569;}
    .prose ul,.prose ol{margin:0.8rem 0 0.8rem 1.5rem;color:#475569;}
    .prose li{margin:0.3rem 0;line-height:1.7;}
    .prose table{width:100%;border-collapse:collapse;margin:1rem 0;font-size:0.875rem;}
    .prose th{background:#eff6ff;color:#1e40af;padding:10px 12px;text-align:left;border:1px solid #bfdbfe;font-weight:600;}
    .prose td{padding:9px 12px;border:1px solid #e2e8f0;color:#475569;}
    .prose tr:hover td{background:#f8fafc;}
    .prose code{background:#f1f5f9;color:#2563eb;padding:2px 6px;border-radius:4px;font-size:0.85em;font-family:'JetBrains Mono',monospace;}
    .prose pre{background:#1e293b;color:#e2e8f0;padding:16px;border-radius:12px;overflow-x:auto;margin:1rem 0;}
    .prose pre code{background:none;color:inherit;padding:0;}
    .prose strong{color:#1e293b;font-weight:600;}
    .prose blockquote{border-left:4px solid #2563eb;padding:8px 16px;background:#eff6ff;margin:1rem 0;border-radius:0 8px 8px 0;}
    .mermaid{text-align:center;margin:1.5rem auto;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px;}
  </style>
</head>
<body class="bg-slate-50 text-slate-800">
__NAV__
<article class="pt-20 pb-16">
  <div class="w-full h-64 sm:h-80 overflow-hidden">
    <img src="__COVER_IMAGE__" alt="__TITLE__" class="w-full h-full object-cover">
  </div>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 mt-8">
    <nav class="text-sm text-slate-500 mb-4" aria-label="面包屑">
      <a href="/" class="text-brand-600 hover:underline">首页</a>
      <span class="mx-1" aria-hidden="true">/</span>
      <a href="__BACK_LINK__" class="text-brand-600 hover:underline">__CRUMB__</a>
    </nav>
    <div class="flex flex-wrap items-center gap-3 mb-4 text-sm">
      <a href="__BACK_LINK__" class="text-brand-600 hover:underline">__BACK_TEXT__</a>
      <span class="bg-brand-50 text-brand-700 px-2 py-0.5 rounded text-xs font-semibold">__CATEGORY__</span>
      <span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-xs">__TAG__</span>
      <span class="text-slate-400 text-xs ml-auto font-mono flex items-center gap-1">
        <span>🕒</span>
        <span>发布时间：__DATE__</span>
      </span>
    </div>
    <h1 class="text-2xl sm:text-3xl font-bold text-slate-900 leading-snug mb-6">__TITLE__</h1>
    <div class="flex flex-wrap gap-3 mb-8 p-4 bg-brand-50 border border-brand-100 rounded-xl">
      __ROI_BADGES__
    </div>
    <div class="prose" id="content-body">
__CONTENT_HTML__
    </div>
    <aside class="mt-10 border-t border-slate-200 pt-8" aria-label="相关阅读">
      <h2 class="text-lg font-bold text-slate-900 mb-3">相关阅读</h2>
      <ul class="list-disc pl-5 space-y-2 text-sm text-brand-700">
        __RELATED__
      </ul>
      <p class="mt-4 text-sm text-slate-600 leading-relaxed">
        <a class="text-brand-700 font-semibold hover:underline" href="/">首页</a>
        <span aria-hidden="true"> · </span>
        <a class="text-brand-700 font-semibold hover:underline" href="/solutions.html">行业解决方案</a>
        <span aria-hidden="true"> · </span>
        <a class="text-brand-700 font-semibold hover:underline" href="/blog.html">技术博文</a>
        <span aria-hidden="true"> · </span>
        <a class="text-brand-700 font-semibold hover:underline" href="/contact.html">联系咨询</a>
      </p>
    </aside>
    <div class="mt-12 bg-brand-700 text-white rounded-2xl p-6 text-center">
      <h2 class="text-xl font-bold mb-2">需要针对贵司场景的专业 IoT 技术咨询？</h2>
      <p class="text-brand-200 text-sm mb-4">码视野研发团队直接对接，30 分钟电话/视频深度沟通，免费出具架构建议与可行性报告</p>
      <div class="flex flex-col sm:flex-row gap-3 justify-center">
        <a href="tel:19168817431" class="bg-white text-brand-700 font-semibold px-5 py-2.5 rounded-xl hover:bg-brand-50 transition-colors text-sm">📞 拨打技术专线：19168817431</a>
        <a href="/contact.html" class="bg-brand-800 text-white font-semibold px-5 py-2.5 rounded-xl hover:bg-brand-900 transition-colors text-sm">预约方案架构师 →</a>
      </div>
    </div>
  </div>
</article>
<footer class="bg-slate-900 text-slate-500 py-8">
  <div class="max-w-4xl mx-auto px-4 text-center text-xs">
    © 2026 码视野物联网软件研发团队 · 广东广州 · 电话/微信：19168817431
  </div>
</footer>
<script>
mermaid.initialize({startOnLoad:false,theme:'default'});
async function render() {
  const container = document.getElementById('content-body');
  if (!container) return;
  container.querySelectorAll('h1').forEach(h => {
    const h2 = document.createElement('h2');
    h2.innerHTML = h.innerHTML;
    h.replaceWith(h2);
  });
  container.querySelectorAll('pre code.language-mermaid').forEach(code => {
    const div = document.createElement('div');
    div.className = 'mermaid';
    div.textContent = code.textContent;
    const pre = code.closest('pre');
    if (pre) pre.replaceWith(div);
  });
  if (container.querySelector('.mermaid')) {
    await mermaid.run({querySelector:'#content-body .mermaid'});
  }
}
render();

// 移动端菜单控制
const menuBtn = document.getElementById('menu-btn');
const mobileMenu = document.getElementById('mobile-menu');
if (menuBtn && mobileMenu) {
  menuBtn.addEventListener('click', () => {
    mobileMenu.classList.toggle('hidden');
  });
  mobileMenu.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      mobileMenu.classList.add('hidden');
    });
  });
}
</script>
</body>
</html>"""


def build_roi_badges(roi_stats):
    badges = []
    for k, v in roi_stats.items():
        badges.append(f'<div class="text-center flex-1 min-w-[100px]"><div class="text-brand-700 font-bold text-base sm:text-lg">{v}</div><div class="text-brand-500 text-xs mt-0.5">{k}</div></div>')
    return '\n      '.join(badges)


def build_post_html(post, is_solution=False, siblings=None, index=0, title_counts=None, seen_titles=None, seen_descs=None):
    siblings = siblings if siblings is not None else [post]
    title_counts = title_counts if title_counts is not None else Counter()
    seen_titles = seen_titles if seen_titles is not None else set()
    seen_descs = seen_descs if seen_descs is not None else set()

    title = (post.get('title') or '').strip()
    date = post.get('date', '')
    item_id = article_slug(post, is_solution)
    doc_title = document_title(title, date, item_id, title_counts, seen_titles)
    description = meta_description(title, post.get('summary', ''), post.get('content_markdown', ''), date, item_id, seen_descs)
    post['seo_description'] = description
    cover = post.get('cover_image') or 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80'
    published = iso_date(date)
    canonical = f'{ORIGIN}{article_path(post, is_solution)}'
    if is_solution:
        back_link = '/solutions.html'
        back_text = '← 返回行业解决方案'
        crumb = '行业解决方案'
        category = post.get('industry', '行业解决方案')
        tag = post.get('industry_tag', '垂直架构')
    else:
        back_link = '/blog.html'
        back_text = '← 返回技术博文'
        crumb = '技术博文'
        category = post.get('category', '技术实战')
        tag = post.get('tag', 'IoT开发')

    page = POST_TEMPLATE
    replacements = {
        '__DOC_TITLE__': attr(doc_title),
        '__TITLE__': text(title),
        '__DESC__': attr(description),
        '__COVER_IMAGE__': attr(cover),
        '__CANONICAL__': attr(canonical),
        '__PUBLISHED__': attr(published),
        '__BACK_LINK__': attr(back_link),
        '__BACK_TEXT__': text(back_text),
        '__CRUMB__': text(crumb),
        '__CATEGORY__': text(category),
        '__TAG__': text(tag),
        '__DATE__': text(date),
        '__ROI_BADGES__': build_roi_badges(post.get('roi_data') or post.get('roi_stats') or {}),
        '__NAV__': get_nav_html(is_solution=is_solution),
        '__LD_JSON__': structured_data(title, description, canonical, cover, published, crumb, back_link),
        '__RELATED__': related_markup(siblings, index, is_solution),
    }
    for key, value in replacements.items():
        page = page.replace(key, value)
    if not published:
        page = page.replace('  <meta property="article:published_time" content="">\n', '')
    page = page.replace('__CONTENT_HTML__', render_markdown(post.get('content_markdown', '')))
    return page


def update_blog_html(posts):
    blog_file = BASE_DIR / "blog.html"
    if not blog_file.exists():
        return

    content = blog_file.read_text(encoding="utf-8")
    # 1. 移除 Google Fonts
    content = re.sub(r"@import\s+url\(['\"]https://fonts\.googleapis\.com/[^'\"]+['\"]\);\s*", "", content)
    content = content.replace("font-family: 'Noto Sans SC', 'PingFang SC', system-ui, sans-serif;", 
                              "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;")

    # 2. 生成静态博文卡片
    cards = []
    for p in posts:
        pid = p['id'] if str(p['id']).startswith('post_') else f"post_{p['id']}"
        roi_spans = []
        roi_data = p.get('roi_stats') or p.get('roi_data') or {}
        for k, v in list(roi_data.items())[:2]:
            roi_spans.append(f'<span class="bg-emerald-50 text-emerald-700 text-xs px-2 py-0.5 rounded">{k}: {v}</span>')
        roi_html = ''.join(roi_spans)

        cards.append(f'''
    <a href="posts/{pid}.html" class="post-card bg-white border border-slate-200 rounded-2xl overflow-hidden hover:shadow-xl hover:border-brand-300 transition-all duration-300 group block" data-category="{p.get('category', '技术实战解析')}">
      <div class="h-44 overflow-hidden bg-slate-100">
        <img src="{p.get('cover_image', 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80')}" alt="{p.get('title', '')}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" loading="lazy">
      </div>
      <div class="p-5">
        <div class="flex items-center justify-between gap-2 mb-2">
          <span class="bg-brand-50 text-brand-700 text-xs font-semibold px-2.5 py-0.5 rounded-full">{p.get('category', '技术实战')}</span>
          <span class="text-xs text-slate-400 font-mono flex items-center gap-1" title="发布时间">
            <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <span>{p.get('date', '')}</span>
          </span>
        </div>
        <h2 class="font-bold text-slate-900 leading-snug line-clamp-2 mb-2 group-hover:text-brand-600 transition-colors">{p.get('title', '')}</h2>
        <p class="text-sm text-slate-500 line-clamp-2 mb-3 leading-relaxed">{text(p.get('seo_description') or p.get('summary', ''))}</p>
        <div class="flex flex-wrap gap-1.5">
          <span class="bg-slate-100 text-slate-600 text-xs px-2 py-0.5 rounded">{p.get('tag', 'IoT')}</span>
          {roi_html}
        </div>
      </div>
    </a>''')

    cards_html = '\n'.join(cards)
    grid_pattern = r'<div id="blog-grid"[^>]*>[\s\S]*?</div>\s*<!-- 更多链接'
    replacement = f'<div id="blog-grid" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">\n{cards_html}\n    </div>\n    <!-- 更多链接'
    content = re.sub(grid_pattern, replacement, content)

    # 替换 post-count
    content = re.sub(r'<span id="post-count">\d*</span>', f'<span id="post-count">{len(posts)}</span>', content)
    content = content.replace('<div id="load-more-wrap" class="text-center mt-10 hidden">', '<div id="load-more-wrap" class="text-center mt-10">')

    # 更新前端筛选 JS：不再需要 fetch posts_index.json，直接极速过滤本地 DOM
    old_script_pattern = r'let allPosts = \[\];[\s\S]*?loadPosts\(\);'
    new_script = '''// 本地 DOM 极速分类筛选 (0 延迟秒开，无需跨洋 fetch JSON)
document.querySelectorAll('.cat-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.cat-btn').forEach(b => {
      b.className = 'cat-btn bg-white border border-slate-200 text-slate-600 text-sm px-4 py-1.5 rounded-full hover:border-brand-400';
    });
    btn.className = 'cat-btn active bg-brand-600 text-white text-sm px-4 py-1.5 rounded-full';
    const targetCat = btn.dataset.cat;
    let visibleCount = 0;
    document.querySelectorAll('.post-card').forEach(card => {
      const cardCat = card.getAttribute('data-category');
      if (targetCat === '全部' || cardCat === targetCat) {
        card.style.display = '';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });
    const countEl = document.getElementById('post-count');
    if (countEl) countEl.textContent = visibleCount;
  });
});'''
    content = re.sub(old_script_pattern, new_script, content)

    blog_file.write_text(content, encoding="utf-8")
    print(f"[Build Blog Page] blog.html 静态预渲染已生成！包含 {len(posts)} 篇博文，彻底消除网络加载延迟。")


def update_solutions_html(solutions):
    sol_file = BASE_DIR / "solutions.html"
    if not sol_file.exists():
        return

    content = sol_file.read_text(encoding="utf-8")
    content = re.sub(r"@import\s+url\(['\"]https://fonts\.googleapis\.com/[^'\"]+['\"]\);\s*", "", content)
    content = content.replace("font-family: 'Noto Sans SC', 'PingFang SC', system-ui, sans-serif;", 
                              "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;")

    cards = []
    for s in solutions:
        sid = s['id'] if str(s['id']).startswith('sol_') else f"sol_{s['id']}"
        roi_badges = ""
        roi_data = s.get('roi_data') or s.get('roi_stats') or {}
        for k, v in list(roi_data.items())[:3]:
            roi_badges += f'''
        <div class="bg-blue-50/70 border border-blue-100 rounded-lg p-2 text-center">
          <div class="text-xs font-bold text-brand-700">{v}</div>
          <div class="text-[11px] text-slate-500 mt-0.5">{k}</div>
        </div>'''

        proto_spans = ""
        for p in (s.get('protocols') or [])[:4]:
            proto_spans += f'<span class="bg-slate-100 text-slate-600 text-xs px-2 py-0.5 rounded font-mono">{p}</span>'

        cover = s.get('cover_image', 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&q=80')

        cards.append(f'''
      <article class="bg-white border border-slate-200 rounded-2xl overflow-hidden hover:shadow-xl hover:border-brand-400 transition-all duration-300 flex flex-col group">
        <div class="h-48 overflow-hidden relative">
          <img src="{cover}" alt="{s.get('title', '')}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" loading="lazy">
          <div class="absolute top-3 left-3 bg-brand-600/90 backdrop-blur text-white text-xs font-semibold px-2.5 py-1 rounded-md">
            {s.get('industry', '行业方案')}
          </div>
          <div class="absolute bottom-3 right-3 bg-white/90 backdrop-blur text-slate-700 text-xs font-medium px-2.5 py-1 rounded-md shadow-sm">
            ⏱ {s.get('deploy_cycle', '快速部署')}
          </div>
        </div>
        <div class="p-6 flex-1 flex flex-col justify-between">
          <div>
            <h2 class="text-xl font-bold text-slate-900 group-hover:text-brand-600 transition-colors mb-3 leading-snug">
              {s.get('title', '')}
            </h2>
            <p class="text-slate-600 text-sm mb-4 line-clamp-3 leading-relaxed">
              {text(s.get('seo_description') or s.get('summary', ''))}
            </p>
            <div class="grid grid-cols-3 gap-2 mb-4">
              {roi_badges}
            </div>
          </div>
          <div class="pt-4 border-t border-slate-100 flex items-center justify-between">
            <div class="flex flex-wrap gap-1.5">
              {proto_spans}
            </div>
            <a href="solutions/{sid}.html" class="inline-flex items-center gap-1 text-sm font-bold text-brand-600 hover:text-brand-700 group-hover:translate-x-1 transition-all">
              <span>查看架构</span>
              <span>→</span>
            </a>
          </div>
        </div>
      </article>''')

    cards_html = '\n'.join(cards)
    grid_pattern = r'<div id="solutions-grid"[^>]*>[\s\S]*?</div>\s*</div>\s*</section>'
    replacement = f'<div id="solutions-grid" class="grid sm:grid-cols-2 lg:grid-cols-2 gap-8">\n{cards_html}\n    </div>\n  </div>\n</section>'
    content = re.sub(grid_pattern, replacement, content)

    old_fetch_pattern = r'async function loadSolutions\(\)[\s\S]*?loadSolutions\(\);'
    content = re.sub(old_fetch_pattern, '// 静态预渲染已激活，无需客户端异步 fetch', content)

    sol_file.write_text(content, encoding="utf-8")
    print(f"[Build Solutions Page] solutions.html 静态预渲染已生成！包含 {len(solutions)} 个方案。")


def update_index_html(posts, solutions, cases):
    index_file = BASE_DIR / "index.html"
    if not index_file.exists():
        return

    content = index_file.read_text(encoding="utf-8")
    # 1. 移除 Google Fonts
    content = re.sub(r"@import\s+url\(['\"]https://fonts\.googleapis\.com/[^'\"]+['\"]\);\s*", "", content)
    content = content.replace("font-family: 'Noto Sans SC', 'PingFang SC', system-ui, sans-serif;", 
                              "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;")

    # 2. 预渲染精选解决方案 (取前 2 个)
    sol_cards = []
    for s in solutions[:2]:
        fileName = s['id'] if str(s['id']).startswith('sol_') else 'sol_' + str(s['id'])
        sol_cards.append(f'''
        <div class="bg-white border border-slate-200 rounded-2xl overflow-hidden hover:shadow-xl hover:border-brand-400 transition-all flex flex-col group">
          <div class="h-44 overflow-hidden relative bg-slate-100">
            <img src="{s.get('cover_image', 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&q=80')}" alt="{s.get('title', '')}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" loading="lazy">
            <div class="absolute top-3 left-3 bg-brand-600/90 text-white text-xs font-semibold px-2.5 py-1 rounded-md backdrop-blur">
              {s.get('industry', '行业方案')}
            </div>
            <div class="absolute bottom-3 right-3 bg-white/90 text-slate-700 text-xs px-2 py-0.5 rounded shadow-sm">
              ⏱ {s.get('deploy_cycle', '交钥匙方案')}
            </div>
          </div>
          <div class="p-6 flex-1 flex flex-col">
            <div class="text-xs font-semibold text-brand-600 mb-1">{s.get('industry_tag', '垂直架构')}</div>
            <h3 class="text-lg font-bold text-slate-900 group-hover:text-brand-600 transition-colors mb-2 leading-snug">
              <a href="solutions/{fileName}.html">{s.get('title', '')}</a>
            </h3>
            <p class="text-xs sm:text-sm text-slate-600 line-clamp-2 mb-4 flex-1">{text(s.get('seo_description') or s.get('summary', ''))}</p>
            <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
              <span class="text-xs text-slate-400 font-mono">{' · '.join((s.get('protocols') or [])[:2])}</span>
              <a href="solutions/{fileName}.html" class="text-brand-600 font-bold text-xs sm:text-sm hover:translate-x-1 transition-transform inline-flex items-center gap-1">
                查阅完整方案 →
              </a>
            </div>
          </div>
        </div>''')

    sol_cards_html = '\n'.join(sol_cards)
    content = re.sub(r'<div id="home-solutions-grid"[^>]*>[\s\S]*?</div>\s*</div>\s*</section>',
                     f'<div id="home-solutions-grid" class="grid sm:grid-cols-2 gap-6">\n{sol_cards_html}\n    </div>\n  </div>\n</section>',
                     content)

    # 3. 预渲染标杆项目案例
    case_cards = []
    for idx, c in enumerate(cases):
        highlights = ""
        for h in (c.get('delivery_highlights') or [])[:3]:
            highlights += f'''
              <div class="text-center bg-blue-50/70 border border-blue-100/60 rounded-lg p-1.5">
                <div class="text-xs font-bold text-brand-700">{h.get('improvement', '')}</div>
                <div class="text-[11px] text-slate-500 mt-0.5">{h.get('metric', '')}</div>
              </div>'''

        case_cards.append(f'''
      <div class="bg-white border border-slate-200 rounded-2xl overflow-hidden hover:shadow-xl hover:border-brand-300 transition-all flex flex-col group">
        <div class="h-44 overflow-hidden relative bg-slate-100">
          <img src="{c.get('cover_image', '')}" alt="{c.get('title', '')}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" loading="lazy">
          <span class="absolute top-3 left-3 bg-slate-900/80 backdrop-blur text-white text-xs px-2.5 py-1 rounded-md font-semibold">{c.get('industry_label', '案例')}</span>
        </div>
        <div class="p-5 flex-1 flex flex-col">
          <div class="text-xs text-slate-400 mb-2 font-mono">工期：{c.get('duration_days', 30)} 天 · 接入设备：{c.get('devices_count', 100)} 台</div>
          <h3 class="font-bold text-slate-900 leading-snug mb-3 text-base flex-1">{c.get('title', '')}</h3>
          <div class="grid grid-cols-3 gap-2 mb-4">
            {highlights}
          </div>
          <p class="text-xs text-slate-500 italic mb-4 border-l-2 border-brand-300 pl-2">"{c.get('client_quote', '')[:50]}…"</p>
          <button onclick="showCaseModal({idx})" class="w-full py-2 bg-slate-100 hover:bg-brand-50 hover:text-brand-700 text-slate-700 text-xs font-bold rounded-xl transition-colors">
            查看案例架构与交付细节 →
          </button>
        </div>
      </div>''')

    case_cards_html = '\n'.join(case_cards)
    content = re.sub(r'<div id="cases-grid"[^>]*>[\s\S]*?</div>\s*</div>\s*</section>',
                     f'<div id="cases-grid" class="grid md:grid-cols-3 gap-6">\n{case_cards_html}\n    </div>\n  </div>\n</section>',
                     content)

    # 4. 预渲染最新 3 篇博文
    blog_cards = []
    for p in posts[:3]:
        pid = p['id'] if str(p['id']).startswith('post_') else f"post_{p['id']}"
        blog_cards.append(f'''
      <a href="posts/{pid}.html" class="bg-white border border-slate-200 rounded-2xl overflow-hidden hover:shadow-lg hover:border-brand-300 transition-all group block">
        <div class="h-36 overflow-hidden bg-slate-100">
          <img src="{p.get('cover_image', '')}" alt="{p.get('title', '')}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" loading="lazy">
        </div>
        <div class="p-4">
          <div class="flex items-center justify-between gap-2 mb-2">
            <span class="bg-brand-50 text-brand-700 text-xs px-2.5 py-0.5 rounded-full font-medium">{p.get('category', '技术实战')}</span>
            <span class="text-xs text-slate-400 font-mono flex items-center gap-1" title="发布时间">
              <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              <span>{p.get('date', '')}</span>
            </span>
          </div>
          <h3 class="font-semibold text-slate-900 text-sm leading-snug line-clamp-2 mb-2 group-hover:text-brand-600 transition-colors">{p.get('title', '')}</h3>
          <p class="text-xs text-slate-500 line-clamp-2 leading-relaxed">{text(p.get('seo_description') or p.get('summary', ''))}</p>
        </div>
      </a>''')

    blog_cards_html = '\n'.join(blog_cards)
    content = re.sub(r'<div id="blog-preview"[^>]*>[\s\S]*?</div>\s*</div>\s*</section>',
                     f'<div id="blog-preview" class="grid sm:grid-cols-3 gap-6">\n{blog_cards_html}\n    </div>\n  </div>\n</section>',
                     content)

    # 5. 注入 cachedCases 并移除 3 个异步 fetch
    cases_json_str = json.dumps(cases, ensure_ascii=False)
    replace_script = f'''let cachedCases = {cases_json_str};
// 静态预渲染已激活：首页核心板块（方案、案例、博文）已全部固化在 HTML 中，0ms 秒开无网络等待'''

    pattern_to_remove = r'// 加载博文预览[\s\S]*?loadBlogPreview\(\);'
    content = re.sub(pattern_to_remove, replace_script, content)

    index_file.write_text(content, encoding="utf-8")
    print(f"[Build Index Page] index.html 静态预渲染成功！包含 2 个精选方案 + {len(cases)} 个案例 + 3 篇最新博文。")


def clean_google_fonts_global():
    for filename in ["index.html", "contact.html"]:
        fpath = BASE_DIR / filename
        if fpath.exists():
            c = fpath.read_text(encoding="utf-8")
            c = re.sub(r"@import\s+url\(['\"]https://fonts\.googleapis\.com/[^'\"]+['\"]\);\s*", "", c)
            c = c.replace("font-family: 'Noto Sans SC', 'PingFang SC', system-ui, sans-serif;", 
                          "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;")
            fpath.write_text(c, encoding="utf-8")
            print(f"[Font Clean] {filename} 已彻底移除 Google Fonts 远程阻塞！")


def load_json(path):
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    # 0. 全局清除 Google Fonts
    clean_google_fonts_global()

    posts = load_json(BASE_DIR / 'posts_index.json')
    solutions = load_json(BASE_DIR / 'solutions_index.json')
    title_counts = Counter((item.get('title') or '').strip() for item in posts)
    title_counts.update((item.get('title') or '').strip() for item in solutions)
    seen_titles, seen_descs = set(), set()

    built_posts = 0
    for index, post in enumerate(posts):
        out_path = POSTS_DIR / f"post_{post['id']}.html"
        page = build_post_html(
            post,
            is_solution=False,
            siblings=posts,
            index=index,
            title_counts=title_counts,
            seen_titles=seen_titles,
            seen_descs=seen_descs,
        )
        out_path.write_text(page, encoding='utf-8')
        built_posts += 1
        print(f"[Build Post] {out_path.name} OK")
    if posts:
        update_blog_html(posts)

    built_solutions = 0
    for index, sol in enumerate(solutions):
        sol_name = article_slug(sol, True)
        out_path = SOLUTIONS_DIR / f'{sol_name}.html'
        page = build_post_html(
            sol,
            is_solution=True,
            siblings=solutions,
            index=index,
            title_counts=title_counts,
            seen_titles=seen_titles,
            seen_descs=seen_descs,
        )
        out_path.write_text(page, encoding='utf-8')
        built_solutions += 1
        print(f"[Build Solution] {out_path.name} OK")
    if solutions:
        update_solutions_html(solutions)

    # 3. 编译首页静态预渲染 (将方案、案例、博文直接固化至 index.html)
    cases_index_path = BASE_DIR / 'cases_index.json'
    cases = []
    if cases_index_path.exists():
        with open(cases_index_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
    update_index_html(posts, solutions, cases)

    print(f"\n[Done] 编译完成: {built_posts} 篇博文，{built_solutions} 个解决方案落地页")

    import generate_sitemap
    generate_sitemap.main()


if __name__ == '__main__':
    main()
