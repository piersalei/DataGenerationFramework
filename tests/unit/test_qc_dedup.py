from smdgf.qc import QualityCandidate
from smdgf.qc.dedup import detect_duplicates, detect_near_duplicates, fingerprint_candidate
from smdgf.schemas import CanonicalAnswer, CanonicalQuestion, CanonicalSample


def make_candidate(candidate_id: str, question_text: str, *, answer: str = "grateful") -> QualityCandidate:
    sample = CanonicalSample(
        sample_id=f"sample-{candidate_id}",
        task_id="emotion.typical",
        scene_text="Mina receives help from a teammate before a talk.",
        latent_state={"Mina": {"emotion": "grateful"}},
        questions=[
            CanonicalQuestion(
                question_id="q1",
                text=question_text,
                target_capability="emotion",
            )
        ],
        answers=[CanonicalAnswer(question_id="q1", value=answer)],
    )
    return QualityCandidate(candidate_id=candidate_id, canonical_sample=sample)


def test_exact_duplicate_detector_flags_same_canonical_signature() -> None:
    left = make_candidate("candidate-a", "How does Mina feel after the help?")
    right = make_candidate("candidate-b", "How does Mina feel after the help?")

    clusters = detect_duplicates([left, right])

    assert fingerprint_candidate(left) == fingerprint_candidate(right)
    assert len(clusters) == 1
    assert clusters[0].cluster_type == "exact"


def test_near_duplicate_detector_groups_similar_questions() -> None:
    left = make_candidate("candidate-a", "How does Mina feel after the help?")
    right = make_candidate("candidate-b", "What emotion does Mina feel after receiving help?")

    clusters = detect_near_duplicates([left, right], threshold=0.35)

    assert len(clusters) == 1
    assert clusters[0].cluster_type == "near"
    assert clusters[0].score is not None
    assert clusters[0].score >= 0.35


def test_duplicate_clusters_include_member_ids_and_reason() -> None:
    left = make_candidate("candidate-a", "How does Mina feel after the help?")
    right = make_candidate("candidate-b", "How does Mina feel after the help?")

    cluster = detect_duplicates([left, right])[0]

    assert cluster.member_ids == ["candidate-a", "candidate-b"]
    assert cluster.reason == "matching canonical fingerprint"
