/**
 * PatchQueueCard Component
 * 
 * War Room V2 - Doctrine Patch Queue
 * 
 * 顯示待審核的 Patches
 */

import { usePatchQueue } from "../../hooks/useDoctrinePatches";
import type { PatchStatus } from "../../types/doctrinePatch";

// Helper function to format relative time
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) {
    return `${diffMins} 分鐘前`;
  } else if (diffHours < 24) {
    return `${diffHours} 小時前`;
  } else if (diffDays < 7) {
    return `${diffDays} 天前`;
  } else {
    return date.toLocaleDateString("zh-TW", { month: "short", day: "numeric" });
  }
}

export function PatchQueueCard() {
  const { data: patches, isLoading, isError, error } = usePatchQueue();

  // Filter for pending/active patches
  const activeStatuses: PatchStatus[] = ["PENDING_SIMULATION", "PENDING_REVIEW", "APPROVED"];
  const pendingPatches = patches?.filter(p => activeStatuses.includes(p.status)) || [];

  const getStatusColor = (status: PatchStatus) => {
    switch (status) {
      case "PENDING_SIMULATION":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "PENDING_REVIEW":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "APPROVED":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "DEPLOYED":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "REJECTED_BY_SIM":
      case "REVERTED":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
    }
  };

  const getSimStatusColor = (status: string) => {
    switch (status) {
      case "APPROVED":
        return "text-green-600 dark:text-green-400";
      case "REJECTED":
        return "text-red-600 dark:text-red-400";
      default:
        return "text-gray-600 dark:text-gray-400";
    }
  };

  const handleViewAll = () => {
    // Dispatch custom event for navigation
    window.dispatchEvent(new CustomEvent("dmc:navigate", {
      detail: { page: "list" }
    }));
  };

  const handlePatchClick = (patchId: string) => {
    // Navigate to DMC page - patches will be shown there
    // In future, could navigate to specific patch detail page
    window.dispatchEvent(new CustomEvent("dmc:navigate", {
      detail: { page: "list", patchId }
    }));
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          待審核 Patch 佇列
        </h3>
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          待審核 Patch 佇列
        </h3>
        <div className="text-red-500 dark:text-red-400 text-sm">
          載入失敗: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          待審核 Patch 佇列
        </h3>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          ({pendingPatches.length})
        </span>
      </div>

      {pendingPatches.length === 0 ? (
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          目前沒有待審核的 Patches
        </div>
      ) : (
        <>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {pendingPatches.slice(0, 5).map((patch) => (
              <div
                key={patch.patch_id}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                onClick={() => handlePatchClick(patch.patch_id)}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-gray-900 dark:text-white mb-1 truncate">
                      {patch.patch_id.slice(0, 8)}...
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-2 line-clamp-2">
                      {patch.description}
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded whitespace-nowrap ml-2 ${getStatusColor(patch.status)}`}>
                    {patch.status.replace(/_/g, ' ')}
                  </span>
                </div>

                <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400">
                  <span>作者: {patch.author_id}</span>
                  <span className={`font-medium ${getSimStatusColor(patch.sim_status)}`}>
                    RuleSim: {patch.sim_status}
                  </span>
                </div>

                <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                  {formatRelativeTime(patch.created_at)}
                </div>
              </div>
            ))}
          </div>

          {pendingPatches.length > 5 && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={handleViewAll}
                className="w-full text-sm text-blue-600 dark:text-blue-400 hover:underline text-center"
              >
                查看所有 Patch ({pendingPatches.length}) →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
