# agents/extraction/llm_client.py
"""
Client LLM — appel à Qwen2.5-7B via Ollama avec mécanisme de retry.
Ce fichier est le seul à dépendre de la bibliothèque ollama.
Changer de LLM = modifier uniquement ce fichier.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)))

import json
import time

import ollama
from loguru import logger

from config import OLLAMA_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE
from agents.extraction.parser import nettoyer_json


def appeler_llm(prompt: str, max_retries: int = 3) -> dict:
    """
    Envoie le prompt à Qwen via Ollama avec mécanisme de retry.

    Le retry est nécessaire car le LLM peut retourner du JSON
    malformé (backticks manquants, champ absent, etc.).
    En cas d'échec après max_retries tentatives, retourne
    succes=False sans lever d'exception — l'agent gère l'erreur.

    Retourne :
        succes        : bool
        reponse_brute : str   — réponse brute du LLM
        json_parse    : dict  — JSON parsé ou None
        tentatives    : int   — nombre de tentatives effectuées
        duree_ms      : float — durée totale en millisecondes
    """
    t_debut = time.perf_counter()

    for tentative in range(1, max_retries + 1):
        try:
            logger.info(f"Appel LLM (tentative {tentative}/{max_retries})...")

            reponse = ollama.chat(
                model    = OLLAMA_MODEL,
                messages = [{"role": "user", "content": prompt}],
                options  = {
                    "temperature": LLM_TEMPERATURE,
                    "num_predict": LLM_MAX_TOKENS,
                }
            )

            reponse_brute = reponse["message"]["content"]
            json_nettoye  = nettoyer_json(reponse_brute)
            json_parse    = json.loads(json_nettoye)

            duree_ms = round((time.perf_counter() - t_debut) * 1000, 1)
            logger.success(
                f"LLM répondu en {duree_ms}ms (tentative {tentative})"
            )

            return {
                "succes":        True,
                "reponse_brute": reponse_brute,
                "json_parse":    json_parse,
                "tentatives":    tentative,
                "duree_ms":      duree_ms
            }

        except json.JSONDecodeError as e:
            logger.warning(f"Tentative {tentative} : JSON invalide — {e}")
            if tentative == max_retries:
                logger.error("Toutes les tentatives ont échoué")

        except Exception as e:
            logger.error(f"Tentative {tentative} : erreur LLM — {e}")
            if tentative == max_retries:
                break

    duree_ms = round((time.perf_counter() - t_debut) * 1000, 1)
    return {
        "succes":        False,
        "reponse_brute": "",
        "json_parse":    None,
        "tentatives":    max_retries,
        "duree_ms":      duree_ms
    }