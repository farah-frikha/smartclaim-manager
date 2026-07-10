"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { obtenirUtilisateur } from "@/lib/auth";

interface UtilisateurItem {
  utilisateur_id: number;
  email: string;
  role: string;
  nom_complet: string;
  actif: number;
  derniere_connexion: string | null;
  created_at: string;
}

const ROLE_STYLE: Record<string, string> = {
  ADMIN: "bg-purple-100 text-purple-700",
  GESTIONNAIRE: "bg-blue-100 text-blue-700",
  EMPLOYE: "bg-gray-100 text-gray-700",
};

export default function UtilisateursPage() {
  const router = useRouter();
  const [utilisateurs, setUtilisateurs] = useState<UtilisateurItem[]>([]);
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    const user = obtenirUtilisateur();
    if (user?.role !== "ADMIN") {
      router.push("/gestionnaire");
      return;
    }

    api
      .get("/auth/utilisateurs")
      .then((res) => setUtilisateurs(res.data))
      .finally(() => setChargement(false));
  }, [router]);

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">
        Gestion des utilisateurs ({utilisateurs.length})
      </h2>

      {chargement ? (
        <p className="text-sm text-gray-500">Chargement...</p>
      ) : (
        <div className="overflow-hidden rounded-lg border bg-surface">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Nom</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Email</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Rôle</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Statut</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Dernière connexion</th>
              </tr>
            </thead>
            <tbody>
              {utilisateurs.map((u) => (
                <tr key={u.utilisateur_id} className="border-b last:border-0">
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {u.nom_complet}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{u.email}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-medium ${ROLE_STYLE[u.role]}`}
                    >
                      {u.role}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {u.actif ? (
                      <span className="text-green-600">Actif</span>
                    ) : (
                      <span className="text-gray-400">Désactivé</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {u.derniere_connexion
                      ? new Date(u.derniere_connexion).toLocaleString("fr-FR")
                      : "Jamais connecté"}
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