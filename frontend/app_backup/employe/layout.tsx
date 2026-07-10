"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { obtenirUtilisateur, deconnecter, Utilisateur } from "@/lib/auth";

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
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-gray-500">Chargement...</p>
      </div>
    );
  }

  const liens = [
    { href: "/employe", label: "Accueil" },
    { href: "/employe/depot", label: "Déposer un document" },
    { href: "/employe/dossiers", label: "Mes dossiers" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-lg font-semibold text-gray-900">
              SmartClaim — Espace Employé
            </h1>
            <p className="text-xs text-gray-500">{utilisateur.nom_complet}</p>
          </div>
          <button
            onClick={deconnecter}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
          >
            Déconnexion
          </button>
        </div>

        <nav className="mx-auto flex max-w-4xl gap-1 px-6">
          {liens.map((lien) => (
            <Link
              key={lien.href}
              href={lien.href}
              className={`border-b-2 px-3 py-2 text-sm ${
                pathname === lien.href
                  ? "border-gray-900 font-medium text-gray-900"
                  : "border-transparent text-gray-500 hover:text-gray-900"
              }`}
            >
              {lien.label}
            </Link>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-8">{children}</main>
    </div>
  );
}