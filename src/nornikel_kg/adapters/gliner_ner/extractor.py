from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from nornikel_kg.domain.extraction import EntityMention

logger = logging.getLogger(__name__)

_MODEL_ID = "urchade/gliner_multi-v2.1"

# Zero-shot labels in both languages; GLiNER maps them onto our entity types.
_LABELS: dict[str, str] = {
    "material": "material",
    "сплав": "material",
    "processing regime": "regime",
    "режим обработки": "regime",
    "material property": "property",
    "свойство материала": "property",
    "equipment": "equipment",
    "оборудование": "equipment",
    "team": "team",
    "команда": "team",
    "person": "person",
    "laboratory": "laboratory",
    "conclusion": "conclusion",
    "решение": "decision",
}

_CHUNK_CHARS = 1500


@lru_cache(maxsize=1)
def _load_model() -> Any:
    from gliner import GLiNER

    logger.info("Loading GLiNER model %s", _MODEL_ID)
    return GLiNER.from_pretrained(_MODEL_ID)


class GLiNERMentionExtractor:
    """Zero-shot multilingual NER pre-pass (cheap, no LLM)."""

    threshold = 0.35

    def extract(self, text: str) -> list[EntityMention]:
        model = _load_model()
        mentions: list[EntityMention] = []
        for offset in range(0, len(text), _CHUNK_CHARS):
            chunk = text[offset : offset + _CHUNK_CHARS]
            for prediction in model.predict_entities(
                chunk, list(_LABELS.keys()), threshold=self.threshold
            ):
                label = str(prediction.get("label", ""))
                entity_type = _LABELS.get(label)
                if entity_type is None:
                    continue
                mentions.append(
                    EntityMention(
                        text=str(prediction.get("text", "")).strip(),
                        entity_type=entity_type,
                        start=int(prediction.get("start", 0)) + offset,
                        end=int(prediction.get("end", 0)) + offset,
                        confidence=float(prediction.get("score", 0.0)),
                        origin="gliner",
                    )
                )
        return mentions
