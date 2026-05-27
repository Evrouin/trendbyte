"""Training pipeline — learns from historical predictions vs actual outcomes."""

from __future__ import annotations

import json
from typing import Any

import psycopg
from psycopg.rows import dict_row

from src.analysis.predictor import TrendPredictor
from src.infra.config import Config
from src.infra.logger import Logger

Logger.setup()
logger = Logger.get(__name__)


class TrainingPipeline:
    """Trains the prediction model using historical data.

    Pipeline:
    1. Label — check which past predictions actually trended
    2. Extract — build feature/label pairs from historical mentions
    3. Train — optimize weights via gradient descent
    4. Evaluate — measure accuracy on held-out data
    5. Save — persist new weights if accuracy improved
    """

    def __init__(self, database_url: str) -> None:
        self._db_url = database_url
        self._predictor = TrendPredictor()

    def run(self) -> dict[str, Any]:
        """Execute full training pipeline. Returns metrics."""
        logger.info("Starting training pipeline")

        labeled = self._label_predictions()
        if len(labeled) < 10:
            logger.warning("Not enough labeled data (%d). Need at least 10.", len(labeled))
            return {"status": "skipped", "reason": "insufficient data", "samples": len(labeled)}

        features, labels = self._build_training_set(labeled)

        old_weights = self._predictor._weights.copy()
        new_weights = self._train(features, labels, old_weights)

        old_accuracy = self._evaluate(features, labels, old_weights)
        new_accuracy = self._evaluate(features, labels, new_weights)

        logger.info(
            "Old accuracy: %.2f%%, New accuracy: %.2f%%", old_accuracy * 100, new_accuracy * 100
        )

        if new_accuracy > old_accuracy:
            self._predictor.save_weights(new_weights)
            logger.info("Model improved — weights saved")
        else:
            logger.info("No improvement — keeping existing weights")

        return {
            "status": "complete",
            "samples": len(labeled),
            "old_accuracy": round(old_accuracy, 4),
            "new_accuracy": round(new_accuracy, 4),
            "improved": new_accuracy > old_accuracy,
        }

    def _label_predictions(self) -> list[dict[str, Any]]:
        """Label past predictions: did the tech actually trend within 7 days?"""
        conn = psycopg.connect(self._db_url, row_factory=dict_row)

        predictions = conn.execute(
            "SELECT p.name, p.confidence, p.predicted_at FROM predictions p "
            "WHERE p.predicted_at < NOW() - INTERVAL '7 days' "
            "AND p.outcome = 'pending'"
        ).fetchall()

        labeled = []
        for pred in predictions:
            trended = conn.execute(
                "SELECT 1 FROM trends WHERE LOWER(name) = LOWER(%s) "
                "AND calculated_at BETWEEN %s AND %s + INTERVAL '7 days' "
                "AND score > (SELECT AVG(score) FROM trends WHERE calculated_at BETWEEN %s AND %s + INTERVAL '7 days')",
                (
                    pred["name"],
                    pred["predicted_at"],
                    pred["predicted_at"],
                    pred["predicted_at"],
                    pred["predicted_at"],
                ),
            ).fetchone()

            outcome = "trended" if trended else "not_trended"
            labeled.append({"name": pred["name"], "label": 1 if trended else 0})

            conn.execute(
                "UPDATE predictions SET outcome = %s, resolved_at = NOW() "
                "WHERE name = %s AND predicted_at = %s",
                (outcome, pred["name"], pred["predicted_at"]),
            )

        conn.commit()
        conn.close()
        logger.info("Labeled %d predictions", len(labeled))
        return labeled

    def _build_training_set(
        self, labeled: list[dict[str, Any]]
    ) -> tuple[list[list[float]], list[int]]:
        """Build feature vectors from historical mentions for labeled items."""
        conn = psycopg.connect(self._db_url, row_factory=dict_row)

        features: list[list[float]] = []
        labels: list[int] = []

        for item in labeled:
            row = conn.execute(
                "SELECT "
                "COUNT(*) as mention_count, "
                "COUNT(DISTINCT source) as source_count, "
                "AVG(score) as avg_score, "
                "MAX(score) as max_score, "
                "VARIANCE(score) as score_variance, "
                "COUNT(*) FILTER (WHERE source = 'github') as has_github, "
                "COUNT(*) FILTER (WHERE source = 'hackernews') as has_hn, "
                "COUNT(*) FILTER (WHERE source = 'devto') as has_devto, "
                "COUNT(*) FILTER (WHERE source = 'lobsters') as has_lobsters "
                "FROM mentions WHERE LOWER(name) = LOWER(%s)",
                (item["name"],),
            ).fetchone()

            if not row or row["mention_count"] == 0:
                continue

            features.append(
                [
                    row["mention_count"],
                    row["source_count"],
                    float(row["avg_score"] or 0),
                    float(row["max_score"] or 0),
                    float(row["score_variance"] or 0),
                    min(row["has_github"], 1),
                    min(row["has_hn"], 1),
                    min(row["has_devto"], 1),
                    min(row["has_lobsters"], 1),
                ]
            )
            labels.append(int(item["label"]))

        conn.close()
        return features, labels

    def _train(
        self,
        features: list[list[float]],
        labels: list[int],
        initial_weights: dict[str, float],
        lr: float = 0.01,
        epochs: int = 100,
    ) -> dict[str, float]:
        """Train via gradient descent on logistic loss."""
        keys = list(initial_weights.keys())
        weights = [initial_weights[k] for k in keys]

        for _ in range(epochs):
            gradients = [0.0] * len(weights)
            for x, y in zip(features, labels, strict=False):
                pred = self._sigmoid(sum(w * xi for w, xi in zip(weights, x, strict=False)))
                error = pred - y
                for j in range(len(weights)):
                    gradients[j] += error * x[j]

            n = len(features)
            for j in range(len(weights)):
                weights[j] -= lr * (gradients[j] / n)

        return dict(zip(keys, [round(w, 6) for w in weights], strict=False))

    def _evaluate(
        self,
        features: list[list[float]],
        labels: list[int],
        weights: dict[str, float],
    ) -> float:
        """Calculate accuracy with given weights."""
        keys = list(weights.keys())
        w = [weights[k] for k in keys]
        correct = 0

        for x, y in zip(features, labels, strict=False):
            pred = self._sigmoid(sum(wi * xi for wi, xi in zip(w, x, strict=False)))
            predicted_label = 1 if pred >= 0.5 else 0
            if predicted_label == y:
                correct += 1

        return correct / len(labels) if labels else 0.0

    @staticmethod
    def _sigmoid(x: float) -> float:
        x = max(min(x, 500), -500)
        return float(1 / (1 + 2.718 ** (-x)))


def train() -> None:
    """Entry point for training."""
    config = Config.from_env()
    pipeline = TrainingPipeline(config.database_url)
    result = pipeline.run()
    logger.info("Training result: %s", json.dumps(result))

    try:
        from src.analysis.classifier import train as train_classifier

        train_classifier()
        logger.info("Category classifier trained successfully")
    except Exception as e:
        logger.warning("Category classifier training failed: %s", e)


if __name__ == "__main__":
    train()
