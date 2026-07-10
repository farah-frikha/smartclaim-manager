"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";

interface LogAudit {
  audit_id: number;
  dossier_id: number | null;
  reference_dossier: string | null;
  agent_nom: string;
  action: string;
  date_action: string;
}

export default function AuditPage() {
  const [logs, setLogs] = useState<LogAudit[]>([]);
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    api
      .get("/dashboard/audit")
      .then((res) => setLogs(res.data))
      .finally(() => setChargement(false));
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">
        Journal d'audit ({logs.length})
      </h2>

      {chargement ? (
        <p className="text-sm text-gray-500">Chargement...</p>
      ) : (
        <div className="overflow-hidden rounded-lg border bg-white">
          <table className="w-full text-sm">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Dossier</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Agent</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Action</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Date</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.audit_id} className="border-b last:border-0">
                  <td className="px-4 py-3 text-gray-700">
                    {log.reference_dossier || "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700">
                      {log.agent_nom}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700">{log.action}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(log.date_action).toLocaleString("fr-FR")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}