"""ML prediction model — predicts which technologies will trend next."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from src.categorization.normalizer import normalize
from src.categorization.stopwords import is_valid_tech_name
from src.infra.logger import Logger
from src.models import Mention

logger = Logger.get(__name__)

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "trend_model.json"


@dataclass(frozen=True)
class PredictionFeatures:
    """Feature vector for a technology."""

    name: str
    mention_count: int
    source_count: int
    avg_score: float
    max_score: float
    score_variance: float
    has_github: int
    has_hackernews: int
    has_devto: int
    has_lobsters: int


@dataclass(frozen=True)
class TrendPrediction:
    """Model output for a technology."""

    name: str
    will_trend_score: float
    features: PredictionFeatures


class TrendPredictor:
    """Lightweight ML model using weighted feature scoring.

    Uses a trained weight vector to predict trending probability.
    No scikit-learn dependency — weights are stored as JSON.
    """

    def __init__(self) -> None:
        self._weights = self._load_weights()

    def extract_features(self, mentions: list[Mention]) -> list[PredictionFeatures]:
        """Extract feature vectors from mentions grouped by technology."""
        grouped: dict[str, list[Mention]] = {}
        for m in mentions:
            key = normalize(m.name)
            grouped.setdefault(key, []).append(m)

        features: list[PredictionFeatures] = []
        for _, items in grouped.items():
            scores = [m.score for m in items]
            sources = {m.source for m in items}
            best = max(items, key=lambda m: m.score)

            avg = sum(scores) / len(scores) if scores else 0
            variance = sum((s - avg) ** 2 for s in scores) / len(scores) if len(scores) > 1 else 0

            features.append(
                PredictionFeatures(
                    name=best.name,
                    mention_count=len(items),
                    source_count=len(sources),
                    avg_score=round(avg, 2),
                    max_score=max(scores),
                    score_variance=round(variance, 2),
                    has_github=int("github" in sources),
                    has_hackernews=int("hackernews" in sources),
                    has_devto=int("devto" in sources),
                    has_lobsters=int("lobsters" in sources),
                )
            )
        return features

    def predict(self, mentions: list[Mention]) -> list[TrendPrediction]:
        """Predict trending probability for each technology."""
        features = self.extract_features(mentions)
        predictions: list[TrendPrediction] = []

        for f in features:
            if not is_valid_tech_name(f.name):
                continue
            score = self._score_features(f)
            predictions.append(TrendPrediction(name=f.name, will_trend_score=score, features=f))

        predictions.sort(key=lambda p: p.will_trend_score, reverse=True)
        return predictions

    def _score_features(self, f: PredictionFeatures) -> float:
        """Calculate weighted prediction score."""
        w = self._weights
        raw = (
            f.mention_count * w["mention_count"]
            + f.source_count * w["source_count"]
            + f.avg_score * w["avg_score"]
            + f.max_score * w["max_score"]
            + f.score_variance * w["score_variance"]
            + f.has_github * w["has_github"]
            + f.has_hackernews * w["has_hackernews"]
            + f.has_devto * w["has_devto"]
            + f.has_lobsters * w["has_lobsters"]
        )
        clamped = max(-500, min(500, raw))
        return float(round(1 / (1 + math.exp(-clamped)), 4))

    def _load_weights(self) -> dict[str, float]:
        """Load model weights from JSON or use defaults."""
        if MODEL_PATH.exists():
            return dict(json.loads(MODEL_PATH.read_text()))
        return self._default_weights()

    @staticmethod
    def _default_weights() -> dict[str, float]:
        """Heuristic weights — replace with trained weights later."""
        return {
            "mention_count": 0.3,
            "source_count": 0.8,
            "avg_score": 0.001,
            "max_score": 0.0005,
            "score_variance": 0.0001,
            "has_github": 0.5,
            "has_hackernews": 0.4,
            "has_devto": 0.2,
            "has_lobsters": 0.3,
        }

    def save_weights(self, weights: dict[str, float]) -> None:
        """Save trained weights to disk."""
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        MODEL_PATH.write_text(json.dumps(weights, indent=2))
        logger.info("Model weights saved to %s", MODEL_PATH)
