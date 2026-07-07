# 数据库设计与部署 AI Agent

用于完成数据库设计课程作业的项目，包含基础任务调研、ER 图设计、建表 SQL、种子数据生成，以及 AI 辅助数据库设计功能。

## 项目结构

```text
数据库设计与部署AI Agent/
├── app/                          # 应用模块（Agent 拆分实现）
│   ├── __init__.py
│   ├── config.py                 # 配置管理（环境变量加载）
│   ├── llm.py                    # DeepSeek API 客户端封装
│   ├── sql_generator.py          # ER 图与 SQL 生成器
│   ├── db_executor.py            # 数据库执行器
│   ├── seed_service.py           # 种子数据生成服务
│   └── agent.py                  # Agent CLI 入口逻辑
├── docs/                         # 调研文档与 ER 图
│   ├── erp-er.md                 # ERP 系统数据模型调研
│   ├── crm-er.md                 # CRM 系统数据模型调研
│   └── erp-crm-er-diagram.md     # ERP + CRM 融合核心业务数据模型
├── .env.example                  # 环境变量模板
├── .gitignore                    # Git 忽略文件
├── Dockerfile                    # 应用容器镜像构建
├── docker-compose.yml            # 容器编排配置
├── requirements.txt              # Python 依赖
├── SKILL.md                      # AI Agent 提示词约束
├── schema.sql                    # 融合 ERP + CRM 的建表 SQL
├── seed.py                       # 种子数据脚本入口
└── agent.py                      # Agent CLI 入口
```

## 快速开始

### 前置条件

- Docker & Docker Compose
- DeepSeek API Key（用于 AI 设计功能）

### 1. 配置环境变量

复制 `.env.example` 为 `.env`，并根据需要修改配置：

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
```

### 2. 启动服务

```bash
docker-compose up -d --build
```

### 3. 执行建表 SQL

```bash
# 进入容器执行 schema.sql
docker-compose exec app python -c "
from app.config import Settings
from app.db_executor import DatabaseExecutor
settings = Settings.from_env()
executor = DatabaseExecutor(settings)
executor.wait_until_ready()
with open('schema.sql', 'r', encoding='utf-8') as f:
    sql = f.read()
executor.execute_sql(sql)
print('建表完成。')
"
```

### 4. 插入种子数据

```bash
docker-compose exec app python seed.py
```

## 使用说明

### Database Design Agent

通过自然语言描述数据库需求，自动生成 ER 图和 SQL：

```bash
# 仅生成 SQL 并打印（dry run）
docker-compose exec app python agent.py "设计一个电商订单管理系统" --dry-run

# 生成并执行部署（需要确认）
docker-compose exec app python agent.py "设计一个图书馆管理系统"
```

参数说明：

- `--dry-run`：仅生成 SQL，不执行到数据库
- `--output-dir <dir>`：指定生成结果保存目录，默认 `generated/`

### 访问数据库

通过任意 MySQL 客户端连接到 `localhost:3306`，使用 `.env` 中配置的账号密码。

## 核心功能

### 第一阶段：基础任务（课程作业核心要求）

1. **ERP 数据模型调研**：见 `docs/erp-er.md`
2. **CRM 数据模型调研**：见 `docs/crm-er.md`
3. **融合 ERP + CRM 核心业务数据模型**：见 `docs/erp-crm-er-diagram.md`
4. **MySQL 8.0 建表 SQL**：见 `schema.sql`，满足以下规范：
   - 使用 InnoDB 引擎
   - 字符集 utf8mb4
   - 统一使用 `CREATE TABLE IF NOT EXISTS`
   - 主键统一 `BIGINT UNSIGNED NOT NULL AUTO_INCREMENT`
   - 统一包含 `created_at`、`updated_at` 时间字段
   - 所有外键建立索引
5. **Docker 部署**：通过 `docker-compose` 一键启动 MySQL 8.0
6. **种子数据生成**：使用 `seed.py` 自动生成符合外键约束的模拟数据

### 第二阶段：AI 辅助数据库设计（扩展功能）

- **Database Design Agent**：通过 DeepSeek API 实现自然语言到 SQL 的自动化生成
- **输出约束**：通过 `SKILL.md` 保证生成 SQL 严格符合要求
- **安全保障**：执行前需要手动确认，支持 `--dry-run` 预览

## 开发环境

### 本地运行

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置 .env（将 MYSQL_HOST 改为 localhost）
```

## 技术栈

- **Python 3.11+**
- **MySQL 8.0**
- **Docker & Docker Compose**
- **DeepSeek API**（通过 requests 直接调用）
- **PyMySQL**（数据库驱动）
- **Faker**（种子数据生成）

## LICENSE

本项目仅供学习使用。
