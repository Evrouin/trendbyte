"""NER training pipeline — fine-tunes spaCy on labeled mentions."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import psycopg
import spacy
from psycopg.rows import dict_row
from spacy.training import Example

MODEL_DIR = Path("models/ner_model")


class NERTrainer:
    def __init__(self, database_url: str) -> None:
        self._db_url = database_url

    def generate_training_data(self) -> list[tuple[str, dict]]:
        conn = psycopg.connect(self._db_url, row_factory=dict_row)
        rows = conn.execute(
            "SELECT DISTINCT ON (description) name, description FROM mentions "
            "WHERE description IS NOT NULL AND description != ''"
        ).fetchall()
        conn.close()

        data: list[tuple[str, dict]] = []
        seen: set[str] = set()
        for row in rows:
            text = row["description"]
            name = row["name"]
            if text in seen:
                continue
            start = text.find(name)
            if start == -1:
                start = text.lower().find(name.lower())
            if start == -1:
                continue
            end = start + len(name)
            seen.add(text)
            data.append((text, {"entities": [(start, end, "TECH")]}))

        return data

    def train(self, n_iter: int = 30) -> dict[str, Any]:
        data = self.generate_training_data()
        if len(data) < 50:
            return {"status": "skipped", "reason": "insufficient data", "samples": len(data)}

        random.shuffle(data)
        split = int(len(data) * 0.8)
        train_data = data[:split]
        test_data = data[split:]

        nlp = spacy.load("en_core_web_sm")
        if "ner" not in nlp.pipe_names:
            ner = nlp.add_pipe("ner")
        else:
            ner = nlp.get_pipe("ner")
        ner.add_label("TECH")

        other_pipes = [p for p in nlp.pipe_names if p != "ner"]
        total_loss = 0.0
        with nlp.disable_pipes(*other_pipes):
            optimizer = nlp.resume_training()
            for _ in range(n_iter):
                random.shuffle(train_data)
                losses: dict[str, float] = {}
                for text, annot in train_data:
                    doc = nlp.make_doc(text)
                    example = Example.from_dict(doc, annot)
                    nlp.update([example], drop=0.35, sgd=optimizer, losses=losses)
                total_loss = losses.get("ner", 0.0)

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        nlp.to_disk(MODEL_DIR)

        accuracy = self.evaluate(test_data, nlp)

        return {
            "status": "complete",
            "samples": len(train_data),
            "test_samples": len(test_data),
            "final_loss": round(total_loss, 4),
            "accuracy": round(accuracy, 4),
        }

    def evaluate(self, test_data: list[tuple[str, dict]], nlp: Any = None) -> float:
        if not test_data:
            return 0.0
        if nlp is None:
            nlp = spacy.load(MODEL_DIR)

        correct = 0
        for text, annot in test_data:
            doc = nlp(text)
            predicted = {(ent.start_char, ent.end_char) for ent in doc.ents if ent.label_ == "TECH"}
            expected = {(s, e) for s, e, _ in annot["entities"]}
            if expected & predicted:
                correct += 1

        return correct / len(test_data)
