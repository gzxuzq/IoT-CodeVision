#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成符合 Google / 百度搜索引擎规范的 sitemap.xml
"""
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
today = datetime.now().strftime('%Y-%m-%d')

urls = [
    ('https://iot-showcase.vercel.app/', '1.0', today),
    ('https://iot-showcase.vercel.app/solutions.html', '0.9', today),
    ('https://iot-showcase.vercel.app/blog.html', '0.8', today),
    ('https://iot-showcase.vercel.app/contact.html', '0.8', today),
]

# 索引博文
posts_file = BASE_DIR / 'posts_index.json'
if posts_file.exists():
    for p in json.load(open(posts_file, encoding='utf-8')):
        pid = p['id']
        date_str = p.get('date', today).split(' ')[0]
        urls.append((f"https://iot-showcase.vercel.app/posts/post_{pid}.html", '0.7', date_str))

# 索引解决方案
sols_file = BASE_DIR / 'solutions_index.json'
if sols_file.exists():
    for s in json.load(open(sols_file, encoding='utf-8')):
        sid = s['id'] if s['id'].startswith('sol_') else f"sol_{s['id']}"
        date_str = s.get('date', today).split(' ')[0]
        urls.append((f"https://iot-showcase.vercel.app/solutions/{sid}.html", '0.85', date_str))

xml_lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
]
for loc, priority, lastmod in urls:
    xml_lines.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>{priority}</priority>\n  </url>")
xml_lines.append('</urlset>')

(BASE_DIR / 'sitemap.xml').write_text('\n'.join(xml_lines), encoding='utf-8')
print(f"[SEO] sitemap.xml 生成完毕，全站共收录 {len(urls)} 个核心页面！")
