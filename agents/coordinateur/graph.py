# agents/coordinateur/graph.py
"""
Construction et compilation du graphe LangGraph.
Ce fichier définit la TOPOLOGIE du pipeline :
quels nœuds existent et comment ils sont connectés.
"""
from langgraph.graph import StateGraph, END

from agents.coordinateur.state   import EtatDossier
from agents.coordinateur.nodes   import (
    noeud_capture, noeud_extraction, noeud_validation,
    noeud_scoring, noeud_decision, noeud_decision_directe,
    noeud_erreur
)
from agents.coordinateur.routers import (
    router_apres_capture, router_apres_extraction,
    router_apres_validation, router_apres_scoring
)


def construire_graphe() -> StateGraph:
    """
    Construit et compile le graphe LangGraph.
    Retourne le graphe compilé prêt à être invoqué.
    """
    graphe = StateGraph(EtatDossier)

    graphe.add_node("capture",          noeud_capture)
    graphe.add_node("extraction",       noeud_extraction)
    graphe.add_node("validation",       noeud_validation)
    graphe.add_node("scoring",          noeud_scoring)
    graphe.add_node("decision",         noeud_decision)
    graphe.add_node("decision_directe", noeud_decision_directe)
    graphe.add_node("erreur",           noeud_erreur)

    graphe.set_entry_point("capture")

    graphe.add_conditional_edges(
        "capture", router_apres_capture,
        {"extraction": "extraction", "erreur": "erreur"}
    )
    graphe.add_conditional_edges(
        "extraction", router_apres_extraction,
        {"validation": "validation", "erreur": "erreur"}
    )
    graphe.add_conditional_edges(
        "validation", router_apres_validation,
        {"scoring": "scoring", "decision_directe": "decision_directe"}
    )
    graphe.add_conditional_edges(
        "scoring", router_apres_scoring,
        {"decision": "decision", "erreur": "erreur"}
    )

    graphe.add_edge("decision",         END)
    graphe.add_edge("decision_directe", END)
    graphe.add_edge("erreur",           END)

    return graphe.compile()