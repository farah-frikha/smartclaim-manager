import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from engines.validation_engine import executer_validation
from engines.scoring_engine     import executer_scoring
from engines.decision_engine    import executer_decision

def mesurer_performance(dossier: dict, n: int = 100) -> dict:
    """
    Mesure la latence des 3 moteurs sur n exécutions.
    Retourne les métriques de performance.
    """
    latences_v, latences_s, latences_d = [], [], []

    for _ in range(n):
        t0 = time.perf_counter()
        r_v = executer_validation(dossier)
        latences_v.append((time.perf_counter() - t0) * 1000)

        if r_v["peut_continuer"]:
            t0 = time.perf_counter()
            r_s = executer_scoring(dossier)
            latences_s.append((time.perf_counter() - t0) * 1000)

            t0 = time.perf_counter()
            executer_decision(r_s["score"], r_s["flags"], dossier.get("montant_reclame", 0))
            latences_d.append((time.perf_counter() - t0) * 1000)

    def stats(lst):
        if not lst: return {}
        return {
            "min_ms":  round(min(lst), 2),
            "max_ms":  round(max(lst), 2),
            "moy_ms":  round(sum(lst) / len(lst), 2),
            "p95_ms":  round(sorted(lst)[int(len(lst) * 0.95)], 2),
        }

    return {
        "n_executions":   n,
        "validation":     stats(latences_v),
        "scoring":        stats(latences_s),
        "decision":       stats(latences_d),
        "pipeline_total": stats([v + s + d for v, s, d in
                                  zip(latences_v, latences_s, latences_d)])
    }


if __name__ == "__main__":
    dossier = {
        "date_sinistre": "2024-03-15",
        "date_debut_contrat": "2023-01-01",
        "date_fin_contrat": "2025-12-31",
        "delai_declaration_jours": 3,
        "jours_depuis_sinistre": 10,
        "jours_depuis_souscription": 438,
        "type_sinistre": "SANTE_CONSUL",
        "garanties_contrat": ["SANTE_CONSUL"],
        "documents_fournis": ["formulaire_sinistre", "piece_identite"],
        "statut_cotisations_cnss_employeur": "a_jour",
        "statut_affiliation": "actif",
        "concerne_ayant_droit": False,
        "cause_sinistre": "accident",
        "montant_net_complementaire": 90.0,
        "montant_reclame": 150.0,
        "nb_soins_12m": 3,
        "depassement_tarif_cnss": False,
        "sinistre_hors_contrat": False,
        "incoherence_duree_arret": False,
        "nb_arrets_24m": 0,
        "depassement_salaire_cnss": False,
        "delai_declaration_at_jours": 2,
        "document_etranger_non_legalise": False,
        "dossier_complet_premiere_fois": True,
        "anciennete_contrat_jours": 1500,
        "coherence_cnss_facture": True,
    }

    print("  Mesure des performances \n")
    metriques = mesurer_performance(dossier, n=100)
    print(json.dumps(metriques, indent=2, ensure_ascii=False))

    # Assertions sur les seuils de performance
    print("\n Vérification des seuils :")
    seuil_ms = 50  # chaque moteur doit répondre en < 50ms
    for agent, stats in metriques.items():
        if isinstance(stats, dict) and "moy_ms" in stats:
            ok = stats["moy_ms"] < seuil_ms
            print(f" {agent:<20} moy={stats['moy_ms']}ms "
                  f"p95={stats['p95_ms']}ms (seuil={seuil_ms}ms)")