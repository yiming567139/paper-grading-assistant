# 初中化学试卷 AI 自动批改

> 基于屏幕截图 + VLM 视觉大模型的全自动试卷批改工具。自动捕获评分界面截图，调用视觉语言模型评分，模拟鼠标点击完成打分操作。

---

## 目录

- [项目介绍](#项目介绍)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
  - [环境要求](#环境要求)
  - [后端启动](#后端启动)
  - [前端启动（开发模式）](#前端启动开发模式)
  - [数据库初始化](#数据库初始化)
- [配置说明](#配置说明)
  - [LLM / VLM 视觉模型](#llm--vlm-视觉模型)
  - [双评分模式（主 + 副 LLM）](#双评分模式主--副-llm)
  - [屏幕区域与按钮坐标](#屏幕区域与按钮坐标)
  - [工作流编排](#工作流编排)
- [API 概览](#api-概览)
- [前端页面](#前端页面)
- [测试](#测试)
- [开发指南](#开发指南)
- [常见问题](#常见问题)

---

## 项目介绍

本项目实现了一套全流程自动化的试卷批改流水线：

1. **截图** — 定时截取评分软件界面上指定区域的答题内容
2. **视觉识别** — 将截图发送给 VLM 视觉大模型（如 Qwen-VL）进行评分
3. **自动打分** — 根据 LLM 返回的分数，模拟鼠标点击对应分数按钮
4. **确认提交** — 自动点击"确认"按钮提交分数
5. **清分 & 下一份** — 清空分数，进入下一份试卷的批改循环

支持**双评分模式**：同一张截图交由主、副两个不同的 LLM 分别评分，并在前端展示一致性比对结果，辅助人工复核。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | Python 3.10+ / Flask + Flask-CORS |
| **前端框架** | Vue 3 + TypeScript + Vite 6 |
| **UI 组件库** | Ant Design Vue 4 |
| **状态管理** | Pinia |
| **路由** | Vue Router 4 |
| **HTTP 客户端** | Axios |
| **CSS 框架** | Tailwind CSS 3 |
| **数据库** | MySQL 8.0+ / PyMySQL |
| **屏幕操作** | PyAutoGUI（鼠标移动 / 点击） |
| **LLM 接入** | DashScope（通义千问-VL）、DeepSeek、OpenAI 兼容接口 |
| **测试（后端）** | Pytest |
| **测试（前端）** | Vitest + @vue/test-utils + happy-dom |

---

## 项目结构

```
├── config/                    # 配置文件
│   ├── config.json            # 主配置（LLM、区域坐标、路径等）
│   ├── config.example.json    # 配置示例（含字段说明注释）
│   ├── config说明.md           # 配置项详细说明文档
│   └── workflow.json          # 工作流步骤编排
├── src/                       # Python 后端源码
│   ├── main.py                # 主入口，启动 HTTP 服务
│   ├── app.py                 # Flask 应用路由（API 端点）
│   ├── config_loader.py       # 配置加载器
│   ├── core/
│   │   ├── screen_capture.py  # 屏幕截图模块
│   │   └── automation.py      # 鼠标自动化操作
│   ├── workflow/
│   │   ├── engine.py          # 工作流引擎（状态机）
│   │   ├── context.py         # 工作流上下文
│   │   ├── dual_grading.py    # 双评分协调
│   │   ├── expression.py      # 表达式解析
│   │   └── steps/             # 工作流步骤实现
│   ├── llm/
│   │   ├── base_client.py     # LLM 客户端基类
│   │   ├── dashscope_client.py# 阿里云 DashScope 接入
│   │   └── deepseek_client.py # DeepSeek 接入
│   ├── db/
│   │   ├── database.py        # 数据库连接池
│   │   ├── schema.py          # 表结构 DDL
│   │   └── repositories.py    # 数据仓库层
│   └── utils/
│       ├── logger.py          # 日志记录（文件 + 数据库）
│       └── config_manager.py  # 配置管理工具
├── web/                       # Vue 3 前端
│   ├── src/
│   │   ├── main.ts            # 入口
│   │   ├── App.vue            # 根组件
│   │   ├── api/               # API 接口层
│   │   ├── components/        # 组件
│   │   │   ├── layout/        # 布局组件（MainLayout）
│   │   │   └── business/      # 业务组件（ProcessControl, CorrectionLog）
│   │   ├── views/             # 页面（7 个）
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── router/            # 路由配置
│   │   ├── types/             # TypeScript 类型定义
│   │   └── utils/             # 工具函数
│   ├── vitest.config.ts       # 测试配置
│   └── package.json
├── testtool/                  # 测试工具
├── static/                    # 静态资源
├── screenshots/               # 截图输出目录
├── logs/                      # 日志输出目录
├── init_db.py                 # 数据库初始化脚本
├── requirements.txt           # Python 依赖
└── restart.bat                # 快速重启脚本
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+（可选，不配置则降级为文件日志）
- Windows 系统（因 PyAutoGUI 屏幕操作依赖）

### 后端启动

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 复制配置文件并编辑
cp config/config.example.json config/config.json
# 编辑 config/config.json，填入 LLM API Key 等参数

# 3. 启动服务
python src/main.py
```

服务默认启动在 `http://localhost:8081`，会自动打开浏览器加载前端页面。

### 前端启动（开发模式）

```bash
cd web
npm install
npm run dev
```

开发服务器默认运行在 `http://localhost:5173`，请求自动代理到后端 `http://localhost:8081`。

### 数据库初始化

```bash
# 使用 config.json 中的数据库配置
python init_db.py

# 重置数据库（删除并重建所有表）
python init_db.py --reset

# 导出建表 SQL
python init_db.py --export-sql
```

定义了 5 张业务表：

| 表名 | 说明 |
|------|------|
| `grading_batches` | 批改批次记录 |
| `grading_records` | 单份试卷批改记录 |
| `step_executions` | 工作流步骤执行日志 |
| `vlm_call_logs` | VLM 模型调用记录 |
| `system_logs` | 系统运行日志 |

---

## 配置说明

配置文件位于 `config/config.json`，完整的字段说明见 [config/config说明.md](config/config说明.md)。

### LLM / VLM 视觉模型

```json
{
  "llm": {
    "provider": "dashscope",
    "api_key": "sk-xxx",
    "model": "qwen-vl-max",
    "base_url": "",
    "timeout": 30,
    "max_retries": 2,
    "prompt_template": ""
  }
}
```

支持通过 `provider` 字段切换模型供应商：

| provider | 说明 |
|----------|------|
| `dashscope` | 阿里云通义千问 VL 系列（qwen-vl-max） |
| `deepseek` | DeepSeek 系列 |
| `openai` | OpenAI 兼容接口（可对接任意 OpenAI 格式供应商） |

### 双评分模式（主 + 副 LLM）

```json
{
  "llm_secondary": {
    "enabled": true,
    "provider": "deepseek",
    "api_key": "sk-xxx",
    "model": "deepseek-chat",
    "timeout": 30,
    "max_retries": 2,
    "prompt_template": ""
  }
}
```

启用后，每张截图会依次由主、副两个 LLM 独立评分，结果在前端并排展示并标注一致性。

### 屏幕区域与按钮坐标

项目通过配置像素坐标来定位屏幕元素，支持：

- `region.capture` — 模型评分的截图区域（x, y, width, height）
- `region.capture_human` — 人工查看的截图区域（x1, y1, x2, y2）
- `region.score_buttons` — 分数 0-6 对应的按钮坐标
- `region.clear_score` — 清分按钮位置
- `region.confirm_button` — 确认按钮位置

> 坐标校准：可在前端"设置"页使用鼠标校准功能，移动鼠标到目标位置获取实时坐标。

### 工作流编排

`config/workflow.json` 定义了批改流水线的步骤顺序，各步骤可独立启停：

| 步骤 | 说明 |
|------|------|
| `ScreenshotStep` | 截取指定区域的屏幕图像 |
| `VLMEvalStep` | 将截图发送给 LLM 评分 |
| `ClickScoreStep` | 根据评分结果点击对应分数按钮 |
| `ConfirmStep` | 点击确认按钮提交分数 |
| `ClearScoreStep` | 清空当前分数 |
| `WaitStep` | 等待指定时长后进入下一轮 |

---

## API 概览

所有 API 端点前缀为 `/api/v1`：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/workflow/start` | POST | 启动批改工作流 |
| `/workflow/stop` | POST | 停止工作流 |
| `/workflow/pause` | POST | 暂停工作流 |
| `/workflow/resume` | POST | 恢复工作流 |
| `/workflow/status` | GET | 查询工作流状态 |
| `/config` | GET/POST | 读写主配置 |
| `/workflow/config` | GET/POST | 读写工作流配置 |
| `/records` | GET | 查询批改记录（支持分页、一致性筛选） |
| `/correction/logs` | GET | 兼容旧前端的日志接口 |
| `/statistics` | GET | 批改统计（支持日期范围筛选） |
| `/llm/test` | POST | 测试 LLM 连接 |
| `/llm/evaluate` | POST | 上传图片进行 LLM 实时评分测试 |
| `/vlm-logs` | GET | VLM 调用日志查询 |
| `/services/status` | GET | 各服务状态 |
| `/health` | GET | 健康检查 |
| `/calibration/screenshot` | POST | 校准截图 |
| `/calibration/move-mouse` | POST | 校准鼠标坐标 |

> 启动/停止/暂停/恢复等操作端点仅限 `127.0.0.1` 本地访问（`@local_only` 装饰器保护）。

---

## 前端页面

| 页面 | 路由 | 功能 |
|------|------|------|
| **批改控制台** | `/` | 工作流控制（启动/停止/暂停）、进度展示、实时状态 |
| **设置** | `/settings` | LLM 配置、区域坐标校准、配置文件编辑 |
| **历史记录** | `/records` | 批改记录分页浏览、一致性筛选、双评分结果对比 |
| **统计** | `/statistics` | 按日期范围的批改统计报表 |
| **服务状态** | `/services` | 后端服务、数据库、LLM 连接状态一览 |
| **模型测试** | `/llm-test` | LLM 连接测试 + 上传图片实时评分测试 |
| **VLM 日志** | `/vlm-logs` | 模型调用历史日志查询 |

---

## 测试

### 后端测试（Pytest）

```bash
# 运行全部后端测试
pytest testtool/ -v

# 带覆盖率报告
pytest testtool/ --cov=src --cov-report=term-missing
```

### 前端测试（Vitest）

```bash
cd web
npm test              # 运行一次
npm run test:watch    # 监听模式
```

前端测试覆盖：

| 层 | 文件 | 用例数 |
|------|------|--------|
| 类型定义 | `types/__tests__/` | 10 |
| HTTP 工具 | `utils/__tests__/` | 8 |
| API 层 | `api/__tests__/` | 8 |
| Pinia 状态 | `stores/__tests__/` | 10 |
| 路由配置 | `router/__tests__/` | 9 |
| 组件渲染 | `components/__tests__/` | 10 |
| **合计** | **8 个测试文件** | **57** |

---

## 开发指南

### 新增 API 端点

1. 在 `src/app.py` 中添加 Flask 路由
2. 如果是数据库操作，在 `src/db/repositories.py` 中增加数据仓库方法
3. （可选）在前端 `web/src/api/` 下添加对应接口调用函数
4. 添加测试

### 新增工作流步骤

1. 在 `src/workflow/steps/` 下创建步骤类，继承基础步骤接口
2. 在 `config/workflow.json` 的 `steps` 数组中注册新步骤
3. 在 `src/workflow/engine.py` 中注册步骤类型到工厂映射

### 添加新的 LLM 供应商

1. 在 `src/llm/` 下创建客户端类，继承 `BaseLLMClient`
2. 实现 `evaluate(image_path, prompt)` 方法
3. 在 `src/llm/__init__.py` 的 `create_llm_client()` 工厂函数中注册

---

## 常见问题

**Q: 配置了 LLM 但评分一直失败？**

A: 先在"模型测试"页面上传一张图片测试 LLM 连接，确认 API Key 和模型名正确。注意区分 VLM 视觉模型和纯文本模型——评分需要 VLM 模型。

**Q: 鼠标点击位置不准确？**

A: 在"设置"页使用鼠标校准功能，移动鼠标到目标按钮观察实时坐标，然后更新 `config.json` 中 `region.score_buttons` 或 `region.confirm_button` 的坐标值。

**Q: 数据库连接失败会影响使用吗？**

A: 不会。后端会自动降级为文件日志模式，所有功能正常可用，只是批改记录不会被持久化到数据库。

**Q: 如何开启双评分？**

A: 在配置中将 `llm_secondary.enabled` 设为 `true`，并填写副 LLM 的 API Key 和模型名。开启后前端历史记录和批改控制台会并排展示两个模型的评分结果和一致性。
