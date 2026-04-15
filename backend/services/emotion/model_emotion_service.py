import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import joblib

logger = logging.getLogger(__name__)


class ModelEmotionService:
    """Optional ML emotion classifier used for post-session analysis.

    If model artifacts are missing, this service stays disabled and callers should
    fall back to rule-based emotion analysis.
    """

    def __init__(self) -> None:
        backend_root = Path(__file__).resolve().parents[2]
        self.artifact_dir = backend_root / "ml" / "artifacts"
        self.pipeline_path = self.artifact_dir / "emotion_text_pipeline.joblib"
        self.meta_path = self.artifact_dir / "emotion_model_meta.json"

        self.pipeline = None
        self.meta: Dict[str, Any] = {}
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        if not self.pipeline_path.exists() or not self.meta_path.exists():
            logger.info("Emotion model artifacts not found; using rule-based analyzer")
            return

        try:
            self.pipeline = joblib.load(self.pipeline_path)
            with self.meta_path.open("r", encoding="utf-8") as file:
                self.meta = json.load(file)
            logger.info("Loaded emotion model artifacts successfully")
        except Exception as exc:
            logger.warning(f"Failed to load emotion model artifacts: {exc}")
            self.pipeline = None
            self.meta = {}

    def is_available(self) -> bool:
        return self.pipeline is not None

    def predict_emotion(self, text: str) -> Optional[Dict[str, Any]]:
        if not self.pipeline or not text:
            return None

        try:
            predicted_label = self.pipeline.predict([text])[0]
            scores: Dict[str, float] = {}

            if hasattr(self.pipeline, "predict_proba"):
                probabilities = self.pipeline.predict_proba([text])[0]
                class_labels = getattr(self.pipeline, "classes_", [])
                scores = {
                    str(label): float(prob)
                    for label, prob in zip(class_labels, probabilities)
                }

            return {
                "label": str(predicted_label),
                "scores": scores,
                "source": "ml_model",
                "model_version": self.meta.get("model_version", "unknown"),
            }
        except Exception as exc:
            logger.warning(f"Emotion model inference failed: {exc}")
            return None


model_emotion_service = ModelEmotionService()
