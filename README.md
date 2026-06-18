# MagicOrigin 🤖

从 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 精简而来的跨平台 AI 助手框架。

## 特性

- ✅ **精简核心** - 只保留 Agent 循环、记忆、基础工具（~1000 行）
- ✅ **模块化设计** - 组件可插拔，按需启用
- ✅ **多 Provider 支持** - DeepSeek、OpenAI、本地 llama.cpp/Ollama
- ✅ **动态切换模型** - 运行时 `/model` 命令切换
- ✅ **跨平台** - Windows / Mac / Linux
- ✅ **易打包** - 依赖少，PyInstaller 友好（目标 ~50MB）

## 架构

```
magic-origin/
├── core/                    # 核心模块（必需）
│   └── agent.py            # Agent 循环（不依赖任何组件）
├── components/              # 可插拔组件（可选）
│   ├── __init__.py         # 组件注册表
│   └── model_provider.py   # 模型提供者管理
├── tools/                   # 工具（可插拔）
│   ├── terminal.py         # 终端命令执行
│   ├── file_ops.py         # 文件操作
│   └── memory.py           # 记忆工具
├── config/                  # 配置管理
│   └── settings.py         # 配置加载/保存
├── main.py                  # 主入口（组装各组件）
└── requirements.txt         # 依赖
```

### 设计原则

1. **核心解耦** - `core/agent.py` 不依赖任何组件，通过依赖注入
2. **组件可选** - `components/` 和 `tools/` 都可以独立启用/禁用
3. **入口组装** - `main.py` 负责加载配置、初始化组件、启动 Agent

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/fclwtt/magic-origin.git
cd magic-origin
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

**依赖列表**：
- `httpx` - HTTP 客户端（调用 LLM API）

### 3. 配置 API Key

**方式 1：环境变量（推荐）**

```bash
# Linux/Mac
export DEEPSEEK_API_KEY="sk-xxx"

# Windows CMD
set DEEPSEEK_API_KEY=sk-xxx

# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-xxx"
```

**方式 2：首次运行向导**

直接运行 `python main.py`，会引导你配置。

### 4. 启动

```bash
python main.py
```

首次运行会进入设置向导：

```
==================================================
MagicOrigin 首次设置
==================================================

选择 LLM Provider:
  1. DeepSeek（默认）
  2. OpenAI
  3. 本地 llama.cpp
  4. 本地 Ollama
  5. 自定义

选择 [1]: 
```

## 使用本地模型（llama.cpp / Ollama）

### 1. 启动本地服务

**llama.cpp**：
```bash
llama-server.exe -m your-model.gguf --port 8080
```

**Ollama**：
```bash
ollama serve
# 默认端口 11434
```

### 2. 配置 MagicOrigin

首次设置时选择 `3. 本地 llama.cpp` 或 `4. 本地 Ollama`。

API Key 可直接回车跳过（本地不需要验证）。

### 3. 运行时切换模型

```
你: /model
📍 当前模型:
  Provider: DeepSeek
  Model: deepseek-chat
  Base URL: https://api.deepseek.com

📋 可用 Provider:
  - DeepSeek ✓
  - OpenAI
  - Local (llama.cpp)
  - Local (Ollama)

你: /model llama3 --provider local-llama
✅ 已切换到: llama3 (自动检测)
   Provider: local-llama
   Base URL: http://localhost:8080/v1
```

## 命令参考

| 命令 | 说明 |
|------|------|
| `/model` | 查看当前模型和可用 Provider |
| `/model <name>` | 切换模型 |
| `/model <name> --provider <id>` | 切换到指定 Provider 的模型 |
| `/reset` | 重置对话历史 |
| `/memories` | 查看已保存的记忆 |
| `exit` / `quit` | 退出 |

## 打包为 exe（Windows）

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
pyinstaller --onefile --name magic-origin main.py

# 生成的 exe 在 dist/ 目录
```

## 配置说明

配置文件位置：
- Windows: `%APPDATA%\magic-origin\config.json`
- Mac/Linux: `~/.config/magic-origin/config.json`

```json
{
  "provider_id": "deepseek",
  "base_url": "https://api.deepseek.com",
  "model": "deepseek-chat",
  "api_key": "",
  "max_iterations": 50,
  "temperature": 0.7,
  "memory_enabled": true,
  "tools_enabled": true,
  "custom_providers": {}
}
```

**注意**：API Key 不保存到文件，应使用环境变量。

## 扩展开发

### 添加新工具

在 `tools/` 目录创建文件：

```python
# tools/my_tool.py

def my_function(param1: str, param2: int = 10):
    """工具描述（会显示给 LLM）"""
    return f"结果: {param1} {param2}"
```

在 `main.py` 注册：

```python
from tools.my_tool import my_function

agent.tools['my_tool'] = my_function
agent.tool_definitions = agent._build_tool_definitions()
```

### 添加新组件

在 `components/` 目录创建文件，参考 `model_provider.py` 的结构。

组件应该是可选的，不安装时不影响核心功能。

## 与 Hermes 的对比

| 特性 | Hermes | MagicOrigin |
|------|--------|-----------|
| 代码量 | 20000+ 行 | ~1000 行 |
| 依赖 | 50+ 包 | 1 个核心包 |
| 打包体积 | 500MB+ | ~50MB（目标） |
| 学习成本 | 高 | 低 |
| 功能完整度 | 完整 | 核心功能 |
| 组件系统 | 完整 | 可插拔 |

## 后续计划

- [ ] Skill 系统（工作流编排）
- [ ] 上下文压缩（长对话管理）
- [ ] 子代理委派（多 Agent 协作）
- [ ] 更多工具（浏览器、代码执行等）

## 组件库

可插拔组件来自 [agent-components](https://github.com/fclwtt/agent-components) 仓库：

- `model-provider` - 模型提供者管理

## License

MIT
