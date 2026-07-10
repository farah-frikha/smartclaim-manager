// app/employe/depot/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { Card, CardBody } from "@/components/ui-kit/Card";
import {
  UploadCloud, FileText, CheckCircle2, XCircle, AlertCircle,
  Loader2, ArrowRight, RefreshCw,
} from "lucide-react";

export default function DepotPage() {
  const router = useRouter();
  const [fichier, setFichier] = useState<File | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [resultat, setResultat] = useState<any>(null);
  const [erreur, setErreur] = useState("");
  const [dragActive, setDragActive] = useState(false);

  function selectionner(f: File | undefined) {
    if (f) {
      setFichier(f);
      setResultat(null);
      setErreur("");
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragActive(false);
    selectionner(e.dataTransfer.files?.[0]);
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
      setErreur(err.response?.data?.detail || "Erreur lors du traitement du document");
    } finally {
      setEnCours(false);
    }
  }

  const decisionConfig: Record<string, { icon: any; couleur: string; bg: string; label: string }> = {
    accepter: { icon: CheckCircle2, couleur: "text-emerald-600", bg: "bg-emerald-50", label: "Dossier accepté" },
    refuser: { icon: XCircle, couleur: "text-red-600", bg: "bg-red-50", label: "Dossier refusé" },
    complement_requis: { icon: AlertCircle, couleur: "text-amber-600", bg: "bg-amber-50", label: "Complément requis" },
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Déposer un document</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Formats acceptés : PDF, JPG, PNG — 10 Mo maximum
        </p>
      </div>

      {!resultat ? (
        <Card>
          <CardBody>
            {/* Zone de drop */}
            <div
              onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              className={`rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
                dragActive
                  ? "border-teal-500 bg-teal-50"
                  : fichier
                  ? "border-teal-300 bg-teal-50/50"
                  : "border-border-app bg-muted"
              }`}
            >
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={(e) => selectionner(e.target.files?.[0])}
                className="hidden"
                id="fichier-input"
              />

              {fichier ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-teal-100 text-teal-600">
                    <FileText className="h-7 w-7" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-text-primary">{fichier.name}</p>
                    <p className="text-xs text-text-muted">
                      {(fichier.size / 1024).toFixed(0)} Ko
                    </p>
                  </div>
                  <label
                    htmlFor="fichier-input"
                    className="cursor-pointer text-xs font-medium text-teal-600 hover:text-teal-700"
                  >
                    Changer de fichier
                  </label>
                </div>
              ) : (
                <label htmlFor="fichier-input" className="cursor-pointer">
                  <div className="flex flex-col items-center gap-3">
                    <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-surface text-text-muted">
                      <UploadCloud className="h-7 w-7" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text-primary">
                        Glissez-déposez votre fichier ici
                      </p>
                      <p className="mt-0.5 text-xs text-text-muted">
                        ou cliquez pour parcourir
                      </p>
                    </div>
                  </div>
                </label>
              )}
            </div>

            {erreur && (
              <div className="mt-4 flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2.5 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {erreur}
              </div>
            )}

            <button
              onClick={handleUpload}
              disabled={!fichier || enCours}
              className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-teal-700 disabled:opacity-50"
            >
              {enCours ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Traitement en cours (30-60 s)...
                </>
              ) : (
                <>
                  <UploadCloud className="h-4 w-4" />
                  Envoyer le document
                </>
              )}
            </button>

            {enCours && (
              <p className="mt-3 text-center text-xs text-text-muted">
                Capture OCR → Extraction IA → Validation → Scoring → Décision
              </p>
            )}
          </CardBody>
        </Card>
      ) : (
        <Card>
          <CardBody>
            {(() => {
              const config = decisionConfig[resultat.decision] || decisionConfig.complement_requis;
              const Icon = config.icon;
              return (
                <div className="text-center">
                  <div className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full ${config.bg} ${config.couleur}`}>
                    <Icon className="h-8 w-8" />
                  </div>
                  <h2 className="mt-4 text-lg font-semibold text-text-primary">
                    {config.label}
                  </h2>
                  <p className="mt-1 text-sm text-text-secondary">Traitement terminé</p>

                  <div className="mx-auto mt-6 max-w-sm space-y-3 rounded-xl bg-muted p-4 text-left">
                    <div className="flex justify-between text-sm">
                      <span className="text-text-secondary">Référence</span>
                      <span className="font-medium text-text-primary">
                        {resultat.reference_dossier}
                      </span>
                    </div>
                    {resultat.score !== null && resultat.score !== undefined && (
                      <div className="flex justify-between text-sm">
                        <span className="text-text-secondary">Score</span>
                        <span className="font-medium text-text-primary">
                          {resultat.score}/100
                        </span>
                      </div>
                    )}
                    {resultat.message && (
                      <p className="border-t border-border-app pt-3 text-sm text-text-secondary">
                        {resultat.message}
                      </p>
                    )}
                  </div>

                  <div className="mt-6 flex justify-center gap-3">
                    <button
                      onClick={() => { setResultat(null); setFichier(null); }}
                      className="inline-flex items-center gap-2 rounded-lg border border-border-app px-4 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-hover"
                    >
                      <RefreshCw className="h-4 w-4" />
                      Nouveau dépôt
                    </button>
                    <button
                      onClick={() => router.push("/employe/dossiers")}
                      className="inline-flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-teal-700"
                    >
                      Voir mes dossiers
                      <ArrowRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              );
            })()}
          </CardBody>
        </Card>
      )}
    </div>
  );
}