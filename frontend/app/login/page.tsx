// app/login/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { sauvegarderSession } from "@/lib/auth";
import { Shield, Mail, Lock, ArrowRight, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreur, setErreur] = useState("");
  const [chargement, setChargement] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErreur("");
    setChargement(true);

    try {
      const reponse = await api.post("/auth/login", {
        email,
        mot_de_passe: motDePasse,
      });
      const { access_token, utilisateur } = reponse.data;
      sauvegarderSession(access_token, utilisateur);

      if (utilisateur.role === "EMPLOYE") {
        router.push("/employe");
      } else {
        router.push("/gestionnaire");
      }
    } catch (err: any) {
      setErreur(err.response?.data?.detail || "Email ou mot de passe incorrect");
    } finally {
      setChargement(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Panneau gauche — branding */}
      <div className="relative hidden w-1/2 flex-col justify-between bg-gradient-to-br from-teal-600 to-teal-800 p-12 text-white lg:flex">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/20 backdrop-blur">
            <Shield className="h-5 w-5" strokeWidth={2.5} />
          </div>
          <span className="text-lg font-semibold">SmartClaim</span>
        </div>

        <div className="space-y-4">
          <h1 className="text-3xl font-bold leading-tight">
            Gestion automatisée des sinistres d'assurance groupe
          </h1>
          <p className="text-teal-100">
            Traitement intelligent des dossiers par intelligence artificielle —
            capture, extraction, validation réglementaire et décision, en quelques secondes.
          </p>
        </div>

        <div className="flex gap-8 text-sm">
          <div>
            <p className="text-2xl font-bold">5</p>
            <p className="text-teal-200">Agents IA</p>
          </div>
          <div>
            <p className="text-2xl font-bold">14</p>
            <p className="text-teal-200">Règles métier</p>
          </div>
          <div>
            <p className="text-2xl font-bold">~40s</p>
            <p className="text-teal-200">Par dossier</p>
          </div>
        </div>
      </div>

      {/* Panneau droit — formulaire */}
      <div className="flex w-full items-center justify-center bg-app px-6 lg:w-1/2">
        <div className="w-full max-w-sm animate-fade-in">
          {/* Logo mobile */}
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-600">
              <Shield className="h-5 w-5 text-white" strokeWidth={2.5} />
            </div>
            <span className="text-lg font-semibold text-text-primary">SmartClaim</span>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-text-primary">Connexion</h2>
            <p className="mt-1 text-sm text-text-secondary">
              Accédez à votre espace de travail
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-text-secondary">
                Adresse email
              </label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-lg border border-border-app bg-surface py-2.5 pl-10 pr-3 text-sm text-text-primary outline-none transition-colors focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
                  placeholder="vous@assurance.tn"
                />
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-text-secondary">
                Mot de passe
              </label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                <input
                  type="password"
                  required
                  value={motDePasse}
                  onChange={(e) => setMotDePasse(e.target.value)}
                  className="w-full rounded-lg border border-border-app bg-surface py-2.5 pl-10 pr-3 text-sm text-text-primary outline-none transition-colors focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {erreur && (
              <div className="flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2.5 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {erreur}
              </div>
            )}

            <button
              type="submit"
              disabled={chargement}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-teal-700 disabled:opacity-50"
            >
              {chargement ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Connexion...
                </>
              ) : (
                <>
                  Se connecter
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-xs text-text-muted">
            SmartClaim Manager — Système de gestion des sinistres
          </p>
        </div>
      </div>
    </div>
  );
}