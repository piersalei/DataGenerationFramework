from pathlib import Path

from smdgf.generation import (
    GenerationRequest,
    GenerationRunManifest,
    GenerationRuntime,
    GenerationUsage,
    ProviderConfig,
)
from smdgf.generation.models import GenerationError, GenerationResult
from smdgf.schemas import (
    LatentStateAssignment,
    SampledRelation,
    SampledRole,
    ScenarioSample,
)


class StubProvider:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def generate(self, request: GenerationRequest, config: ProviderConfig) -> GenerationResult:
        outcome = self.outcomes[min(self.calls, len(self.outcomes) - 1)]
        self.calls += 1
        if outcome == "success":
            return GenerationResult(
                request_id=request.request_id,
                provider_id=config.provider_id,
                model_id=config.model,
                prompt_text=request.prompt_text,
                prompt_fingerprint=request.prompt_metadata.get("prompt_fingerprint"),
                response_text="generated answer",
                status="completed",
                seed=request.seed,
                usage=GenerationUsage(total_tokens=12),
            )
        return GenerationResult(
            request_id=request.request_id,
            provider_id=config.provider_id,
            model_id=config.model,
            prompt_text=request.prompt_text,
            prompt_fingerprint=request.prompt_metadata.get("prompt_fingerprint"),
            response_text=None,
            status="failed",
            seed=request.seed,
            error=GenerationError(
                error_type="RuntimeError",
                message="temporary failure",
                retriable=True,
            ),
        )


def make_request(request_id: str = "req-1") -> GenerationRequest:
    sample = ScenarioSample(
        sample_id="sample-1",
        template_id="template-1",
        task_id="belief.false_location",
        scene_blueprint="{observer} watches {actor}.",
        sampled_slots={"observer": "Mina", "actor": "Jun"},
        roles=[
            SampledRole(role_id="observer", role_type="agent", display_name="Mina"),
            SampledRole(role_id="actor", role_type="agent", display_name="Jun"),
        ],
        relations=[
            SampledRelation(
                relation_id="rel-1",
                source_role="observer",
                relation_type="observes",
                target_role="actor",
            )
        ],
        latent_state_assignments=[
            LatentStateAssignment(
                state_id="belief-location",
                owner_role="observer",
                state_type="belief",
                value="drawer",
                sampling_strategy="choice",
            )
        ],
        provenance={"seed": 17},
    )
    return GenerationRequest(
        request_id=request_id,
        task_id="belief.false_location",
        scenario_sample=sample,
        prompt_text="Prompt text",
        provider="openai",
        model="gpt-4o-mini",
        seed=17,
        prompt_metadata={"prompt_fingerprint": "fingerprint-1"},
    )


def test_runtime_resume_skips_completed_requests(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "manifest.json"
    config = ProviderConfig(provider_id="openai", model="gpt-4o-mini")

    runtime = GenerationRuntime(
        provider=StubProvider(["success"]),
        provider_config=config,
        checkpoint_path=checkpoint_path,
        max_retries=0,
    )
    manifest = runtime.run("run-1", [make_request()], resume=False)
    assert manifest.items[0].status == "completed"

    resume_provider = StubProvider(["success"])
    resumed_runtime = GenerationRuntime(
        provider=resume_provider,
        provider_config=config,
        checkpoint_path=checkpoint_path,
        max_retries=0,
    )
    resumed_manifest = resumed_runtime.run("run-1", [make_request()], resume=True)

    assert resumed_manifest.items[0].status == "completed"
    assert resume_provider.calls == 0


def test_runtime_retries_failed_requests_before_marking_failed(tmp_path: Path) -> None:
    runtime = GenerationRuntime(
        provider=StubProvider(["failed", "success"]),
        provider_config=ProviderConfig(provider_id="openai", model="gpt-4o-mini"),
        checkpoint_path=tmp_path / "manifest.json",
        max_retries=1,
    )

    manifest = runtime.run("run-2", [make_request()], resume=False)

    assert manifest.items[0].status == "completed"
    assert manifest.items[0].result is not None
    assert manifest.items[0].result.response_text == "generated answer"


def test_runtime_records_explicit_item_status_transitions(tmp_path: Path) -> None:
    runtime = GenerationRuntime(
        provider=StubProvider(["failed", "failed"]),
        provider_config=ProviderConfig(provider_id="openai", model="gpt-4o-mini"),
        checkpoint_path=tmp_path / "manifest.json",
        max_retries=1,
    )

    manifest = runtime.run("run-3", [make_request("req-3")], resume=False)

    assert isinstance(manifest, GenerationRunManifest)
    assert manifest.items[0].status == "failed"
    assert manifest.items[0].error is not None
    assert manifest.items[0].prompt_fingerprint == "fingerprint-1"
