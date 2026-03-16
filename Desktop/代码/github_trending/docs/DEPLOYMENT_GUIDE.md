# GitHub Trending 爬虫系统 - 详细部署指南

本文档详细说明了 GitHub Trending 爬虫系统的完整部署流程，包括系统架构、工作流程、Docker 配置和故障排查。

## 目录

1. [系统架构](#系统架构)
2. [工作流程](#工作流程)
3. [部署前准备](#部署前准备)
4. [Docker 部署详解](#docker-部署详解)
5. [配置详解](#配置详解)
6. [运维管理](#运维管理)
7. [故障排查](#故障排查)

---

## 系统架构

### 整体架构图

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

### 核心组件

1. **Scheduler（调度器）**
   - 使用 APScheduler 实现定时任务
   - 默认每天 09:00 执行
   - 编排整个工作流程

2. **Scraper（爬虫）**
   - 使用 Selenium + Chrome headless
   - 爬取三个时间维度（今日/本周/本月）
   - 反爬虫机制（随机延迟、User-Agent 轮换）

3. **Parser（解析器）**
   - 使用 BeautifulSoup 解析 HTML
   - 提取项目信息（名称、描述、stars、语言等）
   - 数据验证和清洗

4. **Analyzer（分析器）**
   - 检测项目亮点（新上榜、快速增长、高人气等）
   - 生成趋势统计
   - 排名变化追踪

5. **Database（数据库）**
   - SQLite 存储历史数据
   - 支持趋势分析
   - 三张表：projects、trending_records、daily_reports

6. **ReportGenerator（报告生成器）**
   - Jinja2 模板引擎
   - 生成响应式 HTML 报告
   - 支持三个标签页切换

7. **OSSUploader（OSS 上传器）**
   - 上传报告到阿里云 OSS
   - 生成公网访问 URL
   - 自动设置公共读权限

8. **DingTalkBot（钉钉机器人）**
   - 通过 Webhook 发送通知
   - 支持 Markdown 格式
   - HMAC-SHA256 签名验证

---

## 工作流程

### 完整执行流程

```
开始
  │
  ├─> Step 1: 爬取 GitHub Trending
  │   ├─> 爬取今日 trending
  │   ├─> 爬取本周 trending
  │   └─> 爬取本月 trending
  │
  ├─> Step 2: 解析 HTML 内容
  │   ├─> 提取项目信息
  │   ├─> 数据验证
  │   └─> 过滤无效数据
  │
  ├─> Step 3: 分析项目
  │   ├─> 检测项目亮点
  │   ├─> 计算排名变化
  │   └─> 生成统计数据
  │
  ├─> Step 4: 保存到数据库
  │   ├─> 更新 projects 表
  │   ├─> 插入 trending_records
  │   └─> 事务提交
  │
  ├─> Step 5: 生成摘要统计
  │   ├─> 计算总 stars
  │   ├─> 统计热门语言
  │   └─> 生成 top 项目列表
  │
  ├─> Step 6: 生成 HTML 报告
  │   ├─> 渲染 Jinja2 模板
  │   ├─> 填充项目数据
  │   └─> 保存到临时目录
  │
  ├─> Step 7: 上传到 OSS
  │   ├─> 连接 OSS
  │   ├─> 上传文件
  │   ├─> 设置公共读权限
  │   └─> 获取公网 URL
  │
  ├─> Step 8: 发送钉钉通知
  │   ├─> 构建消息内容
  │   ├─> 生成签名
  │   └─> 发送 Webhook 请求
  │
  └─> Step 9: 保存报告元数据
      ├─> 记录 OSS URL
      ├─> 标记发送状态
      └─> 完成
```

### 时间线

假设配置为每天 09:00 执行：

```
08:59:59 - 调度器等待中
09:00:00 - 触发任务执行
09:00:01 - 开始爬取 GitHub Trending
09:00:30 - 爬取完成（约 30 秒）
09:00:31 - 开始解析 HTML
09:00:35 - 解析完成（约 4 秒）
09:00:36 - 开始分析项目
09:00:38 - 分析完成（约 2 秒）
09:00:39 - 保存到数据库
09:00:40 - 生成 HTML 报告
09:00:42 - 上传到 OSS
09:00:45 - 发送钉钉通知
09:00:46 - 任务完成
```

总耗时约 **45-60 秒**。

---

## 部署前准备

### 1. 服务器要求

**最低配置：**
- CPU: 1 核
- 内存: 1GB
- 磁盘: 10GB
- 操作系统: Linux (Ubuntu 20.04+ / CentOS 7+)

**推荐配置：**
- CPU: 2 核
- 内存: 2GB
- 磁盘: 20GB
- 操作系统: Ubuntu 22.04 LTS

### 2. 安装 Docker

**Ubuntu/Debian:**

```bash
# 更新包索引
sudo apt-get update

# 安装依赖
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker 官方 GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 验证安装
sudo docker --version
sudo docker compose version
```

**CentOS/RHEL:**

```bash
# 安装依赖
sudo yum install -y yum-utils

# 添加 Docker 仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
sudo docker --version
sudo docker compose version
```

### 3. 配置 Docker 权限（可选）

```bash
# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker

# 验证（无需 sudo）
docker ps
```

### 4. 准备阿里云 OSS

1. 登录阿里云控制台
2. 进入 OSS 服务
3. 创建 Bucket：
   - 名称：如 `github-trending-reports`
   - 区域：选择离你最近的区域
   - 读写权限：私有（程序会设置单个文件为公共读）
   - 存储类型：标准存储

4. 获取访问密钥：
   - 进入 AccessKey 管理
   - 创建 AccessKey
   - 记录 AccessKeyId 和 AccessKeySecret

### 5. 配置钉钉机器人

1. 打开钉钉群聊
2. 点击群设置 -> 智能群助手 -> 添加机器人
3. 选择"自定义"机器人
4. 配置：
   - 名称：GitHub Trending 日报
   - 安全设置：选择"加签"
   - 记录 Webhook URL 和加签密钥

---

## Docker 部署详解

### Dockerfile 解析

让我们逐行解析 Dockerfile：

```dockerfile
# 使用 Python 3.11 slim 镜像作为基础镜像
# slim 版本体积小，包含基本的 Python 运行环境
FROM python:3.11-slim

# 设置工作目录为 /app
# 后续所有操作都在这个目录下进行
WORKDIR /app

# 安装系统依赖
# wget: 下载文件
# gnupg: GPG 密钥管理
# unzip: 解压文件
# curl: HTTP 请求工具
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*  # 清理缓存，减小镜像体积

# 安装 Google Chrome
# 1. 添加 Google 的 GPG 密钥
# 2. 添加 Chrome 的 apt 源
# 3. 更新包列表
# 4. 安装 Chrome stable 版本
# 5. 清理缓存
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 先复制 requirements.txt
# 利用 Docker 层缓存机制，如果依赖没变，这一层会被缓存
COPY requirements.txt .

# 安装 Python 依赖
# --no-cache-dir: 不缓存下载的包，减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
# 这些文件变化频繁，放在后面可以利用前面的缓存层
COPY src/ ./src/
COPY templates/ ./templates/
COPY config.yaml .

# 创建必要的目录
# /data: 存储 SQLite 数据库
# /app/logs: 存储日志文件
RUN mkdir -p /data /app/logs

# 设置环境变量
# PYTHONUNBUFFERED=1: 禁用 Python 输出缓冲，实时看到日志
# TZ: 设置时区为上海（东八区）
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 容器启动时执行的命令
# 运行 scheduler 模块
CMD ["python", "-m", "src.scheduler"]
```

### docker-compose.yml 解析

```yaml
version: '3.8'  # Docker Compose 文件版本

services:
  github-trending-scraper:  # 服务名称
    build: .  # 使用当前目录的 Dockerfile 构建镜像
    container_name: github_trending_scraper  # 容器名称
    restart: unless-stopped  # 重启策略：除非手动停止，否则总是重启

    volumes:  # 数据卷挂载
      # 将宿主机的 ./data 目录挂载到容器的 /data
      # 用于持久化 SQLite 数据库
      - ./data:/data

      # 将宿主机的 ./logs 目录挂载到容器的 /app/logs
      # 用于持久化日志文件
      - ./logs:/app/logs

      # 将配置文件挂载为只读（:ro）
      # 方便在不重建镜像的情况下修改配置
      - ./config.yaml:/app/config.yaml:ro

    environment:  # 环境变量
      - TZ=Asia/Shanghai  # 时区设置

      # OSS 配置（从 .env 文件读取）
      - OSS_ACCESS_KEY_ID=${OSS_ACCESS_KEY_ID}
      - OSS_ACCESS_KEY_SECRET=${OSS_ACCESS_KEY_SECRET}
      - OSS_BUCKET_NAME=${OSS_BUCKET_NAME}

      # DingTalk 配置（从 .env 文件读取）
      - DINGTALK_WEBHOOK_URL=${DINGTALK_WEBHOOK_URL}
      - DINGTALK_SECRET=${DINGTALK_SECRET}

    env_file:  # 从文件加载环境变量
      - .env

    deploy:  # 资源限制（可选）
      resources:
        limits:  # 最大资源限制
          cpus: '1.0'      # 最多使用 1 个 CPU 核心
          memory: 1G       # 最多使用 1GB 内存
        reservations:  # 预留资源
          cpus: '0.5'      # 预留 0.5 个 CPU 核心
          memory: 512M     # 预留 512MB 内存

    healthcheck:  # 健康检查（可选）
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s      # 每 30 秒检查一次
      timeout: 10s       # 超时时间 10 秒
      retries: 3         # 失败 3 次后标记为不健康
      start_period: 40s  # 启动后 40 秒才开始检查
```

### 部署步骤详解

#### 步骤 1: 克隆项目

```bash
# 克隆代码仓库
git clone <repository_url>
cd github-trending

# 查看项目结构
ls -la
```

#### 步骤 2: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量文件
vim .env  # 或使用 nano .env
```

`.env` 文件内容示例：

```bash
# 阿里云 OSS 配置
OSS_ACCESS_KEY_ID=LTAI5tXXXXXXXXXXXXXX
OSS_ACCESS_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OSS_BUCKET_NAME=github-trending-reports

# 钉钉机器人配置
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DINGTALK_SECRET=SECxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 时区配置
TZ=Asia/Shanghai
```

**重要提示：**
- 不要将 `.env` 文件提交到 Git 仓库
- 确保 `.env` 文件权限为 600（只有所有者可读写）

```bash
chmod 600 .env
```

#### 步骤 3: 修改配置文件（可选）

编辑 `config.yaml` 修改调度时间等配置：

```yaml
# 调度配置
scheduler:
  run_time: "09:00"  # 修改为你想要的执行时间
  timezone: "Asia/Shanghai"

# 爬虫配置
scraper:
  headless: true  # 生产环境建议保持 true
  timeout: 30
  retry_times: 3

# 日志配置
logging:
  level: "INFO"  # 可选: DEBUG, INFO, WARNING, ERROR
  file: "/app/logs/scraper.log"
```

#### 步骤 4: 构建 Docker 镜像

```bash
# 构建镜像
docker-compose build

# 查看构建的镜像
docker images | grep github-trending
```

**构建过程说明：**

1. **下载基础镜像** (python:3.11-slim)
   - 约 150MB
   - 包含 Python 3.11 运行环境

2. **安装系统依赖**
   - wget, gnupg, unzip, curl
   - 约 50MB

3. **安装 Chrome**
   - Google Chrome Stable
   - 约 200MB

4. **安装 Python 依赖**
   - Selenium, BeautifulSoup, Jinja2 等
   - 约 100MB

5. **复制应用代码**
   - 源代码和模板
   - 约 1MB

**总镜像大小：** 约 500-600MB

#### 步骤 5: 启动容器

```bash
# 启动容器（后台运行）
docker-compose up -d

# 查看容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f
```

**预期输出：**

```
Creating network "github-trending_default" with the default driver
Creating github_trending_scraper ... done
```

#### 步骤 6: 验证部署

```bash
# 检查容器是否运行
docker ps | grep github_trending

# 查看日志
docker-compose logs --tail=50

# 进入容器（调试用）
docker-compose exec github-trending-scraper bash
```

#### 步骤 7: 手动触发测试

```bash
# 手动执行一次任务
docker-compose exec github-trending-scraper python -m src.scheduler --once

# 观察日志输出
docker-compose logs -f
```

**预期日志输出：**

```
2024-03-15 09:00:00 | INFO | Starting trending scraping job for 2024-03-15
2024-03-15 09:00:01 | INFO | Step 1: Scraping GitHub trending pages
2024-03-15 09:00:30 | INFO | Successfully scraped daily trending
2024-03-15 09:00:31 | INFO | Step 2: Parsing HTML content
2024-03-15 09:00:35 | INFO | Parsed 25 projects from daily
2024-03-15 09:00:36 | INFO | Step 3: Analyzing projects and adding highlights
2024-03-15 09:00:38 | INFO | Analyzed 25 projects for daily
2024-03-15 09:00:39 | INFO | Step 4: Saving data to database
2024-03-15 09:00:40 | INFO | Saved 25 projects for daily
2024-03-15 09:00:41 | INFO | Step 5: Generating summaries
2024-03-15 09:00:42 | INFO | Step 6: Generating HTML report
2024-03-15 09:00:43 | INFO | Report generated: /tmp/reports/github-trending-2024-03-15.html
2024-03-15 09:00:44 | INFO | Step 7: Uploading report to OSS
2024-03-15 09:00:45 | INFO | Report uploaded to OSS: https://xxx.oss-cn-hangzhou.aliyuncs.com/github-trending/github-trending-2024-03-15.html
2024-03-15 09:00:46 | INFO | Step 8: Sending DingTalk notification
2024-03-15 09:00:47 | INFO | DingTalk notification sent successfully
2024-03-15 09:00:48 | INFO | Step 9: Saving report metadata
2024-03-15 09:00:49 | INFO | Job completed successfully for 2024-03-15
```

---

## 配置详解

### 环境变量说明

| 变量名 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| OSS_ACCESS_KEY_ID | 是 | 阿里云 OSS AccessKey ID | LTAI5tXXXXXXXXXXXXXX |
| OSS_ACCESS_KEY_SECRET | 是 | 阿里云 OSS AccessKey Secret | xxxxxxxxxxxxxxxx |
| OSS_BUCKET_NAME | 是 | OSS Bucket 名称 | github-trending-reports |
| DINGTALK_WEBHOOK_URL | 是 | 钉钉机器人 Webhook URL | https://oapi.dingtalk.com/robot/send?access_token=xxx |
| DINGTALK_SECRET | 否 | 钉钉机器人加签密钥 | SECxxxxxxxxxxxxxxxx |
| TZ | 否 | 时区设置 | Asia/Shanghai |

### config.yaml 配置项

```yaml
# 爬虫配置
scraper:
  headless: true          # 是否使用 headless 模式
  timeout: 30             # 页面加载超时时间（秒）
  retry_times: 3          # 重试次数
  retry_backoff: [1, 2, 4]  # 重试间隔（秒）
  user_agents:            # User-Agent 列表（随机选择）
    - "Mozilla/5.0 ..."

# 数据库配置
database:
  path: "/data/github_trending.db"  # 数据库文件路径

# OSS 配置
oss:
  access_key_id: ${OSS_ACCESS_KEY_ID}      # 从环境变量读取
  access_key_secret: ${OSS_ACCESS_KEY_SECRET}
  bucket_name: ${OSS_BUCKET_NAME}
  endpoint: "oss-cn-hangzhou.aliyuncs.com"  # OSS 区域节点
  path_prefix: "github-trending/"           # 文件路径前缀

# 钉钉配置
dingtalk:
  webhook_url: ${DINGTALK_WEBHOOK_URL}
  secret: ${DINGTALK_SECRET}

# 调度配置
scheduler:
  run_time: "09:00"                # 每天执行时间（24小时制）
  timezone: "Asia/Shanghai"        # 时区

# 日志配置
logging:
  level: "INFO"                    # 日志级别
  file: "/app/logs/scraper.log"   # 日志文件路径
  max_bytes: 10485760              # 单个日志文件最大大小（10MB）
  backup_count: 5                  # 保留的日志文件数量
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
```

---

## 运维管理

### 日常运维命令

```bash
# 查看容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 查看最近 100 行日志
docker-compose logs --tail=100

# 重启容器
docker-compose restart

# 停止容器
docker-compose stop

# 启动容器
docker-compose start

# 停止并删除容器
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

### 数据管理

#### 查看数据库

```bash
# 进入容器
docker-compose exec github-trending-scraper bash

# 使用 sqlite3 查看数据库
sqlite3 /data/github_trending.db

# 查看表结构
.schema

# 查询项目数量
SELECT COUNT(*) FROM projects;

# 查询最近的 trending 记录
SELECT * FROM trending_records ORDER BY created_at DESC LIMIT 10;

# 退出
.quit
exit
```

#### 备份数据库

```bash
# 备份数据库文件
cp data/github_trending.db data/github_trending.db.backup.$(date +%Y%m%d)

# 或使用 docker cp
docker cp github_trending_scraper:/data/github_trending.db ./backup/
```

#### 恢复数据库

```bash
# 停止容器
docker-compose stop

# 恢复数据库文件
cp backup/github_trending.db data/

# 启动容器
docker-compose start
```

### 日志管理

#### 查看日志

```bash
# 查看容器日志
docker-compose logs -f

# 查看应用日志文件
tail -f logs/scraper.log

# 查看特定日期的日志
grep "2024-03-15" logs/scraper.log

# 查看错误日志
grep "ERROR" logs/scraper.log
```

#### 日志轮转

日志文件会自动轮转（根据 config.yaml 配置）：
- 单个文件最大 10MB
- 保留最近 5 个文件
- 自动压缩旧文件

手动清理日志：

```bash
# 删除旧日志
rm logs/scraper.log.*

# 或保留最近 7 天的日志
find logs/ -name "*.log.*" -mtime +7 -delete
```

### 更新部署

#### 更新代码

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 重启容器
docker-compose up -d
```

#### 更新配置

```bash
# 修改配置文件
vim config.yaml

# 重启容器使配置生效
docker-compose restart
```

#### 更新环境变量

```bash
# 修改环境变量
vim .env

# 重新创建容器
docker-compose up -d --force-recreate
```

### 监控和告警

#### 容器监控

```bash
# 查看容器资源使用情况
docker stats github_trending_scraper

# 查看容器详细信息
docker inspect github_trending_scraper
```

#### 设置告警

可以使用以下工具监控容器状态：

1. **Docker 自带健康检查**
   - 已在 docker-compose.yml 中配置
   - 自动检测容器健康状态

2. **Prometheus + Grafana**
   - 监控容器指标
   - 可视化展示

3. **钉钉告警**
   - 任务失败时自动发送钉钉通知
   - 已在代码中实现

---

## 故障排查

### 常见问题

#### 1. 容器无法启动

**症状：**
```bash
docker-compose ps
# 显示容器状态为 Exit 或 Restarting
```

**排查步骤：**

```bash
# 查看容器日志
docker-compose logs

# 检查配置文件
cat config.yaml

# 检查环境变量
cat .env

# 验证 Docker 镜像
docker images | grep github-trending
```

**常见原因：**
- 配置文件格式错误
- 环境变量缺失
- 端口冲突
- 权限问题

#### 2. Chrome 驱动问题

**症状：**
```
selenium.common.exceptions.WebDriverException: Message: unknown error: Chrome failed to start
```

**解决方案：**

```bash
# 进入容器检查 Chrome
docker-compose exec github-trending-scraper bash
google-chrome --version

# 如果 Chrome 未安装，重新构建镜像
docker-compose build --no-cache
```

#### 3. OSS 上传失败

**症状：**
```
OSSException: Failed to upload to OSS
```

**排查步骤：**

```bash
# 检查 OSS 配置
echo $OSS_ACCESS_KEY_ID
echo $OSS_BUCKET_NAME

# 测试 OSS 连接
docker-compose exec github-trending-scraper python -c "
from src.oss_uploader import OSSUploader
uploader = OSSUploader(
    access_key_id='$OSS_ACCESS_KEY_ID',
    access_key_secret='$OSS_ACCESS_KEY_SECRET',
    bucket_name='$OSS_BUCKET_NAME',
    endpoint='oss-cn-hangzhou.aliyuncs.com'
)
print('OSS connection successful')
"
```

**常见原因：**
- AccessKey 错误
- Bucket 不存在
- 网络连接问题
- 权限不足

#### 4. 钉钉通知失败

**症状：**
```
DingTalkException: Failed to send message
```

**排查步骤：**

```bash
# 检查 Webhook URL
echo $DINGTALK_WEBHOOK_URL

# 测试钉钉连接
curl -X POST "$DINGTALK_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{"msgtype":"text","text":{"content":"测试消息"}}'
```

**常见原因：**
- Webhook URL 错误
- 签名密钥错误
- 机器人被限流
- 网络连接问题

#### 5. 数据库锁定

**症状：**
```
DatabaseException: database is locked
```

**解决方案：**

```bash
# 停止容器
docker-compose stop

# 检查数据库文件
ls -lh data/github_trending.db

# 删除锁文件（如果存在）
rm data/github_trending.db-journal

# 启动容器
docker-compose start
```

#### 6. 内存不足

**症状：**
```
Killed
或
MemoryError
```

**解决方案：**

```bash
# 增加 Docker 内存限制
# 编辑 docker-compose.yml
vim docker-compose.yml

# 修改内存限制
deploy:
  resources:
    limits:
      memory: 2G  # 增加到 2GB

# 重启容器
docker-compose up -d --force-recreate
```

### 调试技巧

#### 1. 进入容器调试

```bash
# 进入容器
docker-compose exec github-trending-scraper bash

# 手动运行 Python 脚本
python -m src.scheduler --once

# 测试单个模块
python -c "from src.scraper import GitHubTrendingScraper; print('OK')"
```

#### 2. 查看详细日志

```bash
# 修改日志级别为 DEBUG
vim config.yaml
# 将 logging.level 改为 "DEBUG"

# 重启容器
docker-compose restart

# 查看详细日志
docker-compose logs -f
```

#### 3. 测试网络连接

```bash
# 进入容器
docker-compose exec github-trending-scraper bash

# 测试 GitHub 连接
curl -I https://github.com/trending

# 测试 OSS 连接
curl -I https://oss-cn-hangzhou.aliyuncs.com

# 测试钉钉连接
curl -I https://oapi.dingtalk.com
```

### 性能优化

#### 1. 减少镜像大小

```dockerfile
# 使用多阶段构建
FROM python:3.11-slim as builder
# ... 构建步骤

FROM python:3.11-slim
COPY --from=builder /app /app
```

#### 2. 优化爬取速度

```yaml
# config.yaml
scraper:
  timeout: 20  # 减少超时时间
  retry_times: 2  # 减少重试次数
```

#### 3. 数据库优化

```bash
# 定期清理旧数据
docker-compose exec github-trending-scraper python -c "
from src.database import Database
db = Database('/data/github_trending.db')
# 删除 90 天前的数据
# db.cleanup_old_records(days=90)
"
```

---

## 安全建议

### 1. 保护敏感信息

```bash
# 设置 .env 文件权限
chmod 600 .env

# 不要将 .env 提交到 Git
echo ".env" >> .gitignore

# 使用 Docker secrets（生产环境）
docker secret create oss_key /path/to/key
```

### 2. 网络安全

```yaml
# docker-compose.yml
services:
  github-trending-scraper:
    networks:
      - internal  # 使用内部网络

networks:
  internal:
    driver: bridge
```

### 3. 定期更新

```bash
# 更新基础镜像
docker pull python:3.11-slim

# 更新依赖
pip list --outdated
pip install --upgrade <package>

# 重新构建镜像
docker-compose build --no-cache
```

---

## 附录

### A. 完整的部署检查清单

- [ ] 服务器满足最低配置要求
- [ ] Docker 和 Docker Compose 已安装
- [ ] 阿里云 OSS Bucket 已创建
- [ ] OSS AccessKey 已获取
- [ ] 钉钉机器人已配置
- [ ] 项目代码已克隆
- [ ] .env 文件已配置
- [ ] config.yaml 已根据需求修改
- [ ] Docker 镜像已构建
- [ ] 容器已启动
- [ ] 手动测试已通过
- [ ] 日志输出正常
- [ ] 钉钉通知已收到
- [ ] 数据库文件已生成
- [ ] OSS 文件已上传

### B. 常用命令速查

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重启
docker-compose restart

# 查看日志
docker-compose logs -f

# 手动执行
docker-compose exec github-trending-scraper python -m src.scheduler --once

# 进入容器
docker-compose exec github-trending-scraper bash

# 查看数据库
docker-compose exec github-trending-scraper sqlite3 /data/github_trending.db

# 备份数据
docker cp github_trending_scraper:/data/github_trending.db ./backup/

# 查看资源使用
docker stats github_trending_scraper
```

### C. 相关资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [阿里云 OSS 文档](https://help.aliyun.com/product/31815.html)
- [钉钉机器人文档](https://open.dingtalk.com/document/robots/custom-robot-access)
- [Selenium 文档](https://www.selenium.dev/documentation/)
- [APScheduler 文档](https://apscheduler.readthedocs.io/)

---

## 总结

本文档详细介绍了 GitHub Trending 爬虫系统的完整部署流程，包括：

1. **系统架构**：了解各个组件的作用和交互方式
2. **工作流程**：掌握完整的数据处理流程
3. **部署准备**：准备必要的服务和配置
4. **Docker 部署**：逐步部署和验证系统
5. **配置管理**：理解各项配置的含义
6. **运维管理**：日常维护和监控
7. **故障排查**：快速定位和解决问题

通过本文档，你应该能够：
- 独立完成系统的部署
- 理解系统的工作原理
- 进行日常的运维管理
- 快速排查和解决问题

如有任何问题，请参考相关资源或提交 Issue。

---

**文档版本：** 1.0  
**最后更新：** 2024-03-15  
**维护者：** GitHub Trending Team

