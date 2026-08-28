# 高校艺术赛事投稿助手

面向高校画展 / 毕业展 / 艺术赛事的一站式征集平台：链接直投 + 后台管理 + AI 核验/简报。

## 快速开始

```bash
cd art_exhibition

# 1. 创建虚拟环境（本机推荐 Python 3.11）
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env：填入 MODEL_API_KEY，并修改 ADMIN_KEY

# 4. （可选）加载种子数据，便于演示
python seed.py

# 5. 启动
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

- 投递页（作者）：`http://127.0.0.1:8000/s/<link_token>`
- 后台页（管理员）：`http://127.0.0.1:8000/admin`（登录密钥 = `.env` 中的 `ADMIN_KEY`）
- 接口文档：`http://127.0.0.1:8000/docs`

> 端口 5000 被 macOS 控制中心占用，默认使用 8000。

## 运行测试（第一层 mock 自动化测试）

```bash
cd art_exhibition
source .venv/bin/activate
python -m pytest -q
```

## 真实模型冒烟（第二层，验收前必做）

1. 在 `.env` 填入真实 `MODEL_API_KEY`（DeepSeek/Qwen/GLM，OpenAI 兼容）。
2. 启动服务后，创建活动并通过投递页完成一次真实投稿，核对：
   - 投稿提交后能返回 AI 核验报告；
   - 后台「生成工作简报」返回四栏目简报；
   - 后台「智能问答」能选工具并给出回答。
3. 无 Key 时以上能力自动降级为确定性结果，**不以 mock 结果冒充真实验证**。

## 目录说明

| 文件 | 职责 |
| --- | --- |
| `app.py` | FastAPI 入口：页面路由 + API 挂载 + 文件服务 |
| `api.py` | `/api/v1` 路由：投稿侧 + 管理员侧 |
| `agent.py` | 国内模型 Agent（OpenAI 兼容）+ 宽容 JSON 解析 |
| `checks.py` | 核验：确定性检查 + 模型语义核验合并 |
| `tools.py` | 确定性工具：`run_sql`（只读）/ `campaign_overview` / `list_works` |
| `services.py` | 业务编排：建活动、投稿、导出、简报、智能问答 |
| `models.py` / `db.py` / `schemas.py` / `config.py` | 数据模型 / SQLite / 校验 / 配置 |
| `templates/` | 投递页 + 后台页（Jinja2） |
| `seed.py` | 种子数据 |

## 安全说明

- 密钥仅存 `.env`（已 gitignore），不进代码、前端、日志。
- 后台用管理员密钥 + HttpOnly Cookie 会话保护。
- 上传文件：扩展名白名单 + 大小限制 + 文件名清洗（UUID 重命名）+ 图片内容校验；损坏图片标「无法解析」而不误判缺失。
- `run_sql` 仅允许单条 SELECT/WITH，≤200 行，防写库。
- 错误响应统一结构，不泄露堆栈。

## 当前阶段限制（见 docs/阶段文档-step5.md）

- 本阶段为 MVP：SQLite 单进程；Alembic / SSE / 任务队列暂缓。
- 正式前端（Next.js）暂缓，投递/后台两页由 Jinja2 直出。
- 管理员会话为简单 Cookie 方案，无 CSRF token（单管理员本地使用场景）。
