# 第 1 阶段技术开发文档｜MVP 核心链路

> 配套文档：`prd-art-exhibition.md`（已定稿）、`AI产品Vibe Coding通用技术栈手册(1).md`（V2.1）、`../docs/技术适配声明.md`
> 本文档只覆盖第 1 阶段（PRD Step 5 代码生成）。

## 一、阶段目标
- **交付范围**：`art_exhibition/` 应用，跑通「建活动 → 链接直投 → 分步投稿 → AI 核验 → 后台查数/筛选/导出 → 工作简报 → 智能问答」全链路。
- **阶段产物**：可运行的 FastAPI 应用 + 投递页/后台页 + 种子数据 + pytest 测试 + 本 README。
- **验收标准**：作者能通过链接完成 4 步投稿并看到核验报告；管理员能建活动、看总览、筛作品、导 CSV、生成简报。
- **明确不做**（后续阶段）：正式前端（Next.js）、Alembic 迁移、SSE/任务队列、多管理员权限体系、补件通知（PRD 已取消）。
- **本阶段主链路片段**：投稿提交 → s04 核验钩子（服务内触发）→ `check_submission` 产出报告回显 → 后台 `campaign_overview`/`list_works`/CSV → `generate_brief`。

## 二、技术适配摘要
- 开发路径：**后端先行**（表单提交/后台导出类）。
- 采用默认：Python 3.11、FastAPI、Pydantic、pytest、OpenAI 兼容接口、Jinja2 模板直出两页。
- 启用按需模块：SQLite + SQLAlchemy（多实体关系/筛选统计/`run_sql`）、文件上传处理、Pillow（图片校验）。
- 偏离/暂缓：PRD 草图 Flask → FastAPI；Alembic/SSE/任务队列/Next.js 暂缓（见技术适配声明）。

## 三、技术栈与模型
- FastAPI + Uvicorn + SQLAlchemy(SQLite) + Jinja2 + Pillow + openai SDK + pytest。
- 模型：默认 **DeepSeek deepseek-chat**（`MODEL_BASE_URL=https://api.deepseek.com/v1`），可切 Qwen/GLM。

## 四、环境与配置
- `.env.example`：`MODEL_BASE_URL / MODEL_API_KEY / MODEL_NAME / ADMIN_KEY / DATABASE_URL / UPLOAD_DIR / RESUME_MAX_MB / HOST / PORT`。
- 需用户提供：`MODEL_API_KEY`（验收前提供）、`ADMIN_KEY`（自行修改）。
- 端口：8000（5000 被 macOS 控制中心占用）。

## 五、项目结构
```
art_exhibition/
├── app.py / api.py / agent.py / checks.py / tools.py / services.py
├── config.py / db.py / models.py / schemas.py
├── templates/{submit.html, admin.html}
├── tests/{conftest.py, test_checks.py, test_tools.py, test_api.py}
├── seed.py / requirements.txt / .env.example / README.md
└── data/（gitignore：app.db + uploads）
```

## 六、数据、资产与状态
- 持久化：SQLite（`data/app.db`），schema 版本标记 `schema_version=1`（暂缓 Alembic）。
- 表：`campaigns / applicants / works / check_reports`（字段见 PRD）。
- 资产：`data/uploads/`，UUID 重命名；图片校验（PIL），简历仅 pdf/docx ≤20MB。
- 状态机：`applicants.status`：`submitted → checked`（提交即核验，落库后才核验，可恢复）。

## 七、API / 工具设计
- 公开：`GET /api/v1/campaigns/{token}`、`POST /api/v1/campaigns/{token}/submissions`（multipart，works_json + images[]）。
- 管理员：`POST /admin/login|logout`、`GET/POST /admin/campaigns`、`GET /admin/campaigns/{id}/overview|works|export.csv`、`POST /admin/campaigns/{id}/brief|query`、`POST /admin/run_sql`。
- 工具：`check_submission`（确定性+模型合并）、`run_sql`（仅单条 SELECT/WITH，≤200 行）、`campaign_overview`、`list_works`（medium/school 筛选）。
- 智能问答：单步工具分发（模型选 tool+args → 确定性执行 → 模型合成答案），白名单内、只读、失败降级。
- 本阶段无 SSE（核验/简报为同步短请求）。

## 八、Prompt 设计
- `CHECK_SYSTEM`：输出 `{"missing","format_issues","notes"}`，只输出 JSON；宽容解析（去代码块围栏、截取首 JSON）。
- `BRIEF_SYSTEM`：四栏目简报（艺术家信息/学校分布/作品数量/作品种类）。
- `QUERY_SYSTEM`：从 overview/list_works/run_sql 三工具中选一并给参数。
- 解析：后端 `_extract_json` 宽容解析 + Pydantic `CheckReportOut` 强校验，失败走确定性降级。

## 九、验收界面
- 投递页（`/s/{token}`）：4 步向导 + 核验报告回显。
- 后台页（`/admin`）：登录 → 建活动 → 列表 → 总览/筛选/导出/简报/问答。
- 两页为产品实际界面（Jinja2 直出），非临时壳。

## 十、测试要求
- **第一层 mock 测试（必跑，离线）**：
  - `test_checks.py`：缺失字段、邮箱或微信二选一、坏扩展名/超限/无法解析判为格式问题而非缺失。
  - `test_tools.py`：`run_sql` SELECT 通过、写库/多语句/禁关键字拒绝、总览统计、作品筛选。
  - `test_api.py`：建活动→投稿→报告回显、空姓名 400、未登录 401、坏扩展名 400、总览/导出/简报、`run_sql` 端点只读。
- **第二层真实冒烟（验收前必做，无 Key 明确待验）**：真实投稿核验、简报四栏目、智能问答，记录模型/耗时/成本/结果。

## 十一、验收清单（产品经理照做）
- [ ] 启动服务，打开后台 `/admin`，用 `.env` 的 ADMIN_KEY 登录。
- [ ] 创建活动，复制投递链接，在新窗口打开完成 4 步投稿，看到核验报告。
- [ ] 后台看到该投稿的艺术家/作品统计与明细，点「导出 CSV」能下载。
- [ ] 点「生成工作简报」，看到含四栏目的简报（无 Key 时为确定性版）。
- [ ] （有 Key）测试「智能问答」返回合理回答。

## 十二、风险与待确认项
- 模型输出质量需真实 Key 验证；数量/内容约束瑕疵由产品经理判断容忍度。
- 管理员会话为简单 Cookie 方案（单管理员本地场景），生产需升级。
- 待产品经理决定：无（模型厂商已按 DeepSeek 默认，可切换）。

## 十三、交接给下一阶段
- 已就绪：全链路 API、SQLite 数据模型、核验/简报/问答、两页界面、种子数据。
- 下一阶段复用：API 契约与工具层，可直接接正式前端或增加批量核验/离线简报等二期能力。
