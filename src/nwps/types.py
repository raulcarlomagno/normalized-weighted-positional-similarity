from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class NWPSResult:
    """Stable result object returned by all NWPS evaluators.

    For a complete prediction, ``lower_bound == upper_bound`` and ``score``
    returns that point value. For a right-censored prediction, ``score`` is
    ``None`` and the fidelity is represented by the interval.
    """

    lower_bound: float
    upper_bound: float
    weighted_coverage_observed: float
    conditional_positional_fidelity_observed: float
    half_life: float
    reference_depth: int
    observed_prediction_depth: int
    is_censored: bool
    upper_bound_method: str = "point"

    @property
    def score(self) -> float | None:
        if self.is_censored:
            return None
        return self.lower_bound

    @property
    def interval_width(self) -> float:
        return self.upper_bound - self.lower_bound

    def as_dict(self) -> dict[str, float | int | bool | str | None]:
        return {
            "score": self.score,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "weighted_coverage_observed": self.weighted_coverage_observed,
            "conditional_positional_fidelity_observed": self.conditional_positional_fidelity_observed,
            "half_life": self.half_life,
            "reference_depth": self.reference_depth,
            "observed_prediction_depth": self.observed_prediction_depth,
            "is_censored": self.is_censored,
            "upper_bound_method": self.upper_bound_method,
        }
