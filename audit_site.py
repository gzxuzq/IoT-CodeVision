#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
码视野官网 - 全站系统性健康体检与性能/体验/SEO扫描器
"""
import os
import re
import json
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path('e:/person/corp/auto-run/iot-showcase')
HTML_FILES = list(BASE_DIR.glob('*.html')) + list(BASE_DIR.glob('posts/*.html')) + list(BASE_DIR.glob('solutions/*.html'))

report = {
    'total_pages': len(HTML_FILES),
    'errors': [],
    'warnings': [],
    'suggestions': []
}

print(f"=== 开始全站体检（共 {len(HTML_FILES)} 个 HTML 页面）===")

for h in HTML_FILES:
    text = h.read_text(encoding='utf-8', errors='replace')
    rel = str(h.relative_to(BASE_DIR))

    # 1. 敏感词/占位符检查
    if '🔗' in text:
        report['warnings'].append(f"[{rel}] 页面仍残留 🔗 图标")
    if '一个人' in text or '个人开发者' in text:
        report['warnings'].append(f"[{rel}] 页面出现个人化表述")

    # 2. SEO & 页面头部标签检查
    if '<title>' not in text:
        report['errors'].append(f"[{rel}] 缺少 <title> 标签")
    if 'name="description"' not in text:
        report['warnings'].append(f"[{rel}] 缺少 meta description 描述")
    if 'rel="icon"' not in text and 'rel="shortcut icon"' not in text:
        report['warnings'].append(f"[{rel}] 缺少 favicon 声明")

    # 3. 内部超链接检查
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', text)
    for href in hrefs:
        if href.startswith(('http://', 'https://', 'tel:', 'mailto:', '#', 'javascript:', 'data:')):
            continue
        clean_href = href.split('#')[0].split('?')[0]
        if not clean_href:
            continue
        if clean_href.startswith('/'):
            target = BASE_DIR / clean_href.lstrip('/')
        else:
            target = (h.parent / clean_href).resolve()
        if not target.exists() and not (target.is_dir() and (target / 'index.html').exists()):
            report['errors'].append(f"[{rel}] 死链: {href} (目标文件不存在: {target.name})")

    # 4. 本地静态资源检查
    srcs = re.findall(r'src=["\']([^"\']+)["\']', text)
    for src in srcs:
        if src.startswith(('http://', 'https://', 'data:')):
            continue
        clean_src = src.split('?')[0]
        if clean_src.startswith('/'):
            target = BASE_DIR / clean_src.lstrip('/')
        else:
            target = (h.parent / clean_src).resolve()
        if not target.exists():
            report['errors'].append(f"[{rel}] 资源引用 404: {src}")

    # 5. 用户体验 (UX) 建议
    if '19065223505' not in text:
        report['suggestions'].append(f"[{rel}] 缺少客服电话或联系方式曝光")

# 检查 JSON 数据完整性
for jname in ['site_config.json', 'cases_index.json', 'posts_index.json', 'solutions_index.json']:
    jpath = BASE_DIR / jname
    if not jpath.exists():
        report['errors'].append(f"核心配置文件缺失: {jname}")
    else:
        try:
            data = json.load(open(jpath, encoding='utf-8'))
            if isinstance(data, list) and len(data) == 0:
                report['warnings'].append(f"数据文件为空: {jname}")
        except Exception as e:
            report['errors'].append(f"JSON 语法错误 {jname}: {e}")

print(f"\n体检扫描完成:")
print(f"❌ 严重错误 (404/死链): {len(report['errors'])} 项")
print(f"⚠️ 警告建议: {len(report['warnings'])} 项")
print(f"💡 优化建议: {len(report['suggestions'])} 项")

if report['errors']:
    print("\n[严重错误详情]")
    for e in report['errors']:
        print("  -", e)

if report['warnings']:
    print("\n[警告建议详情]")
    for w in report['warnings']:
        print("  -", w)

out_file = BASE_DIR / 'audit_report.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f"\n完整审计报告已保存至 {out_file.name}")
