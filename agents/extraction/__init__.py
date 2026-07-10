# agents/extraction/__init__.py
"""
Package extraction — point d'entrée public.
Tous les imports existants continuent de fonctionner :
    from agents.extraction import executer_extraction
"""
from agents.extraction.agent   import executer_extraction
from agents.extraction.display import afficher_rapport_extraction
from agents.extraction.schema  import (
    SCHEMA_EXTRACTION,
    TYPES_SINISTRES_VALIDES,
    CHAMPS_CRITIQUES
)

__all__ = [
    "executer_extraction",
    "afficher_rapport_extraction",
    "SCHEMA_EXTRACTION",
    "TYPES_SINISTRES_VALIDES",
    "CHAMPS_CRITIQUES",
]