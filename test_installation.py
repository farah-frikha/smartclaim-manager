# test_installation.py
print("Test des installations SmartClaim...\n")

tests = []

# Test Python
import sys
tests.append(("Python 3.11", sys.version.startswith("3.11"), sys.version))

# Test PaddleOCR
try:
    from paddleocr import PaddleOCR
    tests.append(("PaddleOCR", True, "OK"))
except ImportError as e:
    tests.append(("PaddleOCR", False, str(e)))

# Test LangGraph
try:
    import langgraph
    tests.append(("LangGraph", True, "ok"))
except ImportError as e:
    tests.append(("LangGraph", False, str(e)))

# Test Ollama
try:
    import ollama
    models = ollama.list()
    noms = [m['name'] for m in models.get('models', [])]
    qwen_present = any('qwen2.5' in n for n in noms)
    tests.append(("Ollama + Qwen2.5", qwen_present,
                  "Modèle présent" if qwen_present else f"Modèles dispo: {noms}"))
except Exception as e:
    tests.append(("Ollama + Qwen2.5", False, str(e)))

# Test PyMuPDF
try:
    import fitz
    tests.append(("PyMuPDF", True, fitz.__version__))
except ImportError as e:
    tests.append(("PyMuPDF", False, str(e)))

# Test Streamlit
try:
    import streamlit
    tests.append(("Streamlit", True, streamlit.__version__))
except ImportError as e:
    tests.append(("Streamlit", False, str(e)))

# Test SQLite
import sqlite3
tests.append(("SQLite", True, sqlite3.sqlite_version))

# Test config.py
try:
    from config import BASE_DIR, VALIDATION_RULES, OLLAMA_MODEL
    tests.append(("config.py", True, f"BASE_DIR={BASE_DIR}"))
except Exception as e:
    tests.append(("config.py", False, str(e)))

# Affichage résultats
print(f"{'Composant':<25} {'Statut':<10} Détail")
print("─" * 65)
tous_ok = True
for nom, ok, detail in tests:
    statut = "✅ OK" if ok else "❌ FAIL"
    if not ok:
        tous_ok = False
    print(f"{nom:<25} {statut:<10} {detail}")

print("\n" + ("✅ Installation complète — prêt à coder !" 
              if tous_ok else 
              "❌ Certains composants manquent — relancez pip install"))