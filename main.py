#!/usr/bin/env python3
"""
WorkBuddy - 智能 AI 助手

从 Hermes Agent 精简而来的跨平台 AI 助手
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.agent import WorkBuddyAgent
from config.settings import load_config, setup_wizard
from tools.terminal import run_command
from tools.file_ops import read_file, write_file, list_files


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def register_default_tools(agent: WorkBuddyAgent):
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
    
    # 注册工具
    agent.tools = {
        'terminal': terminal,
        'read': read,
        'write': write,
        'ls': ls,
    }
    
    # 重新构建工具定义
    agent.tool_definitions = agent._build_tool_definitions()


def main():
    """主入口"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("=" * 50)
    print("🤖 WorkBuddy - 智能 AI 助手")
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
    
    # 创建 Agent
    try:
        agent = WorkBuddyAgent(
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
