/**
 * ExecutiveSummary Component
 * 
 * War Room V2 - Executive Summary Row
 * 
 * 顯示三張卡片：
 * 1. 系統風險 (Critical Alerts)
 * 2. 治理瓶頸 (Patch Queue)
 * 3. 決策效能 (AB Test Summary)
 */

import { useGovernanceSummary } from "../../hooks/useObserver";
import { usePatchQueue } from "../../hooks/useDoctrinePatches";
import { useRecentDecisionAbReports } from "../../hooks/useDecisionAbTest";

export function ExecutiveSummary() {
  const { 
    data: governanceSummary, 
    isLoading: governanceLoading, 
    isError: governanceError 
  } = useGovernanceSummary();
  
  const { 
    data: patches, 
    isLoading: patchesLoading, 
    isError: patchesError 
  } = usePatchQueue();
  
  const { 
    data: abReports, 
    isLoading: abLoading, 
    isError: abError 
  } = useRecentDecisionAbReports(1);

  // Calculate critical alerts count
  const criticalAlertsCount = governanceSummary?.critical_alerts_active ?? 0;

  // Calculate pending review patches (PENDING_REVIEW + PENDING_SIMULATION)
  const pendingReviewPatches = patches?.filter(
    p => p.status === "PENDING_REVIEW" || p.status === "PENDING_SIMULATION"
  ).length ?? 0;
  
  // Get pending review count from governance summary
  const pendingReviewDoctrine = governanceSummary?.pending_review_count ?? 0;
  
  // Total governance bottleneck (doctrine pending_review + patches pending_review + patches pending_simulation)
  const totalBottleneck = pendingReviewDoctrine + pendingReviewPatches;

  // Get latest AB test report
  const latestAbReport = abReports?.[0];
  const sharpeDelta = latestAbReport?.sharpe_delta ?? null;
  const recommendation = latestAbReport?.recommendation ?? null;

  // Determine colors
  const alertColor = criticalAlertsCount === 0 ? "green" : criticalAlertsCount <= 2 ? "yellow" : "red";
  const patchColor = totalBottleneck === 0 ? "green" : totalBottleneck <= 5 ? "yellow" : "red";
  const abTestColor = sharpeDelta === null 
    ? "yellow" 
    : sharpeDelta > 0 ? "green" : sharpeDelta < 0 ? "red" : "yellow";

  // Loading skeleton
  const CardSkeleton = () => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border-l-4 border-gray-300 animate-pulse">
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 mb-4" />
      <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-16 mb-2" />
      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-32" />
    </div>
  );

  // Error display
  const ErrorCard = ({ message }: { message: string }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border-l-4 border-red-500">
      <h3 className="text-sm font-medium text-red-600 dark:text-red-400 mb-2">
        載入失敗
      </h3>
      <p className="text-xs text-gray-600 dark:text-gray-400">{message}</p>
    </div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      {/* Card 1: Critical Alerts */}
      {governanceLoading ? (
        <CardSkeleton />
      ) : governanceError ? (
        <ErrorCard message="Observer 資料載入失敗" />
      ) : (
        <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border-l-4 ${
          alertColor === "green" ? "border-green-500" :
          alertColor === "yellow" ? "border-yellow-500" : "border-red-500"
        }`}>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
            系統風險
          </h3>
          <div className={`text-3xl font-bold ${
            alertColor === "green" ? "text-green-600 dark:text-green-400" :
            alertColor === "yellow" ? "text-yellow-600 dark:text-yellow-400" : "text-red-600 dark:text-red-400"
          }`}>
            {criticalAlertsCount}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
            Critical Alerts Active
          </p>
        </div>
      )}

      {/* Card 2: Patch Queue */}
      {(patchesLoading || governanceLoading) ? (
        <CardSkeleton />
      ) : (patchesError || governanceError) ? (
        <ErrorCard message="治理資料載入失敗" />
      ) : (
        <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border-l-4 ${
          patchColor === "green" ? "border-green-500" :
          patchColor === "yellow" ? "border-yellow-500" : "border-red-500"
        }`}>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
            治理瓶頸
          </h3>
          <div className={`text-3xl font-bold ${
            patchColor === "green" ? "text-green-600 dark:text-green-400" :
            patchColor === "yellow" ? "text-yellow-600 dark:text-yellow-400" : "text-red-600 dark:text-red-400"
          }`}>
            {totalBottleneck}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
            等待審核：{pendingReviewDoctrine} 條 Doctrine<br />
            等待模擬/審核：{pendingReviewPatches} 個 Patch
          </p>
        </div>
      )}

      {/* Card 3: AB Test Summary */}
      {abLoading ? (
        <CardSkeleton />
      ) : abError ? (
        <ErrorCard message="AB Test 資料載入失敗" />
      ) : (
        <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border-l-4 ${
          abTestColor === "green" ? "border-green-500" :
          abTestColor === "yellow" ? "border-yellow-500" : "border-red-500"
        }`}>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
            決策效能
          </h3>
          {sharpeDelta === null ? (
            <>
              <div className="text-xl font-bold text-gray-600 dark:text-gray-400">
                尚未執行
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
                AB Test
              </p>
            </>
          ) : (
            <>
              <div className={`text-2xl font-bold ${
                abTestColor === "green" ? "text-green-600 dark:text-green-400" :
                abTestColor === "yellow" ? "text-yellow-600 dark:text-yellow-400" : "text-red-600 dark:text-red-400"
              }`}>
                {sharpeDelta > 0 ? "+" : ""}{sharpeDelta.toFixed(2)}
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
                Sharpe Delta
              </p>
              {recommendation && (
                <div className="mt-2">
                  <span className={`inline-block px-2 py-1 text-xs rounded ${
                    recommendation === "V2_PREFERRED" ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" :
                    recommendation === "V1_PREFERRED" ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" :
                    recommendation === "V2_NOT_RECOMMENDED" ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" :
                    "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                  }`}>
                    {recommendation === "V2_PREFERRED" ? "V2 推薦" :
                     recommendation === "V1_PREFERRED" ? "V1 推薦" :
                     recommendation === "V2_NOT_RECOMMENDED" ? "V2 不建議" : "無顯著差異"}
                  </span>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
