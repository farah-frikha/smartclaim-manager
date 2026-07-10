// app/gestionnaire/page.tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api from "@/lib/api";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart,
} from "recharts";
import {
  FolderOpen, CheckCircle2, XCircle, AlertCircle, Clock,
  TrendingUp, Gauge, ArrowUpRight, Activity, ScrollText,
} from "lucide-react";
import { StatCard } from "@/components/ui-kit/StatCard";
import { Card, CardHeader, CardBody } from "@/components/ui-kit/Card";
import { SkeletonCard } from "@/components/ui-kit/Skeleton";
import { StatutBadge } from "@/components/ui-kit/StatutBadge";
import { EmptyState } from "@/components/ui-kit/EmptyState";
import { ProgressBar } from "@/components/ui-kit/ProgressBar";

interface Stats {
  total_dossiers: number;
  acceptes: number;
  refuses: number;
  complement_requis: number;
  en_cours: number;
  taux_acceptation: number;
  score_moyen: number | null;
  activite_7_jours: { jour: string; nb: number }[];
}

interface Dossier {
  dossier_id: number;
  reference_dossier: string;
  statut_global: string;
  montant_reclame: number | null;
  created_at: string;
}

const COULEURS_DECISION = {
  acceptes: "#10b981",
  refuses: "#ef4444",
  complement_requis: "#f59e0b",
  en_cours: "#3b82f6",
};

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [derniers, setDerniers] = useState<Dossier[]>([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    Promise.all([
      api.get("/dashboard/stats"),
      api.get("/dossiers", { params: { limite: 6 } }),
    ])
      .then(([resStats, resDossiers]) => {
        setStats(resStats.data);
        setDerniers(resDossiers.data.slice(0, 6));
      })
      .catch(() => setErreur("Impossible de charger le tableau de bord"))
      .finally(() => setChargement(false));
  }, []);

  if (chargement) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  if (erreur || !stats) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="Erreur de chargement"
        description={erreur}
      />
    );
  }

  const donneesRepartition = [
    { nom: "Acceptés", valeur: stats.acceptes, couleur: COULEURS_DECISION.acceptes },
    { nom: "Refusés", valeur: stats.refuses, couleur: COULEURS_DECISION.refuses },
    { nom: "Complément", valeur: stats.complement_requis, couleur: COULEURS_DECISION.complement_requis },
    { nom: "En cours", valeur: stats.en_cours, couleur: COULEURS_DECISION.en_cours },
  ].filter((d) => d.valeur > 0);

  const totalTraite = stats.acceptes + stats.refuses;
  const tauxRefus = totalTraite > 0 ? Math.round((stats.refuses / totalTraite) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">
            Tableau de bord
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Vue d'ensemble de l'activité de traitement des sinistres
          </p>
        </div>
        <Link
          href="/gestionnaire/dossiers"
          className="inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-teal-700"
        >
          Voir tous les dossiers
          <ArrowUpRight className="h-4 w-4" />
        </Link>
      </div>

      {/* KPIs principaux */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Total dossiers"
          value={stats.total_dossiers}
          icon={FolderOpen}
          tone="brand"
          hint="Depuis le lancement"
          href="/gestionnaire/dossiers"
        />
        <StatCard
          label="Acceptés"
          value={stats.acceptes}
          icon={CheckCircle2}
          tone="success"
          hint={`${stats.taux_acceptation}% du traité`}
          href="/gestionnaire/dossiers?statut=accepte"
        />
        <StatCard
          label="Refusés"
          value={stats.refuses}
          icon={XCircle}
          tone="danger"
          hint={`${tauxRefus}% du traité`}
          href="/gestionnaire/dossiers?statut=refuse"
        />
        <StatCard
          label="Score moyen"
          value={stats.score_moyen !== null ? `${stats.score_moyen}` : "—"}
          icon={Gauge}
          tone="warning"
          hint="Sur 100 points"
        />
      </div>

      {/* Ligne graphiques */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Activité 7 jours */}
        <Card className="lg:col-span-2">
          <CardHeader
            title="Activité des 7 derniers jours"
            subtitle="Nombre de dossiers traités par jour"
          />
          <CardBody>
            {stats.activite_7_jours.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={stats.activite_7_jours}>
                  <defs>
                    <linearGradient id="colorActivite" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                  <XAxis
                    dataKey="jour"
                    tick={{ fontSize: 11, fill: "#94a3b8" }}
                    tickLine={false}
                    axisLine={{ stroke: "#e2e8f0" }}
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fontSize: 11, fill: "#94a3b8" }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: 8,
                      border: "1px solid #e2e8f0",
                      fontSize: 12,
                      boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="nb"
                    stroke="#0d9488"
                    strokeWidth={2}
                    fill="url(#colorActivite)"
                    name="Dossiers"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState icon={Activity} title="Aucune activité récente" />
            )}
          </CardBody>
        </Card>

        {/* Répartition décisions */}
        <Card>
          <CardHeader title="Répartition" subtitle="Par type de décision" />
          <CardBody>
            {donneesRepartition.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart>
                    <Pie
                      data={donneesRepartition}
                      dataKey="valeur"
                      nameKey="nom"
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={75}
                      paddingAngle={2}
                    >
                      {donneesRepartition.map((d, i) => (
                        <Cell key={i} fill={d.couleur} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        borderRadius: 8,
                        border: "1px solid #e2e8f0",
                        fontSize: 12,
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-3 space-y-2">
                  {donneesRepartition.map((d) => (
                    <div key={d.nom} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <span
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ backgroundColor: d.couleur }}
                        />
                        <span className="text-slate-600">{d.nom}</span>
                      </div>
                      <span className="font-medium text-slate-900">{d.valeur}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <EmptyState icon={Activity} title="Aucune donnée" />
            )}
          </CardBody>
        </Card>
      </div>

      {/* Ligne inférieure */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Indicateurs de performance */}
        <Card>
          <CardHeader title="Performance" subtitle="Indicateurs clés" />
          <CardBody className="space-y-5">
            <div>
              <div className="mb-1.5 flex items-center justify-between text-sm">
                <span className="text-slate-600">Taux d'acceptation</span>
                <span className="font-semibold text-slate-900">
                  {stats.taux_acceptation}%
                </span>
              </div>
              <ProgressBar value={stats.taux_acceptation} tone="success" />
            </div>
            <div>
              <div className="mb-1.5 flex items-center justify-between text-sm">
                <span className="text-slate-600">Taux de refus</span>
                <span className="font-semibold text-slate-900">{tauxRefus}%</span>
              </div>
              <ProgressBar value={tauxRefus} tone="danger" />
            </div>
            <div>
              <div className="mb-1.5 flex items-center justify-between text-sm">
                <span className="text-slate-600">Score moyen</span>
                <span className="font-semibold text-slate-900">
                  {stats.score_moyen ?? 0}/100
                </span>
              </div>
              <ProgressBar value={stats.score_moyen ?? 0} tone="brand" />
            </div>
            <div className="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2.5">
              <Clock className="h-4 w-4 text-blue-500" />
              <span className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">{stats.en_cours}</span>{" "}
                dossier(s) en cours de traitement
              </span>
            </div>
          </CardBody>
        </Card>

        {/* Derniers dossiers */}
        <Card className="lg:col-span-2">
          <CardHeader
            title="Dossiers récents"
            subtitle="Les 6 derniers dossiers créés"
            action={
              <Link
                href="/gestionnaire/dossiers"
                className="text-xs font-medium text-teal-600 hover:text-teal-700"
              >
                Tout voir
              </Link>
            }
          />
          <CardBody className="p-0">
            {derniers.length > 0 ? (
              <div className="divide-y divide-slate-100">
                {derniers.map((d) => (
                  <Link
                    key={d.dossier_id}
                    href={`/gestionnaire/dossiers/${d.dossier_id}`}
                    className="flex items-center justify-between px-5 py-3 transition-colors hover:bg-slate-50"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-900">
                        {d.reference_dossier}
                      </p>
                      <p className="text-xs text-slate-400">
                        {new Date(d.created_at).toLocaleDateString("fr-FR", {
                          day: "2-digit",
                          month: "short",
                          year: "numeric",
                        })}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      {d.montant_reclame && (
                        <span className="text-sm font-medium text-slate-700">
                          {d.montant_reclame.toLocaleString("fr-FR")} TND
                        </span>
                      )}
                      <StatutBadge statut={d.statut_global} />
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="p-5">
                <EmptyState
                  icon={ScrollText}
                  title="Aucun dossier"
                  description="Les dossiers apparaîtront ici"
                />
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}