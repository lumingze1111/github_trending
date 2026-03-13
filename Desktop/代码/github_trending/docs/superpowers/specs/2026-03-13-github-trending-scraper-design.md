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

**接口定义：**
```python
class GitHubScraper:
    def scrape_trending(self, period: str) -> List[Dict]:
        """
        爬取指定时间段的trending项目

        Args:
            period: 'daily', 'weekly', 'monthly'

        Returns:
            List[Dict]: 项目列表，每个项目包含上述提取字段

        Raises:
            ScraperException: 爬取失败（网络错误、页面加载超时等）
        """
        pass
```

**错误处理：**
- **浏览器崩溃：** 捕获WebDriverException，记录日志，抛出ScraperException
- **页面加载超时：** 设置30秒超时，超时后重试，最多3次
- **元素定位失败：** 使用多种选择器策略（CSS、XPath），全部失败则跳过该项目
- **反爬虫检测：** 检测到验证码或403错误时，等待60秒后重试
- **重试策略：** 指数退避（1s, 2s, 4s），3次失败后抛出异常

**反爬虫策略：**
- 随机User-Agent轮换（从配置文件读取列表）
- 请求间随机延迟（2-5秒）
- 智能等待页面元素加载完成（WebDriverWait，最长30秒）
- 模拟人类行为（随机滚动页面）

### 3.2 Data Parser（数据解析模块）

**职责：** 将Scraper返回的原始HTML/文本数据解析为结构化数据，并进行数据验证。

**接口定义：**
```python
class DataParser:
    def parse_project(self, raw_html: str) -> Optional[Dict]:
        """
        解析单个项目的HTML片段

        Args:
            raw_html: 项目HTML片段

        Returns:
            Dict: 结构化项目数据，解析失败返回None
        """
        pass

    def validate(self, project: Dict) -> bool:
        """
        验证项目数据完整性

        必填字段：repo_full_name, repo_url, total_stars
        数字字段：total_stars, total_forks, period_stars 必须为非负整数
        """
        pass
```

**错误处理：**
- **HTML结构变化：** 使用多个备选CSS选择器，全部失败时记录原始HTML到日志并返回None
- **字段缺失：** 非必填字段缺失时使用默认值（描述为空字符串，语言为"Unknown"）
- **数据类型错误：** star/fork数解析失败时记录警告并设为0

### 3.3 Analyzer（数据分析模块）

**职责：** 基于当前数据和历史数据，为项目标注亮点标签。

**接口定义：**
```python
class Analyzer:
    def analyze(self, projects: List[Dict], date: str, period: str) -> List[Dict]:
        """
        分析项目并标注亮点

        Args:
            projects: 解析后的项目列表
            date: 当前日期 YYYY-MM-DD
            period: 'daily', 'weekly', 'monthly'

        Returns:
            List[Dict]: 添加了highlights字段的项目列表
        """
        pass
```

**亮点提取规则：**
- 🆕 新上榜：projects表中无该项目记录（first_seen_date = today）
- 🔥 快速增长：period_stars > 500（daily）或 > 2000（weekly/monthly）
- ⭐ 高人气：total_stars > 10,000
- 📈 排名上升：与昨日同period_type对比，rank降低（数字变小）
- 🏆 榜首：rank == 1

### 3.4 Database（数据库模块）

**表结构：**

```sql
-- 项目表
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_full_name TEXT UNIQUE NOT NULL,  -- 如 "facebook/react"
    repo_url TEXT NOT NULL,
    first_seen_date DATE NOT NULL,
    last_updated DATE NOT NULL,  -- 最后一次出现在trending的日期
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

**接口定义：**
```python
class Database:
    def save_projects(self, projects: List[Dict], date: str, period: str) -> None:
        """
        保存项目数据到数据库

        逻辑：
        1. 对每个项目，检查projects表是否存在（按repo_full_name）
        2. 不存在则插入，存在则更新last_updated
        3. 插入trending_records记录

        使用事务确保原子性，失败时回滚
        """
        pass

    def get_previous_ranking(self, date: str, period: str) -> Dict[str, int]:
        """
        获取前一天的排名数据

        Returns:
            Dict[repo_full_name, rank]: 项目名到排名的映射
        """
        pass
```

**更新逻辑：**
- `last_updated`字段：每次项目出现在trending时更新为当前日期
- 用于识别长期未上榜的项目（可用于未来的数据清理）

### 3.5 Report Generator（报告生成器）

**技术选型：** Jinja2模板引擎

**模板位置：** `templates/report.html`

**接口定义：**
```python
class ReportGenerator:
    def generate(self, data: Dict, output_path: str) -> str:
        """
        生成HTML报告

        Args:
            data: 包含date, daily_projects, weekly_projects, monthly_projects
            output_path: 输出文件路径

        Returns:
            str: 生成的HTML文件路径

        Raises:
            TemplateException: 模板渲染失败
        """
        pass
```

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
  - 排名变化趋势（↑↓符号）

**模板结构：**
```html
<!DOCTYPE html>
<html>
<head>
    <title>GitHub Trending - {{ date }}</title>
    <style>/* 响应式CSS */</style>
</head>
<body>
    <header>
        <h1>GitHub Trending 日报</h1>
        <p>{{ date }}</p>
    </header>
    <div class="tabs">
        <div class="tab" data-period="daily">今日</div>
        <div class="tab" data-period="weekly">本周</div>
        <div class="tab" data-period="monthly">本月</div>
    </div>
    <div class="content">
        {% for project in daily_projects %}
        <div class="project-card">
            <!-- 项目信息 -->
        </div>
        {% endfor %}
    </div>
</body>
</html>
```

**设计特性：**
- 响应式设计，支持移动端和PC端
- 现代化UI风格（使用CSS Grid/Flexbox）
- 无外部依赖（CSS/JS内联）

**错误处理：**
- 模板文件不存在：抛出TemplateException
- 渲染失败：使用简化版模板（纯文本列表）作为降级方案

### 3.6 OSS Uploader（对象存储上传）

**技术选型：** 阿里云OSS Python SDK (oss2)

**接口定义：**
```python
class OSSUploader:
    def upload(self, file_path: str, object_name: str) -> str:
        """
        上传文件到OSS

        Args:
            file_path: 本地文件路径
            object_name: OSS对象名（如 "github-trending/2026-03-13.html"）

        Returns:
            str: 公网访问URL

        Raises:
            OSSException: 上传失败（认证错误、网络错误、权限错误）
        """
        pass
```

**功能：**
- 上传HTML报告到OSS
- 文件命名规则：`{path_prefix}/github-trending-YYYY-MM-DD.html`
- 设置公共读权限（ACL: public-read）
- 返回公网访问URL格式：`https://{bucket}.{endpoint}/{object_name}`

**配置项（从config.yaml读取）：**
- `access_key_id`: OSS AccessKeyId（从环境变量）
- `access_key_secret`: OSS AccessKeySecret（从环境变量）
- `bucket_name`: Bucket名称（从环境变量）
- `endpoint`: 区域节点（如 "oss-cn-hangzhou.aliyuncs.com"）
- `path_prefix`: 文件存储路径前缀（如 "github-trending/"）

**错误处理：**
- **认证失败：** 抛出OSSException，不重试（配置错误）
- **网络错误：** 重试3次，指数退避（1s, 2s, 4s）
- **权限错误：** 抛出OSSException，不重试（配置错误）
- **上传失败（3次后）：** 保存文件到本地备份目录，发送钉钉告警

### 3.7 DingTalk Bot（钉钉机器人）

**技术选型：** 钉钉自定义机器人Webhook API

**接口定义：**
```python
class DingTalkBot:
    def send_report(self, title: str, text: str, report_url: str) -> bool:
        """
        发送报告链接到钉钉

        Args:
            title: 消息标题
            text: 消息摘要
            report_url: 报告URL

        Returns:
            bool: 发送成功返回True

        Raises:
            DingTalkException: 发送失败（网络错误、webhook配置错误）
        """
        pass
```

**配置方式：**
- `webhook_url`: 从环境变量 `DINGTALK_WEBHOOK_URL` 读取
- `secret`: 从环境变量 `DINGTALK_SECRET` 读取（用于加签）

**消息类型：** Link类型

**消息格式：**
```json
{
    "msgtype": "link",
    "link": {
        "title": "GitHub Trending 日报 - 2026-03-13",
        "text": "今日trending: 25个项目，热门语言: Python(8), JavaScript(6), Go(4)",
        "messageUrl": "https://your-bucket.oss-cn-hangzhou.aliyuncs.com/...",
        "picUrl": ""
    }
}
```

**安全机制：**
- 使用HMAC-SHA256加签验证（基于secret和timestamp）
- 签名算法：`sign = base64(hmac_sha256(timestamp + "\n" + secret))`

**错误处理：**
- **网络错误：** 重试3次，指数退避（1s, 2s, 4s）
- **Webhook配置错误：** 抛出DingTalkException，不重试
- **发送失败（3次后）：** 记录到数据库（dingtalk_sent=0），下次手动重试

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

### 5.1 错误分类

**可重试错误（Retryable Errors）：**
- 网络超时
- 临时性网络错误（ConnectionError, Timeout）
- HTTP 5xx错误
- OSS上传临时失败

**不可重试错误（Non-Retryable Errors）：**
- 配置错误（缺少必填配置项、认证失败）
- HTTP 4xx错误（除429外）
- 数据验证失败
- 模板文件不存在

**重试策略：**
- 最多重试3次
- 指数退避：1秒、2秒、4秒
- 记录每次重试的日志

### 5.2 爬虫层面
- **网络超时：** 重试3次，指数退避（1s, 2s, 4s）
- **页面加载失败：** 记录日志，跳过该时间段，继续其他任务
- **反爬虫检测：** 随机User-Agent，添加随机延迟（2-5秒）
- **元素定位失败：** 使用多种选择器策略（CSS、XPath）作为备选

### 5.3 数据处理层面
- **数据解析异常：** 记录原始HTML，跳过该项目，继续处理其他项目
- **数据库写入失败：** 事务回滚，记录错误日志
- **数据完整性检查：** 验证必填字段（项目名、URL、star数）

### 5.4 报告生成层面
- **模板渲染失败：** 使用简化版模板作为降级方案
- **OSS上传失败：** 重试3次，失败则保存本地并发送错误通知
- **钉钉发送失败：** 重试3次，记录失败状态到数据库

### 5.5 通知机制
- **关键错误：** 发送钉钉告警消息（爬取完全失败、数据库损坏）
- **一般错误：** 记录到日志文件，每周汇总

## 6. 配置管理

### 6.1 配置加载策略

**配置来源优先级：**
1. 环境变量（最高优先级）
2. config.yaml文件
3. 默认值（最低优先级）

**配置加载接口：**
```python
class Config:
    @staticmethod
    def load() -> Dict:
        """
        加载配置

        1. 读取config.yaml
        2. 使用环境变量覆盖（${VAR_NAME}语法）
        3. 验证必填配置项

        Raises:
            ConfigException: 配置文件不存在或必填项缺失
        """
        pass
```

**必填配置项：**
- `OSS_ACCESS_KEY_ID`
- `OSS_ACCESS_KEY_SECRET`
- `OSS_BUCKET_NAME`
- `DINGTALK_WEBHOOK_URL`

### 6.2 配置文件（config.yaml）

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
