// app/employe/layout.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { obtenirUtilisateur, deconnecter, Utilisateur } from "@/lib/auth";
import {
  Home, UploadCloud, FolderOpen, Settings, LogOut, Shield, ChevronRight,
} from "lucide-react";

export default function EmployeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [utilisateur, setUtilisateur] = useState<Utilisateur | null>(null);

  useEffect(() => {
    const user = obtenirUtilisateur();
    if (!user) {
      router.push("/login");
      return;
    }
    if (user.role !== "EMPLOYE") {
      router.push("/gestionnaire");
      return;
    }
    setUtilisateur(user);
  }, [router]);

  if (!utilisateur) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-app">
        <div className="flex items-center gap-3 text-text-muted">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-teal-500 border-t-transparent" />
          <span className="text-sm">Chargement...</span>
        </div>
      </div>
    );
  }

  const navigation = [
    { href: "/employe", label: "Accueil", icon: Home },
    { href: "/employe/depot", label: "Déposer un document", icon: UploadCloud },
    { href: "/employe/dossiers", label: "Mes dossiers", icon: FolderOpen },
    { href: "/employe/parametres", label: "Paramètres", icon: Settings },
  ];

  const initiales = utilisateur.nom_complet
    .split(" ")
    .map((m) => m[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  const pageActive = navigation.find((n) => n.href === pathname);

  return (
    <div className="flex min-h-screen bg-app">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-20 flex w-64 flex-col border-r border-border-app bg-surface">
        <div className="flex h-16 items-center gap-2.5 border-b border-border-light px-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-600">
            <Shield className="h-4.5 w-4.5 text-white" strokeWidth={2.5} />
          </div>
          <div>
            <p className="text-sm font-semibold leading-none text-text-primary">
              SmartClaim
            </p>
            <p className="mt-0.5 text-[10px] font-medium uppercase tracking-wider text-teal-600">
              Employé
            </p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {navigation.map((item) => {
            const Icon = item.icon;
            const actif = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  actif
                    ? "bg-teal-50 text-teal-700"
                    : "text-text-secondary hover:bg-surface-hover hover:text-text-primary"
                }`}
              >
                <Icon
                  className={`h-4.5 w-4.5 ${
                    actif ? "text-teal-600" : "text-text-muted group-hover:text-text-secondary"
                  }`}
                />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Profil cliquable */}
        <div className="border-t border-border-light p-3">
          <Link
            href="/employe/parametres"
            className="flex items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-surface-hover"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-teal-600 text-xs font-semibold text-white">
              {initiales}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-text-primary">
                {utilisateur.nom_complet}
              </p>
              <p className="truncate text-xs text-text-secondary">Employé</p>
            </div>
          </Link>
          <button
            onClick={deconnecter}
            className="mt-1 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-red-50 hover:text-red-600"
          >
            <LogOut className="h-4.5 w-4.5" />
            Déconnexion
          </button>
        </div>
      </aside>

      {/* Contenu */}
      <div className="flex flex-1 flex-col pl-64">
        <header className="sticky top-0 z-10 flex h-16 items-center border-b border-border-app bg-surface/80 px-8 backdrop-blur">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-text-muted">Employé</span>
            <ChevronRight className="h-4 w-4 text-text-muted" />
            <span className="font-medium text-text-primary">
              {pageActive?.label || "Détail"}
            </span>
          </div>
        </header>

        <main className="flex-1 px-8 py-8">
          <div className="mx-auto max-w-4xl animate-fade-in">{children}</div>
        </main>
      </div>
    </div>
  );
}