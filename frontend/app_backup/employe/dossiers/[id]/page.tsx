"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import api from "@/lib/api";

interface DossierDetail {
  dossier: {
    reference_dossier: string;
    statut_global: string;
  };
  champs: Record<string, string>;
  decision: {
    decision: string;
    message_client: string;
  } | null;
}

export default function MonDossierDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [data, setData] = useState<DossierDetail | null>(null);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    api
      .get(`/dossiers/${params.id}`)
      .then((res) => setData(res.data))
      .catch(() => setErreur("Vous n'avez pas accès à ce dossier"))
      .finally(() => setChargement(false));
  }, [params.id]);

  if (chargement) return <p className="text-sm text-gray-500">Chargement...</p>;
  if (erreur || !data) return <p className="text-sm text-red-600">{erreur}</p>;

  const { dossier, champs, decision } = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            {dossier.reference_dossier}
          </h2>
          <p className="text-sm text-gray-500">
            Statut : {dossier.statut_global}
          </p>
        </div>
        <button
          onClick={() => router.back()}
          className="text-sm text-gray-500 hover:text-gray-900"
        >
          ← Retour
        </button>
      </div>

      {decision && (
        <div
          className={`rounded-lg border p-4 ${
            decision.decision === "accepter"
              ? "border-green-200 bg-green-50"
              : decision.decision === "refuser"
              ? "border-red-200 bg-red-50"
              : "border-amber-200 bg-amber-50"
          }`}
        >
          <p className="font-medium text-gray-900">
            {decision.decision === "accepter"
              ? "✓ Dossier accepté"
              : decision.decision === "refuser"
              ? "✗ Dossier refusé"
              : "⚠ Complément requis"}
          </p>
          <p className="mt-1 text-sm text-gray-700">
            {decision.message_client}
          </p>
        </div>
      )}

      <div className="rounded-lg border bg-white p-4">
        <h3 className="mb-3 text-sm font-medium text-gray-900">
          Informations du dossier
        </h3>
        <div className="space-y-2 text-sm">
          {Object.entries(champs).map(([nom, valeur]) => (
            <div key={nom} className="flex justify-between">
              <span className="text-gray-500">{nom}</span>
              <span className="font-medium text-gray-900">
                {valeur || "—"}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}