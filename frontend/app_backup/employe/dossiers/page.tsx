"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";

interface Dossier {
  dossier_id: number;
  reference_dossier: string;
  statut_global: string;
  montant_reclame: number | null;
  date_sinistre: string | null;
  created_at: string;
}

const STATUT_STYLE: Record<string, string> = {
  accepte: "bg-green-100 text-green-700",
  refuse: "bg-red-100 text-red-700",
  complement_requis: "bg-amber-100 text-amber-700",
  en_traitement: "bg-blue-100 text-blue-700",
  valide: "bg-blue-100 text-blue-700",
  invalide: "bg-gray-100 text-gray-700",
};

export default function MesDossiersPage() {
  const [dossiers, setDossiers] = useState<Dossier[]>([]);
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    api
      .get("/dossiers/mes-dossiers")
      .then((res) => setDossiers(res.data))
      .finally(() => setChargement(false));
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">
        Mes dossiers ({dossiers.length})
      </h2>

      {chargement ? (
        <p className="text-sm text-gray-500">Chargement...</p>
      ) : dossiers.length === 0 ? (
        <p className="text-sm text-gray-400">
          Vous n'avez déposé aucun dossier pour le moment
        </p>
      ) : (
        <div className="space-y-2">
          {dossiers.map((dossier) => (
            <Link
              key={dossier.dossier_id}
              href={`/employe/dossiers/${dossier.dossier_id}`}
              className="flex items-center justify-between rounded-lg border bg-white p-4 hover:bg-gray-50"
            >
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {dossier.reference_dossier}
                </p>
                <p className="text-xs text-gray-500">
                  {dossier.date_sinistre || "Date non renseignée"} ·{" "}
                  {dossier.montant_reclame
                    ? `${dossier.montant_reclame} TND`
                    : "Montant non renseigné"}
                </p>
              </div>
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                  STATUT_STYLE[dossier.statut_global] || "bg-gray-100 text-gray-700"
                }`}
              >
                {dossier.statut_global}
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}