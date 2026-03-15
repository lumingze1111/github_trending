# GitHub Trending 爬虫系统

自动化爬取 GitHub trending 页面，生成 HTML 报告并通过钉钉机器人发送的完整系统。

## 功能特性

- 🚀 每日自动爬取 GitHub trending（今日/本周/本月）
- 📊 智能分析项目亮点和趋势
- 📝 生成精美的 HTML 可视化报告
- ☁️ 自动上传到阿里云 OSS
- 📱 通过钉钉机器人推送通知
- 💾 SQLite 数据库存储历史数据
- 🐳 Docker 容器化部署

## 快速开始

### 前置要求

- Docker 和 Docker Compose
- 阿里云 OSS 账号
- 钉钉机器人 Webhook

### 1. 克隆项目

```bash
git clone <repository_url>
cd github-trending
```

### 2. 配置环境变量

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置：

```bash
# 阿里云 OSS
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_BUCKET_NAME=your_bucket_name

# 钉钉机器人
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=your_secret

# 时区
TZ=Asia/Shanghai
```

### 3. 启动服务

```bash
# 构建并启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 4. 手动触发一次测试

```bash
docker-compose exec github-trending-scraper python -m src.scheduler --once
```

## 项目结构

```
github-trending/
├── src/                      # 源代码
│   ├── scraper.py           # 爬虫模块
│   ├── parser.py            # HTML 解析
│   ├── analyzer.py          # 数据分析
│   ├── database.py          # 数据库操作
│   ├── report_generator.py # 报告生成
│   ├── oss_uploader.py      # OSS 上传
│   ├── dingtalk_bot.py      # 钉钉机器人
│   ├── scheduler.py         # 调度器
│   ├── config.py            # 配置管理
│   ├── exceptions.py        # 自定义异常
│   └── utils.py             # 工具函数
├── templates/               # HTML 模板
│   └── report.html         # 报告模板
├── tests/                   # 测试文件
├── data/                    # 数据目录（挂载）
├── logs/                    # 日志目录（挂载）
├── config.yaml             # 配置文件
├── requirements.txt        # Python 依赖
├── Dockerfile              # Docker 镜像定义
├── docker-compose.yml      # Docker Compose 配置
└── .env                    # 环境变量（需创建）
```

## 配置说明

### config.yaml

主配置文件，包含以下配置项：

- **scraper**: 爬虫配置（headless 模式、超时时间等）
- **database**: 数据库路径
- **oss**: OSS 配置（endpoint、路径前缀等）
- **dingtalk**: 钉钉配置
- **scheduler**: 调度配置（运行时间、时区）
- **logging**: 日志配置

详细配置说明请参考 `config.yaml` 文件中的注释。

## 开发指南

### 本地开发

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 运行测试：

```bash
pytest tests/ -v
```

3. 运行单次任务：

```bash
python -m src.scheduler --once
```

### 测试覆盖

项目包含完整的单元测试，覆盖所有核心模块：

```bash
# 运行所有测试
pytest tests/ -v

# 查看测试覆盖率
pytest tests/ --cov=src --cov-report=html
```

## 故障排查

### 常见问题

1. **Chrome 驱动问题**
   - 确保 Docker 镜像中已安装 Chrome
   - 检查 headless 模式是否启用

2. **OSS 上传失败**
   - 检查 OSS 凭证是否正确
   - 确认 Bucket 权限设置
   - 查看网络连接

3. **钉钉通知失败**
   - 验证 Webhook URL 是否正确
   - 检查签名密钥配置
   - 确认机器人未被限流

### 查看日志

```bash
# 查看容器日志
docker-compose logs -f

# 查看应用日志文件
tail -f logs/scraper.log
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
