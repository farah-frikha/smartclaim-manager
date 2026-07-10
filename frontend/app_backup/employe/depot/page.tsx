"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function DepotPage() {
  const router = useRouter();
  const [fichier, setFichier] = useState<File | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [resultat, setResultat] = useState<any>(null);
  const [erreur, setErreur] = useState("");

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) {
      setFichier(f);
      setResultat(null);
      setErreur("");
    }
  }

  async function handleUpload() {
    if (!fichier) return;

    setEnCours(true);
    setErreur("");

    const formData = new FormData();
    formData.append("fichier", fichier);

    try {
      const res = await api.post("/dossiers/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResultat(res.data);
    } catch (err: any) {
      setErreur(
        err.response?.data?.detail || "Erreur lors du traitement du document"
      );
    } finally {
      setEnCours(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">
          Déposer un document
        </h2>
        <p className="text-sm text-gray-500">
          Formats acceptés : PDF, JPG, PNG — 10 Mo maximum
        </p>
      </div>

      {!resultat ? (
        <div className="rounded-lg border bg-white p-8">
          <div className="rounded-lg border-2 border-dashed border-gray-300 p-8 text-center">
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileChange}
              className="hidden"
              id="fichier-input"
            />
            <label
              htmlFor="fichier-input"
              className="cursor-pointer text-sm text-gray-600"
            >
              {fichier ? (
                <span className="font-medium text-gray-900">
                  {fichier.name}
                </span>
              ) : (
                "Cliquez pour choisir un fichier"
              )}
            </label>
          </div>

          {erreur && (
            <p className="mt-4 text-sm text-red-600">{erreur}</p>
          )}

          <button
            onClick={handleUpload}
            disabled={!fichier || enCours}
            className="mt-4 w-full rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
          >
            {enCours
              ? "Traitement en cours (peut prendre 30-60 secondes)..."
              : "Envoyer le document"}
          </button>
        </div>
      ) : (
        <div className="rounded-lg border bg-white p-6">
          <div className="mb-4 flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                resultat.decision === "accepter"
                  ? "bg-green-500"
                  : resultat.decision === "refuser"
                  ? "bg-red-500"
                  : "bg-amber-500"
              }`}
            />
            <h3 className="text-sm font-medium text-gray-900">
              Traitement terminé
            </h3>
          </div>

          <div className="space-y-2 text-sm">
            <p>
              <span className="text-gray-500">Référence : </span>
              <span className="font-medium text-gray-900">
                {resultat.reference_dossier}
              </span>
            </p>
            {resultat.score !== null && (
              <p>
                <span className="text-gray-500">Score : </span>
                <span className="font-medium text-gray-900">
                  {resultat.score}/100
                </span>
              </p>
            )}
            <p className="mt-4 rounded-md bg-gray-50 p-3 text-gray-700">
              {resultat.message}
            </p>
          </div>

          <div className="mt-6 flex gap-3">
            <button
              onClick={() => {
                setResultat(null);
                setFichier(null);
              }}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              Déposer un autre document
            </button>
            <button
              onClick={() => router.push("/employe/dossiers")}
              className="rounded-md bg-gray-900 px-4 py-2 text-sm text-white hover:bg-gray-800"
            >
              Voir mes dossiers
            </button>
          </div>
        </div>
      )}
    </div>
  );
}