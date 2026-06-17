#!/usr/bin/env python3
"""
MagicOrigin Agent - 精简版 Agent 核心循环

从 Hermes run_agent.py 精简而来，保留核心功能：
- LLM 对话循环
- 工具调用
- 记忆集成
- 跨平台兼容（Windows/Mac/Linux）
"""

import asyncio
import inspect
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, get_type_hints

# 跨平台路径处理
from pathlib import Path

logger = logging.getLogger(__name__)


class MagicOriginAgent:
    """
    精简版 AI Agent
    
    核心功能：
    - 与 LLM 对话
    - 执行工具调用
    - 维护对话历史
    - 集成记忆系统
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "gpt-4",
        tools: Optional[Dict[str, Callable]] = None,
        memory_dir: Optional[str] = None,
        max_iterations: int = 50,
    ):
        """
        初始化 Agent
        
        Args:
            api_key: LLM API Key
            base_url: API Base URL（支持 OpenAI 兼容 API）
            model: 模型名称
            tools: 工具字典 {name: function}
            memory_dir: 记忆存储目录
            max_iterations: 最大迭代次数
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.max_iterations = max_iterations
        
        # 工具注册
        self.tools = tools or {}
        self.tool_definitions = self._build_tool_definitions()
        
        # 记忆目录（跨平台）
        if memory_dir:
            self.memory_dir = Path(memory_dir)
        else:
            # 默认：用户目录下的 .magic-origin/memory
            home = Path.home()
            self.memory_dir = home / ".magic-origin" / "memory"
        
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 对话历史
        self.messages: List[Dict[str, Any]] = []
        
        # 系统提示词
        self.system_prompt = self._build_system_prompt()
        
        logger.info(f"MagicOrigin Agent 初始化完成，模型: {model}, 记忆目录: {self.memory_dir}")
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是 MagicOrigin，一个智能 AI 助手。

你可以：
1. 回答用户问题
2. 使用工具执行任务（终端命令、文件操作）
3. 记住重要信息供后续使用

## 记忆功能

你可以使用以下工具管理记忆：
- `save_memory(key, content)`: 保存记忆，key 是名称，content 是内容
- `load_memory(key)`: 加载已保存的记忆
- `list_memories()`: 列出所有记忆

**何时保存记忆**：
- 用户说"记住..."、"我的...是..."
- 用户分享偏好、习惯、个人信息
- 发现重要的环境信息

**记忆示例**：
- 用户说"我是你的老板" → save_memory("user_role", "用户是我的老板")
- 用户说"我喜欢简洁" → save_memory("user_preference", "用户喜欢简洁的回复风格")

使用工具时，请按照 JSON 格式调用。

保持友好、专业、简洁。"""
    
    def _build_tool_definitions(self) -> List[Dict]:
        """
        构建 OpenAI 格式的工具定义
        
        使用 inspect 从函数签名提取参数
        """
        definitions = []
        
        # Python 类型到 JSON Schema 类型的映射
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }
        
        for name, func in self.tools.items():
            # 从函数文档字符串提取描述
            doc = func.__doc__ or "No description"
            desc_lines = [l.strip() for l in doc.strip().split('\n') if l.strip()]
            description = desc_lines[0] if desc_lines else "No description"
            
            # 使用 inspect 提取函数签名
            sig = inspect.signature(func)
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                # 获取参数类型
                param_type = "string"  # 默认
                if param.annotation != inspect.Parameter.empty:
                    param_type = type_map.get(param.annotation, "string")
                
                prop = {"type": param_type, "description": param_name}
                properties[param_name] = prop
                
                # 没有默认值的参数是必填的
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
            
            tool_def = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }
            definitions.append(tool_def)
        
        return definitions
    
    def _call_llm(self, messages: List[Dict]) -> Dict:
        """
        调用 LLM API
        
        使用 httpx 直接调用，避免 openai SDK 的复杂依赖
        """
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
        }
        
        # 如果有工具，添加工具定义
        if self.tool_definitions:
            payload["tools"] = self.tool_definitions
            payload["tool_choice"] = "auto"
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"LLM API 调用失败: {e}")
            raise
    
    def _execute_tool(self, tool_name: str, args_str: str) -> str:
        """
        执行工具调用
        
        Args:
            tool_name: 工具名称
            args_str: JSON 格式的参数
        
        Returns:
            工具执行结果（字符串）
        """
        if tool_name not in self.tools:
            return f"错误：工具 '{tool_name}' 不存在"
        
        try:
            args = json.loads(args_str) if args_str else {}
            result = self.tools[tool_name](**args)
            return str(result)
        except json.JSONDecodeError:
            return f"错误：参数格式错误 - {args_str}"
        except Exception as e:
            logger.error(f"工具执行失败: {e}")
            return f"错误：{str(e)}"
    
    def chat(self, user_message: str) -> str:
        """
        与用户对话（主入口）
        
        Args:
            user_message: 用户输入
        
        Returns:
            AI 回复
        """
        # 添加用户消息到历史
        self.messages.append({
            "role": "user",
            "content": user_message
        })
        
        # 构建消息列表（包含系统提示）
        messages = [{"role": "system", "content": self.system_prompt}] + self.messages
        
        # Agent 循环
        for iteration in range(self.max_iterations):
            logger.debug(f"Agent 迭代 {iteration + 1}/{self.max_iterations}")
            
            # 调用 LLM
            response = self._call_llm(messages)
            choice = response["choices"][0]
            assistant_message = choice["message"]
            
            # 检查是否有工具调用
            if assistant_message.get("tool_calls"):
                # 添加助手消息（包含工具调用）
                messages.append(assistant_message)
                
                # 执行每个工具调用
                for tool_call in assistant_message["tool_calls"]:
                    func_name = tool_call["function"]["name"]
                    func_args = tool_call["function"]["arguments"]
                    
                    logger.info(f"调用工具: {func_name}")
                    result = self._execute_tool(func_name, func_args)
                    
                    # 添加工具结果
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result
                    })
                
                # 继续循环，让 LLM 处理工具结果
            
            else:
                # 没有工具调用，返回文本回复
                reply = assistant_message.get("content", "")
                
                # 添加到历史
                self.messages.append({
                    "role": "assistant",
                    "content": reply
                })
                
                return reply
        
        # 超过最大迭代
        return "抱歉，我遇到了问题，请稍后再试。"
    
    def reset(self):
        """重置对话历史"""
        self.messages = []
        logger.info("对话历史已重置")
    
    def save_memory(self, key: str, value: str):
        """
        保存记忆
        
        Args:
            key: 记忆键
            value: 记忆内容
        """
        memory_file = self.memory_dir / f"{key}.md"
        memory_file.write_text(value, encoding="utf-8")
        logger.info(f"记忆已保存: {key}")
    
    def load_memory(self, key: str) -> Optional[str]:
        """
        加载记忆
        
        Args:
            key: 记忆键
        
        Returns:
            记忆内容，不存在则返回 None
        """
        memory_file = self.memory_dir / f"{key}.md"
        if memory_file.exists():
            return memory_file.read_text(encoding="utf-8")
        return None
    
    def list_memories(self) -> List[str]:
        """列出所有记忆"""
        return [f.stem for f in self.memory_dir.glob("*.md")]


# 命令行测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 从环境变量获取 API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("错误：请设置 OPENAI_API_KEY 环境变量")
        sys.exit(1)
    
    # 创建 Agent
    agent = MagicOriginAgent(
        api_key=api_key,
        model="gpt-4"
    )
    
    # 简单对话测试
    print("MagicOrigin Agent 测试")
    print("=" * 40)
    
    while True:
        try:
            user_input = input("\n你: ").strip()
            if user_input.lower() in ['exit', 'quit', '退出']:
                break
            
            reply = agent.chat(user_input)
            print(f"\nAI: {reply}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n错误: {e}")
