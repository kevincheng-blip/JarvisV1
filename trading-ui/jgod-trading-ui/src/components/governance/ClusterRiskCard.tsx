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
  const metrics = cluster.metrics || {};
  const score = cluster.score;
  const status = cluster.status;
  const isStub = cluster.is_stub;
  const isUnknown = status === "UNKNOWN" || isStub;

  const positiveCount = metrics.positive_count ?? 0;
  const negativeCount = metrics.negative_count ?? 0;
  const totalSignals = metrics.total_signals ?? 0;
  const consensusSide = metrics.consensus_side ?? "NONE";

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="flex justify-between items-start mb-2">
        <div className="text-base font-semibold text-gray-900 dark:text-white">Cluster Risk</div>
        <div className={`text-xs px-2 py-1 rounded ${
          status === "HIGH" ? "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300" :
          status === "MEDIUM" ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300" :
          status === "LOW" ? "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300" :
          "bg-gray-100 text-gray-700 dark:bg-gray-900/40 dark:text-gray-300"
        }`}>
          {safeString(status)}
        </div>
      </div>
      
      {isUnknown ? (
        <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">
          No signals / Unknown
        </div>
      ) : (
        <>
          <div className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Signal Consensus Score: {score !== null && score !== undefined ? `${score.toFixed(1)}%` : "N/A"}
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">
            Consensus Details: {positiveCount} Buy / {negativeCount} Sell Signals
          </div>
        </>
      )}
      
      <div className="text-xs text-gray-600 dark:text-gray-400 mb-3">
        Updated: {safeString(cluster.updated_at)}
      </div>
      
      <div className="text-xs text-gray-700 dark:text-gray-200 space-y-1">
        {reasons.length ? reasons.map((r, idx) => <div key={idx}>• {safeString(r)}</div>) : <div>—</div>}
      </div>
      
      {!isUnknown && (
        <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          Total Signals: {totalSignals} | Side: {consensusSide}
        </div>
      )}
    </div>
  );
}

export default ClusterRiskCard;

