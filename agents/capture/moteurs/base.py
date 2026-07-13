# agents/capture/moteurs/base.py
"""
Interface abstraite pour les moteurs OCR.
Tout moteur (Paddle, OCR.space, Surya...) doit respecter ce contrat.
C'est l'application du principe d'inversion de dépendance (SOLID) :
le pipeline dépend de cette abstraction, jamais d'un moteur concret.
"""
from abc import ABC, abstractmethod
import numpy as np


class MoteurOCR(ABC):
    """
    Contrat commun à tous les moteurs OCR.

    Chaque implémentation reçoit une image et retourne un résultat
    normalisé, quel que soit le moteur sous-jacent. Cela permet de
    changer de moteur sans modifier le reste du pipeline.
    """

    @abstractmethod
    def lire_page(self, image_np: np.ndarray, numero_page: int) -> dict:
        """
        Applique l'OCR sur une image de page et retourne un résultat
        normalisé.

        Paramètres :
            image_np    : l'image de la page (tableau numpy)
            numero_page : le numéro de la page

        Retourne un dict avec au minimum :
            numero_page      : int
            texte_brut       : str   — texte extrait
            lignes           : list  — lignes avec leur confiance
            score_confiance  : float — confiance moyenne (0 à 1)
            nb_mots          : int
            langue_detectee  : str

        Ce format est identique pour tous les moteurs, ce qui rend
        le pipeline agnostique du moteur réellement utilisé.
        """
        pass

    @property
    @abstractmethod
    def nom(self) -> str:
        """Nom du moteur, pour la journalisation (ex: 'paddle', 'ocrspace')."""
        pass