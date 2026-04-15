"""Provider adapter interfaces for generation runtime."""

from __future__ import annotations

from typing import Any, Callable, Optional, Protocol

from smdgf.generation.models import (
    GenerationError,
    GenerationRequest,
    GenerationResult,
    GenerationUsage,
    ProviderConfig,
)

try:
    from litellm import completion as litellm_completion
except Exception:  # pragma: no cover - import fallback for environments without deps installed
    litellm_completion = None


class GenerationProvider(Protocol):
    """Protocol for normalized provider execution."""

    def generate(
        self, request: GenerationRequest, config: ProviderConfig
    ) -> GenerationResult:
        """Execute a provider call and return normalized output."""


class LiteLLMGenerationProvider:
    """LiteLLM-backed generation provider using framework-owned request/result models."""

    def __init__(
        self,
        completion_callable: Optional[Callable[..., Any]] = None,
    ) -> None:
        self._completion_callable = completion_callable or litellm_completion

    def generate(
        self, request: GenerationRequest, config: ProviderConfig
    ) -> GenerationResult:
        if self._completion_callable is None:
            raise RuntimeError("LiteLLM completion callable is not available")

        payload = self._build_payload(request, config)
        try:
            raw_response = self._completion_callable(**payload)
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

        return self._normalize_success(request, config, payload, raw_response)

    def _build_payload(
        self, request: GenerationRequest, config: ProviderConfig
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": config.model,
            "messages": [{"role": "user", "content": request.prompt_text}],
            "temperature": config.temperature,
        }
        if config.max_tokens is not None:
            payload["max_tokens"] = config.max_tokens
        if config.api_base:
            payload["api_base"] = config.api_base
        payload.update(config.extra_options)
        return payload

    def _normalize_success(
        self,
        request: GenerationRequest,
        config: ProviderConfig,
        payload: dict[str, Any],
        raw_response: Any,
    ) -> GenerationResult:
        response_dict = self._as_dict(raw_response)
        choices = response_dict.get("choices") or []
        message = ""
        finish_reason = None
        if choices:
            first_choice = choices[0] or {}
            finish_reason = first_choice.get("finish_reason")
            message_payload = first_choice.get("message") or {}
            message = str(message_payload.get("content") or "")
        usage_payload = response_dict.get("usage") or {}

        return GenerationResult(
            request_id=request.request_id,
            provider_id=config.provider_id,
            model_id=str(response_dict.get("model") or config.model),
            prompt_text=request.prompt_text,
            prompt_fingerprint=str(request.prompt_metadata.get("prompt_fingerprint"))
            if request.prompt_metadata.get("prompt_fingerprint") is not None
            else None,
            response_text=message,
            finish_reason=finish_reason,
            status="completed",
            seed=request.seed,
            usage=GenerationUsage(
                prompt_tokens=usage_payload.get("prompt_tokens"),
                completion_tokens=usage_payload.get("completion_tokens"),
                total_tokens=usage_payload.get("total_tokens"),
            ),
            raw_response=response_dict or {"payload": payload},
        )

    @staticmethod
    def _as_dict(raw_response: Any) -> dict[str, Any]:
        if hasattr(raw_response, "model_dump"):
            return raw_response.model_dump()
        if isinstance(raw_response, dict):
            return raw_response
        return {"raw_response": str(raw_response)}
