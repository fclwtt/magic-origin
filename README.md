# MagicOrigin 🤖

从 Hermes Agent 精简而来的跨平台 AI 助手。

## 特性

- ✅ **精简核心** - 只保留 Agent 循环、记忆、基础工具
- ✅ **跨平台** - Windows / Mac / Linux
- ✅ **易打包** - 依赖少，PyInstaller 友好
- ✅ **可扩展** - 模块化设计，易于添加新功能

## 架构

```
magic-origin/
├── core/
│   └── agent.py          # Agent 核心循环
├── tools/
│   ├── terminal.py       # 终端命令执行
│   └── file_ops.py       # 文件操作
├── config/
│   └── settings.py       # 配置管理
├── main.py               # 主入口
└── requirements.txt      # 依赖
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置 API Key

```bash
# 方式 1：环境变量
export OPENAI_API_KEY="your-key-here"

# 方式 2：首次运行时会引导设置
python main.py
```

### 3. 运行

```bash
python main.py
```

## 打包为 exe（Windows）

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
pyinstaller --onefile --name magic-origin main.py

# 生成的 exe 在 dist/ 目录
```

## 与 Hermes 的对比

| 特性 | Hermes | MagicOrigin |
|------|--------|-----------|
| 代码量 | 20000+ 行 | ~1000 行 |
| 依赖 | 50+ 包 | 1 个核心包 |
| 打包体积 | 500MB+ | ~50MB |
| 学习成本 | 高 | 低 |
| 功能完整度 | 完整 | 核心功能 |

## 后续扩展

Phase 2 计划添加：
- Skill 系统
- 上下文压缩
- 子代理委派
- 更多工具

## License

MIT
