#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 sitemap.xml。

线上 Vercel 未开启 cleanUrls：/blog、/solutions、/contact 返回 404，
对应的 .html 地址返回 200。canonical 与 sitemap 因此保留 .html。
"""
import json
import re
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

BASE_DIR = Path(__file__).parent
ORIGIN = 'https://iot-showcase.hei-ai.com'
DAY = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def day_of(value, fallback):
    raw = (value or '').strip().split(' ')[0]
    return raw if DAY.fullmatch(raw) else fallback


def add(urls, loc, priority, lastmod, changefreq):
    urls.append((loc, priority, lastmod, changefreq))


def main():
    today = datetime.now().strftime('%Y-%m-%d')
    urls = []
    add(urls, f'{ORIGIN}/', '1.0', today, 'daily')
    add(urls, f'{ORIGIN}/solutions.html', '0.9', today, 'daily')
    add(urls, f'{ORIGIN}/blog.html', '0.8', today, 'daily')
    add(urls, f'{ORIGIN}/contact.html', '0.8', today, 'monthly')

    posts_file = BASE_DIR / 'posts_index.json'
    if posts_file.exists():
        for post in json.load(open(posts_file, encoding='utf-8')):
            pid = post['id'] if str(post['id']).startswith('post_') else f"post_{post['id']}"
            path = BASE_DIR / 'posts' / f'{pid}.html'
            if not path.exists():
                continue
            add(
                urls,
                f'{ORIGIN}/posts/{pid}.html',
                '0.7',
                day_of(post.get('date'), today),
                'weekly',
            )

    sols_file = BASE_DIR / 'solutions_index.json'
    if sols_file.exists():
        for sol in json.load(open(sols_file, encoding='utf-8')):
            sid = sol['id'] if str(sol['id']).startswith('sol_') else f"sol_{sol['id']}"
            path = BASE_DIR / 'solutions' / f'{sid}.html'
            if not path.exists():
                continue
            add(
                urls,
                f'{ORIGIN}/solutions/{sid}.html',
                '0.85',
                day_of(sol.get('date'), today),
                'weekly',
            )

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    seen = set()
    for loc, priority, lastmod, changefreq in urls:
        if loc in seen:
            continue
        seen.add(loc)
        lines.append(
            '  <url>\n'
            f'    <loc>{escape(loc)}</loc>\n'
            f'    <lastmod>{escape(lastmod)}</lastmod>\n'
            f'    <changefreq>{changefreq}</changefreq>\n'
            f'    <priority>{priority}</priority>\n'
            '  </url>'
        )
    lines.append('</urlset>\n')
    (BASE_DIR / 'sitemap.xml').write_text('\n'.join(lines), encoding='utf-8')
    print(f'[SEO] sitemap.xml 已生成，收录 {len(seen)} 个可访问 URL（保留 .html，cleanUrls 未开启）')


if __name__ == '__main__':
    main()
