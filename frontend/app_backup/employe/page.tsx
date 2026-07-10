"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { obtenirUtilisateur } from "@/lib/auth";

interface Dossier {
  dossier_id: number;
  reference_dossier: string;
  statut_global: string;
  montant_reclame: number | null;
  date_sinistre: string | null;
  created_at: string;
}

const STATUT_LABELS: Record<string, { label: string; couleur: string }> = {
  accepte: { label: "Accepté", couleur: "bg-green-100 text-green-700" },
  refuse: { label: "Refusé", couleur: "bg-red-100 text-red-700" },
  complement_requis: { label: "Complément requis", couleur: "bg-amber-100 text-amber-700" },
  en_traitement: { label: "En traitement", couleur: "bg-blue-100 text-blue-700" },
  valide: { label: "Validé", couleur: "bg-blue-100 text-blue-700" },
  invalide: { label: "Invalide", couleur: "bg-gray-100 text-gray-700" },
};

export default function EmployeAccueilPage() {
  const [dossiers, setDossiers] = useState<Dossier[]>([]);
  const [chargement, setChargement] = useState(true);
  const utilisateur = obtenirUtilisateur();

  useEffect(() => {
    api
      .get("/dossiers/mes-dossiers")
      .then((res) => setDossiers(res.data))
      .finally(() => setChargement(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">
          Bonjour {utilisateur?.nom_complet?.split(" ")[0]}
        </h2>
        <p className="text-sm text-gray-500">
          Voici un résumé de vos dossiers de sinistres
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Link
          href="/employe/depot"
          className="rounded-lg border-2 border-dashed border-gray-300 bg-white p-6 text-center hover:border-gray-400"
        >
          <p className="font-medium text-gray-900">Déposer un document</p>
          <p className="mt-1 text-xs text-gray-500">
            PDF, JPG ou PNG — 10 Mo max
          </p>
        </Link>

        <div className="rounded-lg border bg-white p-6 text-center">
          <p className="text-2xl font-semibold text-gray-900">
            {dossiers.length}
          </p>
          <p className="mt-1 text-xs text-gray-500">Dossiers déposés</p>
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-medium text-gray-900">
          Vos derniers dossiers
        </h3>

        {chargement ? (
          <p className="text-sm text-gray-500">Chargement...</p>
        ) : dossiers.length === 0 ? (
          <p className="text-sm text-gray-400">
            Aucun dossier déposé pour le moment
          </p>
        ) : (
          <div className="space-y-2">
            {dossiers.slice(0, 5).map((dossier) => {
              const statut = STATUT_LABELS[dossier.statut_global] || {
                label: dossier.statut_global,
                couleur: "bg-gray-100 text-gray-700",
              };
              return (
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
                      {dossier.montant_reclame
                        ? `${dossier.montant_reclame} TND`
                        : "Montant non renseigné"}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-medium ${statut.couleur}`}
                  >
                    {statut.label}
                  </span>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}