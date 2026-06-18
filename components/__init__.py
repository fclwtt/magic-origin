"""
Components - 可插拔组件模块

组件是可选的功能模块，可以独立启用/禁用。

可用组件：
- model_provider: 模型提供者管理（多 Provider 支持、动态切换）
"""

# 组件注册表
AVAILABLE_COMPONENTS = {
    "model_provider": {
        "name": "Model Provider",
        "description": "模型提供者管理，支持多 Provider 和动态切换",
        "module": "components.model_provider",
        "required": False,
    },
}


def get_component(name: str):
    """动态加载组件"""
    if name not in AVAILABLE_COMPONENTS:
        return None
    
    try:
        import importlib
        module = importlib.import_module(AVAILABLE_COMPONENTS[name]["module"])
        return module
    except ImportError as e:
        return None


__all__ = ["AVAILABLE_COMPONENTS", "get_component"]
