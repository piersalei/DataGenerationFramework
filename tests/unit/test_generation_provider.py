from smdgf.generation import (
    GenerationRequest,
    GenerationResult,
    LiteLLMGenerationProvider,
    ProviderConfig,
)
from smdgf.schemas import (
    LatentStateAssignment,
    SampledRelation,
    SampledRole,
    ScenarioSample,
)


def make_scenario_sample() -> ScenarioSample:
    return ScenarioSample(
        sample_id="sample-1",
        template_id="template-1",
        task_id="belief.false_location",
        scene_blueprint="{observer} watches {actor}.",
        sampled_slots={"observer": "Mina", "actor": "Jun"},
        roles=[
            SampledRole(
                role_id="observer",
                role_type="agent",
                display_name="Mina",
            ),
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
                state_id="belief-1",
                owner_role="observer",
                state_type="belief",
                value="drawer",
                sampling_strategy="choice",
            )
        ],
        provenance={"seed": 9},
    )


def make_request() -> GenerationRequest:
    return GenerationRequest(
        request_id="req-1",
        task_id="belief.false_location",
        scenario_sample=make_scenario_sample(),
        prompt_text="Answer the belief question.",
        provider="openai",
        model="gpt-4o-mini",
        seed=9,
        prompt_metadata={"prompt_fingerprint": "fingerprint-1"},
    )


def test_provider_config_supports_local_and_remote_backends() -> None:
    remote = ProviderConfig(provider_id="openai", model="gpt-4o-mini", mode="remote")
    local = ProviderConfig(
        provider_id="ollama",
        model="llama3.1",
        mode="local",
        api_base="http://localhost:11434",
    )

    assert remote.mode == "remote"
    assert local.mode == "local"
    assert local.api_base == "http://localhost:11434"


def test_generation_result_captures_provider_provenance() -> None:
    provider = LiteLLMGenerationProvider(
        completion_callable=lambda **_: {
            "model": "gpt-4o-mini",
            "choices": [
                {"message": {"content": "Belief answer"}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
        }
    )

    result = provider.generate(
        make_request(),
        ProviderConfig(provider_id="openai", model="gpt-4o-mini"),
    )

    assert isinstance(result, GenerationResult)
    assert result.provider_id == "openai"
    assert result.model_id == "gpt-4o-mini"
    assert result.prompt_fingerprint == "fingerprint-1"
    assert result.response_text == "Belief answer"
    assert result.usage.total_tokens == 14


def test_litellm_provider_normalizes_error_payloads() -> None:
    def explode(**_: object) -> dict[str, object]:
        raise RuntimeError("provider unavailable")

    provider = LiteLLMGenerationProvider(completion_callable=explode)
    result = provider.generate(
        make_request(),
        ProviderConfig(provider_id="openai", model="gpt-4o-mini"),
    )

    assert result.status == "failed"
    assert result.error is not None
    assert result.error.error_type == "RuntimeError"
    assert "provider unavailable" in result.error.message
