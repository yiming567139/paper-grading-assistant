# 配置文件说明

本文档说明 `config.json` 中每个配置项的含义。修改后保存即可生效（后端重启后读取最新配置）。

## 1. dify - Dify 服务配置

```json
{
  "base_url": "http://192.168.50.126/v1/workflows/run",
  "api_key": "app-L9Qnza6NIx",
  "workflow_id": "",
  "mock_mode": false,
  "mock_response": "2",
  "simulate_click": false,
  "click_confirm": true
}
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `base_url` | Dify 工作流 API 地址，必须以 `/v1/workflows/run` 结尾 | `http://192.168.50.126/v1/workflows/run` |
| `api_key` | Dify 应用的 API Key，在 Dify 应用设置中获取 | `app-xxxxxxxx` |
| `workflow_id` | 工作流 ID（目前通过 API Key 即可调用，留空即可） | `""` |
| `mock_mode` | `true` 时不调用真实 Dify，直接返回 `mock_response` 内容 | `false` / `true` |
| `mock_response` | 模拟模式下返回的预设文本（支持纯数字或带说明的文字，会提取第一个数字作为分数） | `"3"`、`"2分"` |
| `simulate_click` | `true` 时仅模拟鼠标点击（记录日志但不真实操作鼠标），用于调试 | `false` / `true` |
| `click_confirm` | `true` 时打分后自动点击"确认"按钮 | `true` / `false` |

## 2. llm - 主 LLM 配置

```json
{
  "provider": "dashscope",
  "api_key": "",
  "model": "qwen-vl-max",
  "base_url": "",
  "timeout": 30,
  "max_retries": 2,
  "prompt_template": ""
}
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `provider` | 模型提供商，如 `dashscope`、`deepseek`、`openai` 等 | `dashscope` |
| `api_key` | 对应提供商的 API Key | `sk-xxxxxxxx` |
| `model` | 模型名称，如 `qwen-vl-max`、`deepseek-chat` 等 | `qwen-vl-max` |
| `base_url` | 自定义 API 基础地址，留空使用默认 | `""` |
| `timeout` | API 请求超时时间（秒） | `30` |
| `max_retries` | API 请求失败时的最大重试次数 | `2` |
| `prompt_template` | 评分提示词模板 | `""` |

## 3. llm_secondary - 副 LLM 配置（双评分）

```json
{
  "llm_secondary": {
    "enabled": false,
    "provider": "deepseek",
    "api_key": "",
    "model": "deepseek-chat",
    "base_url": "",
    "timeout": 30,
    "max_retries": 2,
    "prompt_template": ""
  }
}
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `enabled` | 双评分总开关。`true` 时启用双评分，同一张截图会由主、副 LLM 分别评分；`false` 或缺失该配置块时，仅使用主 LLM 单评分 | `false` / `true` |
| `provider` | 副 LLM 提供商 | `deepseek` |
| `api_key` | 副 LLM 的 API Key | `sk-xxxxxxxx` |
| `model` | 副 LLM 模型名称 | `deepseek-chat` |
| `base_url` | 自定义 API 基础地址，留空使用默认 | `""` |
| `timeout` | API 请求超时时间（秒） | `30` |
| `max_retries` | API 请求失败时的最大重试次数 | `2` |
| `prompt_template` | 评分提示词模板 | `""` |

## 4. http_server - HTTP 服务配置

```json
{
  "port": 8081,
  "host": "0.0.0.0"
}
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `port` | 后端 API 服务监听端口，前端通过此端口访问后端 | `8081` |
| `host` | 绑定地址，`0.0.0.0` 表示监听所有网卡（局域网可访问） | `0.0.0.0` |

## 5. region - 屏幕区域和按钮坐标配置

### 5.1 capture - 模型评分截图区域

```json
{
  "capture": {
    "x": 46,
    "y": 213,
    "width": 810,
    "height": 700
  }
}
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `x` | 截图区域左上角 X 坐标（像素） | `46` |
| `y` | 截图区域左上角 Y 坐标（像素） | `213` |
| `width` | 截图区域宽度（像素） | `810` |
| `height` | 截图区域高度（像素） | `700` |

> 获取坐标方法：使用系统设置里的"校准区域位置"功能，移动鼠标即可看到实时坐标。

### 5.2 capture_human - 人工查看截图区域

```json
{
  "capture_human": {
    "x1": 0,
    "y1": 0,
    "x2": 1920,
    "y2": 1080
  }
}
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `x1` | 人工查看截图区域左上角 X 坐标（像素） | `0` |
| `y1` | 人工查看截图区域左上角 Y 坐标（像素） | `0` |
| `x2` | 人工查看截图区域右下角 X 坐标（像素） | `1920` |
| `y2` | 人工查看截图区域右下角 Y 坐标（像素） | `1080` |

> 省略该配置项时，不捕获人工查看截图。

### 5.3 score_buttons - 分数按钮坐标

```json
{
  "score_buttons": [
    {"score": 0, "x": 1043, "y": 565},
    {"score": 1, "x": 1000, "y": 521},
    {"score": 2, "x": 1080, "y": 521},
    {"score": 3, "x": 1160, "y": 521},
    {"score": 4, "x": 1000, "y": 472},
    {"score": 5, "x": 1080, "y": 472},
    {"score": 6, "x": 1160, "y": 472}
  ]
}
```

| 字段 | 说明 |
|------|------|
| `score` | 分数值（0-6），必须与 Dify 返回的分数匹配 |
| `x` | 该分数按钮的 X 坐标 |
| `y` | 该分数按钮的 Y 坐标 |

> 注意：数组中必须有 `score: 0` 到 `score: 6` 的配置，否则对应分数无法点击。

### 5.4 clear_score - 清分按钮

```json
{
  "clear_score": {
    "enabled": true,
    "x": 1262,
    "y": 412
  }
}
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `enabled` | `true` 时每次打分前先点击清分按钮（清除已有分数） | `true` / `false` |
| `x` | 清分按钮 X 坐标 | `1262` |
| `y` | 清分按钮 Y 坐标 | `412` |

### 5.5 confirm_button - 确认按钮

```json
{
  "confirm_button": {
    "x": 1122,
    "y": 613
  }
}
```

| 字段 | 说明 |
|------|------|
| `x` | 确认按钮 X 坐标 |
| `y` | 确认按钮 Y 坐标 |

> 确认按钮是否点击由 `dify.click_confirm` 控制，此处只配置坐标。

## 6. paths - 文件路径配置

```json
{
  "paths": {
    "screenshots": "./screenshots",
    "logs": "./logs"
  }
}
```

| 字段 | 说明 |
|------|------|
| `screenshots` | 截图保存目录（相对项目根目录） |
| `logs` | 日志保存目录（相对项目根目录） |

## 7. window - 窗口配置

```json
{
  "window": {
    "always_on_top": true
  }
}
```

| 字段 | 说明 |
|------|------|
| `always_on_top` | GUI 窗口是否始终置顶（仅在使用 GUI 模式时生效） |

---

## 常用调整场景

| 场景 | 修改位置 |
|------|----------|
| 换 Dify 服务器 | `dify.base_url`、`dify.api_key` |
| 调试时不操作鼠标 | `dify.simulate_click` 改为 `true` |
| 关闭打分后确认 | `dify.click_confirm` 改为 `false` |
| 关闭清分步骤 | `region.clear_score.enabled` 改为 `false` |
| 调整模型评分截图区域 | `region.capture` 的 x/y/width/height |
| 调整人工查看截图区域 | `region.capture_human` 的 x1/y1/x2/y2 |
| 启用双评分 | `llm_secondary.enabled` 改为 `true` |
| 分数按钮点不准 | `region.score_buttons` 对应分数的 x/y |
| 确认按钮点不准 | `region.confirm_button` 的 x/y |
