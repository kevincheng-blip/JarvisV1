/**
 * PatchQueueCard Component
 * 
 * War Room V2 - Doctrine Patch Queue
 * 
 * 顯示待審核的 Patches
 */

import { useState } from "react";
import {
  usePatchQueue,
  useRunRuleSim,
  useApprovePatch,
  useRejectPatch,
  useDeployPatch,
  useRevertPatch,
} from "../../hooks/useDoctrinePatches";
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
  const { data: patches, isLoading, isError, error, refetch } = usePatchQueue();
  const runSim = useRunRuleSim();
  const approvePatch = useApprovePatch();
  const rejectPatch = useRejectPatch();
  const deployPatch = useDeployPatch();
  const revertPatch = useRevertPatch();
  
  const [actionMessage, setActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

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

  const handleAction = async (
    action: "run-sim" | "approve" | "reject" | "deploy" | "revert",
    patchId: string,
    patchStatus: PatchStatus,
    simResultStatus: string
  ) => {
    setActionMessage(null);
    
    try {
      const operatorId = "war-room-user"; // In real app, get from auth context
      
      if (action === "run-sim") {
        if (patchStatus !== "PENDING_SIMULATION") {
          setActionMessage({ type: "error", text: "只能對 PENDING_SIMULATION 狀態執行 Run Sim" });
          return;
        }
        await runSim.mutateAsync(patchId);
        setActionMessage({ type: "success", text: "Rule Sim 執行成功" });
      } else if (action === "approve") {
        if (patchStatus !== "PENDING_REVIEW" || simResultStatus !== "APPROVED") {
          setActionMessage({ type: "error", text: "只能審核 PENDING_REVIEW 且 Sim APPROVED 的 Patch" });
          return;
        }
        await approvePatch.mutateAsync({
          patchId,
          request: { reviewer_id: operatorId },
        });
        setActionMessage({ type: "success", text: "Patch 審核通過" });
      } else if (action === "reject") {
        if (patchStatus === "DEPLOYED" || patchStatus === "REVERTED") {
          setActionMessage({ type: "error", text: "無法拒絕已部署或已回滾的 Patch" });
          return;
        }
        await rejectPatch.mutateAsync({
          patchId,
          request: { reviewer_id: operatorId },
        });
        setActionMessage({ type: "success", text: "Patch 已拒絕" });
      } else if (action === "deploy") {
        if (patchStatus !== "APPROVED") {
          setActionMessage({ type: "error", text: "只能部署 APPROVED 狀態的 Patch" });
          return;
        }
        await deployPatch.mutateAsync({
          patchId,
          request: { operator_id: operatorId },
        });
        setActionMessage({ type: "success", text: "Patch 部署成功" });
      } else if (action === "revert") {
        if (patchStatus !== "DEPLOYED") {
          setActionMessage({ type: "error", text: "只能回滾 DEPLOYED 狀態的 Patch" });
          return;
        }
        await revertPatch.mutateAsync({
          patchId,
          request: { operator_id: operatorId },
        });
        setActionMessage({ type: "success", text: "Patch 回滾成功" });
      }
      
      // Auto-refresh queue after action
      setTimeout(() => {
        refetch();
        setActionMessage(null);
      }, 2000);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || "操作失敗";
      setActionMessage({ type: "error", text: errorMsg });
      setTimeout(() => setActionMessage(null), 5000);
    }
  };

  const canRunSim = (status: PatchStatus) => status === "PENDING_SIMULATION";
  const canApprove = (status: PatchStatus, simStatus: string) => 
    status === "PENDING_REVIEW" && simStatus === "APPROVED";
  const canReject = (status: PatchStatus) => 
    status !== "DEPLOYED" && status !== "REVERTED";
  const canDeploy = (status: PatchStatus) => status === "APPROVED";
  const canRevert = (status: PatchStatus) => status === "DEPLOYED";

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

      {/* Action Message */}
      {actionMessage && (
        <div className={`mb-4 p-3 rounded text-sm ${
          actionMessage.type === "success"
            ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
            : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
        }`}>
          {actionMessage.text}
        </div>
      )}

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
                  <span className={`font-medium ${getSimStatusColor(patch.sim_result_status)}`}>
                    RuleSim: {patch.sim_result_status}
                  </span>
                </div>

                <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                  {formatRelativeTime(patch.created_at)}
                </div>

                {/* Quick Actions */}
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 flex gap-2 flex-wrap">
                  {canRunSim(patch.status) && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAction("run-sim", patch.patch_id, patch.status, patch.sim_result_status);
                      }}
                      disabled={runSim.isPending}
                      className="px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded hover:bg-blue-200 dark:hover:bg-blue-800 disabled:opacity-50"
                    >
                      {runSim.isPending ? "執行中..." : "Run Sim"}
                    </button>
                  )}
                  {canApprove(patch.status, patch.sim_result_status) && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAction("approve", patch.patch_id, patch.status, patch.sim_result_status);
                      }}
                      disabled={approvePatch.isPending}
                      className="px-2 py-1 text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded hover:bg-green-200 dark:hover:bg-green-800 disabled:opacity-50"
                    >
                      {approvePatch.isPending ? "處理中..." : "Approve"}
                    </button>
                  )}
                  {canReject(patch.status) && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAction("reject", patch.patch_id, patch.status, patch.sim_result_status);
                      }}
                      disabled={rejectPatch.isPending}
                      className="px-2 py-1 text-xs bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded hover:bg-red-200 dark:hover:bg-red-800 disabled:opacity-50"
                    >
                      {rejectPatch.isPending ? "處理中..." : "Reject"}
                    </button>
                  )}
                  {canDeploy(patch.status) && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAction("deploy", patch.patch_id, patch.status, patch.sim_result_status);
                      }}
                      disabled={deployPatch.isPending}
                      className="px-2 py-1 text-xs bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200 rounded hover:bg-purple-200 dark:hover:bg-purple-800 disabled:opacity-50"
                    >
                      {deployPatch.isPending ? "部署中..." : "Deploy"}
                    </button>
                  )}
                  {canRevert(patch.status) && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAction("revert", patch.patch_id, patch.status, patch.sim_result_status);
                      }}
                      disabled={revertPatch.isPending}
                      className="px-2 py-1 text-xs bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200 rounded hover:bg-orange-200 dark:hover:bg-orange-800 disabled:opacity-50"
                    >
                      {revertPatch.isPending ? "回滾中..." : "Revert"}
                    </button>
                  )}
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
