// frontend/lib/domaines.ts
export const LIBELLES_DOMAINES: Record<string, string> = {
  AUTO:         "Auto",
  CNAM_SOINS:   "CNAM Soins",
  CNAM_MALADIE: "CNAM Maladie",
};

export function libelleDomaine(domaine?: string | null): string {
  if (!domaine) return "Auto";
  return LIBELLES_DOMAINES[domaine] ?? domaine;
}