#!/usr/bin/env python3
"""
码视野 IoT 官网 - 静态页全量编译脚本
1. 将 posts_index.json 中的文章编译为 posts/post_*.html
2. 将 solutions_index.json 中的解决方案编译为 solutions/sol_*.html
"""
import json
import os
import re
from pathlib import Path

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
  <title>__TITLE__ · 码视野IoT研发团队</title>
  <meta name="description" content="__SUMMARY__">
  <meta property="og:title" content="__TITLE__">
  <meta property="og:image" content="__COVER_IMAGE__">
  <meta property="og:type" content="article">
  <meta name="baidu-site-verification" content="codeva-qFRgW9V0Kz" />
  <meta name="msvalidate.01" content="F3C35A8C570163FEFCE56F09F70A0042" />
  <link rel="canonical" href="__CANONICAL__">
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
  {"@context":"https://schema.org","@type":"TechArticle","headline":"__TITLE__","image":"__COVER_IMAGE__","author":{"@type":"Organization","name":"码视野物联网研发团队"},"datePublished":"__DATE__","description":"__SUMMARY__"}
  </script>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>tailwind.config={theme:{extend:{colors:{brand:{50:'#eff6ff',100:'#dbeafe',200:'#bfdbfe',300:'#93c5fd',400:'#60a5fa',500:'#3b82f6',600:'#2563eb',700:'#1d4ed8',800:'#1e40af',900:'#1e3a8a'}}}}}</script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
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
    <div class="prose" id="content-body"></div>
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
const mdContent = `__CONTENT_MD__`;
mermaid.initialize({startOnLoad:false,theme:'default'});
async function render() {
  const container = document.getElementById('content-body');
  const mermaidBlocks = [];
  const processedMd = mdContent.replace(/```mermaid\\n([\\s\\S]*?)```/g, (_, code) => {
    const id = 'mermaid-' + mermaidBlocks.length;
    mermaidBlocks.push({id, code: code.trim()});
    return `<div class="mermaid-placeholder" data-id="${id}"></div>`;
  });
  container.innerHTML = marked.parse(processedMd);
  for(const {id, code} of mermaidBlocks) {
    const placeholder = container.querySelector(`[data-id="${id}"]`);
    if(placeholder) {
      const div = document.createElement('div');
      div.className = 'mermaid';
      div.textContent = code;
      placeholder.replaceWith(div);
    }
  }
  await mermaid.run();
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


def md_to_html_safe(content):
    content = content.replace('\\', '\\\\')
    content = content.replace('`', '\\`')
    content = content.replace('${', '\\${')
    return content


def build_roi_badges(roi_stats):
    badges = []
    for k, v in roi_stats.items():
        badges.append(f'<div class="text-center flex-1 min-w-[100px]"><div class="text-brand-700 font-bold text-base sm:text-lg">{v}</div><div class="text-brand-500 text-xs mt-0.5">{k}</div></div>')
    return '\n      '.join(badges)


def build_post_html(post, is_solution=False):
    content_safe = md_to_html_safe(post.get('content_markdown', ''))
    roi_data = post.get('roi_data') or post.get('roi_stats') or {}
    roi_badges = build_roi_badges(roi_data)
    cover = post.get('cover_image', 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80')

    html = POST_TEMPLATE
    html = html.replace('__TITLE__', post.get('title', ''))
    html = html.replace('__SUMMARY__', post.get('summary', ''))
    html = html.replace('__COVER_IMAGE__', cover)
    
    if is_solution:
        sid = post['id'] if str(post['id']).startswith('sol_') else f"sol_{post['id']}"
        html = html.replace('__CANONICAL__', f"https://iot-showcase.hei-ai.com/solutions/{sid}.html")
        html = html.replace('__BACK_LINK__', "/solutions.html")
        html = html.replace('__BACK_TEXT__', "← 返回行业解决方案")
        html = html.replace('__CATEGORY__', post.get('industry', '行业解决方案'))
        html = html.replace('__TAG__', post.get('industry_tag', '垂直架构'))
        html = html.replace('__READ_TIME__', post.get('deploy_cycle', '深度方案'))
    else:
        pid = post['id'] if str(post['id']).startswith('post_') else f"post_{post['id']}"
        html = html.replace('__CANONICAL__', f"https://iot-showcase.hei-ai.com/posts/{pid}.html")
        html = html.replace('__BACK_LINK__', "/blog.html")
        html = html.replace('__BACK_TEXT__', "← 返回博文矩阵")
        html = html.replace('__CATEGORY__', post.get('category', '技术实战'))
        html = html.replace('__TAG__', post.get('tag', 'IoT开发'))
        html = html.replace('__READ_TIME__', post.get('read_time', '7 分钟'))

    html = html.replace('__DATE__', post.get('date', ''))
    html = html.replace('__ROI_BADGES__', roi_badges)
    html = html.replace('__CONTENT_MD__', content_safe)
    html = html.replace('__NAV__', get_nav_html(is_solution=is_solution))
    return html


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
        <p class="text-sm text-slate-500 line-clamp-2 mb-3 leading-relaxed">{p.get('summary', '')}</p>
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
              {s.get('summary', '')}
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


def main():
    # 0. 全局清除 Google Fonts
    clean_google_fonts_global()

    # 1. 编译博文
    posts_index_path = BASE_DIR / 'posts_index.json'
    built_posts = 0
    posts = []
    if posts_index_path.exists():
        with open(posts_index_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
        for post in posts:
            out_path = POSTS_DIR / f"post_{post['id']}.html"
            html = build_post_html(post, is_solution=False)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html)
            built_posts += 1
            print(f"[Build Post] {out_path.name} OK")

        # 同步静态预渲染 blog.html
        update_blog_html(posts)

    # 2. 编译解决方案
    solutions_index_path = BASE_DIR / 'solutions_index.json'
    built_solutions = 0
    solutions = []
    if solutions_index_path.exists():
        with open(solutions_index_path, 'r', encoding='utf-8') as f:
            solutions = json.load(f)
        for sol in solutions:
            sol_id = sol['id']
            sol_name = sol_id if sol_id.startswith('sol_') else f"sol_{sol_id}"
            out_path = SOLUTIONS_DIR / f"{sol_name}.html"
            html = build_post_html(sol, is_solution=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html)
            built_solutions += 1
            print(f"[Build Solution] {out_path.name} OK")

        # 同步静态预渲染 solutions.html
        update_solutions_html(solutions)

    print(f"\n[Done] 编译完成: {built_posts} 篇博文，{built_solutions} 个解决方案落地页")

    # 3. 同步刷新 sitemap.xml
    try:
        import generate_sitemap
        generate_sitemap.main() if hasattr(generate_sitemap, 'main') else None
    except Exception:
        import sys
        os.system(f'"{sys.executable}" "{BASE_DIR / "generate_sitemap.py"}"')


if __name__ == '__main__':
    main()
