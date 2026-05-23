"""Category auto-classifier using TF-IDF + Logistic Regression."""

from __future__ import annotations

from pathlib import Path

import joblib
import psycopg
from psycopg.rows import dict_row
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.config import Config

MODEL_PATH = Path("models/category_model.pkl")


def train() -> None:
    """Train the classifier from DB mentions that have known categories."""
    config = Config.from_env()
    conn = psycopg.connect(config.database_url, row_factory=dict_row)

    rows = conn.execute(
        "SELECT m.description, c.name as category "
        "FROM mentions m "
        "JOIN category_keywords ck ON LOWER(m.name) = ck.keyword "
        "JOIN categories c ON c.id = ck.category_id "
        "WHERE m.description IS NOT NULL AND m.description != ''"
    ).fetchall()
    conn.close()

    if not rows:
        return

    X = [r["description"] for r in rows]  # noqa: N806
    y = [r["category"] for r in rows]

    pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=5000, stop_words="english")),
            ("clf", LogisticRegression(max_iter=1000, solver="lbfgs")),
        ]
    )
    pipe.fit(X, y)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)


def _load_model() -> Pipeline | None:
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)  # type: ignore[no-any-return]
    return None


def predict(description: str) -> str:
    """Predict category for a description. Returns 'other' as fallback."""
    model = _load_model()
    if model is None:
        return "other"
    proba = model.predict_proba([description])[0]
    if max(proba) < 0.3:
        return "other"
    return model.predict([description])[0]  # type: ignore[no-any-return]


def predict_proba(description: str) -> dict[str, float]:
    """Return confidence per category."""
    model = _load_model()
    if model is None:
        return {"other": 1.0}
    proba = model.predict_proba([description])[0]
    classes = model.classes_
    return {cls: round(float(p), 4) for cls, p in zip(classes, proba, strict=False)}
