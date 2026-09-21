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

NAV_HTML = """
<nav class="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur border-b border-slate-100 shadow-sm">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
    <a href="/" class="flex items-center gap-2 font-bold text-slate-900 text-lg">
      <img src="/images/logo.png" alt="码视野" class="w-8 h-8 rounded-lg shadow-sm object-cover">
      <span>码视野</span>
      <span class="hidden sm:inline text-xs font-normal text-slate-400 ml-1">IoT Lab</span>
    </a>
    <div class="hidden md:flex items-center gap-5 text-sm font-medium text-slate-600">
      <a href="/" class="hover:text-brand-600">官网首页</a>
      <a href="/solutions.html" class="hover:text-brand-600">行业解决方案</a>
      <a href="/#cases" class="hover:text-brand-600">项目案例</a>
      <a href="/blog.html" class="hover:text-brand-600">技术博文</a>
      <a href="/contact.html" class="bg-brand-600 text-white px-4 py-1.5 rounded-full hover:bg-brand-700">免费咨询</a>
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
  <link rel="canonical" href="__CANONICAL__">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"TechArticle","headline":"__TITLE__","image":"__COVER_IMAGE__","author":{"@type":"Organization","name":"码视野物联网研发团队"},"datePublished":"__DATE__","description":"__SUMMARY__"}
  </script>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>tailwind.config={theme:{extend:{colors:{brand:{50:'#eff6ff',100:'#dbeafe',200:'#bfdbfe',300:'#93c5fd',400:'#60a5fa',500:'#3b82f6',600:'#2563eb',700:'#1d4ed8',800:'#1e40af',900:'#1e3a8a'}}}}}</script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');
    body{font-family:'Noto Sans SC','PingFang SC',system-ui,sans-serif;}
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
      <span class="text-slate-400 text-xs ml-auto">__DATE__ · __READ_TIME__</span>
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
        <a href="tel:19065223505" class="bg-white text-brand-700 font-semibold px-5 py-2.5 rounded-xl hover:bg-brand-50 transition-colors text-sm">📞 拨打技术专线：19065223505</a>
        <a href="/contact.html" class="bg-brand-800 text-white font-semibold px-5 py-2.5 rounded-xl hover:bg-brand-900 transition-colors text-sm">预约方案架构师 →</a>
      </div>
    </div>
  </div>
</article>
<footer class="bg-slate-900 text-slate-500 py-8">
  <div class="max-w-4xl mx-auto px-4 text-center text-xs">
    © 2026 码视野物联网软件研发团队 · 广东广州 · 电话/微信：19065223505
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
        html = html.replace('__CANONICAL__', f"https://iot.codevision.cn/solutions/sol_{post['id']}.html")
        html = html.replace('__BACK_LINK__', "/solutions.html")
        html = html.replace('__BACK_TEXT__', "← 返回行业解决方案")
        html = html.replace('__CATEGORY__', post.get('industry', '行业解决方案'))
        html = html.replace('__TAG__', post.get('industry_tag', '垂直架构'))
        html = html.replace('__READ_TIME__', post.get('deploy_cycle', '深度方案'))
    else:
        html = html.replace('__CANONICAL__', f"https://iot.codevision.cn/posts/post_{post['id']}.html")
        html = html.replace('__BACK_LINK__', "/blog.html")
        html = html.replace('__BACK_TEXT__', "← 返回博文矩阵")
        html = html.replace('__CATEGORY__', post.get('category', '技术实战'))
        html = html.replace('__TAG__', post.get('tag', 'IoT开发'))
        html = html.replace('__READ_TIME__', post.get('read_time', '7 分钟'))

    html = html.replace('__DATE__', post.get('date', ''))
    html = html.replace('__ROI_BADGES__', roi_badges)
    html = html.replace('__CONTENT_MD__', content_safe)
    html = html.replace('__NAV__', NAV_HTML)
    return html


def main():
    # 1. 编译博文
    posts_index_path = BASE_DIR / 'posts_index.json'
    built_posts = 0
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

    # 2. 编译解决方案
    solutions_index_path = BASE_DIR / 'solutions_index.json'
    built_solutions = 0
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

    print(f"\n[Done] 编译完成: {built_posts} 篇博文，{built_solutions} 个解决方案落地页")


if __name__ == '__main__':
    main()
