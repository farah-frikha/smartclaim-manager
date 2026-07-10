// app/employe/dossiers/page.tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";
import { Card, CardBody } from "@/components/ui-kit/Card";
import { StatutBadge } from "@/components/ui-kit/StatutBadge";
import { EmptyState } from "@/components/ui-kit/EmptyState";
import { FileText, ArrowRight } from "lucide-react";

interface Dossier {
  dossier_id: number;
  reference_dossier: string;
  statut_global: string;
  montant_reclame: number | null;
  date_sinistre: string | null;
  created_at: string;
}

export default function MesDossiersPage() {
  const [dossiers, setDossiers] = useState<Dossier[]>([]);
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    api
      .get("/dossiers/mes-dossiers")
      .then((res) => setDossiers(res.data))
      .finally(() => setChargement(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Mes dossiers</h1>
        <p className="mt-1 text-sm text-text-secondary">
          {dossiers.length} dossier{dossiers.length > 1 ? "s" : ""} au total
        </p>
      </div>

      {chargement ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton h-20 rounded-xl" />
          ))}
        </div>
      ) : dossiers.length === 0 ? (
        <Card>
          <CardBody>
            <EmptyState
              icon={FileText}
              title="Aucun dossier déposé"
              description="Vous n'avez pas encore déposé de dossier de sinistre."
            />
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-3">
          {dossiers.map((dossier) => (
            <Link
              key={dossier.dossier_id}
              href={`/employe/dossiers/${dossier.dossier_id}`}
              className="flex items-center justify-between rounded-xl border border-border-app bg-surface p-4 shadow-sm transition-all hover:border-teal-300 hover:shadow-md"
            >
              <div className="flex items-center gap-4">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-teal-50 text-teal-600">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    {dossier.reference_dossier}
                  </p>
                  <p className="text-xs text-text-muted">
                    {dossier.date_sinistre || "Date non renseignée"}
                    {dossier.montant_reclame
                      ? ` · ${dossier.montant_reclame.toLocaleString("fr-FR")} TND`
                      : ""}
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
    </div>
  );
}