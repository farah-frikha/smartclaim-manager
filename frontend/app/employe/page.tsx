// app/employe/page.tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { obtenirUtilisateur } from "@/lib/auth";
import { Card, CardHeader, CardBody } from "@/components/ui-kit/Card";
import { StatCard } from "@/components/ui-kit/StatCard";
import { StatutBadge } from "@/components/ui-kit/StatutBadge";
import { EmptyState } from "@/components/ui-kit/EmptyState";
import { SkeletonCard } from "@/components/ui-kit/Skeleton";
import {
  UploadCloud, FolderOpen, CheckCircle2, Clock, FileText, ArrowRight,
} from "lucide-react";

interface Dossier {
  dossier_id: number;
  reference_dossier: string;
  statut_global: string;
  montant_reclame: number | null;
  date_sinistre: string | null;
  created_at: string;
}

export default function EmployeAccueilPage() {
  const [dossiers, setDossiers] = useState<Dossier[]>([]);
  const [chargement, setChargement] = useState(true);
  const utilisateur = obtenirUtilisateur();

  useEffect(() => {
    api
      .get("/dossiers/mes-dossiers")
      .then((res) => setDossiers(res.data))
      .finally(() => setChargement(false));
  }, []);

  const acceptes = dossiers.filter((d) => d.statut_global === "accepte").length;
  const enCours = dossiers.filter((d) =>
    ["en_traitement", "recu", "valide"].includes(d.statut_global)
  ).length;

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">
          Bonjour {utilisateur?.nom_complet?.split(" ")[0]} 👋
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Voici un aperçu de vos dossiers de sinistres
        </p>
      </div>

      {/* Bandeau d'action */}
      <div className="flex items-center justify-between rounded-xl bg-gradient-to-r from-teal-600 to-teal-700 p-6 text-white">
        <div>
          <h2 className="text-lg font-semibold">Un nouveau sinistre à déclarer ?</h2>
          <p className="mt-1 text-sm text-teal-100">
            Déposez votre document, notre IA s'occupe du reste en quelques secondes.
          </p>
        </div>
        <Link
          href="/employe/depot"
          className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-white px-4 py-2.5 text-sm font-medium text-teal-700 shadow-sm transition-transform hover:scale-105"
        >
          <UploadCloud className="h-4 w-4" />
          Déposer un document
        </Link>
      </div>

      {/* Stats */}
      {chargement ? (
        <div className="grid grid-cols-3 gap-4">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          <StatCard label="Total dossiers" value={dossiers.length} icon={FolderOpen} tone="brand" />
          <StatCard label="Acceptés" value={acceptes} icon={CheckCircle2} tone="success" />
          <StatCard label="En cours" value={enCours} icon={Clock} tone="warning" />
        </div>
      )}

      {/* Derniers dossiers */}
      <Card>
        <CardHeader
          title="Vos dossiers récents"
          subtitle="Les derniers dossiers déposés"
          action={
            dossiers.length > 0 ? (
              <Link
                href="/employe/dossiers"
                className="text-xs font-medium text-teal-600 hover:text-teal-700"
              >
                Tout voir
              </Link>
            ) : undefined
          }
        />
        <CardBody className="p-0">
          {chargement ? (
            <div className="space-y-3 p-5">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="skeleton h-14 rounded-lg" />
              ))}
            </div>
          ) : dossiers.length === 0 ? (
            <div className="p-5">
              <EmptyState
                icon={FileText}
                title="Aucun dossier déposé"
                description="Déposez votre premier document pour démarrer une déclaration de sinistre."
              />
            </div>
          ) : (
            <div className="divide-y divide-border-light">
              {dossiers.slice(0, 5).map((dossier) => (
                <Link
                  key={dossier.dossier_id}
                  href={`/employe/dossiers/${dossier.dossier_id}`}
                  className="flex items-center justify-between px-5 py-4 transition-colors hover:bg-surface-hover"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-teal-600">
                      <FileText className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text-primary">
                        {dossier.reference_dossier}
                      </p>
                      <p className="text-xs text-text-muted">
                        {dossier.montant_reclame
                          ? `${dossier.montant_reclame.toLocaleString("fr-FR")} TND`
                          : "Montant non renseigné"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatutBadge statut={dossier.statut_global} />
                    <ArrowRight className="h-4 w-4 text-text-muted" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}