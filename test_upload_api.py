# test_upload_api.py
import requests

# Connexion
r = requests.post("http://localhost:8000/auth/login", json={
    "email": "admin@smartclaim.tn",
    "mot_de_passe": "admin123"
})
token = r.json()["access_token"]
print(f"Token obtenu : {token[:30]}...")

# Upload du PDF
headers = {"Authorization": f"Bearer {token}"}
with open("data/Document Test Assurance Tunisie Ocr.pdf", "rb") as f:
    files = {"fichier": ("Document Test Assurance Tunisie Ocr.pdf", f, "application/pdf")}
    response = requests.post(
        "http://localhost:8000/dossiers/upload",
        headers=headers,
        files=files
    )

print(f"\nStatut HTTP : {response.status_code}")
print(f"Réponse : {response.text}")