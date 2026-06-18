#!/usr/bin/env python3
"""
MagicOrigin - 智能 AI 助手

从 Hermes Agent 精简而来的跨平台 AI 助手
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.agent import MagicOriginAgent
from config.settings import load_config, save_config, setup_wizard, MagicOriginConfig
from tools.terminal import run_command
from tools.file_ops import read_file, write_file, list_files

# 导入 model-provider 组件（可选）
try:
    from components.model_provider import ModelProviderManager
    HAS_MODEL_PROVIDER = True
except ImportError:
    HAS_MODEL_PROVIDER = False
    ModelProviderManager = None


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def register_default_tools(agent: MagicOriginAgent):
    """注册默认工具"""
    
    def terminal(command: str, timeout: int = 30):
        """执行终端命令"""
        result = run_command(command, timeout=timeout)
        if result['success']:
            return result['stdout']
        else:
            return f"错误: {result['stderr']}"
    
    def read(path: str):
        """读取文件内容"""
        result = read_file(path)
        if result['success']:
            return result['content']
        else:
            return f"错误: {result['error']}"
    
    def write(path: str, content: str):
        """写入文件"""
        result = write_file(path, content)
        if result['success']:
            return "文件写入成功"
        else:
            return f"错误: {result['error']}"
    
    def ls(path: str = ".", pattern: str = "*"):
        """列出目录内容"""
        result = list_files(path, pattern=pattern)
        if result['success']:
            return '\n'.join(result['files']) if result['files'] else "(空目录)"
        else:
            return f"错误: {result['error']}"
    
    # 记忆工具
    def save_memory(key: str, content: str):
        """保存记忆到持久化存储。key 是记忆名称，content 是记忆内容。用于记住用户偏好、重要信息等。"""
        agent.save_memory(key, content)
        return f"记忆 '{key}' 已保存"
    
    def load_memory(key: str):
        """加载已保存的记忆。key 是记忆名称。"""
        content = agent.load_memory(key)
        if content:
            return content
        else:
            return f"记忆 '{key}' 不存在"
    
    def list_memories():
        """列出所有已保存的记忆名称"""
        memories = agent.list_memories()
        if memories:
            return '\n'.join(memories)
        else:
            return "(暂无记忆)"
    
    # 注册工具
    agent.tools = {
        'terminal': terminal,
        'read': read,
        'write': write,
        'ls': ls,
        'save_memory': save_memory,
        'load_memory': load_memory,
        'list_memories': list_memories,
    }
    
    # 重新构建工具定义
    agent.tool_definitions = agent._build_tool_definitions()


def create_provider_manager(config: MagicOriginConfig):
    """从配置创建 ModelProviderManager（如果组件可用）"""
    if not HAS_MODEL_PROVIDER:
        return None
    
    manager = ModelProviderManager()
    
    # 添加自定义 Provider
    for pid, pconfig in config.custom_providers.items():
        manager.add_provider(
            provider_id=pid,
            name=pconfig.get("name", pid),
            base_url=pconfig.get("base_url", ""),
            api_key=pconfig.get("api_key", ""),
            default_model=pconfig.get("default_model", ""),
            requires_api_key=pconfig.get("requires_api_key", True),
        )
    
    # 设置当前 Provider
    manager.current_provider_id = config.provider_id
    manager.current_model = config.model
    
    # 确保当前 Provider 的 API Key 已设置
    current = manager.get_provider(config.provider_id)
    if current and config.api_key:
        current.api_key = config.api_key
    
    return manager


def handle_model_command(args: str, agent: MagicOriginAgent, manager, config: MagicOriginConfig):
    """处理 /model 命令"""
    if not args.strip():
        # 显示当前模型和可用 Provider
        current = manager.get_current_config()
        print("\n📍 当前模型:")
        print(f"  Provider: {current.get('provider_name', 'N/A')}")
        print(f"  Model: {current.get('model', 'N/A')}")
        print(f"  Base URL: {current.get('base_url', 'N/A')}")
        print(f"  本地: {'是' if current.get('is_local') else '否'}")
        
        print("\n📋 可用 Provider:")
        for p in manager.list_providers():
            local_tag = " [本地]" if p["is_local"] else ""
            current_tag = " ✓" if p["is_current"] else ""
            print(f"  - {p['name']}{local_tag}{current_tag}")
        
        print("\n💡 用法: /model <模型名> [--provider <provider_id>]")
        print("   例如: /model llama3 --provider local-llama")
        return
    
    # 解析参数
    parts = args.strip().split()
    model = ""
    provider_id = ""
    
    i = 0
    while i < len(parts):
        if parts[i] == "--provider" and i + 1 < len(parts):
            provider_id = parts[i + 1]
            i += 2
        else:
            model = parts[i]
            i += 1
    
    # 切换模型
    result = manager.switch_model(model, provider_id=provider_id)
    
    if result.success:
        # 更新 Agent 配置
        agent.api_key = result.api_key
        agent.base_url = result.base_url
        agent.model = result.model
        
        # 更新全局配置
        config.provider_id = result.provider_id
        config.model = result.model
        config.base_url = result.base_url
        config.api_key = result.api_key
        
        # 保存配置
        save_config(config)
        
        auto_tag = " (自动检测)" if result.auto_detected else ""
        print(f"\n✅ 已切换到: {result.model}{auto_tag}")
        print(f"   Provider: {result.provider_id}")
        print(f"   Base URL: {result.base_url}")
    else:
        print(f"\n❌ 切换失败: {result.error_message}")


def main():
    """主入口"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("=" * 50)
    print("🤖 MagicOrigin - 智能 AI 助手")
    print("=" * 50)
    print()
    
    # 加载配置
    config = load_config()
    
    # 检查 API Key
    if not config.api_key:
        print("未检测到 API Key，需要进行首次设置")
        print()
        config = setup_wizard()
        
        if not config.api_key:
            print("\n错误：未提供 API Key，无法启动")
            print("请设置环境变量 OPENAI_API_KEY 或重新运行设置")
            sys.exit(1)
    
    # 创建 Provider Manager（如果组件可用）
    manager = create_provider_manager(config) if HAS_MODEL_PROVIDER else None
    
    # 创建 Agent
    try:
        agent = MagicOriginAgent(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            memory_dir=config.memory_dir,
            max_iterations=config.max_iterations,
        )
        
        # 注册工具
        if config.tools_enabled:
            register_default_tools(agent)
        
        logger.info(f"Agent 初始化完成，模型: {config.model}")
        
    except Exception as e:
        logger.error(f"Agent 初始化失败: {e}")
        print(f"\n错误：{e}")
        sys.exit(1)
    
    # 交互循环
    print("\n输入 'exit' 或 'quit' 退出")
    print("输入 '/model' 查看/切换模型")
    print("-" * 50)
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', '退出', 'q']:
                print("\n再见！ 👋")
                break
            
            # 特殊命令
            if user_input.lower() == '/reset':
                agent.reset()
                print("对话已重置")
                continue
            
            if user_input.lower() == '/memories':
                memories = agent.list_memories()
                if memories:
                    print("\n已保存的记忆:")
                    for m in memories:
                        print(f"  - {m}")
                else:
                    print("\n暂无记忆")
                continue
            
            # /model 命令
            if user_input.startswith('/model'):
                if manager:
                    args = user_input[6:].strip()  # 去掉 "/model "
                    handle_model_command(args, agent, manager, config)
                else:
                    print("\n⚠️ model-provider 组件未安装")
                continue
            
            # 调用 Agent
            reply = agent.chat(user_input)
            print(f"\nAI: {reply}")
            
        except KeyboardInterrupt:
            print("\n\n再见！ 👋")
            break
        except Exception as e:
            logger.error(f"错误: {e}")
            print(f"\n错误: {e}")


if __name__ == "__main__":
    main()
