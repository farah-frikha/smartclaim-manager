"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";

interface Reclamation {
  reclamation_id: number;
  dossier_id: number;
  reference_dossier: string;
  auteur: string;
  message: string;
  statut: string;
  reponse: string | null;
  created_at: string;
}

export default function ReclamationsPage() {
  const [reclamations, setReclamations] = useState<Reclamation[]>([]);
  const [chargement, setChargement] = useState(true);
  const [reponses, setReponses] = useState<Record<number, string>>({});

  const charger = () => {
    api.get("/reclamations")
      .then((res) => setReclamations(res.data))
      .finally(() => setChargement(false));
  };

  useEffect(charger, []);

  const repondre = async (id: number) => {
    const texte = reponses[id]?.trim();
    if (!texte) return;
    try {
      await api.put(`/reclamations/${id}/reponse`, { reponse: texte });
      setReponses((r) => ({ ...r, [id]: "" }));
      charger();
    } catch {
      alert("Erreur lors de l'envoi de la réponse");
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">
        Réclamations ({reclamations.length})
      </h2>

      {chargement ? (
        <p className="text-sm text-gray-500">Chargement...</p>
      ) : reclamations.length === 0 ? (
        <p className="text-sm text-gray-400">Aucune réclamation</p>
      ) : (
        <div className="space-y-4">
          {reclamations.map((r) => (
            <div key={r.reclamation_id} className="rounded-lg border bg-surface p-5">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <span className="font-medium text-gray-900">{r.auteur}</span>
                  <span className="ml-2 text-sm text-gray-500">
                    — dossier {r.reference_dossier}
                  </span>
                </div>
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                    r.statut === "ouverte"
                      ? "bg-amber-50 text-amber-700"
                      : "bg-emerald-50 text-emerald-700"
                  }`}
                >
                  {r.statut === "ouverte" ? "Ouverte" : "Traitée"}
                </span>
              </div>

              <p className="mb-3 text-sm text-gray-700">{r.message}</p>
              <p className="mb-3 text-xs text-gray-400">
                {new Date(r.created_at).toLocaleString("fr-FR")}
              </p>

              {r.reponse ? (
                <div className="rounded-md bg-gray-50 p-3">
                  <p className="mb-1 text-xs font-medium text-gray-500">Réponse</p>
                  <p className="text-sm text-gray-700">{r.reponse}</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <textarea
                    value={reponses[r.reclamation_id] || ""}
                    onChange={(e) =>
                      setReponses((prev) => ({
                        ...prev,
                        [r.reclamation_id]: e.target.value,
                      }))
                    }
                    rows={3}
                    placeholder="Votre réponse..."
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  />
                  <button
                    onClick={() => repondre(r.reclamation_id)}
                    className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800"
                  >
                    Répondre
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}