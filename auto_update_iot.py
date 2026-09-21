#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
码视野 IoT 官网 - 自动化自造血更新引擎 (Pro Max)
核心功能与排期频率：
1. 【行业解决方案】：一天 1 篇（每 24 小时自动更新 1 篇垂直行业系统解决方案与独立落地页）
2. 【技术深度博文】：一天 6 篇（每 4 小时自动更新 1 篇技术深度博文与独立落地页，一天累计 6 篇）
3. 【落地交付案例】：每 2 天 1 篇（每 48 小时自动更新 1 个真实脱敏交付项目案例）
4. 【手动触发穿透】：GitHub Actions 网页端 workflow_dispatch 手动运行时强制新增并实时构建
5. 全量编译静态页 + 自动 git commit & push 至 GitHub 触发 Vercel 秒级部署上线
"""
import json
import os
import random
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 北京时间时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_now():
    return datetime.now(BEIJING_TZ)

def parse_item_datetime(item, default_dt=None):
    """解析数据项中的日期时间，统一返回带有时区 (BEIJING_TZ) 的 datetime"""
    date_str = item.get('date') or item.get('created_at')
    if date_str:
        for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y/%m/%d %H:%M', '%Y/%m/%d'):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.replace(tzinfo=BEIJING_TZ)
            except ValueError:
                pass
    item_id = str(item.get('id', ''))
    digits = ''.join([c for c in item_id if c.isdigit()])
    if len(digits) >= 12:
        try:
            dt = datetime.strptime(digits[:12], '%Y%m%d%H%M')
            return dt.replace(tzinfo=BEIJING_TZ)
        except ValueError:
            pass
    return default_dt or datetime(2020, 1, 1, tzinfo=BEIJING_TZ)

# 强制禁用控制台编码异常并实时刷新
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
env_path = BASE_DIR / '.env'
if env_path.exists():
    for line in env_path.read_text(encoding='utf-8', errors='replace').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

AGNES_API_KEY = os.getenv('AGNES_API_KEY') or 'sk-SW1i66PiPOCR7gaUqExzJapMsfF0Cl3qEKuWCATG3uYFcqQH'
AGNES_BASE_URL = os.getenv('AGNES_BASE_URL', 'https://apihub.agnes-ai.com/v1')
AGNES_MODEL = os.getenv('AGNES_MODEL', 'agnes-2.5-flash')

POSTS_INDEX_FILE = BASE_DIR / 'posts_index.json'
SOLUTIONS_INDEX_FILE = BASE_DIR / 'solutions_index.json'
CASES_INDEX_FILE = BASE_DIR / 'cases_index.json'

# ==========================================
# 1. 行业解决方案丰富选题库 (支持按小时轮转)
# ==========================================
SOLUTION_TOPICS = [
    {
        "title": "智慧光伏与工商业储能微电网 EMS 能量管理系统解决方案",
        "industry": "新能源与储能",
        "industry_tag": "光储充一体化",
        "deploy_cycle": "15~25 天快速上线",
        "cover_image": "https://images.unsplash.com/photo-1497435334941-8c899ee9e8e9?w=800&q=80",
        "protocols": ["Modbus TCP", "IEC 61850", "MQTT over TLS", "CANopen"],
        "keywords": ["微电网EMS", "工商业储能", "削峰填谷", "光伏并网"]
    },
    {
        "title": "现代中药与高端果品恒温恒湿冷链仓储群 IoT 监测与断链预警方案",
        "industry": "冷链与医药",
        "industry_tag": "温湿度全流程溯源",
        "deploy_cycle": "10~15 天极速落地",
        "cover_image": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&q=80",
        "protocols": ["LoRaWAN", "Modbus RTU", "MQTT", "HTTP REST"],
        "keywords": ["医药冷链", "温湿度断链预警", "GSP认证", "冷库群能耗优化"]
    },
    {
        "title": "半导体与生物制药洁净室微压差恒定与尘埃粒子在线智能微控方案",
        "industry": "高精洁净制造",
        "industry_tag": "微压差精密闭环",
        "deploy_cycle": "20~30 天交付",
        "cover_image": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&q=80",
        "protocols": ["BACnet IP", "Modbus RTU", "OPC-UA", "MQTT"],
        "keywords": ["洁净车间", "微压差变频调节", "尘埃粒子计数", "洁净室自控"]
    },
    {
        "title": "化工园区综合管廊有毒可燃气体泄漏毫秒级遥测与应急联动切断方案",
        "industry": "化工与危化安全",
        "industry_tag": "防爆本质安全",
        "deploy_cycle": "18~28 天交付",
        "cover_image": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&q=80",
        "protocols": ["HART", "Modbus RTU防爆", "LoRaWAN防爆", "MQTT"],
        "keywords": ["化工园区安全", "有毒气体监测", "防爆网关", "应急切断联动"]
    },
    {
        "title": "大型现代化生猪与蛋禽养殖场全自动环控与精准饲喂物联网方案",
        "industry": "现代智慧养殖",
        "industry_tag": "环境自适应调控",
        "deploy_cycle": "12~20 天交付",
        "cover_image": "https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=800&q=80",
        "protocols": ["Modbus RTU", "CAN 2.0", "4G Cat.1", "MQTT"],
        "keywords": ["智慧猪场", "鸡舍环控", "氨气负压监控", "精准饲喂称重"]
    },
    {
        "title": "城市供水管网管压水平衡分析与隐蔽漏损声震智能辨识方案",
        "industry": "智慧市政水务",
        "industry_tag": "漏损声波高频遥测",
        "deploy_cycle": "25~35 天交付",
        "cover_image": "https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=800&q=80",
        "protocols": ["NB-IoT", "Modbus TCP", "MQTT", "CoAP"],
        "keywords": ["管网漏损", "水锤防护", "二次供水监控", "智慧水务水质"]
    },
    {
        "title": "现代化港口与大型电商立体仓无人 AGV 车队高并发通信与调度方案",
        "industry": "智慧港口与物流",
        "industry_tag": "车路协同低延时",
        "deploy_cycle": "30~45 天交付",
        "cover_image": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=800&q=80",
        "protocols": ["5G专网", "MQTT 5.0", "WebSocket", "gRPC"],
        "keywords": ["AGV调度系统", "毫秒级避障", "港口自动化", "高并发长连接"]
    },
    {
        "title": "高层商业综合体中央空调冷水机组智能变频群控与碳足迹核查方案",
        "industry": "智能建筑与碳排",
        "industry_tag": "暖通AI自适应节能",
        "deploy_cycle": "20~30 天交付",
        "cover_image": "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=800&q=80",
        "protocols": ["BACnet/IP", "Modbus TCP", "MQTT", "SNMP"],
        "keywords": ["中央空调冷水机组", "智能变频节能", "分项计量", "国家双碳核查"]
    }
]

# ==========================================
# 2. 真实落地交付案例备选库 (每 2 天自动新增)
# ==========================================
CASE_CANDIDATES = [
    {
        "title": "华东某特种金属精密压铸厂 · 40 台数控冲压设备状态监测与模具寿命预测系统",
        "industry": "industrial",
        "industry_label": "工业制造",
        "client_desc": "华东某高精密压铸上市公司核心制造基地",
        "cover_image": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=800&q=80",
        "duration_days": 42,
        "devices_count": 160,
        "core_protocols": ["Modbus TCP", "OPC-UA", "MQTT"],
        "tech_stack": ["Python", "EMQX", "TimescaleDB", "Vue3", "ECharts"],
        "pain_points": [
            "高温高压环境下模具隐性磨损不可见，突发崩模造成整线报废损失逾百万元",
            "现场各品牌压铸机 PLC 接口老旧封闭，无法统一采集合模力与行程时序",
            "传统人工点检流于形式，无法实现设备预测性维护"
        ],
        "solution_summary": "布设微型外贴式应变与振动高频传感器，通过 Modbus TCP 与 OPC-UA 采集网关汇入 EMQX，结合 Python 边缘异常波形聚类算法实时比对模具磨损特征，突发异常 100ms 紧急切断下发。",
        "architecture_mermaid": "flowchart TD\n    A[\"冲压机合模力/振动探头\"] -->|\"高频采样 1kHz\"| B[\"边缘振动采集卡\"]\n    B -->|\"Modbus TCP\"| C[\"工业网关 (Linux)\"]\n    C -->|\"特征值提取\"| D[\"EMQX 消息总线\"]\n    D --> E[\"Python 模具寿命推演模型\"]\n    E --> F[\"大屏 3D 设备台账看板\"]\n    E --> G[\"PLC 停机联锁信号下发\"]",
        "delivery_highlights": [
            {"metric": "崩模停产事故", "before": "年均 4~6 起", "after": "上线后 0 起", "improvement": "避免直接损失 240万+"},
            {"metric": "模具综合寿命", "before": "固定 5 万次强制更换", "after": "动态评测至 7.2 万次", "improvement": "模具利用率提升 44%"},
            {"metric": "工单处理时效", "before": "停机后报修（2小时）", "after": "临界阈值自动派单", "improvement": "响应时效提升 80%"}
        ],
        "client_quote": "码视野技术团队在重工业现场非常有经验，短短 40 多天不仅打通了我们所有不同年份的老机床，更通过算法帮我们彻底根绝了昂贵的模具非计划损坏！"
    },
    {
        "title": "西南某大型生态蓝莓基地 · 2000 亩水肥一体化脉冲滴灌与气象微站物联网平台",
        "industry": "agriculture",
        "industry_label": "智慧农业",
        "client_desc": "西南高端精品浆果种植示范基地",
        "cover_image": "https://images.unsplash.com/photo-1592417817098-8f3d6ef23984?w=800&q=80",
        "duration_days": 35,
        "devices_count": 520,
        "core_protocols": ["LoRaWAN", "Modbus RTU", "MQTT"],
        "tech_stack": ["Python", "EMQX", "InfluxDB", "Vue3", "微信小程序"],
        "pain_points": [
            "山地起伏大，无线信号遮挡严重，传统 4G 方案电池两月即耗尽",
            "蓝莓根系浅对土壤 EC 值及酸碱度极其敏感，传统人工施肥配比不匀造成大面积减产",
            "水泵阀门靠工人骑摩托车手动开关，费时费力且极易忘关引发水肥冲刷烂根"
        ],
        "solution_summary": "搭建基于 LoRaWAN 的超远距离低功耗无线网状传感器阵列，覆盖土壤氮磷钾、EC、pH 及微气候；云端依据蓝莓物候生长曲线，自动开闭电磁阀与水肥脉冲泵组。",
        "architecture_mermaid": "flowchart LR\n    A[\"深浅层土壤温湿度/EC/pH探头\"] -->|\"LoRa 无线 868MHz\"| B[\"山顶太阳能 LoRa 基站\"]\n    B -->|\"4G 加密回传\"| C[\"码视野智慧农业云平台\"]\n    C --> D[\"水肥配方与滴灌控制算法\"]\n    D -->|\"控制反控指令\"| E[\"水肥机控制器 (Modbus)\"]\n    E --> F[\"分区脉冲电磁阀组\"]\n    C --> G[\"农场主微信小程序监控\"]",
        "delivery_highlights": [
            {"metric": "肥料利用率", "before": "人工漫灌（浪费严重）", "after": "按需精准滴灌", "improvement": "化肥用量减少 38%"},
            {"metric": "优质果品产出比", "before": "优果率 62%", "after": "提升至 88%", "improvement": "果园产值提升 35%"},
            {"metric": "单人管护面积", "before": "20 亩 / 人", "after": "提升至 120 亩 / 人", "improvement": "人效提升 6 倍"}
        ],
        "client_quote": "以前工人每天跑断腿去开阀门还经常浇不透，现在躺在家里看手机小程序，土壤干了系统自动精准滴灌，果子颗粒饱满，收购商抢着要！"
    },
    {
        "title": "华南某医药集团 8 栋自动化立体高位立体库温湿度巡测与消防风阀联动系统",
        "industry": "building",
        "industry_label": "智能楼宇",
        "client_desc": "华南大型中药与生物制品流通企业",
        "cover_image": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=800&q=80",
        "duration_days": 48,
        "devices_count": 960,
        "core_protocols": ["BACnet/IP", "Modbus TCP", "MQTT"],
        "tech_stack": ["Go", "EMQX", "InfluxDB", "Vue3", "Docker"],
        "pain_points": [
            "24米高位货架垂直温差大，顶层局部积温导致药材变质隐患",
            "传统消防防排烟系统与日常新风系统物理隔离，火警响应延迟",
            "GSP 认证飞行检查需要随时调取分钟级不可篡改的历史台账"
        ],
        "solution_summary": "在货架立柱每隔 4 米布置无线高精度探头，建立立体温度场插值模型；边缘网关通过 BACnet/IP 深度接驳冷机变频器与风阀执行器，实现超差 0.5℃ 毫秒级闭环调节。",
        "architecture_mermaid": "flowchart TD\n    A[\"高位货架立体温湿度探头群\"] -->|\"Modbus\"| B[\"库区网关\"]\n    B -->|\"BACnet/IP\"| C[\"风机/排烟阀执行器\"]\n    B -->|\"MQTT TLS\"| D[\"码视野医药冷链监控中台\"]\n    D --> E[\"GSP 不可篡改时序数据存证\"]\n    D --> F[\"3D 库位热力数字孪生大屏\"]",
        "delivery_highlights": [
            {"metric": "立体库垂直温差", "before": "温差达 4.5℃", "after": "平抑至 < 0.8℃", "improvement": "彻底根除高温盲区"},
            {"metric": "GSP合规报表生成", "before": "人工整理需 3 天", "after": "一键实时导出", "improvement": "审计合规 100% 达标"},
            {"metric": "制冷用电单耗", "before": "全功率常开", "after": "按温差动态变频", "improvement": "每月节约电费 3.8 万元"}
        ],
        "client_quote": "码视野团队打造的立体热力图不仅直观，而且自动调控非常平稳，顺利通过了国家药监局最严格的现场飞行检查！"
    }
]

# ==========================================
# 3. 健壮的 Agnes AI 大模型调用封装
# ==========================================
def call_agnes_llm(system_prompt, user_prompt, max_tokens=3000, timeout_sec=90):
    if not AGNES_API_KEY:
        print("[LLM] 未配置 AGNES_API_KEY，回退本地工程模版", flush=True)
        return None

    payload = json.dumps({
        "model": AGNES_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{AGNES_BASE_URL.rstrip('/')}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AGNES_API_KEY}",
            "User-Agent": "CodeVision-Updater/2.0"
        },
        method="POST"
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            choices = data.get('choices', [])
            if choices:
                msg = choices[0].get('message', {})
                content = msg.get('content') or msg.get('reasoning_content', '')
                if content and len(content) > 300:
                    print(f"[LLM] Agnes AI 成功深度响应 ({time.time()-t0:.1f}s, {len(content)} 字符)", flush=True)
                    return content
                else:
                    print(f"[LLM] Agnes AI 响应内容较短 ({len(content) if content else 0} 字符)，准备安全回退", flush=True)
    except Exception as e:
        print(f"[LLM] Agnes AI 调用未完成 ({e})，准备安全回退", flush=True)
    return None


# ==========================================
# 4. 自动更新行业解决方案 (一天 1 篇 / 24 小时周期)
# ==========================================
def update_solutions_daily(force=False):
    print("\n--- [任务 1] 检查更新垂直行业解决方案 (一天 1 篇周期) ---", flush=True)
    if not SOLUTIONS_INDEX_FILE.exists():
        solutions = []
    else:
        with open(SOLUTIONS_INDEX_FILE, 'r', encoding='utf-8') as f:
            solutions = json.load(f)

    is_manual = force or os.getenv('GITHUB_EVENT_NAME') == 'workflow_dispatch' or os.getenv('FORCE_UPDATE') == 'true'
    need_update = False
    if is_manual:
        need_update = True
        print("[Solutions] ⚡ 检测到手动触发指令 (workflow_dispatch)，无视周期限制，强制新增行业解决方案！", flush=True)
    elif not solutions:
        need_update = True
    else:
        latest_dt = parse_item_datetime(solutions[0])
        diff_hours = (get_beijing_now() - latest_dt).total_seconds() / 3600
        # 一天 1 篇，周期限制为 24 小时
        if diff_hours >= 24:
            need_update = True
            print(f"[Solutions] 上次方案更新于 {solutions[0].get('date', '')} (距今 {diff_hours:.1f}h >= 24h)，满足一天一篇周期，触发更新！", flush=True)
        else:
            print(f"[Solutions] 上次方案更新于 {solutions[0].get('date', '')} (距今 {diff_hours:.1f}h < 24h)，未满一天周期（1天/篇），保持现状。", flush=True)

    if not need_update:
        return

    existing_titles = {s['title'] for s in solutions}
    target_topic = None
    for t in SOLUTION_TOPICS:
        if t['title'] not in existing_titles:
            target_topic = t
            break
    if not target_topic:
        base_t = random.choice(SOLUTION_TOPICS)
        target_topic = dict(base_t)
        target_topic['title'] = f"{base_t['title']} (升级迭代版)"

    now = get_beijing_now()
    sol_id = f"sol_{now.strftime('%Y%m%d%H%M%S')}"

    system_prompt = (
        "你是码视野物联网软件研发团队的资深解决方案总架构师（深耕工业IoT与边缘计算6年）。\n"
        "请为指定垂直行业撰写一份极度详尽、专业、包含硬件选型清单BOM、Mermaid系统拓扑架构图与量化ROI表格的交钥匙解决方案Markdown全文。\n"
        "【严控红线】：严禁出现个人开发者或一个人字样，全篇以'码视野研发团队'对外呈现。\n"
        "文末自然嵌入联系方式：电话/微信 19065223505。"
    )
    user_prompt = f"请为【{target_topic['title']}】撰写完整交钥匙方案，行业：{target_topic['industry']}，协议：{', '.join(target_topic['protocols'])}。"

    print(f"[Solutions] 正在筹备行业方案：《{target_topic['title']}》...", flush=True)
    content = call_agnes_llm(system_prompt, user_prompt, max_tokens=3000, timeout_sec=90)

    if not content:
        # 高保真工程模板回退生成
        content = f"""# {target_topic['title']}

## 一、 行业背景与核心痛点剖析
在{target_topic['industry']}的实际生产运行中，多源设备协议不兼容、通信网络可靠性差以及数据时钟不同步是导致数字化项目搁浅的最核心瓶颈。现场存在大量的异构接口与数据孤岛，企业亟需一套轻量可靠、开箱即用的边缘控制与云端中台解决方案。

## 二、 码视野全流程架构拓扑
码视野研发团队针对该行业打造了**“边缘端高速闭环 + 云端业务统筹”**的双层架构：

```mermaid
flowchart TD
    A["现场物理设备与传感器群"] -->|"标准工业总线 ({target_topic['protocols'][0]})"| B["码视野边缘智能网关 (ARM Linux)"]
    B -->|"MQTT over TLS 加密隧道"| C["云端物联网消息集群 (EMQX)"]
    C --> D["时序数据仓库 (InfluxDB)"]
    C --> E["核心业务规则与AI预测引擎"]
    E --> F["数字孪生大屏与移动端推送"]
```

## 三、 硬件物料清单（BOM）与协议选型
系统深度兼容主流协议标准：`{' · '.join(target_topic['protocols'])}`。
- **采集感知层**：工业级传感器（抗电磁干扰，IP67 防护）；
- **边缘网关层**：四核工业级网关，支持断网本地暂存与断点续传；
- **平台服务层**：微服务架构，支持本地私有化一键 Docker 部署。

## 四、 投资回报率（ROI）测算
| 评估维度 | 改造前状况 | 码视野方案落地后 | 效益量化 |
| :--- | :--- | :--- | :--- |
| **设备综合OEE** | 70% ~ 75% 粗放管理 | **88% 以上精准受控** | **综合效率提升 18%** |
| **异常故障响应** | 人工巡检（> 1 小时） | **毫秒级告警下发** | **停机损失减少 80%** |
| **项目上线周期** | 传统需 3~6 个月 | **{target_topic.get('deploy_cycle', '20天内')} 交付 MVP** | **时间成本削减 70%** |

## 五、 咨询与落地合作
码视野技术团队承诺工作日 1 小时内响应需求，免费出具针对贵司场站的可行性评估与架构图。
- **技术总监专线/微信**：`19065223505`
- **咨询邮箱**：`contact@codevision-iot.com`
"""

    new_solution = {
        "id": sol_id,
        "title": target_topic['title'],
        "industry": target_topic['industry'],
        "industry_tag": target_topic['industry_tag'],
        "summary": f"面向{target_topic['industry']}垂直业务场景，码视野研发团队提供从底层传感器选型、工业网关协议转换到云端时序大屏的端到端交钥匙方案，支持{' · '.join(target_topic['protocols'][:3])}等主流通信标准。",
        "cover_image": target_topic['cover_image'],
        "date": now.strftime('%Y-%m-%d %H:%M'),
        "deploy_cycle": target_topic.get('deploy_cycle', '15~25 天快速上线'),
        "roi_data": {
            "综合能耗降低": "16% ~ 28%",
            "故障定位时效": "< 3 分钟",
            "系统综合回报期": "缩短 30%+"
        },
        "protocols": target_topic['protocols'],
        "content_markdown": content
    }

    solutions.insert(0, new_solution)
    with open(SOLUTIONS_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(solutions, f, ensure_ascii=False, indent=2)
    print(f"[Solutions] solutions_index.json 已更新，共 {len(solutions)} 篇解决方案", flush=True)


# ==========================================
# 5. 自动新增落地交付案例 (每 2 天周期判定 / 手动强制支持)
# ==========================================
def update_cases_every_two_days(force=False):
    print("\n--- [任务 2] 检查更新落地项目案例 (每两天周期) ---", flush=True)
    if not CASES_INDEX_FILE.exists():
        cases = []
    else:
        with open(CASES_INDEX_FILE, 'r', encoding='utf-8') as f:
            cases = json.load(f)

    is_manual = force or os.getenv('GITHUB_EVENT_NAME') == 'workflow_dispatch' or os.getenv('FORCE_UPDATE') == 'true'
    need_update = False
    if is_manual:
        need_update = True
        print("[Cases] ⚡ 检测到手动触发指令 (workflow_dispatch)，无视 48 小时周期限制，强制新增落地案例！", flush=True)
    elif not cases:
        need_update = True
    else:
        latest_date_str = cases[0].get('created_at', '2020-01-01')
        try:
            latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d').replace(tzinfo=BEIJING_TZ)
            # 若距离当前时间大于等于 2 天（48 小时）
            diff_hours = (get_beijing_now() - latest_date).total_seconds() / 3600
            if diff_hours >= 48:
                need_update = True
                print(f"[Cases] 上次案例创建于 {latest_date_str} (距今 {diff_hours:.1f}h >= 48h)，触发新增案例！", flush=True)
            else:
                print(f"[Cases] 上次案例创建于 {latest_date_str} (距今 {diff_hours:.1f}h < 48h)，未满周期，暂不新增。", flush=True)
        except Exception:
            need_update = True

    if need_update:
        existing_titles = {c['title'] for c in cases}
        candidate = None
        for c in CASE_CANDIDATES:
            if c['title'] not in existing_titles:
                candidate = c
                break
        if not candidate:
            base_c = random.choice(CASE_CANDIDATES)
            candidate = dict(base_c)
            candidate['title'] = f"{base_c['title']} (二期扩容工程)"

        now = get_beijing_now()
        case_data = dict(candidate)
        case_data['id'] = f"case_{now.strftime('%Y%m%d%H%M%S')}"
        case_data['created_at'] = now.strftime('%Y-%m-%d')

        cases.insert(0, case_data)
        with open(CASES_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        print(f"[Cases] ✅ 成功新增落地项目案例: 《{case_data['title']}》，当前案例总数: {len(cases)}", flush=True)


# ==========================================
# 6. 自动新增技术深度博文 (一天 6 篇 / 4 小时周期)
# ==========================================
def update_blog_daily_six(force=False):
    print("\n--- [任务 3] 检查更新技术深度博文 (一天 6 篇周期 / 4h一篇) ---", flush=True)
    if not POSTS_INDEX_FILE.exists():
        posts = []
    else:
        with open(POSTS_INDEX_FILE, 'r', encoding='utf-8') as f:
            posts = json.load(f)

    is_manual = force or os.getenv('GITHUB_EVENT_NAME') == 'workflow_dispatch' or os.getenv('FORCE_UPDATE') == 'true'
    need_update = False
    if is_manual:
        need_update = True
        print("[Blog] ⚡ 检测到手动触发指令 (workflow_dispatch)，无视周期限制，强制新增技术博文！", flush=True)
    elif not posts:
        need_update = True
    else:
        latest_dt = parse_item_datetime(posts[0])
        diff_hours = (get_beijing_now() - latest_dt).total_seconds() / 3600
        # 一天 6 篇，即每 4 小时一篇 (24 / 6 = 4)
        if diff_hours >= 4:
            need_update = True
            print(f"[Blog] 上次博文更新于 {posts[0].get('date', '')} (距今 {diff_hours:.1f}h >= 4h)，满足更新周期（一天6篇，即4h/篇），触发更新！", flush=True)
        else:
            print(f"[Blog] 上次博文更新于 {posts[0].get('date', '')} (距今 {diff_hours:.1f}h < 4h)，未满更新周期（一天6篇，即4h/篇），保持现状。", flush=True)

    if not need_update:
        return

    now = get_beijing_now()
    article_id = now.strftime('%Y%m%d%H%M%S')

    blog_topics = [
        {"title": "MQTT 5.0 用户属性与原因码实战：如何实现毫秒级设备鉴权与精准异常定位？", "category": "技术实战解析", "tag": "MQTT 5.0", "cover": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80"},
        {"title": "工业物联网网关断网本地续传：如何用 SQLite 保证时序数据 100% 零丢失？", "category": "项目经验复盘", "tag": "边缘存储", "cover": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&q=80"},
        {"title": "从串口帧到时序库：Modbus RTU 转 MQTT 边缘网关调优全流程实战指南", "category": "技术实战解析", "tag": "Modbus转MQTT", "cover": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&q=80"},
        {"title": "高并发工业遥测平台选型：Kafka 与 EMQX 消息队列的边界与融合实践", "category": "选型决策指南", "tag": "架构选型", "cover": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80"}
    ]

    existing_titles = {p['title'] for p in posts}
    target = None
    for b in blog_topics:
        if b['title'] not in existing_titles:
            target = b
            break
    if not target:
        base_b = random.choice(blog_topics)
        target = dict(base_b)
        target['title'] = f"{base_b['title']} (深度实战篇)"

    system_prompt = (
        "你是码视野物联网软件研发团队的首席资深架构师（工业IoT与边缘计算深耕6年）。\n"
        "你正在为企业技术专栏撰写一篇极具工程说服力、深度、干货满满的万字级实战技术博文（2,500~3,500字）。\n"
        "【严禁事项】：严禁任何空洞废话套话，全篇以真实工业产线第一视角展开。\n"
        "【必须包含完整五大部分】：\n"
        "一、 工业现场真实硬件环境与底层痛点深度剖析（报文时序、串口反射、485总线抖动、网络断连）；\n"
        "二、 码视野高可用边缘系统拓扑架构（必须包含一段原生标准可渲染的 Mermaid flowchart 流程拓扑图）；\n"
        "三、 工业级生产环境完整实现代码示例（Python 或 Go 真实驱动与持久化缓存、重传逻辑，带详细中文注释）；\n"
        "四、 关键技术指标与改造前后 ROI 性能对比表格；\n"
        "五、 总结与技术支持咨询通道（专属技术顾问电话/微信：19065223505）。"
    )
    print(f"[Blog] 正在撰写深度博文：《{target['title']}》...", flush=True)
    content = call_agnes_llm(system_prompt, f"请撰写完整技术长文《{target['title']}》", max_tokens=3500, timeout_sec=90)

    if not content:
        content = f"""# {target['title']}

## 一、 为什么在 IoT 生产环境中这项技术至关重要？
在大型物联网与工业设备采集场景中，通信链路常受到现场强电磁干扰与弱网波动影响。如何保障数据可靠性是每一个架构师不可回避的命题。

## 二、 核心系统拓扑架构
码视野研发团队推荐以下高可用架构实现：

```mermaid
flowchart LR
    A["工业设备"] --> B["边缘智能网关"]
    B -->|"高频数据流"| C["EMQX 消息队列"]
    C --> D["时序存储引擎 (InfluxDB)"]
    C --> E["监控告警与看板"]
```

## 三、 关键实现代码片段
```python
# 码视野生产环境边缘数据消费与幂等写入样例
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe("factory/+/telemetry", qos=1)

client = mqtt.Client(client_id="codevision-edge-worker")
client.on_connect = on_connect
client.connect("broker.codevision.internal", 8883)
client.loop_forever()
```

## 四、 总结与技术支持通道
码视野研发团队致力于为企业提供高水准、高可靠的 IoT 软件系统。
- 电话/微信：**19065223505**（备注技术咨询）
- 邮箱：contact@codevision-iot.com
"""

    new_post = {
        "id": article_id,
        "title": target['title'],
        "category": target['category'],
        "tag": target['tag'],
        "read_time": "8 分钟",
        "date": now.strftime('%Y-%m-%d %H:%M'),
        "summary": f"针对{target['tag']}在实际工业场景中的工程难题，码视野研发团队深度复盘核心架构设计、高可用优化与实战避坑经验。",
        "cover_image": target['cover'],
        "roi_stats": {"消息可靠性": "99.99%", "延迟": "< 50ms"},
        "content_markdown": content
    }
    posts.insert(0, new_post)
    with open(POSTS_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"[Blog] posts_index.json 已更新，共 {len(posts)} 篇文章", flush=True)


# ==========================================
# 7. 全量静态编译与 Git 部署推送
# ==========================================
def compile_and_deploy():
    print("\n--- [任务 4] 全量静态落地页编译与自动推流部署 ---", flush=True)
    res = subprocess.run([sys.executable, str(BASE_DIR / 'build_static_posts.py')], capture_output=True, text=True, cwd=str(BASE_DIR))
    print(res.stdout, flush=True)
    if res.stderr:
        print("[Build Warning]", res.stderr[:200], flush=True)

    try:
        status_res = subprocess.run(['git', 'status', '--porcelain'], cwd=str(BASE_DIR), capture_output=True, text=True)
        if not status_res.stdout.strip():
            print("[Git] ℹ️ 本次运行各板块均处于周期内，无新增内容，保持最新状态无需重复推流。", flush=True)
            return

        subprocess.run(['git', 'add', '.'], cwd=str(BASE_DIR), check=True, capture_output=True)
        now_str = get_beijing_now().strftime('%m-%d %H:%M')
        subprocess.run(['git', 'commit', '-m', f'[auto-update] 解决方案/案例/博文定时自造血更新 ({now_str})'], cwd=str(BASE_DIR), check=True, capture_output=True)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=str(BASE_DIR), check=True, capture_output=True)
        print("[Git] ✅ 代码已成功推送到 GitHub main 分支，Vercel 自动构建中！", flush=True)
    except Exception as e:
        print(f"[Git] 暂无新变动或推送略过: {e}", flush=True)


def main():
    print("=" * 60, flush=True)
    print(f"[{get_beijing_now().strftime('%Y-%m-%d %H:%M:%S')}] 启动码视野 IoT 官网全流程自造血更新", flush=True)
    print("=" * 60, flush=True)

    # 1. 更新垂直行业解决方案（一天 1 篇 / 24 小时周期）
    update_solutions_daily()

    # 2. 更新落地交付案例（每 2 天 1 篇 / 48 小时周期）
    update_cases_every_two_days()

    # 3. 更新技术深度博文（一天 6 篇 / 每 4 小时周期）
    update_blog_daily_six()

    # 4. 全量编译与部署
    compile_and_deploy()

    print("\n🎉 全部自造血流水线执行完毕！", flush=True)


if __name__ == '__main__':
    main()
