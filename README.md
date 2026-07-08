# 数据库设计与部署 AI Agent

本项目围绕以下两项核心内容整理与交付：

1. AI 根据用户需求生成并部署一个数据库。
2. 编写一个 `SKILL`，覆盖 ERP/CRM 数据模型调研、Docker 部署数据库、根据 ER 模型建表，以及根据模型生成插入测试数据的代码。

本项目实现了一个可运行的 Database Design Agent，能够根据自然语言生成数据库设计结果，并在确认后部署到 MySQL 8.0。`seed.py` 与 `app/seed_service.py` 用于生成符合约束关系的测试数据。

## 项目结构

```text
数据库设计与部署AI Agent/
├── app/
│   ├── __init__.py
│   ├── agent.py                  # Agent CLI 主逻辑
│   ├── config.py                 # 环境变量与配置加载
│   ├── db_executor.py            # MySQL 连接、等待和 SQL 执行
│   ├── init_db.py                # 容器启动时自动执行 schema.sql
│   ├── llm.py                    # DeepSeek API 封装
│   ├── seed_service.py           # 测试数据生成服务
│   └── sql_generator.py          # 数据库设计结果提取与 SQL 规则校验
├── docs/
│   ├── crm-er.md                 # CRM 数据模型调研（含 ER / 类图视角）
│   ├── erp-crm-er-diagram.md     # 融合模型 ER 图
│   └── erp-er.md                 # ERP 数据模型调研（含 ER / 类图视角）
├── tests/
│   └── test_sql_generator.py     # SQL 生成与规则校验测试
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── SKILL.md
├── agent.py
├── requirements.txt
├── schema.sql
└── seed.py
```

## 功能对应关系

### 1. AI 根据用户需求生成并部署数据库

- 命令行入口：`agent.py`
- 核心模块：`app/agent.py`、`app/llm.py`、`app/sql_generator.py`、`app/db_executor.py`
- 运行方式：用户输入自然语言需求后，系统生成摘要、ER 图和 SQL；使用 `--dry-run` 时只预览，不执行；默认模式下输入 `yes` 后执行到 MySQL

### 2. 编写一个 SKILL

- 技能文件：`SKILL.md`
- 技能内容：
  - 参考 ERP、CRM 常见数据模型进行数据库抽象
  - 输出 ER 结构摘要并生成 MySQL 8.0 DDL
  - 结合 Docker 中的 MySQL 环境完成部署
  - 配合 `seed.py` / `app/seed_service.py` 生成符合外键约束的测试数据插入代码

## 快速开始

### 1. 配置环境变量

复制 `.env.example` 为 `.env`，填写数据库与 DeepSeek 参数：

```bash
cp .env.example .env
```

### 2. 一键启动并自动建表

```bash
docker compose up -d --build
```

说明：

- `db` 服务启动 MySQL 8.0
- `app` 服务在启动时会自动执行 `python -m app.init_db`
- `schema.sql` 使用 `CREATE TABLE IF NOT EXISTS`，因此重复执行不会重复建表

如果你已经保留了旧的数据卷并想重新初始化，可先清理容器与数据卷：

```bash
docker compose down -v
docker compose up -d --build
```

### 3. 插入测试数据

```bash
docker compose exec app python seed.py
```

### 4. 使用 AI Agent 生成并部署数据库

```bash
# 仅生成结果，不执行数据库部署
docker compose exec app python agent.py "设计一个图书馆借阅数据库" --dry-run

# 生成结果并在确认后执行
docker compose exec app python agent.py "设计一个电商订单数据库"
```

## 主要交付物

- `docs/erp-er.md`：ERP 数据模型调研
- `docs/crm-er.md`：CRM 数据模型调研
- `docs/erp-crm-er-diagram.md`：融合模型 ER 图
- `schema.sql`：MySQL 8.0 建表脚本
- `seed.py`、`app/seed_service.py`：测试数据生成代码
- `SKILL.md`：技能提示词与执行规则
- `README.md`：项目说明与使用方法
- `.env.example`、`docker-compose.yml`、`Dockerfile`：环境配置与容器部署文件

## 关键实现说明

### Docker 自动建表链路

- `docker-compose.yml` 中 `app` 服务依赖 `db` 健康检查
- `app` 启动后自动执行 `app/init_db.py`
- `app/init_db.py` 会等待 MySQL 就绪，再读取 `schema.sql` 并执行

### SQL 规则校验

`app/sql_generator.py` 在调用模型后，会对每个 `CREATE TABLE` 语句做结构化校验，主要检查：

- 是否使用 `CREATE TABLE IF NOT EXISTS`
- 是否设置 `ENGINE=InnoDB`
- 是否设置 `DEFAULT CHARSET=utf8mb4`
- 主键是否为单列 `BIGINT UNSIGNED NOT NULL AUTO_INCREMENT`
- 是否包含 `created_at`、`updated_at`
- 外键字段是否显式建立索引

### 测试数据生成

`seed.py` 通过 `Faker` 生成客户、联系人、产品、库存、订单、供应商等数据，并按照先父表后子表的顺序插入，保证外键约束成立。

## 技术栈

- Python 3.11
- MySQL 8.0
- Docker Compose
- DeepSeek API
- requests
- PyMySQL
- python-dotenv
- Faker

