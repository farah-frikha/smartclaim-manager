"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { obtenirUtilisateur } from "@/lib/auth";

const TYPES_REGLES = ["validation", "scoring", "decision", "coordinateur"];

export default function ReglesPage() {
  const router = useRouter();
  const [typeSelectionne, setTypeSelectionne] = useState("validation");
  const [contenu, setContenu] = useState("");
  const [motif, setMotif] = useState("");
  const [chargement, setChargement] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const user = obtenirUtilisateur();
    if (user?.role !== "ADMIN") {
      router.push("/gestionnaire");
      return;
    }
    chargerRegles(typeSelectionne);
  }, [typeSelectionne, router]);

  function chargerRegles(type: string) {
    setChargement(true);
    setMessage("");
    api
      .get(`/regles/${type}`)
      .then((res) => setContenu(JSON.stringify(res.data.contenu, null, 2)))
      .catch(() => setMessage("Erreur de chargement"))
      .finally(() => setChargement(false));
  }

  async function sauvegarder() {
    try {
      const contenuParsed = JSON.parse(contenu);
      await api.put(`/regles/${typeSelectionne}`, {
        contenu: contenuParsed,
        motif: motif || "Modification depuis l'interface",
      });
      setMessage("✓ Règles mises à jour avec succès");
      setMotif("");
    } catch (err: any) {
      if (err instanceof SyntaxError) {
        setMessage("✗ JSON invalide — vérifiez la syntaxe");
      } else {
        setMessage("✗ Erreur lors de la sauvegarde");
      }
    }
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">
        Édition des règles métier
      </h2>

      <div className="flex gap-2">
        {TYPES_REGLES.map((type) => (
          <button
            key={type}
            onClick={() => setTypeSelectionne(type)}
            className={`rounded-md px-3 py-1.5 text-sm ${
              typeSelectionne === type
                ? "bg-gray-900 text-white"
                : "border border-gray-300 text-gray-700 hover:bg-gray-50"
            }`}
          >
            {type}
          </button>
        ))}
      </div>

      {chargement ? (
        <p className="text-sm text-gray-500">Chargement...</p>
      ) : (
        <>
          <textarea
            value={contenu}
            onChange={(e) => setContenu(e.target.value)}
            className="h-96 w-full rounded-md border border-gray-300 p-3 font-mono text-xs focus:border-gray-900 focus:outline-none"
            spellCheck={false}
          />

          <input
            type="text"
            placeholder="Motif de la modification (tracé dans l'audit)"
            value={motif}
            onChange={(e) => setMotif(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
          />

          {message && (
            <p
              className={`text-sm ${
                message.startsWith("✓") ? "text-green-600" : "text-red-600"
              }`}
            >
              {message}
            </p>
          )}

          <button
            onClick={sauvegarder}
            className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
          >
            Sauvegarder les modifications
          </button>
        </>
      )}
    </div>
  );
}