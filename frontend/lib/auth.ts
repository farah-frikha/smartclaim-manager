// lib/auth.ts
export interface Utilisateur {
  utilisateur_id: number;
  email: string;
  role: "EMPLOYE" | "GESTIONNAIRE" | "ADMIN";
  nom_complet: string;
}

export function sauvegarderSession(token: string, utilisateur: Utilisateur) {
  localStorage.setItem("smartclaim_token", token);
  localStorage.setItem("smartclaim_user", JSON.stringify(utilisateur));
}

export function obtenirUtilisateur(): Utilisateur | null {
  const data = localStorage.getItem("smartclaim_user");
  return data ? JSON.parse(data) : null;
}

export function obtenirToken(): string | null {
  return localStorage.getItem("smartclaim_token");
}

export function deconnecter() {
  localStorage.removeItem("smartclaim_token");
  localStorage.removeItem("smartclaim_user");
  window.location.href = "/login";
}

export function estConnecte(): boolean {
  return obtenirToken() !== null;
}