import type { GovernanceModuleStatus } from "../../types";

const safeString = (v: unknown, fallback = "—") =>
  typeof v === "string" && v.trim().length > 0 ? v : fallback;

type Props = {
  data?: GovernanceModuleStatus | null;
  isLoading?: boolean;
  error?: unknown;
};

export function ClusterRiskCard({ data, isLoading, error }: Props) {
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div className="text-sm text-gray-500 dark:text-gray-400">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div className="text-sm text-red-600 dark:text-red-400">
          {error instanceof Error ? error.message : "Failed to load"}
        </div>
      </div>
    );
  }

  const cluster = data || {};
  const reasons = Array.isArray(cluster.reasons) ? cluster.reasons.slice(0, 3) : [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="flex justify-between items-start mb-2">
        <div className="text-base font-semibold text-gray-900 dark:text-white">Cluster Risk</div>
        {cluster.is_stub && (
          <span className="text-xxs px-2 py-1 rounded bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300">
            STUB
          </span>
        )}
      </div>
      <div className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
        {safeString(cluster.status)}
      </div>
      <div className="text-xs text-gray-600 dark:text-gray-400 mb-3">
        Updated: {safeString(cluster.updated_at)}
      </div>
      <div className="text-xs text-gray-700 dark:text-gray-200 space-y-1">
        {reasons.length ? reasons.map((r, idx) => <div key={idx}>• {safeString(r)}</div>) : <div>—</div>}
      </div>
    </div>
  );
}

export default ClusterRiskCard;

