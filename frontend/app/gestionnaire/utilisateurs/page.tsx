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
  const [formOuvert, setFormOuvert] = useState(false);
  const [nouveau, setNouveau] = useState({
    email: "",
    mot_de_passe: "",
    nom_complet: "",
    role: "EMPLOYE",
    numero_cnss: "",
  });
  const [erreur, setErreur] = useState("");
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
  const basculerStatut = async (u: UtilisateurItem) => {
      const action = u.actif ? "désactiver" : "activer";
      if (!confirm(`Voulez-vous ${action} le compte de ${u.nom_complet} ?`)) return;

      try {
        await api.put(`/auth/utilisateurs/${u.utilisateur_id}/statut`, {
          actif: !u.actif,
        });
        setUtilisateurs((liste) =>
          liste.map((item) =>
            item.utilisateur_id === u.utilisateur_id
              ? { ...item, actif: item.actif ? 0 : 1 }
              : item
          )
        );
      } catch (err) {
        alert("Erreur lors de la modification du statut");
      }
    };
    const creerUtilisateur = async () => {
    setErreur("");
    if (!nouveau.email || !nouveau.mot_de_passe || !nouveau.nom_complet) {
      setErreur("Tous les champs marqués sont obligatoires");
      return;
    }
    if (nouveau.role === "EMPLOYE" && !nouveau.numero_cnss) {
      setErreur("Le numéro CNSS est obligatoire pour un employé");
      return;
    }

    try {
      await api.post("/auth/register", nouveau);
      const res = await api.get("/auth/utilisateurs");
      setUtilisateurs(res.data);
      setFormOuvert(false);
      setNouveau({ email: "", mot_de_passe: "", nom_complet: "",
                   role: "EMPLOYE", numero_cnss: "" });
    } catch (err: any) {
      setErreur(err.response?.data?.detail || "Erreur lors de la création");
    }
  };
return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          Gestion des utilisateurs ({utilisateurs.length})
        </h2>
        <button
          onClick={() => setFormOuvert(true)}
          className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800"
        >
          Nouvel utilisateur
        </button>
      </div>

      {formOuvert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg bg-surface p-6 shadow-lg">
            <h3 className="mb-4 text-base font-semibold text-gray-900">
              Créer un utilisateur
            </h3>

            {erreur && (
              <p className="mb-3 rounded bg-red-50 px-3 py-2 text-sm text-red-700">
                {erreur}
              </p>
            )}

            <div className="space-y-3">
              <input
                type="text"
                placeholder="Nom complet *"
                value={nouveau.nom_complet}
                onChange={(e) => setNouveau({ ...nouveau, nom_complet: e.target.value })}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
              <input
                type="email"
                placeholder="Email *"
                value={nouveau.email}
                onChange={(e) => setNouveau({ ...nouveau, email: e.target.value })}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
              <input
                type="password"
                placeholder="Mot de passe *"
                value={nouveau.mot_de_passe}
                onChange={(e) => setNouveau({ ...nouveau, mot_de_passe: e.target.value })}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
              <select
                value={nouveau.role}
                onChange={(e) => setNouveau({ ...nouveau, role: e.target.value })}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="EMPLOYE">Employé</option>
                <option value="GESTIONNAIRE">Gestionnaire</option>
                <option value="ADMIN">Administrateur</option>
              </select>

              {nouveau.role === "EMPLOYE" && (
                <input
                  type="text"
                  placeholder="Numéro CNSS *"
                  value={nouveau.numero_cnss}
                  onChange={(e) => setNouveau({ ...nouveau, numero_cnss: e.target.value })}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              )}
            </div>

            <div className="mt-5 flex justify-end gap-2">
              <button
                onClick={() => { setFormOuvert(false); setErreur(""); }}
                className="rounded-md px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
              >
                Annuler
              </button>
              <button
                onClick={creerUtilisateur}
                className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800"
              >
                Créer
              </button>
            </div>
          </div>
        </div>
      )}
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
                <th className="px-4 py-3 text-left font-medium text-gray-500">Action</th>
                
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
                  
                  <td className="px-4 py-3">
                  <button
                    onClick={() => basculerStatut(u)}
                    className={`rounded-md px-3 py-1 text-xs font-medium transition ${
                      u.actif
                        ? "bg-red-50 text-red-700 hover:bg-red-100"
                        : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                    }`}
                  >
                    {u.actif ? "Désactiver" : "Activer"}
                  </button>
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