from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import psycopg
import spacy
from psycopg.rows import dict_row
from spacy.training import Example

from src.infra.logger import Logger

logger = Logger.get(__name__)

MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "ner_model"


class NERTrainer:
    def __init__(self, database_url: str) -> None:
        self._db_url = database_url

    def generate_training_data(self) -> list[tuple[str, dict[str, Any]]]:
        with psycopg.connect(self._db_url, row_factory=dict_row) as conn:
            rows = conn.execute(
                "SELECT DISTINCT ON (description) name, description "
                "FROM mentions WHERE description != '' AND LENGTH(description) > 10 "
                "LIMIT 2000"
            ).fetchall()

        data: list[tuple[str, dict[str, Any]]] = []
        for row in rows:
            text = row["description"]
            name = row["name"]
            start = text.find(name)
            if start == -1:
                start = text.lower().find(name.lower())
            if start == -1:
                continue
            end = start + len(name)
            data.append((text, {"entities": [(start, end, "TECH")]}))

        return data

    def train(self, n_iter: int = 30) -> dict[str, Any]:
        training_data = self.generate_training_data()
        if len(training_data) < 50:
            return {
                "status": "skipped",
                "reason": "insufficient data",
                "samples": len(training_data),
            }

        random.shuffle(training_data)
        split = int(len(training_data) * 0.8)
        train_data = training_data[:split]
        test_data = training_data[split:]

        nlp = spacy.load("en_core_web_sm")
        if "ner" not in nlp.pipe_names:
            nlp.add_pipe("ner", last=True)
        ner = nlp.get_pipe("ner")
        ner.add_label("TECH")

        other_pipes = [p for p in nlp.pipe_names if p != "ner"]
        with nlp.disable_pipes(*other_pipes):
            optimizer = nlp.resume_training()
            last_loss = 0.0
            for _ in range(n_iter):
                random.shuffle(train_data)
                losses: dict[str, float] = {}
                for text, annot in train_data:
                    try:
                        doc = nlp.make_doc(text)
                        example = Example.from_dict(doc, annot)
                        nlp.update([example], drop=0.3, sgd=optimizer, losses=losses)
                    except Exception:
                        continue
                last_loss = losses.get("ner", 0.0)

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        nlp.to_disk(str(MODEL_DIR))

        accuracy = self.evaluate(nlp, test_data)

        logger.info(
            "NER training complete",
            extra={
                "samples": len(train_data),
                "loss": round(last_loss, 4),
                "accuracy": round(accuracy, 4),
            },
        )

        return {
            "status": "complete",
            "samples": len(train_data),
            "test_samples": len(test_data),
            "loss": round(last_loss, 4),
            "accuracy": round(accuracy, 4),
        }

    def evaluate(self, nlp: Any, test_data: list[tuple[str, dict[str, Any]]]) -> float:
        correct = 0
        total = 0
        for text, annot in test_data:
            doc = nlp(text)
            expected = {text[s:e] for s, e, _ in annot["entities"]}
            predicted = {ent.text for ent in doc.ents if ent.label_ == "TECH"}
            if expected & predicted:
                correct += 1
            total += 1
        return correct / total if total > 0 else 0.0
