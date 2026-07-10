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

  useEffect(() => {
    api
      .get(`/dossiers/${params.id}`)
      .then((res) => setData(res.data))
      .catch(() => setErreur("Vous n'avez pas accès à ce dossier"))
      .finally(() => setChargement(false));
  }, [params.id]);

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
      <Card>
        <CardHeader title="Informations du dossier" subtitle="Données extraites de votre document" />
        <CardBody className="p-0">
          <div className="divide-y divide-border-light">
            {Object.entries(champs).map(([nom, valeur]) => (
              <div key={nom} className="flex items-center justify-between px-5 py-3">
                <span className="text-sm text-text-secondary capitalize">
                  {nom.replace(/_/g, " ")}
                </span>
                <span className="text-sm font-medium text-text-primary text-right max-w-md">
                  {valeur || "—"}
                </span>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}