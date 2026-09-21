#!/usr/bin/env python3
"""
码视野 IoT 官网 - Agnes AI 自动博文更新脚本
每小时运行一次，生成 IoT 垂直深度技术博文并编译为静态页
"""
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# 尝试加载 .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / '.env')
except ImportError:
    # 手动加载 .env
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

AGNES_API_KEY = os.getenv('AGNES_API_KEY', '')
AGNES_BASE_URL = os.getenv('AGNES_BASE_URL', 'https://apihub.agnes-ai.com/v1')
AGNES_MODEL = os.getenv('AGNES_MODEL', 'agnes-3.0-flash')

BASE_DIR = Path(__file__).parent
POSTS_DIR = BASE_DIR / 'posts'
POSTS_DIR.mkdir(exist_ok=True)

# ===== IoT 博文选题库（20 篇循环，逐渐扩充）=====
TOPIC_BANK = [
    {"title": "EMQX vs Mosquitto vs HiveMQ：三大 MQTT Broker 企业级选型完全指南", "category": "选型决策指南", "tag": "MQTT Broker", "read_time": "8 分钟", "keywords": ["EMQX", "Mosquitto", "MQTT Broker选型"], "roi_stats": {"对比维度": "8项", "覆盖规模": "百~百万设备"}, "cover_key": "server"},
    {"title": "工业 OPC-UA 协议深度解析：为什么它是工业 4.0 的核心通信标准？", "category": "技术实战解析", "tag": "OPC-UA", "read_time": "10 分钟", "keywords": ["OPC-UA", "工业4.0", "工业物联网"], "roi_stats": {"协议安全性": "端对端加密", "互操作性": "跨厂商兼容"}, "cover_key": "factory"},
    {"title": "LoRa vs NB-IoT vs 4G Cat-M：低功耗广域网选型避坑指南", "category": "选型决策指南", "tag": "LPWAN选型", "read_time": "9 分钟", "keywords": ["LoRa", "NB-IoT", "LPWAN", "物联网选型"], "roi_stats": {"覆盖范围": "15km+", "功耗对比": "电池寿命5年+"}, "cover_key": "antenna"},
    {"title": "智慧农业传感器数据平台：从 LoRa 接入到数字化溯源的全栈实现", "category": "项目经验复盘", "tag": "智慧农业", "read_time": "12 分钟", "keywords": ["智慧农业", "LoRa", "农业IoT"], "roi_stats": {"节水效果": "31%", "人力节省": "60%"}, "cover_key": "agriculture"},
    {"title": "物联网数据安全加固：MQTT TLS 双向认证实战配置全流程", "category": "技术实战解析", "tag": "IoT安全", "read_time": "8 分钟", "keywords": ["MQTT TLS", "物联网安全", "mTLS"], "roi_stats": {"安全等级": "生产级", "认证方式": "X.509双向"}, "cover_key": "security"},
    {"title": "时序数据库选型：InfluxDB vs TimescaleDB，IoT 场景如何决策？", "category": "选型决策指南", "tag": "时序数据库", "read_time": "7 分钟", "keywords": ["InfluxDB", "TimescaleDB", "时序数据库"], "roi_stats": {"写入性能": "百万点/秒", "压缩比": "10:1"}, "cover_key": "database"},
    {"title": "边缘计算 vs 云计算：工业物联网场景下的架构决策框架", "category": "行业深度洞察", "tag": "边缘计算", "read_time": "9 分钟", "keywords": ["边缘计算", "云计算", "工业物联网架构"], "roi_stats": {"延迟降低": "80%", "带宽节省": "70%"}, "cover_key": "cloud"},
    {"title": "ThingsBoard 二次开发实战：定制化工业监控大屏完整方案", "category": "技术实战解析", "tag": "ThingsBoard", "read_time": "11 分钟", "keywords": ["ThingsBoard", "物联网平台", "二次开发"], "roi_stats": {"开发提速": "3倍", "功能覆盖": "85%开箱即用"}, "cover_key": "dashboard"},
    {"title": "智能楼宇 BACnet 协议接入：从协议解析到能耗管理平台全栈实现", "category": "项目经验复盘", "tag": "BACnet", "read_time": "10 分钟", "keywords": ["BACnet", "楼宇自控", "能耗管理"], "roi_stats": {"节能效果": "18%", "接入点位": "1260个"}, "cover_key": "building"},
    {"title": "Node-RED 可视化编程入门：5 小时搭建 IoT 数据处理流水线", "category": "技术实战解析", "tag": "Node-RED", "read_time": "8 分钟", "keywords": ["Node-RED", "IoT数据处理", "可视化编程"], "roi_stats": {"开发效率": "提升5倍", "代码量": "减少70%"}, "cover_key": "code"},
    {"title": "Modbus RTU 帧格式深度解析：工业设备接入必须掌握的协议细节", "category": "技术实战解析", "tag": "Modbus", "read_time": "9 分钟", "keywords": ["Modbus RTU", "工业协议", "设备接入"], "roi_stats": {"协议兼容性": "99%工业设备", "接入成本": "零硬件改造"}, "cover_key": "industrial"},
    {"title": "IoT 设备管理平台设计：设备注册、影子、OTA 升级三位一体架构", "category": "技术实战解析", "tag": "设备管理", "read_time": "12 分钟", "keywords": ["IoT设备管理", "设备影子", "OTA升级"], "roi_stats": {"管理设备": "万级并发", "故障定位": "分钟级"}, "cover_key": "management"},
    {"title": "Grafana + InfluxDB 搭建工业设备实时监控大屏完整教程", "category": "技术实战解析", "tag": "Grafana", "read_time": "10 分钟", "keywords": ["Grafana", "InfluxDB", "监控大屏"], "roi_stats": {"部署时间": "< 4小时", "图表类型": "20+"}, "cover_key": "monitoring"},
    {"title": "物联网项目甲方必读：外包开发合同的 8 个关键条款", "category": "行业深度洞察", "tag": "项目管理", "read_time": "7 分钟", "keywords": ["物联网外包", "合同条款", "项目管理"], "roi_stats": {"风险降低": "80%", "纠纷预防": "全覆盖"}, "cover_key": "contract"},
    {"title": "工厂能耗监控系统架构复盘：320 台设备从 0 到 1 的完整实施路径", "category": "项目经验复盘", "tag": "工业监控", "read_time": "14 分钟", "keywords": ["工厂能耗监控", "工业IoT", "设备监控"], "roi_stats": {"OEE提升": "18%", "故障响应": "缩短93%"}, "cover_key": "factory"},
    {"title": "Python asyncio + MQTT：高并发物联网数据采集服务的正确姿势", "category": "技术实战解析", "tag": "Python异步", "read_time": "10 分钟", "keywords": ["Python asyncio", "MQTT", "高并发IoT"], "roi_stats": {"并发能力": "10万连接", "CPU占用": "降低60%"}, "cover_key": "python"},
    {"title": "冷链物流温湿度监控系统：IoT + LoRa + 4G 全链路方案设计", "category": "行业深度洞察", "tag": "冷链监控", "read_time": "9 分钟", "keywords": ["冷链监控", "温湿度IoT", "物流物联网"], "roi_stats": {"货损率": "降低45%", "合规性": "FDA21 CFR兼容"}, "cover_key": "coldchain"},
    {"title": "MQTT 消息去重与幂等处理：保证 IoT 数据精确一次投递的工程实践", "category": "技术实战解析", "tag": "消息可靠性", "read_time": "8 分钟", "keywords": ["MQTT幂等", "消息去重", "IoT数据质量"], "roi_stats": {"数据准确率": "99.99%", "重复率": "< 0.001%"}, "cover_key": "reliability"},
    {"title": "2026 年中国工业物联网市场深度报告：机会在哪里，陷阱在哪里？", "category": "行业深度洞察", "tag": "行业趋势", "read_time": "11 分钟", "keywords": ["工业物联网", "IIoT市场", "物联网趋势"], "roi_stats": {"市场规模": "万亿级", "增速": "年均23%"}, "cover_key": "market"},
    {"title": "从 Arduino 到云端：硬件创业公司如何以最低成本快速上云？", "category": "行业深度洞察", "tag": "硬件创业", "read_time": "9 分钟", "keywords": ["Arduino", "硬件上云", "IoT创业"], "roi_stats": {"上云成本": "< 2万", "开发周期": "2周MVP"}, "cover_key": "hardware"},
]

# 封面图映射
COVER_IMAGE_MAP = {
    "server": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80",
    "factory": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&q=80",
    "antenna": "https://images.unsplash.com/photo-1516546453174-5e1098a4b4af?w=800&q=80",
    "agriculture": "https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=800&q=80",
    "security": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&q=80",
    "database": "https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=800&q=80",
    "cloud": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80",
    "dashboard": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80",
    "building": "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=800&q=80",
    "code": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80",
    "industrial": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&q=80",
    "management": "https://images.unsplash.com/photo-1573804633927-bfcbcd909acd?w=800&q=80",
    "monitoring": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80",
    "contract": "https://images.unsplash.com/photo-1554774853-aae0a22c8aa4?w=800&q=80",
    "python": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&q=80",
    "coldchain": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&q=80",
    "reliability": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80",
    "market": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80",
    "hardware": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80",
}

SYSTEM_PROMPT = """你是码视野物联网软件开发团队的技术博客作者，资深物联网架构师，有 6 年 IoT 项目交付经验。
请为给定选题撰写一篇高质量的物联网技术博文，要求：

1. 文章结构：标题（H1）→ 背景与痛点分析（H2）→ 核心技术方案（H2，含 Mermaid 架构图）→ 关键实现细节（H2，含代码片段）→ 量化对比表格（ROI维度对比）→ 实战建议与联系方式（H2）
2. 技术细节真实，不要空泛描述，要有具体的参数、配置、代码
3. 必须包含一个 Mermaid 流程图或时序图（使用 ```mermaid ... ``` 代码块）
4. 必须包含一个 Markdown 表格做量化对比
5. 结尾自然地提到码视野团队，电话/微信 19065223505，提供免费技术诊断
6. 字数 1500-2500 字，中文撰写
7. 只输出 Markdown 正文，不要输出 JSON 或其他格式"""


def pick_next_topic(posts):
    """选取下一个未发布的选题"""
    published_titles = {p['title'] for p in posts}
    for topic in TOPIC_BANK:
        if topic['title'] not in published_titles:
            return topic
    # 全部发完后，修改第一个选题复用
    import random
    return random.choice(TOPIC_BANK)


def generate_article_llm(topic):
    """调用 Agnes AI 生成文章内容"""
    if not AGNES_API_KEY:
        print("[LLM] 未配置 AGNES_API_KEY，使用本地模板")
        return generate_article_template(topic)

    prompt = f"选题：{topic['title']}\n分类：{topic['category']}\n目标关键词：{', '.join(topic['keywords'])}"
    payload = json.dumps({
        "model": AGNES_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 3000,
        "temperature": 0.7
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{AGNES_BASE_URL}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AGNES_API_KEY}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            choices = data.get('choices', [])
            if choices:
                msg = choices[0].get('message', {})
                content = msg.get('content') or msg.get('reasoning_content', '')
                if content and len(content) > 200:
                    print(f"[LLM] Agnes AI 生成成功，{len(content)} 字符")
                    return content
    except Exception as e:
        print(f"[LLM] Agnes AI 调用失败: {e}，回退本地模板")

    return generate_article_template(topic)


def generate_article_template(topic):
    """本地模板生成文章（回退方案）"""
    title = topic['title']
    cat = topic['category']
    keywords = topic['keywords']

    return f"""# {title}

## 一、行业背景与核心痛点

在物联网行业快速发展的今天，{keywords[0]} 已经成为企业数字化转型的关键技术节点。然而，许多企业在实施过程中面临以下核心挑战：

- **技术选型困难**：市场上同类解决方案众多，缺乏系统性的对比框架
- **工程实施复杂**：从理论到落地往往存在大量工程细节
- **运维成本高昂**：缺乏专业团队，系统上线后维护困难

码视野团队在 6 年 38+ 物联网项目的实战中，积累了大量这方面的经验，本文将系统梳理核心解决思路。

## 二、核心技术方案

针对上述痛点，我们推荐以下经过实战验证的架构方案：

```mermaid
flowchart TD
    A["设备层（传感器/PLC/控制器）"] -->|"标准协议接入"| B["协议适配层（网关/驱动）"]
    B -->|"MQTT/HTTP"| C["消息中间件（EMQX/Kafka）"]
    C --> D["数据处理服务（Python/Go）"]
    D --> E["时序数据库（InfluxDB）"]
    E --> F["可视化层（Grafana/自研大屏）"]
    D --> G["告警引擎"]
    G --> H["通知渠道（钉钉/短信/微信）"]
```

该架构具备以下核心优势：
1. **水平扩展能力**：消息中间件集群可线性扩展，支持百万设备并发
2. **协议解耦**：设备层与业务层通过 MQTT 主题完全解耦，易于扩展新设备类型
3. **高可用设计**：每一层均可独立进行故障切换和负载均衡

## 三、关键技术实现

### 3.1 设备接入配置示例

```python
import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        # 订阅所有设备的遥测数据
        client.subscribe("devices/+/telemetry", qos=1)
        print("连接成功，开始监听设备数据")

def on_message(client, userdata, msg):
    device_id = msg.topic.split("/")[1]
    payload = json.loads(msg.payload.decode())
    # 处理设备上报数据
    process_telemetry(device_id, payload)

client = mqtt.Client(client_id="data-collector-001")
client.username_pw_set("iot_user", "secure_password")
client.tls_set()  # 启用 TLS 加密
client.on_connect = on_connect
client.on_message = on_message
client.connect("your-emqx-broker.com", 8883)
client.loop_forever()
```

## 四、量化效果对比

| 评估维度 | 传统方案 | 码视野方案 | 改善幅度 |
| :--- | :--- | :--- | :--- |
| **设备接入效率** | 每台设备需单独适配 | 协议适配层统一处理 | 效率提升 5 倍 |
| **数据延迟** | 分钟级轮询 | 实时推送，< 100ms | 延迟降低 99% |
| **运维复杂度** | 多个系统独立运维 | 统一平台，一键运维 | 工作量减少 70% |
| **可扩展性** | 扩容需停机改造 | 在线动态扩容 | 零停机扩展 |
| **开发成本** | 协议适配约 3 个月 | 标准接入约 1~2 周 | 成本降低 80% |

## 五、落地建议

对于准备实施的团队，我们建议按以下步骤推进：

1. **第一阶段（1~2 周）**：先接入 1~3 种最主要的设备类型，验证数据流通路
2. **第二阶段（2~4 周）**：完善数据处理逻辑，搭建基础监控看板
3. **第三阶段（持续迭代）**：逐步接入更多设备，完善告警规则和报表

如果您正在为 {keywords[0]} 的落地实施感到困惑，欢迎联系码视野技术团队获取**免费 30 分钟技术诊断**。

📞 **电话/微信：19065223505**（备注"{cat}"）
"""


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 码视野 IoT 博文自动更新开始...")

    # 读取现有文章
    posts_index_path = BASE_DIR / 'posts_index.json'
    if posts_index_path.exists():
        with open(posts_index_path, 'r', encoding='utf-8') as f:
            posts = json.load(f)
    else:
        posts = []

    # 选题
    topic = pick_next_topic(posts)
    print(f"[选题] {topic['title']}")

    # 生成内容
    content = generate_article_llm(topic)

    # 构造文章数据
    now = datetime.now()
    article_id = now.strftime('%Y%m%d%H%M%S')
    cover_image = COVER_IMAGE_MAP.get(topic.get('cover_key', 'server'), COVER_IMAGE_MAP['server'])

    article = {
        "id": article_id,
        "title": topic['title'],
        "category": topic['category'],
        "tag": topic['tag'],
        "read_time": topic['read_time'],
        "date": now.strftime('%Y-%m-%d %H:%M'),
        "summary": topic.get('summary', topic['title'][:80] + '…'),
        "cover_image": cover_image,
        "roi_stats": topic['roi_stats'],
        "keywords": topic['keywords'],
        "content_markdown": content
    }

    # 更新 posts_index.json（新文章置顶）
    posts.insert(0, article)
    with open(posts_index_path, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"[Index] posts_index.json 已更新，共 {len(posts)} 篇")

    # 编译静态页
    result = subprocess.run(
        [sys.executable, str(BASE_DIR / 'build_static_posts.py')],
        capture_output=True, text=True, cwd=str(BASE_DIR)
    )
    if result.returncode == 0:
        print(f"[Build] 静态页编译成功")
    else:
        print(f"[Build] 编译警告: {result.stderr[:200]}")

    # Git 推送
    try:
        import subprocess as sp
        sp.run(['git', 'add', '.'], cwd=str(BASE_DIR), check=True, capture_output=True)
        commit_msg = f"[auto] 新博文: {topic['title'][:40]} ({now.strftime('%m-%d %H:%M')})"
        sp.run(['git', 'commit', '-m', commit_msg], cwd=str(BASE_DIR), check=True, capture_output=True)
        sp.run(['git', 'push', 'origin', 'main'], cwd=str(BASE_DIR), check=True, capture_output=True)
        print(f"[Git] 已推送到 GitHub")
    except Exception as e:
        print(f"[Git] 推送跳过（仓库未初始化或网络问题）: {e}")

    print(f"✅ 更新完成！文章：{topic['title']}")


if __name__ == '__main__':
    main()
