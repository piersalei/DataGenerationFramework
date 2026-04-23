"""Simple config: one place to set model / provider / API key / base URL."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml


# 预定义的 provider 映射，key = 用户写的简短名字
PROVIDER_ALIASES: dict[str, dict] = {
    "openai": {
        "provider_id": "openai",
        "default_model": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
        "api_base_default": None,
        "api_base_env": "OPENAI_API_BASE",
    },
    "anthropic": {
        "provider_id": "anthropic",
        "default_model": "claude-3-5-haiku-20241022",
        "api_key_env": "ANTHROPIC_API_KEY",
        "api_base_default": "https://api.anthropic.com",
        "api_base_env": "ANTHROPIC_API_BASE",
    },
    "ollama": {
        "provider_id": "ollama",
        "default_model": "llama3",
        "api_key_env": None,
        "api_base_default": "http://localhost:11434",
        "api_base_env": None,
    },
}


class Config:
    """One-stop config for generation.

    用法::

        config = Config("openai", model="gpt-4o-mini", api_key="sk-...")
        config = Config("anthropic", model="claude-3-5-sonnet-20241022", api_key="sk-ant-...")
        config = Config("ollama", model="llama3", api_base="http://localhost:11434")

        # 然后传给 provider
        from smdgf.generation import ProviderConfig
        provider_cfg = config.to_provider_config()
    """

    def __init__(
        self,
        provider: Literal["openai", "anthropic", "ollama"] | None = None,
        model: str | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        *,
        config_file: Path | None = None,
    ) -> None:
        """初始化配置。

        Args:
            provider: "openai" / "anthropic" / "ollama"
            model: 模型名，不填则用默认值
            api_key: API key，不填则从环境变量读取
            api_base: API base URL，不填则用默认值（ollama 需要填）
            temperature: 生成温度，默认 0.0
            max_tokens: 最大 token 数，默认不限
            config_file: 可选，从 YAML 文件加载配置（provider 可省略）
        """
        if config_file and config_file.exists():
            self._from_file(config_file)
        else:
            if provider is None:
                raise TypeError("provider is required unless loading from config_file")
            alias = PROVIDER_ALIASES[provider]
            self.provider = provider
            self.model = model or alias["default_model"]
            self.api_key = api_key or os.environ.get(alias["api_key_env"] or "")
            # api_base 优先：参数 > 环境变量 > 默认值
            base_env = alias.get("api_base_env")
            self.api_base = api_base or (os.environ[base_env] if base_env and base_env in os.environ else None) or alias["api_base_default"]
            self.temperature = temperature
            self.max_tokens = max_tokens

        self._apply_env()

    def _from_file(self, path: Path) -> None:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        p = data.get("provider", "openai")
        alias = PROVIDER_ALIASES[p]
        self.provider = p
        self.model = data.get("model") or alias["default_model"]
        self.api_key = data.get("api_key") or os.environ.get(alias["api_key_env"] or "")
        base_env = alias.get("api_base_env")
        default = os.environ[base_env] if base_env and base_env in os.environ else alias["api_base_default"]
        self.api_base = data.get("api_base") or default
        self.temperature = data.get("temperature", 0.0)
        self.max_tokens = data.get("max_tokens")

    def _apply_env(self) -> None:
        """把 api_key 写入环境变量（供 LiteLLM 读取）。"""
        if self.api_key:
            alias = PROVIDER_ALIASES[self.provider]
            if alias["api_key_env"]:
                os.environ[alias["api_key_env"]] = self.api_key
        if self.api_base:
            alias = PROVIDER_ALIASES[self.provider]
            base_env = alias.get("api_base_env")
            if base_env:
                os.environ[base_env] = self.api_base

    def to_provider_config(self) -> "ProviderConfig":
        """转成框架的 ProviderConfig。"""
        from smdgf.generation.models import ProviderConfig

        return ProviderConfig(
            provider_id=PROVIDER_ALIASES[self.provider]["provider_id"],
            model=self.model,
            api_base=self.api_base,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """从 YAML 文件加载配置。

        示例 config.yaml::

            provider: openai
            model: gpt-4o-mini
            api_key: sk-...        # 可省略，从环境变量读
            api_base: https://your-proxy.com/v1  # 可省略，用第三方代理时填
            temperature: 0.0
        """
        return cls(config_file=path)

    def save_template(self, path: Path) -> None:
        """保存配置模板到文件。"""
        template = {
            "provider": self.provider,
            "model": self.model,
            "api_key": "",          # 留空，手动填写
            "api_base": self.api_base or "",
            "temperature": self.temperature,
            "max_tokens": self.max_tokens or "",
        }
        path.write_text(yaml.dump(template, allow_unicode=True), encoding="utf-8")
