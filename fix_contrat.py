# fix_contrat.py
import sqlite3

conn = sqlite3.connect('data/smartclaim.db')

conn.execute("""
    UPDATE contrats_collectifs
    SET date_echeance = '2027-01-05',
        garanties_couvertes = 'AUTO_ACCIDENT,AUTO_VOL,AUTO_BRIS_GLACE,SANTE_CONSUL'
    WHERE numero_contrat = 'STAR-AUTO-2024-00847'
""")
conn.commit()

# Vérification
rows = conn.execute("""
    SELECT numero_contrat, date_effet, date_echeance, garanties_couvertes
    FROM contrats_collectifs
""").fetchall()

for row in rows:
    print(row)

conn.close()
print("Contrat mis à jour avec succès")