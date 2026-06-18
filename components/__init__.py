"""
Model Provider - 模型提供者管理组件

提供：
- Provider 注册表
- 动态切换模型
- 本地模型自动检测
- API Key 智能处理
"""

from .model_provider import (
    ModelProviderManager,
    ProviderConfig,
    ModelSwitchResult,
    BUILTIN_PROVIDERS,
)

__all__ = [
    "ModelProviderManager",
    "ProviderConfig",
    "ModelSwitchResult",
    "BUILTIN_PROVIDERS",
]

__version__ = "0.1.0"
