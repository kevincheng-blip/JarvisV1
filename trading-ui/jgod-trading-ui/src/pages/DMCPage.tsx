/**
 * Doctrine Management Console (DMC) Main Page
 * 
 * Main view showing Doctrine sections list with filtering and pagination.
 */

import { useState } from "react";
import { useDoctrineSections } from "../hooks/useDoctrineV2";
import { useApproveVersion, useRejectVersion } from "../hooks/useDoctrineV2";
import type { DoctrineSection, SectionStatus } from "../types/doctrineV2";

export function DMCPage() {
  const [statusFilter, setStatusFilter] = useState<SectionStatus | "all">("all");
  const [page, setPage] = useState(1);
  const [selectedSections, setSelectedSections] = useState<Set<string>>(new Set());
  
  const { data, isLoading, isError, error, refetch } = useDoctrineSections(
    statusFilter === "all" ? null : statusFilter,
    page,
    50
  );
  
  const approveMutation = useApproveVersion();
  const rejectMutation = useRejectVersion();
  
  const getStatusBadgeClass = (status: SectionStatus) => {
    switch (status) {
      case "APPROVED":
        return "bg-green-500 text-white";
      case "PENDING_REVIEW":
        return "bg-yellow-500 text-white";
      case "DRAFT":
        return "bg-gray-500 text-white";
      case "DEPRECATED":
        return "bg-red-500 text-white";
      default:
        return "bg-gray-400 text-white";
    }
  };
  
  const handleBulkApprove = () => {
    selectedSections.forEach((sectionId) => {
      const section = data?.sections.find((s) => s.section_id === sectionId);
      if (section && section.draft_version_id && section.status === "PENDING_REVIEW") {
        approveMutation.mutate({
          sectionId: sectionId,
          versionId: section.draft_version_id,
        });
      }
    });
    setSelectedSections(new Set());
  };
  
  const handleBulkReject = () => {
    selectedSections.forEach((sectionId) => {
      const section = data?.sections.find((s) => s.section_id === sectionId);
      if (section && section.draft_version_id && section.status === "PENDING_REVIEW") {
        rejectMutation.mutate({
          sectionId: sectionId,
          versionId: section.draft_version_id,
        });
      }
    });
    setSelectedSections(new Set());
  };
  
  if (isLoading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Doctrine Management Console</h1>
        <div className="text-gray-500">載入中...</div>
      </div>
    );
  }
  
  if (isError) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Doctrine Management Console</h1>
        <div className="text-red-500">
          錯誤: {error instanceof Error ? error.message : "未知錯誤"}
        </div>
      </div>
    );
  }
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Doctrine Management Console</h1>
      
      {/* Filters and Actions */}
      <div className="mb-4 flex gap-4 items-center">
        <div>
          <label className="mr-2">狀態過濾:</label>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as SectionStatus | "all");
              setPage(1);
            }}
            className="px-3 py-1 border rounded"
          >
            <option value="all">全部</option>
            <option value="APPROVED">已批准</option>
            <option value="PENDING_REVIEW">待審核</option>
            <option value="DRAFT">草稿</option>
            <option value="DEPRECATED">已棄用</option>
          </select>
        </div>
        
        {selectedSections.size > 0 && statusFilter === "PENDING_REVIEW" && (
          <div className="flex gap-2">
            <button
              onClick={handleBulkApprove}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              批量批准 ({selectedSections.size})
            </button>
            <button
              onClick={handleBulkReject}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              批量拒絕 ({selectedSections.size})
            </button>
          </div>
        )}
      </div>
      
      {/* Sections Table */}
      {data && data.sections.length > 0 ? (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white dark:bg-gray-800 rounded-lg shadow">
              <thead>
                <tr className="bg-gray-100 dark:bg-gray-700">
                  {statusFilter === "PENDING_REVIEW" && (
                    <th className="px-4 py-2 text-left">
                      <input
                        type="checkbox"
                        checked={selectedSections.size === data.sections.length}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedSections(new Set(data.sections.map((s) => s.section_id)));
                          } else {
                            setSelectedSections(new Set());
                          }
                        }}
                      />
                    </th>
                  )}
                  <th className="px-4 py-2 text-left">ID</th>
                  <th className="px-4 py-2 text-left">Title</th>
                  <th className="px-4 py-2 text-left">Status</th>
                  <th className="px-4 py-2 text-left">Source</th>
                  <th className="px-4 py-2 text-left">Last Updated</th>
                  <th className="px-4 py-2 text-left">Severity</th>
                  <th className="px-4 py-2 text-left">操作</th>
                </tr>
              </thead>
              <tbody>
                {data.sections.map((section) => (
                  <tr
                    key={section.section_id}
                    className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    {statusFilter === "PENDING_REVIEW" && (
                      <td className="px-4 py-2">
                        <input
                          type="checkbox"
                          checked={selectedSections.has(section.section_id)}
                          onChange={(e) => {
                            const newSelected = new Set(selectedSections);
                            if (e.target.checked) {
                              newSelected.add(section.section_id);
                            } else {
                              newSelected.delete(section.section_id);
                            }
                            setSelectedSections(newSelected);
                          }}
                        />
                      </td>
                    )}
                    <td className="px-4 py-2 font-mono text-sm">{section.section_id}</td>
                    <td className="px-4 py-2">{section.title}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 text-xs rounded ${getStatusBadgeClass(section.status)}`}>
                        {section.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-sm">
                      {section.source === "self-repair" ? (
                        <span className="text-blue-500">Self-Repair</span>
                      ) : (
                        <span className="text-gray-500">Manual</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                      {new Date(section.updated_at).toLocaleString("zh-TW")}
                    </td>
                    <td className="px-4 py-2">
                      {section.severity && (
                        <span className="text-xs text-orange-500">{section.severity}</span>
                      )}
                    </td>
                    <td className="px-4 py-2">
                      <div className="flex gap-2">
                        {section.draft_version_id && section.status === "PENDING_REVIEW" && (
                          <button
                            onClick={() => {
                              // Navigate to review page (to be handled by parent)
                              window.dispatchEvent(new CustomEvent('dmc:navigate', {
                                detail: { page: 'review', sectionId: section.section_id, versionId: section.draft_version_id }
                              }));
                            }}
                            className="px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600"
                          >
                            審核
                          </button>
                        )}
                        <button
                          onClick={() => {
                            window.dispatchEvent(new CustomEvent('dmc:navigate', {
                              detail: { page: 'edit', sectionId: section.section_id }
                            }));
                          }}
                          className="px-2 py-1 bg-gray-500 text-white text-xs rounded hover:bg-gray-600"
                        >
                          編輯
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* Pagination */}
          {data.total_pages > 1 && (
            <div className="mt-4 flex justify-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-gray-500 text-white rounded disabled:opacity-50"
              >
                上一頁
              </button>
              <span className="px-4 py-2">
                第 {page} / {data.total_pages} 頁 (共 {data.total} 筆)
              </span>
              <button
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page >= data.total_pages}
                className="px-4 py-2 bg-gray-500 text-white rounded disabled:opacity-50"
              >
                下一頁
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="text-gray-500 text-center py-8">
          目前沒有任何 Doctrine 條文
        </div>
      )}
    </div>
  );
}

