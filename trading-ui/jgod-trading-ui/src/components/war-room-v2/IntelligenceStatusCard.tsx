/**
 * Intelligence Status Card
 * 
 * Displays Method Layer Drift Score and Status
 */

import { useIntelligenceStatus } from "../../hooks/useIntelligence";

export function IntelligenceStatusCard() {
  const { data, isLoading, isError, error } = useIntelligenceStatus();

  const getStatusColor = (status: string) => {
    switch (status) {
      case "LOW":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "MEDIUM":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "HIGH":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "—";
    try {
      const date = new Date(dateStr);
      return date.toLocaleString("zh-TW", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Intelligence Status
        </h3>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse rounded w-24" />
          <div className="h-8 bg-gray-200 dark:bg-gray-700 animate-pulse rounded w-32" />
          <div className="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse rounded w-40" />
        </div>
      ) : isError ? (
        <div className="text-red-500 dark:text-red-400 text-sm">
          <p className="font-medium">Failed to load drift status</p>
          {error instanceof Error && (
            <p className="mt-1 text-xs">{error.message}</p>
          )}
        </div>
      ) : data ? (
        <div className="space-y-4">
          {/* Drift Score */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Method Layer Drift Score
              </span>
              <span
                className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
                  data.method_layer_drift_status
                )}`}
              >
                {data.method_layer_drift_status}
              </span>
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {data.method_layer_drift_score.toFixed(2)}
            </div>
            <div className="mt-1">
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    data.method_layer_drift_score < 0.3
                      ? "bg-green-500"
                      : data.method_layer_drift_score < 0.7
                      ? "bg-yellow-500"
                      : "bg-red-500"
                  }`}
                  style={{
                    width: `${Math.min(data.method_layer_drift_score * 100, 100)}%`,
                  }}
                />
              </div>
            </div>
          </div>

          {/* Updated At */}
          <div>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Last Updated: {formatDate(data.method_layer_drift_updated_at)}
            </span>
          </div>
        </div>
      ) : (
        <div className="text-gray-500 dark:text-gray-400 text-sm">
          No data available
        </div>
      )}
    </div>
  );
}

