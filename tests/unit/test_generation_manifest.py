from pathlib import Path

from smdgf.generation import GenerationRequest, GenerationRuntime, GenerationUsage, ProviderConfig
from smdgf.generation.models import GenerationResult, GenerationRunManifest
from smdgf.schemas import (
    LatentStateAssignment,
    SampledRole,
    ScenarioSample,
)


class SuccessProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, request: GenerationRequest, config: ProviderConfig) -> GenerationResult:
        self.calls += 1
        return GenerationResult(
            request_id=request.request_id,
            provider_id=config.provider_id,
            model_id=config.model,
            prompt_text=request.prompt_text,
            prompt_fingerprint=request.prompt_metadata.get("prompt_fingerprint"),
            response_text="candidate response",
            status="completed",
            seed=request.seed,
            usage=GenerationUsage(prompt_tokens=5, completion_tokens=7, total_tokens=12),
            raw_response={"id": "raw-1"},
        )


def make_request() -> GenerationRequest:
    scenario = ScenarioSample(
        sample_id="scenario-1",
        template_id="template-1",
        task_id="emotion.typical",
        scene_blueprint="{target} receives help.",
        sampled_slots={"target": "Mina"},
        roles=[SampledRole(role_id="target", role_type="agent", display_name="Mina")],
        relations=[],
        latent_state_assignments=[
            LatentStateAssignment(
                state_id="target-emotion",
                owner_role="target",
                state_type="emotion",
                value="grateful",
                sampling_strategy="choice",
            )
        ],
        provenance={"seed": 21},
    )
    return GenerationRequest(
        request_id="req-manifest-1",
        task_id="emotion.typical",
        scenario_sample=scenario,
        prompt_text="Prompt text for manifest.",
        provider="openai",
        model="gpt-4o-mini",
        seed=21,
        prompt_metadata={"prompt_fingerprint": "manifest-fingerprint"},
    )


def run_once(path: Path, provider: SuccessProvider) -> GenerationRunManifest:
    runtime = GenerationRuntime(
        provider=provider,
        provider_config=ProviderConfig(provider_id="openai", model="gpt-4o-mini"),
        checkpoint_path=path,
        max_retries=0,
    )
    return runtime.run("run-manifest", [make_request()], resume=False)


def test_manifest_records_prompt_seed_provider_and_response(tmp_path: Path) -> None:
    manifest = run_once(tmp_path / "manifest.json", SuccessProvider())
    item = manifest.items[0]

    assert item.status == "completed"
    assert item.seed == 21
    assert item.prompt_fingerprint == "manifest-fingerprint"
    assert item.result is not None
    assert item.result.provider_id == "openai"
    assert item.result.model_id == "gpt-4o-mini"
    assert item.result.prompt_text == "Prompt text for manifest."
    assert item.result.response_text == "candidate response"
    assert item.result.usage.total_tokens == 12


def test_manifest_round_trip_preserves_item_status(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    manifest = run_once(path, SuccessProvider())
    loaded = GenerationRunManifest.read_json(path)

    assert loaded.run_id == manifest.run_id
    assert loaded.items[0].status == "completed"
    assert loaded.items[0].result is not None
    assert loaded.items[0].result.response_text == "candidate response"


def test_manifest_backed_rerun_skips_completed_items(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    run_once(path, SuccessProvider())

    provider = SuccessProvider()
    runtime = GenerationRuntime(
        provider=provider,
        provider_config=ProviderConfig(provider_id="openai", model="gpt-4o-mini"),
        checkpoint_path=path,
        max_retries=0,
    )
    manifest = runtime.run("run-manifest", [make_request()], resume=True)

    assert manifest.items[0].status == "completed"
    assert provider.calls == 0
