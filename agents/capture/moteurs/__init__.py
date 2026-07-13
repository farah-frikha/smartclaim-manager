# agents/capture/moteurs/__init__.py
from agents.capture.moteurs.factory import obtenir_moteur_ocr
from agents.capture.moteurs.base import MoteurOCR

__all__ = ["obtenir_moteur_ocr", "MoteurOCR"]