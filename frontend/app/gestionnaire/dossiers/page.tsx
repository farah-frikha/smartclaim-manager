"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import api from "@/lib/api";
import { libelleDomaine } from "@/lib/domaines";

interface Dossier {
  dossier_id: number;
  reference_dossier: string;
  statut_global: string;
  domaine: string | null;
  montant_reclame: number | null;
  date_sinistre: string | null;
  created_at: string;
}

const STATUTS = [
  { valeur: "", label: "Tous les statuts" },
  { valeur: "accepte", label: "Accepté" },
  { valeur: "refuse", label: "Refusé" },
  { valeur: "complement_requis", label: "Complément requis" },
  { valeur: "en_traitement", label: "En traitement" },
];

const DOMAINES = [
  { valeur: "", label: "Tous les domaines" },
  { valeur: "AUTO", label: "Auto" },
  { valeur: "CNAM_SOINS", label: "CNAM Soins" },
];

const STATUT_STYLE: Record<string, string> = {
  accepte: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  refuse: "bg-red-50 text-red-700 ring-red-600/20",
  complement_requis: "bg-amber-50 text-amber-700 ring-amber-600/20",
  en_traitement: "bg-blue-50 text-blue-700 ring-blue-600/20",
  recu: "bg-blue-50 text-blue-700 ring-blue-600/20",
  valide: "bg-blue-50 text-blue-700 ring-blue-600/20",
  invalide: "bg-slate-100 text-text-secondary ring-slate-500/20",
};

export default function DossiersListePage() {
  const searchParams = useSearchParams();
  const statutInitial = searchParams.get("statut") || "";
  const domaineInitial = searchParams.get("domaine") || "";

  const [dossiers, setDossiers] = useState<Dossier[]>([]);
  const [filtreStatut, setFiltreStatut] = useState(statutInitial);
  const [filtreDomaine, setFiltreDomaine] = useState(domaineInitial);
  const [recherche, setRecherche] = useState("");
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    setChargement(true);

    const params: Record<string, string> = {};
    if (filtreStatut) params.statut = filtreStatut;
    if (filtreDomaine) params.domaine = filtreDomaine;

    api
      .get("/dossiers", { params })
      .then((res) => setDossiers(res.data))
      .finally(() => setChargement(false));
  }, [filtreStatut, filtreDomaine]);

  const dossiersFiltres = dossiers.filter((d) =>
    d.reference_dossier.toLowerCase().includes(recherche.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          Tous les dossiers ({dossiersFiltres.length})
        </h2>
      </div>

      <div className="flex gap-3">
        <input
          type="text"
          placeholder="Rechercher par référence..."
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
        />

        <select
          value={filtreStatut}
          onChange={(e) => setFiltreStatut(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
        >
          {STATUTS.map((s) => (
            <option key={s.valeur} value={s.valeur}>
              {s.label}
            </option>
          ))}
        </select>

        <select
          value={filtreDomaine}
          onChange={(e) => setFiltreDomaine(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
        >
          {DOMAINES.map((d) => (
            <option key={d.valeur} value={d.valeur}>
              {d.label}
            </option>
          ))}
        </select>
      </div>

      {chargement ? (
        <p className="text-sm text-gray-500">Chargement...</p>
      ) : dossiersFiltres.length === 0 ? (
        <p className="text-sm text-gray-400">Aucun dossier trouvé</p>
      ) : (
        <div className="overflow-hidden rounded-lg border bg-surface">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Référence</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Statut</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Domaine</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Montant</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Date sinistre</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Créé le</th>
              </tr>
            </thead>
            <tbody>
              {dossiersFiltres.map((dossier) => (
                <tr
                  key={dossier.dossier_id}
                  className="cursor-pointer border-b last:border-0 hover:bg-gray-50"
                  onClick={() =>
                    (window.location.href = `/gestionnaire/dossiers/${dossier.dossier_id}`)
                  }
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/gestionnaire/dossiers/${dossier.dossier_id}`}
                      className="font-medium text-gray-900 hover:underline"
                    >
                      {dossier.reference_dossier}
                    </Link>
                  </td>

                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                        STATUT_STYLE[dossier.statut_global] || "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {dossier.statut_global}
                    </span>
                  </td>

                  <td className="px-4 py-3">
                    <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-text-secondary ring-1 ring-inset ring-slate-500/20">
                      {libelleDomaine(dossier.domaine)}
                    </span>
                  </td>

                  <td className="px-4 py-3 text-gray-700">
                    {dossier.montant_reclame ? `${dossier.montant_reclame} TND` : "—"}
                  </td>

                  <td className="px-4 py-3 text-gray-700">
                    {dossier.date_sinistre || "—"}
                  </td>

                  <td className="px-4 py-3 text-gray-500">
                    {new Date(dossier.created_at).toLocaleDateString("fr-FR")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}