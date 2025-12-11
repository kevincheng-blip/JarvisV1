/**
 * Doctrine Patch Management Page
 * 
 * Main view for Doctrine Patch & Rollout workflow.
 */

import { useState } from "react";
import {
  usePatchQueue,
  usePatch,
  useRunRuleSim,
  useApprovePatch,
  useRejectPatch,
  useDeployPatch,
  useRevertPatch,
} from "../hooks/useDoctrinePatches";
import type { PatchStatus, DoctrinePatchSummary } from "../types/doctrinePatch";

export function DMCPatchPage() {
  const [statusFilter, setStatusFilter] = useState<PatchStatus | "all">("all");
  const [selectedPatchId, setSelectedPatchId] = useState<string | null>(null);
  const [reviewerId, setReviewerId] = useState("admin"); // 簡化版，實際應從使用者登入狀態取得
  
  const { data: patches, isLoading, isError, error } = usePatchQueue(
    statusFilter === "all" ? null : statusFilter,
    50
  );
  
  const { data: selectedPatch } = usePatch(selectedPatchId);
  
  const runSimMutation = useRunRuleSim();
  const approveMutation = useApprovePatch();
  const rejectMutation = useRejectPatch();
  const deployMutation = useDeployPatch();
  const revertMutation = useRevertPatch();
  
  const getStatusBadgeClass = (status: PatchStatus) => {
    switch (status) {
      case "PENDING_SIMULATION":
        return "bg-gray-500 text-white";
      case "PENDING_REVIEW":
        return "bg-yellow-500 text-white";
      case "APPROVED":
        return "bg-blue-500 text-white";
      case "DEPLOYED":
        return "bg-green-500 text-white";
      case "REJECTED_BY_SIM":
      case "REVERTED":
        return "bg-red-500 text-white";
      case "DEPLOYING":
        return "bg-purple-500 text-white";
      default:
        return "bg-gray-400 text-white";
    }
  };
  
  const getSimStatusBadgeClass = (simStatus: string) => {
    switch (simStatus) {
      case "APPROVED":
        return "bg-green-500 text-white";
      case "REJECTED":
        return "bg-red-500 text-white";
      case "PENDING":
        return "bg-gray-500 text-white";
      default:
        return "bg-gray-400 text-white";
    }
  };
  
  const handleRunSim = (patchId: string) => {
    if (confirm("確定要執行 Rule Sim 驗證嗎？這可能需要一些時間。")) {
      runSimMutation.mutate(patchId);
    }
  };
  
  const handleApprove = (patchId: string) => {
    if (confirm("確定要批准這個 Patch 嗎？")) {
      approveMutation.mutate({
        patchId,
        request: { reviewer_id: reviewerId },
      });
    }
  };
  
  const handleReject = (patchId: string) => {
    if (confirm("確定要拒絕這個 Patch 嗎？")) {
      rejectMutation.mutate({
        patchId,
        request: { reviewer_id: reviewerId },
      });
    }
  };
  
  const handleDeploy = (patchId: string) => {
    if (confirm("確定要部署這個 Patch 到 Production 嗎？這將修改正式的 Doctrine 版本。")) {
      deployMutation.mutate({
        patchId,
        request: { operator_id: reviewerId },
      });
    }
  };
  
  const handleRevert = (patchId: string) => {
    if (confirm("確定要回滾這個 Patch 嗎？這將恢復到部署前的版本。")) {
      revertMutation.mutate({
        patchId,
        request: { operator_id: reviewerId },
      });
    }
  };
  
  if (isLoading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Doctrine Patch 管理</h1>
        <div className="text-gray-500">載入中...</div>
      </div>
    );
  }
  
  if (isError) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Doctrine Patch 管理</h1>
        <div className="text-red-500">
          錯誤: {error instanceof Error ? error.message : "未知錯誤"}
        </div>
      </div>
    );
  }
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Doctrine Patch 管理</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Patch List */}
        <div>
          <div className="mb-4">
            <label className="mr-2">狀態過濾:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as PatchStatus | "all")}
              className="px-3 py-1 border rounded"
            >
              <option value="all">全部</option>
              <option value="PENDING_SIMULATION">等待 Rule Sim</option>
              <option value="PENDING_REVIEW">待審核</option>
              <option value="APPROVED">已批准</option>
              <option value="DEPLOYED">已部署</option>
              <option value="REJECTED_BY_SIM">Rule Sim 拒絕</option>
              <option value="REVERTED">已回滾</option>
            </select>
          </div>
          
          {/* Patch List */}
          {patches && patches.length > 0 ? (
            <div className="space-y-2">
              {patches.map((patch) => (
                <div
                  key={patch.patch_id}
                  onClick={() => setSelectedPatchId(patch.patch_id)}
                  className={`p-4 border rounded cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 ${
                    selectedPatchId === patch.patch_id
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                      : "border-gray-200 dark:border-gray-700"
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="font-mono text-sm text-gray-600 dark:text-gray-400">
                      {patch.patch_id.substring(0, 8)}...
                    </div>
                    <div className="flex gap-2">
                      <span className={`px-2 py-1 text-xs rounded ${getStatusBadgeClass(patch.status as PatchStatus)}`}>
                        {patch.status}
                      </span>
                      <span className={`px-2 py-1 text-xs rounded ${getSimStatusBadgeClass(patch.sim_result_status)}`}>
                        Sim: {patch.sim_result_status}
                      </span>
                    </div>
                  </div>
                  <div className="text-sm font-medium mb-1">{patch.description}</div>
                  <div className="text-xs text-gray-500">
                    建立者: {patch.author_id} | {new Date(patch.created_at).toLocaleString("zh-TW")}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              目前沒有任何 Patch
            </div>
          )}
        </div>
        
        {/* Right: Patch Details */}
        <div>
          {selectedPatch ? (
            <div className="border rounded-lg p-4">
              <h2 className="text-xl font-bold mb-4">Patch 詳情</h2>
              
              {/* Basic Info */}
              <div className="mb-4 space-y-2">
                <div>
                  <span className="font-semibold">Patch ID:</span>{" "}
                  <span className="font-mono text-sm">{selectedPatch.patch_id}</span>
                </div>
                <div>
                  <span className="font-semibold">狀態:</span>{" "}
                  <span className={`px-2 py-1 text-xs rounded ${getStatusBadgeClass(selectedPatch.status)}`}>
                    {selectedPatch.status}
                  </span>
                </div>
                <div>
                  <span className="font-semibold">Sim 狀態:</span>{" "}
                  <span className={`px-2 py-1 text-xs rounded ${getSimStatusBadgeClass(selectedPatch.sim_result_status)}`}>
                    {selectedPatch.sim_result_status}
                  </span>
                </div>
                <div>
                  <span className="font-semibold">建立者:</span> {selectedPatch.author_id}
                </div>
                <div>
                  <span className="font-semibold">建立時間:</span>{" "}
                  {new Date(selectedPatch.created_at).toLocaleString("zh-TW")}
                </div>
                <div>
                  <span className="font-semibold">說明:</span> {selectedPatch.description}
                </div>
                {selectedPatch.rule_sim_report_id && (
                  <div>
                    <span className="font-semibold">Rule Sim 報告:</span>{" "}
                    <a
                      href={`/rule-sim/${selectedPatch.rule_sim_report_id}`}
                      className="text-blue-500 hover:underline"
                      target="_blank"
                    >
                      {selectedPatch.rule_sim_report_id}
                    </a>
                  </div>
                )}
              </div>
              
              {/* Changes */}
              <div className="mb-4">
                <h3 className="font-semibold mb-2">變更項目:</h3>
                <div className="space-y-2">
                  {selectedPatch.changes.map((change, idx) => (
                    <div key={idx} className="border rounded p-2 text-sm">
                      <div className="font-semibold mb-1">
                        {change.change_type}: {change.rule_id}
                      </div>
                      {change.change_type === "ADD" && change.new_text && (
                        <div className="bg-green-50 dark:bg-green-900/20 p-2 rounded mt-1">
                          <div className="text-xs text-green-700 dark:text-green-300 mb-1">新增內容:</div>
                          <pre className="text-xs whitespace-pre-wrap">{change.new_text}</pre>
                        </div>
                      )}
                      {change.change_type === "UPDATE" && (
                        <div className="space-y-2 mt-1">
                          {change.old_text && (
                            <div className="bg-red-50 dark:bg-red-900/20 p-2 rounded">
                              <div className="text-xs text-red-700 dark:text-red-300 mb-1">舊內容:</div>
                              <pre className="text-xs whitespace-pre-wrap">{change.old_text}</pre>
                            </div>
                          )}
                          {change.new_text && (
                            <div className="bg-green-50 dark:bg-green-900/20 p-2 rounded">
                              <div className="text-xs text-green-700 dark:text-green-300 mb-1">新內容:</div>
                              <pre className="text-xs whitespace-pre-wrap">{change.new_text}</pre>
                            </div>
                          )}
                        </div>
                      )}
                      {change.change_type === "DELETE" && change.old_text && (
                        <div className="bg-red-50 dark:bg-red-900/20 p-2 rounded mt-1">
                          <div className="text-xs text-red-700 dark:text-red-300 mb-1">刪除內容:</div>
                          <pre className="text-xs whitespace-pre-wrap">{change.old_text}</pre>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Actions */}
              <div className="space-y-2">
                {selectedPatch.status === "PENDING_SIMULATION" && (
                  <button
                    onClick={() => handleRunSim(selectedPatch.patch_id)}
                    disabled={runSimMutation.isPending}
                    className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                  >
                    {runSimMutation.isPending ? "執行中..." : "執行 Rule Sim 驗證"}
                  </button>
                )}
                
                {selectedPatch.status === "PENDING_REVIEW" && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleApprove(selectedPatch.patch_id)}
                      disabled={approveMutation.isPending}
                      className="flex-1 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
                    >
                      {approveMutation.isPending ? "處理中..." : "批准"}
                    </button>
                    <button
                      onClick={() => handleReject(selectedPatch.patch_id)}
                      disabled={rejectMutation.isPending}
                      className="flex-1 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
                    >
                      {rejectMutation.isPending ? "處理中..." : "拒絕"}
                    </button>
                  </div>
                )}
                
                {selectedPatch.status === "APPROVED" && (
                  <button
                    onClick={() => handleDeploy(selectedPatch.patch_id)}
                    disabled={deployMutation.isPending}
                    className="w-full px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
                  >
                    {deployMutation.isPending ? "部署中..." : "部署到 Production"}
                  </button>
                )}
                
                {selectedPatch.status === "DEPLOYED" && (
                  <button
                    onClick={() => handleRevert(selectedPatch.patch_id)}
                    disabled={revertMutation.isPending}
                    className="w-full px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
                  >
                    {revertMutation.isPending ? "回滾中..." : "緊急回滾"}
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="border rounded-lg p-8 text-center text-gray-500">
              請從左側選擇一個 Patch 查看詳情
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
