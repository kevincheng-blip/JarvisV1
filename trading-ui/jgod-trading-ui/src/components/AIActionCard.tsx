import type { GovernanceModuleStatus, GovernanceSummary } from "../types";

type Props = {
  summary?: GovernanceSummary | null;
  isLoading?: boolean;
  error?: unknown;
};

const safeString = (value: unknown, fallback = "—") =>
  typeof value === "string" && value.trim().length > 0 ? value : fallback;

const safeList = (value: unknown) => (Array.isArray(value) ? value : []);

const safeNumber = (value: unknown, fallback = "—") => {
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
};

const fallbackModule: GovernanceModuleStatus = {
  status: "UNKNOWN",
  updated_at: "",
  is_stub: true,
  reasons: [],
};

export function AIActionCard({ summary, isLoading, error }: Props) {
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">AI Action</h3>
        <div className="text-gray-500 dark:text-gray-400 text-sm">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">AI Action</h3>
        <div className="text-red-600 dark:text-red-400 text-sm">
          {error instanceof Error ? error.message : "Failed to load"}
        </div>
      </div>
    );
  }

  const s: GovernanceSummary | null | undefined = summary;
  const exec = s?.execution_confidence || fallbackModule;
  const cluster = s?.cluster_risk || fallbackModule;
  const regime = s?.regime || fallbackModule;
  const reasons = safeList(s?.reasons);
  const ops = s?.recommended_ops || {};

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">AI Action</h3>
        {s?.is_stub && (
          <span className="text-xs px-2 py-1 rounded bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300">
            STUB
          </span>
        )}
      </div>

      <div className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
        {safeString(s?.ai_action)}
      </div>
      <div className="text-sm text-gray-700 dark:text-gray-200 mb-2">
        {safeString(s?.human_sentence)}
      </div>
      <div className="text-sm text-gray-600 dark:text-gray-300 mb-3">
        {safeString(s?.recommended_human_action)}
      </div>

      <div className="text-xs text-gray-600 dark:text-gray-400 mb-3 space-y-1">
        <div>Primary reason code: {safeString(s?.primary_reason_code)}</div>
        <div>Action confidence: {safeString(s?.action_confidence)}</div>
        <div>Updated: {safeString(s?.updated_at)}</div>
        {s?.is_stub && <div className="text-yellow-600 dark:text-yellow-300">STUB data</div>}
      </div>

      <div className="text-sm text-gray-900 dark:text-white font-semibold mt-2">Ops (machine readable)</div>
      <div className="text-xs text-gray-700 dark:text-gray-200 space-y-1 mb-3">
        <div>Mode: {safeString((ops as any).mode)}</div>
        <div>Suggested exposure cap: {safeNumber((ops as any).suggested_exposure_cap)}</div>
      </div>

      {/* Decision Context (P2.0 Governance Matrix) */}
      {s?.decision_context && (
        <div className="mt-2">
          <div className="text-sm text-gray-900 dark:text-white font-semibold">Decision Context</div>
          <div className="text-xs text-gray-700 dark:text-gray-200 space-y-1 mb-3">
            <div>Regime: {safeString((s.decision_context as any)?.regime)}</div>
            <div>Cluster: {safeString((s.decision_context as any)?.cluster)}</div>
          </div>
        </div>
      )}

      <div className="mt-2 text-sm text-gray-900 dark:text-white font-semibold">Details</div>
      <div className="grid grid-cols-2 gap-2 text-sm text-gray-700 dark:text-gray-200 mt-1">
        <div>Drift: <strong>{safeString(s?.drift_status)}</strong></div>
        <div>Execution: <strong>{safeString(exec.status)}</strong></div>
        <div>Cluster: <strong>{safeString(cluster.status)}</strong></div>
        <div>Regime: <strong>{safeString(regime.status)}</strong></div>
        <div>Market Complexity: <strong>{safeString(s?.market_complexity)}</strong></div>
      </div>

      <div className="mt-4">
        <div className="text-sm font-semibold text-gray-900 dark:text-white mb-1">Reason codes</div>
        {reasons.length ? (
          <ul className="list-disc list-inside text-sm text-gray-700 dark:text-gray-200 space-y-1">
            {reasons.map((r, idx) => (
              <li key={idx}>{safeString(r)}</li>
            ))}
          </ul>
        ) : (
          <div className="text-sm text-gray-500 dark:text-gray-400">—</div>
        )}
      </div>
    </div>
  );
}

export default AIActionCard;
 