// @ts-nocheck
/**
 * DoctrineAlertPanel Component v1.1
 * 
 * Anomaly Layer - Doctrine Alert Panel
 * 
 * 顯示 Doctrine 風控警報：Filter + 列表表格 + Detail Pane
 */

import { useState } from "react";
import { useDoctrineAlerts } from "../../../hooks/useDoctrineAlerts";
import { useWarRoomStore } from "../../../store/warRoomStore";
import type { DoctrineAlertItem, DoctrineAlertSeverity, DoctrineAlertSource } from "../../../types/doctrineAlert";

export function DoctrineAlertPanel() {
  const { selectedSymbol, setSelectedSymbol } = useWarRoomStore();
  const [severityFilter, setSeverityFilter] = useState<DoctrineAlertSeverity | "all">("all");
  const [sourceFilter, setSourceFilter] = useState<DoctrineAlertSource | "all">("all");
  const [symbolFilter, setSymbolFilter] = useState<string>("");
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);

  // If selectedSymbol is set, filter by that symbol; otherwise use symbolFilter
  const effectiveSymbol = selectedSymbol || symbolFilter || undefined;

  const { data: alerts, isLoading, isError, error, refetch } = useDoctrineAlerts(
    effectiveSymbol,
    severityFilter,
    sourceFilter,
    true
  );

  // Filter alerts by symbolFilter (client-side)
  const filteredAlerts = alerts?.filter((alert) => {
    if (!symbolFilter) return true;
    return alert.symbol.toLowerCase().includes(symbolFilter.toLowerCase()) ||
           alert.name?.toLowerCase().includes(symbolFilter.toLowerCase());
  }) || [];

  // Get selected alert
  const selectedAlert = filteredAlerts.find((a) => a.id === selectedAlertId);

  // Check if selectedSymbol has CRITICAL alerts
  const hasCriticalForSelected = selectedSymbol &&
    filteredAlerts.some((a) => a.symbol === selectedSymbol && a.severity === "critical");

  // Helper: Get severity badge color
  const getSeverityBadgeClass = (severity: DoctrineAlertSeverity) => {
    switch (severity) {
      case "critical":
        return "bg-red-500 text-white";
      case "warning":
        return "bg-yellow-500 text-white";
      case "info":
        return "bg-blue-500 text-white";
    }
  };

  // Helper: Get source label
  const getSourceLabel = (source: DoctrineAlertSource) => {
    switch (source) {
      case "position":
        return "部位";
      case "prediction":
        return "預測";
      case "conflict":
        return "衝突";
      case "error":
        return "錯誤";
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Doctrine 風控警報
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          載入 Doctrine 風控警報中…
        </div>
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Doctrine 風控警報
        </h3>
        <div className="text-red-500 dark:text-red-400 text-center py-8">
          <div className="mb-4">無法取得 Doctrine 警報</div>
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            {error instanceof Error ? error.message : "未知錯誤"}
          </div>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
          >
            重試
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      {/* Header with Critical Badge */}
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Doctrine 風控警報
        {hasCriticalForSelected && (
          <span className="ml-2 px-2 py-1 bg-red-500 text-white text-xs rounded font-semibold">
            ⚠ 該標的存在 Doctrine CRITICAL 警報
          </span>
        )}
      </h3>

      {/* Filter Section */}
      <div className="mb-4 space-y-2">
        {/* Severity Filter */}
        <div>
          <label className="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
            嚴重程度
          </label>
          <div className="flex gap-2">
            {(["all", "critical", "warning", "info"] as const).map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-3 py-1 text-xs rounded ${
                  severityFilter === sev
                    ? "bg-blue-500 text-white"
                    : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                }`}
              >
                {sev === "all" ? "全部" : sev.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Source Filter */}
        <div>
          <label className="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
            來源
          </label>
          <div className="flex gap-2 flex-wrap">
            {(["all", "position", "prediction", "conflict", "error"] as const).map((src) => (
              <button
                key={src}
                onClick={() => setSourceFilter(src)}
                className={`px-3 py-1 text-xs rounded ${
                  sourceFilter === src
                    ? "bg-blue-500 text-white"
                    : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                }`}
              >
                {src === "all" ? "全部" : getSourceLabel(src)}
              </button>
            ))}
          </div>
        </div>

        {/* Symbol Filter */}
        <div>
          <label className="text-xs text-gray-600 dark:text-gray-400 mb-1 block">
            股票代號
          </label>
          <input
            type="text"
            value={symbolFilter}
            onChange={(e) => setSymbolFilter(e.target.value)}
            placeholder="2330, 1101..."
            className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            disabled={!!selectedSymbol} // Disable if selectedSymbol is set
          />
        </div>
      </div>

      {/* Alert Table */}
      {filteredAlerts.length === 0 ? (
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          {selectedSymbol
            ? "目前該標的沒有 Doctrine 風控異常。"
            : "目前沒有任何 Doctrine 風控警報"}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Table */}
          <div className="space-y-2 max-h-96 overflow-y-auto">
            <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">
              共 {filteredAlerts.length} 筆警報
            </div>
            <div className="space-y-1">
              {filteredAlerts.map((alert) => (
                <div
                  key={alert.id}
                  onClick={() => {
                    setSelectedAlertId(alert.id);
                    setSelectedSymbol(alert.symbol);
                  }}
                  className={`p-2 rounded border cursor-pointer transition-colors ${
                    selectedAlertId === alert.id
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                      : "border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={`px-2 py-0.5 text-xs rounded ${getSeverityBadgeClass(alert.severity)}`}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {getSourceLabel(alert.source)}
                    </span>
                  </div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-white">
                    {alert.symbol} {alert.name || ""}
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400 truncate">
                    {alert.title}
                  </div>
                  {alert.metric_value !== null && alert.metric_value !== undefined && (
                    <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                      {alert.metric_name}: {alert.metric_value.toFixed(2)}
                      {alert.threshold && ` / ${alert.threshold.toFixed(2)}`}
                    </div>
                  )}
                  <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    {new Date(alert.created_at).toLocaleString("zh-TW", {
                      month: "2-digit",
                      day: "2-digit",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Detail Pane */}
          {selectedAlert ? (
            <div className="bg-gray-50 dark:bg-gray-900/50 rounded p-4">
              <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">
                {selectedAlert.symbol} {selectedAlert.name || ""}
              </h4>

              <div className="space-y-3">
                {/* All Alerts for This Symbol */}
                {filteredAlerts
                  .filter((a) => a.symbol === selectedAlert.symbol)
                  .sort((a, b) => {
                    const severityOrder = { critical: 0, warning: 1, info: 2 };
                    return (
                      severityOrder[a.severity] - severityOrder[b.severity]
                    );
                  })
                  .map((alert) => (
                    <div
                      key={alert.id}
                      className={`p-3 rounded border-l-4 ${
                        alert.severity === "critical"
                          ? "border-red-500 bg-red-50 dark:bg-red-900/20"
                          : alert.severity === "warning"
                          ? "border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20"
                          : "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className={`px-2 py-1 text-xs rounded ${getSeverityBadgeClass(alert.severity)}`}>
                          {alert.severity.toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {getSourceLabel(alert.source)}
                        </span>
                      </div>
                      <div className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                        {alert.title}
                      </div>
                      <div className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                        {alert.message}
                      </div>

                      {/* Metric Info */}
                      {alert.metric_value !== null && alert.metric_value !== undefined && (
                        <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                          <div>
                            {alert.metric_name}: {alert.metric_value.toFixed(2)}
                          </div>
                          {alert.threshold && (
                            <div>
                              門檻: {alert.threshold.toFixed(2)}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Conflict/Consensus Scores */}
                      {(alert.conflict_score !== null || alert.consensus_score !== null) && (
                        <div className="text-xs text-gray-600 dark:text-gray-400 mb-2 space-y-1">
                          {alert.conflict_score !== null && (
                            <div>衝突分數: {alert.conflict_score.toFixed(1)}</div>
                          )}
                          {alert.consensus_score !== null && (
                            <div>共識分數: {alert.consensus_score.toFixed(1)}</div>
                          )}
                        </div>
                      )}

                      {/* Final/Raw Scores */}
                      {(alert.final_score !== null || alert.raw_score !== null) && (
                        <div className="text-xs text-gray-600 dark:text-gray-400 mb-2 space-y-1">
                          {alert.final_score !== null && (
                            <div>Final Score: {alert.final_score.toFixed(2)}</div>
                          )}
                          {alert.raw_score !== null && (
                            <div>Raw Score: {alert.raw_score.toFixed(2)}</div>
                          )}
                        </div>
                      )}

                      {/* Doctrine Refs */}
                      {alert.doctrine_refs.length > 0 && (
                        <div className="mt-2">
                          <div className="text-xs text-gray-500 dark:text-gray-500 mb-1">
                            Doctrine 參考:
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {alert.doctrine_refs.map((ref, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded"
                              >
                                {ref.book_id}#{ref.section_id}
                                {ref.rule_id && `-${ref.rule_id}`}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Tags */}
                      {alert.tags.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {alert.tags.map((tag, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-xs rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 dark:bg-gray-900/50 rounded p-4 flex items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
              請在左側列表中點擊一筆警報以查看詳細資訊
            </div>
          )}
        </div>
      )}
    </div>
  );
}
