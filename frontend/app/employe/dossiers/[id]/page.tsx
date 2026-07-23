// app/employe/dossiers/[id]/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import api from "@/lib/api";
import { Card, CardHeader, CardBody } from "@/components/ui-kit/Card";
import { StatutBadge } from "@/components/ui-kit/StatutBadge";
import { EmptyState } from "@/components/ui-kit/EmptyState";
import {
  ArrowLeft, CheckCircle2, XCircle, AlertCircle, FileText,
} from "lucide-react";

interface DossierDetail {
  dossier: {
    reference_dossier: string;
    statut_global: string;
  };
  champs: Record<string, string>;
  decision: {
    decision: string;
    message_client: string;
  } | null;
}

export default function MonDossierDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [data, setData] = useState<DossierDetail | null>(null);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [reclamOuvert, setReclamOuvert] = useState(false);
  const [messageReclam, setMessageReclam] = useState("");
  const [envoiOk, setEnvoiOk] = useState(false);
  const [mesReclamations, setMesReclamations] = useState<any[]>([]);

  useEffect(() => {
    api
      .get(`/dossiers/${params.id}`)
      .then((res) => setData(res.data))
      .catch(() => setErreur("Vous n'avez pas accès à ce dossier"))
      .finally(() => setChargement(false));
  }, [params.id]);
const chargerReclamations = () => {
    api.get("/reclamations/mes-reclamations")
      .then((res) =>
        setMesReclamations(
          res.data.filter((r: any) => r.dossier_id === Number(params.id))
        )
      )
      .catch(() => {});
  };

  useEffect(chargerReclamations, [params.id]);  
const envoyerReclamation = async () => {
    if (!messageReclam.trim()) return;
    try {
      await api.post("/reclamations", {
        dossier_id: Number(params.id),
        message: messageReclam.trim(),
      });
      setEnvoiOk(true);
      setMessageReclam("");
      chargerReclamations();
      setTimeout(() => { setReclamOuvert(false); setEnvoiOk(false); }, 2000);
    } catch {
      alert("Erreur lors de l'envoi de la réclamation");
    }
  };
  if (chargement) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-8 w-48 rounded-lg" />
        <div className="skeleton h-32 rounded-xl" />
        <div className="skeleton h-64 rounded-xl" />
      </div>
    );
  }

  if (erreur || !data) {
    return (
      <EmptyState icon={AlertCircle} title="Accès refusé" description={erreur} />
    );
  }

  const { dossier, champs, decision } = data;

  const decisionConfig: Record<string, { icon: any; couleur: string; bg: string; border: string; label: string }> = {
    accepter: { icon: CheckCircle2, couleur: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200", label: "Dossier accepté" },
    refuser: { icon: XCircle, couleur: "text-red-600", bg: "bg-red-50", border: "border-red-200", label: "Dossier refusé" },
    complement_requis: { icon: AlertCircle, couleur: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200", label: "Complément requis" },
  };

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border-app text-text-secondary transition-colors hover:bg-surface-hover"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="text-xl font-semibold text-text-primary">
              {dossier.reference_dossier}
            </h1>
            <div className="mt-1">
              <StatutBadge statut={dossier.statut_global} />
            </div>
          </div>
        </div>
      </div>

      {/* Bandeau décision */}
      {decision && (() => {
        const config = decisionConfig[decision.decision] || decisionConfig.complement_requis;
        const Icon = config.icon;
        return (
          <div className={`flex items-start gap-4 rounded-xl border ${config.border} ${config.bg} p-5`}>
            <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-surface ${config.couleur}`}>
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <p className="font-semibold text-text-primary">{config.label}</p>
              <p className="mt-1 text-sm text-text-secondary">
                {decision.message_client}
              </p>
            </div>
          </div>
        );
      })()}

      {/* Informations */}
{/* Réclamation */}
      <Card>
        <CardHeader
          title="Une question sur ce dossier ?"
          subtitle="Adressez une réclamation au service de gestion"
        />
        <CardBody>
          {/* Réclamations déjà déposées */}
          {mesReclamations.length > 0 && (
            <div className="mb-5 space-y-3">
              {mesReclamations.map((r) => (
                <div
                  key={r.reclamation_id}
                  className="rounded-lg border border-border-light p-4"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs text-text-muted">
                      {new Date(r.created_at).toLocaleDateString("fr-FR")}
                    </span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        r.statut === "ouverte"
                          ? "bg-amber-50 text-amber-700"
                          : "bg-emerald-50 text-emerald-700"
                      }`}
                    >
                      {r.statut === "ouverte" ? "En attente" : "Répondue"}
                    </span>
                  </div>

                  <p className="text-sm text-text-primary">{r.message}</p>

                  {r.reponse && (
                    <div className="mt-3 rounded-md bg-surface-hover p-3">
                      <p className="mb-1 text-xs font-medium text-text-muted">
                        Réponse du service de gestion
                      </p>
                      <p className="text-sm text-text-primary">{r.reponse}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          {envoiOk ? (
            <p className="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              Votre réclamation a bien été transmise. Un gestionnaire vous répondra.
            </p>
          ) : !reclamOuvert ? (
            <button
              onClick={() => setReclamOuvert(true)}
              className="flex items-center gap-2 rounded-lg border border-border-app px-4 py-2 text-sm font-medium text-text-primary transition-colors hover:bg-surface-hover"
            >
              <FileText className="h-4 w-4" />
              Déposer une réclamation
            </button>
          ) : (
            <div className="space-y-3">
              <textarea
                value={messageReclam}
                onChange={(e) => setMessageReclam(e.target.value)}
                rows={4}
                placeholder="Décrivez le motif de votre réclamation..."
                className="w-full rounded-lg border border-border-app bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:border-teal-600 focus:outline-none"
              />
              <div className="flex gap-2">
                <button
                  onClick={envoyerReclamation}
                  disabled={!messageReclam.trim()}
                  className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-teal-800 disabled:opacity-50"
                >
                  Envoyer
                </button>
                <button
                  onClick={() => { setReclamOuvert(false); setMessageReclam(""); }}
                  className="rounded-lg px-4 py-2 text-sm text-text-secondary transition-colors hover:bg-surface-hover"
                >
                  Annuler
                </button>
              </div>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}