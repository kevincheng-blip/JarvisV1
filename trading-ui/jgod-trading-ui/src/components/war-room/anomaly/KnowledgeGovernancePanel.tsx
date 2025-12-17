// @ts-nocheck
/**
 * Knowledge Governance Panel
 * 
 * Lightweight War Room panel showing pending Doctrine reviews.
 */

import { useDoctrineSections } from "../../../hooks/useDoctrineV2";
import { useRuleSimExperiments } from "../../../hooks/useRuleSim";
import { useState } from "react";

export function KnowledgeGovernancePanel() {
  const [showDetails, setShowDetails] = useState(false);
  
  const { data: pendingData } = useDoctrineSections("PENDING_REVIEW", 1, 5, true);
  const { data: ruleSimData } = useRuleSimExperiments(10, true);
  
  const pendingCount = pendingData?.total || 0;
  const topPending = pendingData?.sections || [];
  
  // Count rule sim experiments
  const ruleSimCount = ruleSimData?.length || 0;
  const approveCount = ruleSimData?.filter((e) => e.recommendation === "APPROVE").length || 0;
  const rejectCount = ruleSimData?.filter((e) => e.recommendation === "REJECT").length || 0;
  
  const criticalCount = topPending.filter(
    (s) => s.severity === "CRITICAL" || s.metadata?.confidence && s.metadata.confidence < 0.6
  ).length;
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          知識治理 (Knowledge Governance)
        </h3>
        {pendingCount > 0 && (
          <span className="px-2 py-1 bg-red-500 text-white text-xs rounded font-semibold">
            {pendingCount} 待審核
          </span>
        )}
      </div>
      
      {pendingCount === 0 ? (
        <div className="text-gray-500 dark:text-gray-400 text-center py-4 text-sm">
          目前沒有待審核的 Doctrine 條文
        </div>
      ) : (
        <>
          <div className="mb-2 text-sm text-gray-600 dark:text-gray-400">
            {criticalCount > 0 && (
              <span className="text-red-500 font-semibold">
                ⚠ {criticalCount} 個 CRITICAL 待審核
              </span>
            )}
          </div>
          
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {topPending.map((section) => (
              <div
                key={section.section_id}
                className="p-2 border border-gray-200 dark:border-gray-700 rounded hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer"
                onClick={() => {
                  if (section.draft_version_id) {
                    window.dispatchEvent(new CustomEvent('dmc:navigate', {
                      detail: {
                        page: 'review',
                        sectionId: section.section_id,
                        versionId: section.draft_version_id,
                      }
                    }));
                  }
                }}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold text-sm text-gray-900 dark:text-white">
                      {section.section_id}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      {section.title}
                    </div>
                  </div>
                  <div className="text-right">
                    {section.source === "self-repair" && (
                      <span className="text-xs text-blue-500">Self-Repair</span>
                    )}
                    {section.metadata?.confidence && (
                      <div className="text-xs text-gray-500">
                        {(section.metadata.confidence * 100).toFixed(0)}%
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {pendingCount > 5 && (
            <div className="mt-2 text-center">
              <button
                onClick={() => {
                  window.dispatchEvent(new CustomEvent('dmc:navigate', {
                    detail: { page: 'list', status: 'PENDING_REVIEW' }
                  }));
                }}
                className="text-xs text-blue-500 hover:underline"
              >
                查看全部 {pendingCount} 筆待審核項目
              </button>
            </div>
          )}
        </>
      )}
      
      {/* Rule Simulation Summary */}
      {ruleSimCount > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            最近規則沙盒實驗：{ruleSimCount} 次
            {approveCount > 0 && <span className="text-green-600 ml-2">({approveCount} 次建議 APPROVE</span>}
            {rejectCount > 0 && <span className="text-red-600">, {rejectCount} 次 REJECT)</span>}
            {approveCount === 0 && rejectCount === 0 && <span>)</span>}
          </div>
          <button
            onClick={() => {
              window.dispatchEvent(new CustomEvent('ruleSim:navigate', {
                detail: { page: 'list' }
              }));
            }}
            className="text-xs text-blue-500 hover:underline"
          >
            查看全部實驗 →
          </button>
        </div>
      )}
    </div>
  );
}

