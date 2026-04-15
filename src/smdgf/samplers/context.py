"""Deterministic sampling context helpers."""

from __future__ import annotations

import hashlib
import random
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


T = TypeVar("T")


class SamplingContext(BaseModel):
    """Stable RNG wrapper used throughout sampling."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    seed: int
    metadata: dict[str, str] = Field(default_factory=dict)
    rng: random.Random = Field(default_factory=random.Random)

    _rng: random.Random = PrivateAttr()

    def model_post_init(self, __context: object) -> None:
        self._rng = random.Random(self.seed)
        self.rng = self._rng

    def choose(self, values: list[T]) -> T:
        """Choose one item deterministically from a non-empty list."""

        if not values:
            raise ValueError("values must not be empty")
        return values[self._rng.randrange(len(values))]

    def shuffle_copy(self, values: list[T]) -> list[T]:
        """Return a deterministically shuffled copy of values."""

        shuffled = list(values)
        self._rng.shuffle(shuffled)
        return shuffled

    def child(self, label: str) -> "SamplingContext":
        """Derive a stable child RNG from the current seed and a label."""

        digest = hashlib.sha256(f"{self.seed}:{label}".encode("utf-8")).hexdigest()
        child_seed = int(digest[:16], 16)
        metadata = dict(self.metadata)
        metadata["parent_seed"] = str(self.seed)
        metadata["label"] = label
        return SamplingContext(seed=child_seed, metadata=metadata)
