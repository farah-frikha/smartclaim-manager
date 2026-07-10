"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import api from "@/lib/api";

interface DossierDetail {
  dossier: {
    dossier_id: number;
    reference_dossier: string;
    statut_global: string;
    montant_reclame: number | null;
    date_sinistre: string | null;
  };
  champs: Record<string, string>;
  validation: { regle_id: string; resultat: string; message: string }[];
  score: { score_final: number } | null;
  decision: {
    decision: string;
    motif_principal: string;
    message_client: string;
    necessite_validation_humaine: number;
  } | null;
  audit_logs: { agent_nom: string; action: string; date_action: string }[];
}

export default function DossierDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [data, setData] = useState<DossierDetail | null>(null);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [champEnEdition, setChampEnEdition] = useState<string | null>(null);
  const [nouvelleValeur, setNouvelleValeur] = useState("");

  useEffect(() => {
    charger();
  }, [params.id]);

  function charger() {
    setChargement(true);
    api
      .get(`/dossiers/${params.id}`)
      .then((res) => setData(res.data))
      .catch(() => setErreur("Dossier introuvable"))
      .finally(() => setChargement(false));
  }

  async function sauvegarderCorrection(nomChamp: string) {
    try {
      await api.put(`/dossiers/${params.id}/champs`, {
        nom_champ: nomChamp,
        valeur_corrigee: nouvelleValeur,
        motif_correction: "Correction manuelle par le gestionnaire",
      });
      setChampEnEdition(null);
      charger();
    } catch {
      alert("Erreur lors de la correction");
    }
  }

  if (chargement) return <p className="text-sm text-gray-500">Chargement...</p>;
  if (erreur || !data) return <p className="text-sm text-red-600">{erreur}</p>;

  const { dossier, champs, validation, score, decision, audit_logs } = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            {dossier.reference_dossier}
          </h2>
          <p className="text-sm text-gray-500">Statut : {dossier.statut_global}</p>
        </div>
        <button
          onClick={() => router.back()}
          className="text-sm text-gray-500 hover:text-gray-900"
        >
          ← Retour
        </button>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-lg border bg-surface p-4">
          <h3 className="mb-3 text-sm font-medium text-gray-900">
            Champs extraits
          </h3>
          <div className="space-y-2">
            {Object.entries(champs).map(([nom, valeur]) => (
              <div key={nom} className="flex items-center justify-between text-sm">
                <span className="text-gray-500">{nom}</span>
                {champEnEdition === nom ? (
                  <div className="flex gap-1">
                    <input
                      value={nouvelleValeur}
                      onChange={(e) => setNouvelleValeur(e.target.value)}
                      className="w-32 rounded border border-gray-300 px-2 py-1 text-xs"
                      autoFocus
                    />
                    <button
                      onClick={() => sauvegarderCorrection(nom)}
                      className="text-xs text-green-600"
                    >
                      ✓
                    </button>
                    <button
                      onClick={() => setChampEnEdition(null)}
                      className="text-xs text-gray-400"
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => {
                      setChampEnEdition(nom);
                      setNouvelleValeur(valeur || "");
                    }}
                    className="font-medium text-gray-900 hover:underline"
                  >
                    {valeur || "—"}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          {score && (
            <div className="rounded-lg border bg-surface p-4">
              <h3 className="mb-2 text-sm font-medium text-gray-900">Score</h3>
              <p className="text-2xl font-semibold text-gray-900">
                {score.score_final}/100
              </p>
            </div>
          )}

          {decision && (
            <div className="rounded-lg border bg-surface p-4">
              <h3 className="mb-2 text-sm font-medium text-gray-900">Décision</h3>
              <p className="text-sm font-medium text-gray-900">
                {decision.decision.toUpperCase()}
              </p>
              <p className="mt-1 text-xs text-gray-500">{decision.motif_principal}</p>
              {decision.necessite_validation_humaine === 1 && (
                <p className="mt-2 rounded bg-amber-50 px-2 py-1 text-xs text-amber-700">
                  ⚠ Escalade humaine requise
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="rounded-lg border bg-surface p-4">
        <h3 className="mb-3 text-sm font-medium text-gray-900">
          Résultats de validation
        </h3>
        <div className="space-y-1">
          {validation.map((v, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <span
                className={
                  v.resultat === "PASS" ? "text-green-600" : "text-red-600"
                }
              >
                {v.resultat === "PASS" ? "✓" : "✗"}
              </span>
              <span className="text-gray-700">{v.regle_id}</span>
              {v.message && (
                <span className="text-xs text-gray-400">— {v.message}</span>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border bg-surface p-4">
        <h3 className="mb-3 text-sm font-medium text-gray-900">
          Journal d'audit
        </h3>
        <div className="space-y-2">
          {audit_logs.map((log, i) => (
            <div key={i} className="flex justify-between text-xs text-gray-500">
              <span>
                <strong className="text-gray-700">{log.agent_nom}</strong> —{" "}
                {log.action}
              </span>
              <span>{new Date(log.date_action).toLocaleString("fr-FR")}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}