# GitHub Trending 爬虫系统设计文档

**日期：** 2026-03-13
**版本：** 1.0
**状态：** 设计阶段

## 1. 项目概述

### 1.1 目标
设计并实现一个自动化系统，每天爬取GitHub trending页面，提取项目信息和亮点，生成HTML报告并通过钉钉机器人发送。

### 1.2 核心需求
- 每天爬取GitHub trending（今日、本周、本月三个时间维度）
- 提取项目基础信息、项目亮点、star/fork数据
- 生成HTML格式的可视化报告
- 将报告上传到阿里云OSS获取公网访问链接
- 通过钉钉机器人发送报告链接
- 使用Python实现，Docker容器化部署
- 存储历史数据支持趋势分析

## 2. 系统架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Container                      │
│                                                          │
│  ┌──────────────┐      ┌─────────────┐                 │
│  │   Scheduler  │─────>│   Scraper   │                 │
│  │ (APScheduler)│      │ (Selenium)  │                 │
│  └──────────────┘      └──────┬──────┘                 │
│                               │                          │
│                               v                          │
│                        ┌──────────────┐                 │
│                        │  Data Parser │                 │
│                        │  & Analyzer  │                 │
│                        └──────┬───────┘                 │
│                               │                          │
│                    ┌──────────┴──────────┐              │
│                    v                     v               │
│            ┌──────────────┐      ┌─────────────┐       │
│            │   SQLite DB  │      │   Report    │       │
│            │   (History)  │      │  Generator  │       │
│            └──────────────┘      └──────┬──────┘       │
│                                          │               │
│                                          v               │
│                                  ┌──────────────┐       │
│                                  │  OSS Uploader│       │
│                                  └──────┬───────┘       │
│                                          │               │
│                                          v               │
│                                  ┌──────────────┐       │
│                                  │ DingTalk Bot │       │
│                                  └──────────────┘       │
└─────────────────────────────────────────────────────────┘
```

### 2.2 核心流程
1. APScheduler每天定时触发爬取任务
2. Selenium访问GitHub trending（今日/本周/本月）
3. 解析HTML提取项目信息和亮点
4. 存储到SQLite（支持历史对比）
5. 生成HTML报告
6. 上传到阿里云OSS获取公网URL
7. 钉钉机器人发送报告链接

## 3. 核心组件设计

### 3.1 Scraper（爬虫模块）

**技术选型：** Selenium + Chrome headless

**功能：**
- 爬取三个时间维度：
  - 今日trending: `https://github.com/trending`
  - 本周trending: `https://github.com/trending?since=weekly`
  - 本月trending: `https://github.com/trending?since=monthly`

**提取字段：**
- 项目名称（owner/repo）
- 项目描述
- 编程语言
- 当前总star数
- 当前总fork数
- 今日/本周/本月新增star数
- 项目URL

**反爬虫策略：**
- 随机User-Agent轮换
- 请求间随机延迟（2-5秒）
- 智能等待页面元素加载完成
- 失败重试机制（最多3次，指数退避）

### 3.2 Data Parser & Analyzer（数据解析与分析）

**功能：**
- 解析HTML结构提取结构化数据
- 项目亮点识别和标注
- 历史数据对比分析

**项目亮点提取规则：**
- 🆕 新上榜：首次出现在trending
- 🔥 快速增长：日增star > 500
- ⭐ 高人气：总star > 10,000
- 📈 排名上升：与昨日对比排名提升
- 🏆 榜首：排名第1

**数据验证：**
- 必填字段检查（项目名、URL、star数）
- 数据类型验证
- 异常值检测

### 3.3 SQLite Database（数据存储）

**表结构：**

```sql
-- 项目表
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_full_name TEXT UNIQUE NOT NULL,  -- 如 "facebook/react"
    repo_url TEXT NOT NULL,
    first_seen_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trending记录表
CREATE TABLE trending_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    record_date DATE NOT NULL,
    period_type TEXT NOT NULL,  -- 'daily', 'weekly', 'monthly'
    rank INTEGER NOT NULL,
    description TEXT,
    language TEXT,
    total_stars INTEGER,
    total_forks INTEGER,
    period_stars INTEGER,  -- 该时间段新增star数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    UNIQUE(project_id, record_date, period_type)
);

-- 报告表
CREATE TABLE daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE UNIQUE NOT NULL,
    oss_url TEXT,
    dingtalk_sent BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**索引设计：**
```sql
CREATE INDEX idx_trending_date ON trending_records(record_date);
CREATE INDEX idx_trending_project ON trending_records(project_id);
CREATE INDEX idx_projects_name ON projects(repo_full_name);
```

### 3.4 Report Generator（报告生成器）

**技术选型：** Jinja2模板引擎

**报告内容：**
- 日期和统计摘要（总项目数、热门语言分布）
- 三个标签页（今日/本周/本月trending）
- 每个项目卡片显示：
  - 项目名称（链接到GitHub）
  - 项目描述
  - 编程语言标签
  - Star/Fork数据
  - 新增star数
  - 亮点标签（新上榜、快速增长等）
  - 排名变化趋势

**设计特性：**
- 响应式设计，支持移动端和PC端
- 现代化UI风格
- 数据可视化（语言分布饼图、增长趋势图）

### 3.5 OSS Uploader（对象存储上传）

**技术选型：** 阿里云OSS Python SDK (oss2)

**功能：**
- 上传HTML报告到OSS
- 文件命名规则：`github-trending-YYYY-MM-DD.html`
- 设置公共读权限
- 返回公网访问URL
- 失败重试机制（最多3次）

**配置项：**
- AccessKeyId / AccessKeySecret
- Bucket名称
- Endpoint（区域节点）
- 文件存储路径前缀

### 3.6 DingTalk Bot（钉钉机器人）

**技术选型：** 钉钉自定义机器人Webhook API

**消息类型：** Link类型

**消息内容：**
- 标题：`GitHub Trending 日报 - YYYY-MM-DD`
- 摘要：今日trending项目数量和热门语言统计
- 报告链接：OSS公网URL
- 缩略图（可选）

**安全机制：**
- 支持加签验证（使用secret）
- 失败重试机制（最多3次）

## 4. 数据流设计

### 4.1 完整数据流

```
1. 爬取阶段
   Selenium → 原始HTML → 解析器 → 结构化数据（JSON）

2. 存储阶段
   检查项目是否存在 → 插入/更新projects表 → 插入trending_records

3. 分析阶段
   查询历史数据 → 计算趋势 → 标注亮点

4. 生成阶段
   从数据库读取 → Jinja2模板 → HTML文件

5. 发送阶段
   上传OSS → 获取URL → 钉钉发送 → 更新daily_reports表
```

### 4.2 数据处理流程

**输入：** GitHub trending页面HTML
**输出：** 钉钉消息 + OSS存储的HTML报告

**中间数据格式：**
```python
{
    "date": "2026-03-13",
    "period": "daily",  # daily/weekly/monthly
    "projects": [
        {
            "rank": 1,
            "name": "facebook/react",
            "url": "https://github.com/facebook/react",
            "description": "A declarative, efficient...",
            "language": "JavaScript",
            "total_stars": 220000,
            "total_forks": 45000,
            "period_stars": 1500,
            "highlights": ["🔥", "⭐"]
        },
        ...
    ]
}
```

## 5. 错误处理策略

### 5.1 爬虫层面
- **网络超时：** 重试3次，指数退避（1s, 2s, 4s）
- **页面加载失败：** 记录日志，跳过该时间段，继续其他任务
- **反爬虫检测：** 随机User-Agent，添加随机延迟（2-5秒）
- **元素定位失败：** 使用多种选择器策略（CSS、XPath）作为备选

### 5.2 数据处理层面
- **数据解析异常：** 记录原始HTML，跳过该项目，继续处理其他项目
- **数据库写入失败：** 事务回滚，记录错误日志
- **数据完整性检查：** 验证必填字段（项目名、URL、star数）

### 5.3 报告生成层面
- **模板渲染失败：** 使用简化版模板作为降级方案
- **OSS上传失败：** 重试3次，失败则保存本地并发送错误通知
- **钉钉发送失败：** 重试3次，记录失败状态到数据库

### 5.4 通知机制
- **关键错误：** 发送钉钉告警消息（爬取完全失败、数据库损坏）
- **一般错误：** 记录到日志文件，每周汇总

## 6. 配置管理

### 6.1 配置文件（config.yaml）

```yaml
# 爬虫配置
scraper:
  headless: true
  timeout: 30
  retry_times: 3
  user_agents:
    - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    - "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# 数据库配置
database:
  path: "/data/github_trending.db"

# 阿里云OSS配置
oss:
  access_key_id: ${OSS_ACCESS_KEY_ID}
  access_key_secret: ${OSS_ACCESS_KEY_SECRET}
  bucket_name: ${OSS_BUCKET_NAME}
  endpoint: "oss-cn-hangzhou.aliyuncs.com"
  path_prefix: "github-trending/"

# 钉钉配置
dingtalk:
  webhook_url: ${DINGTALK_WEBHOOK_URL}
  secret: ${DINGTALK_SECRET}

# 调度配置
scheduler:
  run_time: "09:00"  # 每天9点执行
  timezone: "Asia/Shanghai"

# 日志配置
logging:
  level: "INFO"
  file: "/app/logs/scraper.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

### 6.2 环境变量（.env）

```bash
# 阿里云OSS
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_BUCKET_NAME=your_bucket_name

# 钉钉机器人
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=your_secret

# 时区
TZ=Asia/Shanghai
```

## 7. 测试策略

### 7.1 单元测试

**测试框架：** pytest

**测试覆盖：**
- `test_scraper.py`：测试HTML解析逻辑，使用mock的HTML数据
- `test_parser.py`：测试数据提取和验证
- `test_database.py`：测试CRUD操作，使用内存SQLite
- `test_analyzer.py`：测试亮点识别逻辑
- `test_report_generator.py`：测试模板渲染，验证HTML输出
- `test_oss_uploader.py`：测试上传逻辑（mock OSS SDK）
- `test_dingtalk_bot.py`：测试消息发送（mock HTTP请求）

**覆盖率目标：** >80%

### 7.2 集成测试

**测试场景：**
1. 端到端流程：爬取 → 存储 → 生成 → 上传 → 发送
2. 使用测试环境的OSS bucket和钉钉测试群
3. 验证数据完整性和一致性
4. 测试错误恢复机制

### 7.3 手动测试

**测试清单：**
- [ ] 首次部署时手动触发一次完整流程
- [ ] 验证HTML报告在移动端和PC端的显示效果
- [ ] 检查钉钉消息格式和链接可访问性
- [ ] 验证数据库数据正确性
- [ ] 测试各种异常场景（网络中断、GitHub限流等）

## 8. 部署方案

### 8.1 Docker配置

**Dockerfile：**
```dockerfile
FROM python:3.11-slim

# 安装Chrome和ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "src/scheduler.py"]
```

**docker-compose.yml：**
```yaml
version: '3.8'

services:
  github-trending-scraper:
    build: .
    container_name: github_trending
    volumes:
      - ./data:/data          # 数据持久化
      - ./logs:/app/logs      # 日志持久化
    environment:
      - TZ=Asia/Shanghai
    env_file:
      - .env
    restart: unless-stopped
```

### 8.2 目录结构

```
github-trending-scraper/
├── src/
│   ├── __init__.py
│   ├── scraper.py          # 爬虫模块
│   ├── parser.py           # 数据解析
│   ├── database.py         # 数据库操作
│   ├── analyzer.py         # 数据分析
│   ├── report_generator.py # 报告生成
│   ├── oss_uploader.py     # OSS上传
│   ├── dingtalk_bot.py     # 钉钉机器人
│   ├── scheduler.py        # 调度器（主入口）
│   └── utils.py            # 工具函数
├── templates/
│   └── report.html         # HTML模板
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py
│   ├── test_parser.py
│   ├── test_database.py
│   ├── test_analyzer.py
│   ├── test_report_generator.py
│   ├── test_oss_uploader.py
│   └── test_dingtalk_bot.py
├── data/                   # 数据目录（挂载volume）
│   └── github_trending.db
├── logs/                   # 日志目录（挂载volume）
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-03-13-github-trending-scraper-design.md
├── config.yaml             # 配置文件
├── requirements.txt        # Python依赖
├── Dockerfile
├── docker-compose.yml
├── .env.example           # 环境变量示例
├── .gitignore
└── README.md
```

### 8.3 部署步骤

1. **准备环境**
   ```bash
   # 克隆代码
   git clone <repo_url>
   cd github-trending-scraper

   # 配置环境变量
   cp .env.example .env
   # 编辑.env文件，填入OSS和钉钉配置
   ```

2. **构建和启动**
   ```bash
   # 构建镜像
   docker-compose build

   # 启动容器
   docker-compose up -d
   ```

3. **验证运行**
   ```bash
   # 查看日志
   docker-compose logs -f

   # 手动触发一次测试
   docker-compose exec github-trending-scraper python -c "from src.scheduler import run_job; run_job()"
   ```

4. **监控和维护**
   ```bash
   # 查看容器状态
   docker-compose ps

   # 重启服务
   docker-compose restart

   # 查看数据库
   sqlite3 data/github_trending.db
   ```

## 9. 依赖清单

### 9.1 Python依赖（requirements.txt）

```
# Web爬虫
selenium==4.18.1
webdriver-manager==4.0.1

# 数据处理
beautifulsoup4==4.12.3
lxml==5.1.0

# 数据库
# SQLite是Python内置的，无需额外安装

# 报告生成
jinja2==3.1.3

# 阿里云OSS
oss2==2.18.4

# HTTP请求
requests==2.31.0

# 任务调度
APScheduler==3.10.4

# 配置管理
pyyaml==6.0.1
python-dotenv==1.0.1

# 日志
loguru==0.7.2

# 测试
pytest==8.0.2
pytest-cov==4.1.0
pytest-mock==3.12.0
```

## 10. 风险与限制

### 10.1 技术风险

1. **GitHub反爬虫**
   - 风险：GitHub可能检测并限制爬虫访问
   - 缓解：使用合理的请求频率，添加User-Agent，考虑使用GitHub API作为备选方案

2. **页面结构变化**
   - 风险：GitHub trending页面HTML结构可能变化导致解析失败
   - 缓解：使用多种选择器策略，添加结构变化检测和告警

3. **OSS费用**
   - 风险：长期存储HTML文件可能产生费用
   - 缓解：设置文件过期策略（如保留最近30天），定期清理旧文件

### 10.2 功能限制

1. **数据准确性**
   - trending页面的star增长数是GitHub计算的，可能与实际值有偏差
   - 项目亮点提取基于规则，可能不够智能

2. **实时性**
   - 每天只爬取一次，无法实时追踪trending变化
   - 如需实时性，需要增加爬取频率

3. **语言支持**
   - 当前设计爬取所有语言的trending
   - 如需特定语言，需要修改URL参数

## 11. 未来扩展

### 11.1 短期优化（1-2个月）
- 添加项目详情页爬取（README、贡献者、技术栈）
- 使用GitHub API补充数据（更准确的star历史）
- 增加数据可视化图表（趋势曲线、语言分布）
- 支持自定义爬取时间和频率

### 11.2 长期规划（3-6个月）
- 使用AI分析项目描述，自动生成项目亮点摘要
- 支持多平台trending（GitLab、Gitee等）
- 提供Web界面查询历史数据
- 支持订阅特定语言或主题的trending
- 集成邮件通知作为钉钉的备选方案

## 12. 总结

本设计文档详细描述了GitHub Trending爬虫系统的架构、组件、数据流、错误处理、测试和部署方案。系统采用模块化设计，各组件职责清晰，易于维护和扩展。

**核心优势：**
- 完整的数据采集和分析流程
- 可靠的错误处理和重试机制
- Docker容器化部署，易于迁移
- 历史数据存储，支持趋势分析
- 自动化报告生成和发送

**下一步：**
编写详细的实现计划（implementation plan），将设计转化为可执行的开发任务。
