#!/usr/bin/env python3
"""
Model Provider - 模型提供者管理组件

从 Hermes 精简而来，提供：
- Provider 注册表（DeepSeek、OpenAI、本地 llama.cpp 等）
- 动态切换模型
- 本地模型自动检测
- API Key 智能处理（本地可跳过）

用法：
    from model_provider import ModelProviderManager
    
    manager = ModelProviderManager()
    manager.add_provider("local", base_url="http://localhost:8080/v1")
    manager.switch_model("llama3", provider="local")
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider 定义
# ---------------------------------------------------------------------------

@dataclass
class ProviderConfig:
    """Provider 配置"""
    
    id: str
    name: str
    base_url: str
    api_key: str = ""
    default_model: str = ""
    
    # 是否需要 API Key（本地模型通常不需要）
    requires_api_key: bool = True
    
    # 模型列表（可选，用于自动检测）
    models: List[str] = field(default_factory=list)
    
    def is_local(self) -> bool:
        """是否是本地 provider"""
        parsed = urlparse(self.base_url)
        return parsed.hostname in ("localhost", "127.0.0.1", "::1")


@dataclass
class ModelSwitchResult:
    """模型切换结果"""
    
    success: bool
    provider_id: str = ""
    model: str = ""
    base_url: str = ""
    api_key: str = ""
    error_message: str = ""
    auto_detected: bool = False


# ---------------------------------------------------------------------------
# 内置 Provider 模板
# ---------------------------------------------------------------------------

BUILTIN_PROVIDERS: Dict[str, Dict[str, Any]] = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "requires_api_key": True,
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4",
        "requires_api_key": True,
    },
    "local-llama": {
        "name": "Local (llama.cpp)",
        "base_url": "http://localhost:8080/v1",
        "default_model": "",
        "requires_api_key": False,
    },
    "local-ollama": {
        "name": "Local (Ollama)",
        "base_url": "http://localhost:11434/v1",
        "default_model": "",
        "requires_api_key": False,
    },
}


# ---------------------------------------------------------------------------
# Model Provider Manager
# ---------------------------------------------------------------------------

class ModelProviderManager:
    """
    模型提供者管理器
    
    功能：
    - 注册/管理多个 Provider
    - 动态切换模型
    - 自动检测本地模型
    - 智能处理 API Key
    """
    
    def __init__(self):
        """初始化管理器"""
        self.providers: Dict[str, ProviderConfig] = {}
        self.current_provider_id: str = ""
        self.current_model: str = ""
        
        # 加载内置 Provider
        for pid, pconfig in BUILTIN_PROVIDERS.items():
            self.providers[pid] = ProviderConfig(
                id=pid,
                name=pconfig["name"],
                base_url=pconfig["base_url"],
                default_model=pconfig.get("default_model", ""),
                requires_api_key=pconfig.get("requires_api_key", True),
            )
    
    # -----------------------------------------------------------------------
    # Provider 管理
    # -----------------------------------------------------------------------
    
    def add_provider(
        self,
        provider_id: str,
        name: str,
        base_url: str,
        api_key: str = "",
        default_model: str = "",
        requires_api_key: bool = True,
    ) -> ProviderConfig:
        """
        添加自定义 Provider
        
        Args:
            provider_id: Provider 唯一标识
            name: 显示名称
            base_url: API Base URL
            api_key: API Key（可选）
            default_model: 默认模型名
            requires_api_key: 是否需要 API Key
        
        Returns:
            创建的 ProviderConfig
        """
        provider = ProviderConfig(
            id=provider_id,
            name=name,
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            default_model=default_model,
            requires_api_key=requires_api_key,
        )
        self.providers[provider_id] = provider
        logger.info(f"Provider 已添加: {name} ({base_url})")
        return provider
    
    def get_provider(self, provider_id: str) -> Optional[ProviderConfig]:
        """获取 Provider 配置"""
        return self.providers.get(provider_id)
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """列出所有 Provider"""
        result = []
        for pid, pconfig in self.providers.items():
            result.append({
                "id": pid,
                "name": pconfig.name,
                "base_url": pconfig.base_url,
                "is_local": pconfig.is_local(),
                "is_current": pid == self.current_provider_id,
                "default_model": pconfig.default_model,
            })
        return result
    
    # -----------------------------------------------------------------------
    # 模型切换
    # -----------------------------------------------------------------------
    
    def switch_model(
        self,
        model: str,
        provider_id: str = "",
        api_key: str = "",
    ) -> ModelSwitchResult:
        """
        切换模型
        
        Args:
            model: 模型名称
            provider_id: Provider ID（可选，不指定则用当前）
            api_key: API Key（可选，覆盖 Provider 默认）
        
        Returns:
            ModelSwitchResult
        """
        # 确定 Provider
        if provider_id:
            provider = self.get_provider(provider_id)
            if not provider:
                return ModelSwitchResult(
                    success=False,
                    error_message=f"Provider '{provider_id}' 不存在",
                )
        elif self.current_provider_id:
            provider = self.get_provider(self.current_provider_id)
        else:
            # 默认使用第一个
            if not self.providers:
                return ModelSwitchResult(
                    success=False,
                    error_message="没有可用的 Provider",
                )
            provider = next(iter(self.providers.values()))
        
        # 处理 API Key
        effective_api_key = api_key or provider.api_key
        
        # 本地 Provider 自动处理 API Key
        if provider.is_local():
            if not effective_api_key:
                effective_api_key = "no-key-required"
                logger.info("本地 Provider，自动跳过 API Key 验证")
        
        # 检查 API Key
        if provider.requires_api_key and not effective_api_key:
            return ModelSwitchResult(
                success=False,
                error_message=f"Provider '{provider.name}' 需要 API Key",
            )
        
        # 如果模型名为空，尝试自动检测
        if not model and provider.is_local():
            detected = self._auto_detect_model(provider.base_url, effective_api_key)
            if detected:
                model = detected
                logger.info(f"自动检测到模型: {model}")
            else:
                return ModelSwitchResult(
                    success=False,
                    error_message="无法自动检测模型，请手动指定",
                )
        
        # 更新当前状态
        self.current_provider_id = provider.id
        self.current_model = model or provider.default_model
        
        return ModelSwitchResult(
            success=True,
            provider_id=provider.id,
            model=self.current_model,
            base_url=provider.base_url,
            api_key=effective_api_key,
            auto_detected=(not model),
        )
    
    def _auto_detect_model(self, base_url: str, api_key: str) -> str:
        """
        自动检测本地模型
        
        调用 /v1/models 端点获取可用模型
        
        Args:
            base_url: API Base URL
            api_key: API Key
        
        Returns:
            检测到的模型名，失败返回空字符串
        """
        try:
            import httpx
            
            url = f"{base_url}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url, headers=headers)
                
                if not response.is_success:
                    return ""
                
                data = response.json()
                models = data.get("data", [])
                
                if not models:
                    return ""
                
                # 如果只有一个模型，直接返回
                if len(models) == 1:
                    return models[0].get("id", "")
                
                # 多个模型时，返回第一个（通常是默认的）
                return models[0].get("id", "")
                
        except Exception as e:
            logger.debug(f"自动检测模型失败: {e}")
            return ""
    
    # -----------------------------------------------------------------------
    # 当前状态
    # -----------------------------------------------------------------------
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        if not self.current_provider_id:
            return {}
        
        provider = self.get_provider(self.current_provider_id)
        if not provider:
            return {}
        
        return {
            "provider_id": self.current_provider_id,
            "provider_name": provider.name,
            "model": self.current_model,
            "base_url": provider.base_url,
            "api_key": provider.api_key,
            "is_local": provider.is_local(),
        }
    
    # -----------------------------------------------------------------------
    # 便捷方法
    # -----------------------------------------------------------------------
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "ModelProviderManager":
        """
        从配置字典创建
        
        配置格式：
        {
            "providers": {
                "my-local": {
                    "name": "My Local",
                    "base_url": "http://localhost:8080/v1",
                    "requires_api_key": False
                }
            },
            "current_provider": "my-local",
            "current_model": "llama3"
        }
        """
        manager = cls()
        
        # 添加自定义 Provider
        for pid, pconfig in config.get("providers", {}).items():
            manager.add_provider(
                provider_id=pid,
                name=pconfig.get("name", pid),
                base_url=pconfig.get("base_url", ""),
                api_key=pconfig.get("api_key", ""),
                default_model=pconfig.get("default_model", ""),
                requires_api_key=pconfig.get("requires_api_key", True),
            )
        
        # 设置当前 Provider
        if config.get("current_provider"):
            manager.current_provider_id = config["current_provider"]
        
        if config.get("current_model"):
            manager.current_model = config["current_model"]
        
        return manager
    
    def to_config(self) -> Dict[str, Any]:
        """导出为配置字典"""
        providers = {}
        for pid, pconfig in self.providers.items():
            providers[pid] = {
                "name": pconfig.name,
                "base_url": pconfig.base_url,
                "api_key": pconfig.api_key,
                "default_model": pconfig.default_model,
                "requires_api_key": pconfig.requires_api_key,
            }
        
        return {
            "providers": providers,
            "current_provider": self.current_provider_id,
            "current_model": self.current_model,
        }


# ---------------------------------------------------------------------------
# 命令行测试
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Model Provider Manager 测试")
    print("=" * 40)
    
    # 创建管理器
    manager = ModelProviderManager()
    
    # 列出内置 Provider
    print("\n内置 Provider:")
    for p in manager.list_providers():
        local_tag = " [本地]" if p["is_local"] else ""
        print(f"  - {p['name']}{local_tag}: {p['base_url']}")
    
    # 添加自定义本地 Provider
    manager.add_provider(
        provider_id="my-llama",
        name="My llama.cpp",
        base_url="http://localhost:8080/v1",
        requires_api_key=False,
    )
    
    print("\n添加自定义 Provider 后:")
    for p in manager.list_providers():
        local_tag = " [本地]" if p["is_local"] else ""
        current_tag = " [当前]" if p["is_current"] else ""
        print(f"  - {p['name']}{local_tag}{current_tag}: {p['base_url']}")
    
    # 测试切换（会失败，因为没有本地服务）
    print("\n测试切换到本地模型...")
    result = manager.switch_model("llama3", provider_id="my-llama")
    if result.success:
        print(f"  成功: {result.model} @ {result.base_url}")
    else:
        print(f"  失败: {result.error_message}")
    
    print("\n测试完成")
