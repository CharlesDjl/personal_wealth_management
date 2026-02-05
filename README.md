# 个人财富管理系统

全栈个人财富管理 Web 应用，帮助您管理资产、跟踪投资组合，并提供智能的再平衡建议。

## 技术栈

### 前端
- React 18.3 + TypeScript 5.8
- Vite 6.3 (构建工具)
- Tailwind CSS (样式框架)
- React Router 7.3 (路由)
- Zustand (状态管理)
- Chart.js (数据可视化)
- Supabase Auth (身份认证)

### 后端
- Python FastAPI
- Uvicorn (ASGI 服务器)
- Supabase (数据库)
- Pydantic (数据验证)

### 数据服务
- Tushare (股票行情数据)
- 新浪财经 API (实时价格)
- 阿里云 DashScope (LLM 截图解析)

### 部署
- Vercel (前端 + Python Serverless)

## 功能特性

| 功能 | 描述 |
|------|------|
| 用户认证 | 基于 Supabase 的邮箱密码登录 |
| 资产管理 | 增删改查资产，支持批量操作 |
| 截图导入 | 上传资产截图，LLM 自动解析并导入 |
| 实时行情 | 集成 Tushare 和新浪财经获取中国市场数据 |
| 组合概览 | 按类别统计总资产，可视化展示 |
| 再平衡建议 | 基于"永久组合"策略（25% 现金/股票/债券/黄金） |
| 日报 | 每日报告与健康评分 |

## 项目结构

```
personal_wealth_management/
├── api/                      # FastAPI 后端
│   ├── main.py              # 应用入口
│   ├── database.py          # Supabase 客户端
│   ├── models/schemas.py    # Pydantic 数据模型
│   ├── routers/             # API 路由
│   └── services/            # 业务服务
├── src/                     # React 前端
│   ├── main.tsx            # React 入口
│   ├── App.tsx             # 主应用组件
│   ├── api/client.ts       # Axios API 客户端
│   ├── components/         # UI 组件
│   ├── context/            # React Context
│   ├── pages/               # 页面组件
│   └── types/               # TypeScript 类型
├── public/                   # 静态资源
├── start.sh                 # 一键启动脚本
├── .env.example             # 环境变量模板
└── README.md                # 项目文档
```

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- npm 或 pnpm

### 1. 克隆项目

```bash
git clone <repository-url>
cd personal_wealth_management
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入以下配置：

```env
# Supabase 配置 (必需)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Tushare 配置 (用于获取股票行情数据)
TUSHARE_TOKEN=your-tushare-token

# DashScope 配置 (用于 LLM 解析资产截图)
DASHSCOPE_API_KEY=your-dashscope-api-key

# 前端环境变量 (Vite 使用)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### 3. 一键启动

```bash
./start.sh
```

启动脚本会自动：
- 创建 Python 虚拟环境并安装依赖
- 安装前端 npm 依赖
- 启动后端服务 (http://127.0.0.1:8000)
- 启动前端开发服务器 (http://localhost:5173)

### 4. 访问应用

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost:5173 |
| 后端 API | http://127.0.0.1:8000 |
| API 文档 | http://127.0.0.1:8000/docs |

## 手动启动

如需分别启动前后端：

### 后端

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/assets` | GET | 获取所有资产 |
| `/api/assets` | POST | 创建资产 |
| `/api/assets/{id}` | GET | 获取单个资产 |
| `/api/assets/{id}` | PUT | 更新资产 |
| `/api/assets/{id}` | DELETE | 删除资产 |
| `/api/assets/import-screenshot` | POST | 截图导入 |
| `/api/assets/overview` | GET | 资产概览 |
| `/api/reports/daily` | GET | 每日报告 |
| `/api/rebalancing/suggestions` | GET | 再平衡建议 |

## 开发命令

```bash
# 前端
npm run dev      # 启动开发服务器
npm run build    # 构建生产版本
npm run preview  # 预览生产构建
npm run lint     # 运行 ESLint

# 后端
uvicorn api.main:app --reload  # 启动开发服务器
```

## 部署

项目已配置 Vercel 部署，推送代码到主分支即可自动部署。

## License

MIT
