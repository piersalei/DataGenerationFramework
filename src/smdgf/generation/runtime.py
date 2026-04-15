"""Batch generation runtime with retry and resume behavior."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

from smdgf.generation.models import (
    GenerationRequest,
    GenerationResult,
    GenerationRunItem,
    GenerationRunManifest,
    ProviderConfig,
)
from smdgf.generation.providers import GenerationProvider


class GenerationRuntime:
    """Execute, checkpoint, and resume generation batches."""

    def __init__(
        self,
        provider: GenerationProvider,
        provider_config: ProviderConfig,
        checkpoint_path: Optional[Path] = None,
        max_retries: int = 1,
    ) -> None:
        self.provider = provider
        self.provider_config = provider_config
        self.checkpoint_path = checkpoint_path
        self.max_retries = max_retries

    def run(
        self,
        run_id: str,
        requests: Iterable[GenerationRequest],
        resume: bool = False,
    ) -> GenerationRunManifest:
        """Run generation requests, optionally resuming from checkpoint state."""

        manifest = self._load_or_initialize_manifest(run_id, list(requests), resume)
        request_map = {request.request_id: request for request in requests}

        for item in manifest.items:
            if item.status == "completed":
                continue
            request = request_map[item.request_id]
            item.status = "running"
            self.checkpoint(manifest)
            result, attempts = self._execute_with_retries(request)
            item.attempts = item.attempts + attempts
            item.seed = request.seed
            item.prompt_fingerprint = request.prompt_metadata.get("prompt_fingerprint")
            if result.status == "completed":
                item.status = "completed"
                item.result = result
                item.error = None
            else:
                item.status = "failed"
                item.result = result
                item.error = result.error
            self.checkpoint(manifest)

        return manifest

    def checkpoint(self, manifest: GenerationRunManifest) -> None:
        """Persist the current manifest state if checkpointing is enabled."""

        if self.checkpoint_path is None:
            return
        manifest.write_json(self.checkpoint_path)

    def _execute_with_retries(
        self, request: GenerationRequest
    ) -> tuple[GenerationResult, int]:
        attempt = 0
        last_result: Optional[GenerationResult] = None
        while attempt <= self.max_retries:
            result = self.provider.generate(request, self.provider_config)
            attempt += 1
            if result.status == "completed":
                return result, attempt
            last_result = result

        if last_result is None:
            raise RuntimeError("runtime reached retry exit without a provider result")
        return last_result, attempt

    def _load_or_initialize_manifest(
        self,
        run_id: str,
        requests: List[GenerationRequest],
        resume: bool,
    ) -> GenerationRunManifest:
        if resume and self.checkpoint_path is not None and self.checkpoint_path.exists():
            return GenerationRunManifest.read_json(self.checkpoint_path)

        items = [
            GenerationRunItem(
                request_id=request.request_id,
                task_id=request.task_id,
                scenario_sample_id=request.scenario_sample.sample_id,
                seed=request.seed,
                prompt_fingerprint=request.prompt_metadata.get("prompt_fingerprint"),
            )
            for request in requests
        ]
        manifest = GenerationRunManifest(
            run_id=run_id,
            provider=self.provider_config,
            items=items,
        )
        self.checkpoint(manifest)
        return manifest
