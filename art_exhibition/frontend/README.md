# 投稿助手前端（Next.js）

基于 Next.js App Router + TypeScript strict + Tailwind CSS 4 的正式前端，替换原 Jinja2 两页。

## 页面

- `/s/[token]`：投递页（4 步向导：个人资料 → 简历 → 作品 → 确认提交 → 核验报告）
- `/admin`：后台页（登录 / 建活动 / 总览 / 明细筛选 / CSV 导出 / 工作简报 / 智能问答）
- `/`：重定向到 `/admin`

## 启动

先确保后端已运行在 `http://127.0.0.1:8000`（见上级 `../README.md`）。

```bash
cd frontend
npm install

# 开发模式
npm run dev          # http://localhost:3000

# 生产构建 + 预览
npm run build
BACKEND_URL=http://127.0.0.1:8000 npm run start
```

> 注意：`next.config.ts` 中 rewrites 的 `BACKEND_URL` 在 **build 时**固化，构建前请注入正确后端地址。

## 质量检查

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

## 结构

```
src/
├── app/
│   ├── admin/page.tsx           # 后台页（客户端）
│   ├── s/[token]/page.tsx       # 投递页路由（服务端，取 params）
│   ├── s/[token]/submission-wizard.tsx
│   └── globals.css              # Tailwind + 设计 token
├── components/ui/               # Button / Input / Field / Card / Alert / Spinner
├── components/__tests__/        # 组件测试
└── lib/                         # api.ts（集中式 API 层）、types.ts
```

## 设计 token（中性方案，可在 globals.css 调整）

主色靛蓝 `#4f46e5`，中性灰底 `#fafafa`，系统中文黑体（PingFang SC / Microsoft YaHei / Noto Sans CJK SC）fallback。
