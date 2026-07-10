// app/gestionnaire/parametres/page.tsx
"use client";

import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import api from "@/lib/api";
import { obtenirUtilisateur } from "@/lib/auth";
import { Card, CardHeader, CardBody } from "@/components/ui-kit/Card";
import {
  Lock, Palette, Check, Sun, Moon, Monitor,
} from "lucide-react";

export default function ParametresPage() {
  const utilisateur = obtenirUtilisateur();
  const { theme, setTheme } = useTheme();

  const [monte, setMonte] = useState(false);
  const [langue, setLangue] = useState("fr");
  const [ancienMdp, setAncienMdp] = useState("");
  const [nouveauMdp, setNouveauMdp] = useState("");
  const [confirmMdp, setConfirmMdp] = useState("");
  const [chargement, setChargement] = useState(false);
  const [message, setMessage] = useState<{ type: string; texte: string } | null>(null);

  // Évite les erreurs d'hydratation avec next-themes
  useEffect(() => setMonte(true), []);

  const initiales = utilisateur?.nom_complet
    .split(" ")
    .map((m) => m[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  async function changerMotDePasse() {
    setMessage(null);

    if (nouveauMdp !== confirmMdp) {
      setMessage({ type: "erreur", texte: "Les mots de passe ne correspondent pas" });
      return;
    }
    if (nouveauMdp.length < 6) {
      setMessage({ type: "erreur", texte: "Le mot de passe doit faire au moins 6 caractères" });
      return;
    }

    setChargement(true);
    try {
      await api.put("/auth/mot-de-passe", {
        ancien_mot_de_passe: ancienMdp,
        nouveau_mot_de_passe: nouveauMdp,
      });
      setMessage({ type: "succes", texte: "Mot de passe mis à jour avec succès" });
      setAncienMdp("");
      setNouveauMdp("");
      setConfirmMdp("");
    } catch (err: any) {
      setMessage({
        type: "erreur",
        texte: err.response?.data?.detail || "Erreur lors de la modification",
      });
    } finally {
      setChargement(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Paramètres</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Gérez votre profil et vos préférences
        </p>
      </div>

      {/* Profil */}
      <Card>
        <CardHeader title="Profil" subtitle="Vos informations personnelles" />
        <CardBody>
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-teal-600 text-xl font-semibold text-white">
              {initiales}
            </div>
            <div>
              <p className="text-base font-semibold text-text-primary">
                {utilisateur?.nom_complet}
              </p>
              <p className="text-sm text-text-secondary">{utilisateur?.email}</p>
              <span className="mt-1 inline-flex items-center gap-1 rounded-full bg-teal-50 px-2.5 py-0.5 text-xs font-medium text-teal-700 ring-1 ring-inset ring-teal-600/20">
                {utilisateur?.role}
              </span>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Apparence */}
      <Card>
        <CardHeader title="Apparence" subtitle="Personnalisez l'affichage" />
        <CardBody>
          <label className="mb-2 flex items-center gap-2 text-sm font-medium text-text-secondary">
            <Palette className="h-4 w-4 text-text-muted" />
            Thème
          </label>
          <div className="grid grid-cols-3 gap-3">
            {[
              { val: "light", label: "Clair", icon: Sun },
              { val: "dark", label: "Sombre", icon: Moon },
              { val: "system", label: "Système", icon: Monitor },
            ].map((t) => {
              const Icon = t.icon;
              const actif = monte && theme === t.val;
              return (
                <button
                  key={t.val}
                  onClick={() => setTheme(t.val)}
                  className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-colors ${
                    actif
                      ? "border-teal-500 bg-teal-50"
                      : "border-border-app hover:border-border-app"
                  }`}
                >
                  <Icon className={`h-5 w-5 ${actif ? "text-teal-600" : "text-text-muted"}`} />
                  <span className={`text-sm font-medium ${actif ? "text-teal-700" : "text-text-secondary"}`}>
                    {t.label}
                  </span>
                  {actif && <Check className="h-3.5 w-3.5 text-teal-600" />}
                </button>
              );
            })}
          </div>
        </CardBody>
      </Card>

      {/* Langue */}
      <Card>
        <CardHeader title="Langue" subtitle="Choisissez votre langue préférée" />
        <CardBody>
          <div className="grid grid-cols-2 gap-3">
            {[
              { val: "fr", label: "Français", drapeau: "🇫🇷" },
              { val: "en", label: "English", drapeau: "🇬🇧" },
            ].map((l) => {
              const actif = langue === l.val;
              return (
                <button
                  key={l.val}
                  onClick={() => setLangue(l.val)}
                  className={`flex items-center gap-3 rounded-lg border-2 p-3 transition-colors ${
                    actif
                      ? "border-teal-500 bg-teal-50"
                      : "border-border-app hover:border-border-app"
                  }`}
                >
                  <span className="text-xl">{l.drapeau}</span>
                  <span className={`text-sm font-medium ${actif ? "text-teal-700" : "text-text-secondary"}`}>
                    {l.label}
                  </span>
                  {actif && <Check className="ml-auto h-4 w-4 text-teal-600" />}
                </button>
              );
            })}
          </div>
          <p className="mt-2 text-xs text-text-muted">
            La traduction complète sera activée prochainement
          </p>
        </CardBody>
      </Card>

      {/* Sécurité */}
      <Card>
        <CardHeader title="Sécurité" subtitle="Modifiez votre mot de passe" />
        <CardBody className="space-y-4">
          {message && (
            <div
              className={`rounded-lg px-4 py-3 text-sm ${
                message.type === "succes"
                  ? "bg-emerald-50 text-emerald-700"
                  : "bg-red-50 text-red-700"
              }`}
            >
              {message.texte}
            </div>
          )}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-text-secondary">
              Mot de passe actuel
            </label>
            <input
              type="password"
              value={ancienMdp}
              onChange={(e) => setAncienMdp(e.target.value)}
              className="w-full rounded-lg border border-border-app px-3 py-2 text-sm outline-none transition-colors focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
              placeholder="••••••••"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-text-secondary">
                Nouveau mot de passe
              </label>
              <input
                type="password"
                value={nouveauMdp}
                onChange={(e) => setNouveauMdp(e.target.value)}
                className="w-full rounded-lg border border-border-app px-3 py-2 text-sm outline-none transition-colors focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-text-secondary">
                Confirmer
              </label>
              <input
                type="password"
                value={confirmMdp}
                onChange={(e) => setConfirmMdp(e.target.value)}
                className="w-full rounded-lg border border-border-app px-3 py-2 text-sm outline-none transition-colors focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
                placeholder="••••••••"
              />
            </div>
          </div>
          <button
            onClick={changerMotDePasse}
            disabled={chargement || !ancienMdp || !nouveauMdp || !confirmMdp}
            className="inline-flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-teal-700 disabled:opacity-50"
          >
            <Lock className="h-4 w-4" />
            {chargement ? "Modification..." : "Mettre à jour le mot de passe"}
          </button>
        </CardBody>
      </Card>
    </div>
  );
}