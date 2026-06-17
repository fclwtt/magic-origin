#!/usr/bin/env python3
"""
配置管理 - 跨平台

处理：
- API Key 存储
- 模型配置
- 用户偏好
"""

import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class MagicOriginConfig:
    """MagicOrigin 配置"""
    
    # LLM 配置
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-flash"
    
    # 行为配置
    max_iterations: int = 50
    temperature: float = 0.7
    
    # 记忆配置
    memory_enabled: bool = True
    memory_dir: str = ""  # 空则使用默认
    
    # 工具配置
    tools_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MagicOriginConfig':
        """从字典创建"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def get_config_dir() -> Path:
    """获取配置目录（跨平台）"""
    # Windows: %APPDATA%\MagicOrigin
    # Mac/Linux: ~/.config/magic-origin
    
    if os.name == 'nt':  # Windows
        base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
    else:
        base = Path.home() / '.config'
    
    config_dir = base / 'magic-origin'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """获取配置文件路径"""
    return get_config_dir() / 'config.json'


def load_config() -> MagicOriginConfig:
    """
    加载配置
    
    优先级：
    1. 环境变量
    2. 配置文件
    3. 默认值
    """
    config_path = get_config_path()
    
    # 尝试从文件加载
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding='utf-8'))
            config = MagicOriginConfig.from_dict(data)
            logger.info(f"配置已加载: {config_path}")
        except Exception as e:
            logger.warning(f"加载配置失败: {e}，使用默认配置")
            config = MagicOriginConfig()
    else:
        config = MagicOriginConfig()
    
    # 环境变量覆盖（用于敏感信息如 API Key）
    if os.environ.get('DEEPSEEK_API_KEY'):
        config.api_key = os.environ['DEEPSEEK_API_KEY']
    elif os.environ.get('OPENAI_API_KEY'):
        config.api_key = os.environ['OPENAI_API_KEY']
    
    if os.environ.get('DEEPSEEK_BASE_URL'):
        config.base_url = os.environ['DEEPSEEK_BASE_URL']
    elif os.environ.get('OPENAI_BASE_URL'):
        config.base_url = os.environ['OPENAI_BASE_URL']
    
    if os.environ.get('MAGIC_ORIGIN_MODEL'):
        config.model = os.environ['MAGIC_ORIGIN_MODEL']
    
    # 设置默认记忆目录
    if not config.memory_dir:
        config.memory_dir = str(Path.home() / '.magic-origin' / 'memory')
    
    return config


def save_config(config: MagicOriginConfig) -> bool:
    """
    保存配置
    
    注意：API Key 不保存到文件，应使用环境变量
    """
    config_path = get_config_path()
    
    try:
        # 复制配置，隐藏 API Key
        data = config.to_dict()
        data['api_key'] = ''  # 不保存 API Key 到文件
        
        config_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        
        logger.info(f"配置已保存: {config_path}")
        return True
    
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return False


def setup_wizard() -> MagicOriginConfig:
    """
    首次运行设置向导
    
    引导用户配置 API Key 等
    """
    print("=" * 50)
    print("MagicOrigin 首次设置")
    print("=" * 50)
    print()
    
    config = MagicOriginConfig()
    
    # API Key
    print("请输入 DeepSeek API Key")
    print("提示：API Key 不会保存到文件，仅存储在环境变量中")
    api_key = input("API Key: ").strip()
    if api_key:
        config.api_key = api_key
    else:
        print("警告：未提供 API Key，部分功能可能无法使用")
    
    # Base URL
    print("\nAPI Base URL（直接回车使用默认 DeepSeek）")
    base_url = input(f"Base URL [{config.base_url}]: ").strip()
    if base_url:
        config.base_url = base_url
    
    # Model
    print("\n模型名称（直接回车使用默认）")
    model = input(f"Model [{config.model}]: ").strip()
    if model:
        config.model = model
    
    # 保存配置
    save_config(config)
    
    print("\n设置完成！")
    print(f"配置文件: {get_config_path()}")
    print()
    
    return config


# 测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("配置管理测试")
    print("=" * 40)
    
    # 加载配置
    config = load_config()
    print(f"\n当前配置:")
    print(f"  Base URL: {config.base_url}")
    print(f"  Model: {config.model}")
    print(f"  API Key: {'*' * 8 if config.api_key else '(未设置)'}")
    print(f"  记忆目录: {config.memory_dir}")
    
    # 配置目录
    print(f"\n配置目录: {get_config_dir()}")
