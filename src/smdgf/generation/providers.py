"""Direct HTTP provider for generation runtime."""

from __future__ import annotations

from typing import Any, Protocol

import requests

from smdgf.generation.models import (
    GenerationError,
    GenerationRequest,
    GenerationResult,
    GenerationUsage,
    ProviderConfig,
)


class GenerationProvider(Protocol):
    """Protocol for normalized provider execution."""

    def generate(
        self, request: GenerationRequest, config: ProviderConfig
    ) -> GenerationResult:
        """Execute a provider call and return normalized output."""


class DirectHTTPProvider:
    """Direct HTTP calls to OpenAI-compatible endpoints."""

    def generate(
        self, request: GenerationRequest, config: ProviderConfig
    ) -> GenerationResult:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key or ''}",
        }
        payload: dict[str, Any] = {
            "model": config.model,
            "messages": [{"role": "user", "content": request.prompt_text}],
            "temperature": config.temperature,
        }
        if config.max_tokens is not None:
            payload["max_tokens"] = config.max_tokens

        base = config.api_base.rstrip("/")
        if "/v1" not in base:
            base = f"{base}/v1"
        url = f"{base}/chat/completions"
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=120)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            return GenerationResult(
                request_id=request.request_id,
                provider_id=config.provider_id,
                model_id=config.model,
                prompt_text=request.prompt_text,
                prompt_fingerprint=str(request.prompt_metadata.get("prompt_fingerprint"))
                if request.prompt_metadata.get("prompt_fingerprint") is not None
                else None,
                status="failed",
                seed=request.seed,
                usage=GenerationUsage(),
                error=GenerationError(
                    error_type=exc.__class__.__name__,
                    message=str(exc),
                    retriable=True,
                    raw_payload={"payload": payload},
                ),
                raw_response={"payload": payload},
            )

        choices = data.get("choices") or []
        first = choices[0] or {}
        message = first.get("message", {}).get("content", "") or ""
        usage = data.get("usage") or {}

        return GenerationResult(
            request_id=request.request_id,
            provider_id=config.provider_id,
            model_id=data.get("model") or config.model,
            prompt_text=request.prompt_text,
            prompt_fingerprint=str(request.prompt_metadata.get("prompt_fingerprint"))
            if request.prompt_metadata.get("prompt_fingerprint") is not None
            else None,
            response_text=message,
            finish_reason=first.get("finish_reason"),
            status="completed",
            seed=request.seed,
            usage=GenerationUsage(
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
            ),
            raw_response=data,
        )
