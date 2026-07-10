// app/login/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { sauvegarderSession } from "@/lib/auth";

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

      // Redirection selon le rôle reçu dans le token
      if (utilisateur.role === "EMPLOYE") {
        router.push("/employe");
      } else {
        router.push("/gestionnaire");
      }
    } catch (err: any) {
      setErreur(
        err.response?.data?.detail || "Email ou mot de passe incorrect"
      );
    } finally {
      setChargement(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-lg border bg-white p-8 shadow-sm">
        <h1 className="mb-1 text-xl font-semibold text-gray-900">
          SmartClaim Manager
        </h1>
        <p className="mb-6 text-sm text-gray-500">
          Connectez-vous à votre espace
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
              placeholder="vous@assurance.tn"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Mot de passe
            </label>
            <input
              type="password"
              required
              value={motDePasse}
              onChange={(e) => setMotDePasse(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
              placeholder="••••••••"
            />
          </div>

          {erreur && (
            <p className="text-sm text-red-600">{erreur}</p>
          )}

          <button
            type="submit"
            disabled={chargement}
            className="w-full rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
          >
            {chargement ? "Connexion..." : "Se connecter"}
          </button>
        </form>
      </div>
    </div>
  );
}