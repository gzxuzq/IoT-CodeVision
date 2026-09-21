#!/usr/bin/env python3
"""
码视野 IoT 官网 - 博文静态页编译脚本
将 posts_index.json 中的文章编译为静态 HTML 落地页
"""
import json
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
POSTS_DIR = BASE_DIR / "posts"
POSTS_DIR.mkdir(exist_ok=True)

NAV_HTML = """
<nav class="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur border-b border-slate-100 shadow-sm">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
    <a href="/" class="flex items-center gap-2 font-bold text-brand-700 text-lg">
      <span class="text-2xl">🔗</span><span>码视野</span>
    </a>
    <div class="hidden md:flex items-center gap-5 text-sm font-medium text-slate-600">
      <a href="/" class="hover:text-brand-600">官网首页</a>
      <a href="/#services" class="hover:text-brand-600">服务能力</a>
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
  <title>__TITLE__ · 码视野IoT技术博客</title>
  <meta name="description" content="__SUMMARY__">
  <meta property="og:title" content="__TITLE__">
  <meta property="og:image" content="__COVER_IMAGE__">
  <meta property="og:type" content="article">
  <link rel="canonical" href="__CANONICAL__">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"TechArticle","headline":"__TITLE__","image":"__COVER_IMAGE__","author":{"@type":"Organization","name":"码视野"},"datePublished":"__DATE__","description":"__SUMMARY__"}
  </script>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>tailwind.config={theme:{extend:{colors:{brand:{50:'#eff6ff',100:'#dbeafe',200:'#bfdbfe',300:'#93c5fd',400:'#60a5fa',500:'#3b82f6',600:'#2563eb',700:'#1d4ed8',800:'#1e40af',900:'#1e3a8a'}}}}}</script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');
    body{font-family:'Noto Sans SC','PingFang SC',system-ui,sans-serif;}
    .prose h2{font-size:1.4rem;font-weight:700;margin:1.8rem 0 0.8rem;color:#1e293b;border-left:4px solid #2563eb;padding-left:12px;}
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
  <!-- Hero 图 -->
  <div class="w-full h-64 sm:h-80 overflow-hidden">
    <img src="__COVER_IMAGE__" alt="__TITLE__" class="w-full h-full object-cover">
  </div>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 mt-8">
    <!-- 元信息 -->
    <div class="flex flex-wrap items-center gap-3 mb-4 text-sm">
      <a href="/blog.html" class="text-brand-600 hover:underline">← 返回博文矩阵</a>
      <span class="bg-brand-50 text-brand-700 px-2 py-0.5 rounded text-xs font-semibold">__CATEGORY__</span>
      <span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-xs">__TAG__</span>
      <span class="text-slate-400 text-xs ml-auto">__DATE__ · __READ_TIME__</span>
    </div>
    <h1 class="text-2xl sm:text-3xl font-bold text-slate-900 leading-snug mb-6">__TITLE__</h1>
    <!-- ROI 指标条 -->
    <div class="flex flex-wrap gap-3 mb-8 p-4 bg-brand-50 border border-brand-100 rounded-xl">
      __ROI_BADGES__
    </div>
    <!-- 正文 -->
    <div class="prose" id="content-body"></div>
    <!-- CTA -->
    <div class="mt-12 bg-brand-700 text-white rounded-2xl p-6 text-center">
      <h2 class="text-xl font-bold mb-2">有 IoT 项目需要咨询？</h2>
      <p class="text-brand-200 text-sm mb-4">免费 30 分钟技术诊断，直接对话架构师，给出可落地方案</p>
      <div class="flex flex-col sm:flex-row gap-3 justify-center">
        <a href="tel:19065223505" class="bg-white text-brand-700 font-semibold px-5 py-2.5 rounded-xl hover:bg-brand-50 transition-colors text-sm">📞 立即拨打 19065223505</a>
        <a href="/contact.html" class="bg-brand-800 text-white font-semibold px-5 py-2.5 rounded-xl hover:bg-brand-900 transition-colors text-sm">预约在线咨询 →</a>
      </div>
    </div>
  </div>
</article>
<footer class="bg-slate-900 text-slate-500 py-8">
  <div class="max-w-4xl mx-auto px-4 text-center text-xs">
    © 2026 码视野物联网软件开发团队 · 广东广州 · 电话/微信：19065223505
  </div>
</footer>
<script>
const mdContent = `__CONTENT_MD__`;
mermaid.initialize({startOnLoad:false,theme:'default'});
async function render() {
  const container = document.getElementById('content-body');
  // 提取 mermaid 代码块
  const mermaidBlocks = [];
  const processedMd = mdContent.replace(/```mermaid\n([\s\S]*?)```/g, (_, code) => {
    const id = 'mermaid-' + mermaidBlocks.length;
    mermaidBlocks.push({id, code: code.trim()});
    return `<div class="mermaid-placeholder" data-id="${id}"></div>`;
  });
  container.innerHTML = marked.parse(processedMd);
  // 渲染 mermaid
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
    """将 Markdown 内容转义为 JS 字符串安全格式"""
    content = content.replace('\\', '\\\\')
    content = content.replace('`', '\\`')
    content = content.replace('${', '\\${')
    return content


def build_roi_badges(roi_stats):
    badges = []
    for k, v in roi_stats.items():
        badges.append(f'<div class="text-center"><div class="text-brand-700 font-bold text-lg">{v}</div><div class="text-brand-500 text-xs">{k}</div></div>')
    return '\n      '.join(badges)


def build_post_html(post):
    content_safe = md_to_html_safe(post.get('content_markdown', ''))
    roi_badges = build_roi_badges(post.get('roi_stats', {}))
    cover = post.get('cover_image', 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80')

    html = POST_TEMPLATE
    html = html.replace('__TITLE__', post.get('title', ''))
    html = html.replace('__SUMMARY__', post.get('summary', ''))
    html = html.replace('__COVER_IMAGE__', cover)
    html = html.replace('__CANONICAL__', f"https://iot.codevision.cn/posts/post_{post['id']}.html")
    html = html.replace('__DATE__', post.get('date', ''))
    html = html.replace('__READ_TIME__', post.get('read_time', ''))
    html = html.replace('__CATEGORY__', post.get('category', ''))
    html = html.replace('__TAG__', post.get('tag', ''))
    html = html.replace('__ROI_BADGES__', roi_badges)
    html = html.replace('__CONTENT_MD__', content_safe)
    html = html.replace('__NAV__', NAV_HTML)
    return html


def update_blog_index(posts):
    """更新 blog.html 不需要做什么（JS 动态加载），只需确保 posts_index.json 是最新的"""
    print(f"[BlogIndex] posts_index.json 已包含 {len(posts)} 篇文章")


def main():
    posts_index_path = BASE_DIR / 'posts_index.json'
    if not posts_index_path.exists():
        print("posts_index.json 不存在！")
        return

    with open(posts_index_path, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    built = 0
    for post in posts:
        out_path = POSTS_DIR / f"post_{post['id']}.html"
        html = build_post_html(post)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        built += 1
        print(f"[Build] {out_path.name} OK")

    update_blog_index(posts)
    print(f"\n[Done] 共编译 {built} 个博文静态页到 posts/ 目录")


if __name__ == '__main__':
    main()
