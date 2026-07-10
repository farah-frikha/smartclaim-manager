import { Badge } from "./Badge";
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  FileCheck,
  FileX,
} from "lucide-react";

const CONFIG: Record<
  string,
  { label: string; variant: "success" | "danger" | "warning" | "info" | "neutral"; icon: typeof CheckCircle2 }
> = {
  accepte: { label: "Accepté", variant: "success", icon: CheckCircle2 },
  refuse: { label: "Refusé", variant: "danger", icon: XCircle },
  complement_requis: { label: "Complément requis", variant: "warning", icon: AlertCircle },
  en_traitement: { label: "En traitement", variant: "info", icon: Clock },
  recu: { label: "Reçu", variant: "info", icon: Clock },
  valide: { label: "Validé", variant: "info", icon: FileCheck },
  invalide: { label: "Invalide", variant: "neutral", icon: FileX },
};

export function StatutBadge({ statut }: { statut: string }) {
  const config = CONFIG[statut] || {
    label: statut,
    variant: "neutral" as const,
    icon: FileCheck,
  };
  const Icon = config.icon;

  return (
    <Badge variant={config.variant}>
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  );
}