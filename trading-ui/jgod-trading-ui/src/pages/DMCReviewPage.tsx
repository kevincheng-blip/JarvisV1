/**
 * Doctrine Review & Diff View
 * 
 * Review workbench for FixProposals with side-by-side diff.
 */

import { useState } from "react";
import { useDoctrineSection, useVersionContent, useVersionDiff, useApproveVersion, useRejectVersion } from "../hooks/useDoctrineV2";
import { useRunRuleSimExperiment } from "../hooks/useRuleSim";
import type { RuleSetRef } from "../types/ruleSim";

interface DMCReviewPageProps {
  sectionId: string;
  versionId: string;
  onBack?: () => void;
}

export function DMCReviewPage({ sectionId, versionId, onBack }: DMCReviewPageProps) {
  
  const { data: section, isLoading: sectionLoading } = useDoctrineSection(sectionId || null);
  const { data: currentContent } = useVersionContent(sectionId || null, section?.current_version_id || null);
  const { data: pendingContent } = useVersionContent(sectionId || null, versionId || null);
  const { data: diffData } = useVersionDiff(
    sectionId || null,
    section?.current_version_id || null,
    versionId || null
  );
  
  const approveMutation = useApproveVersion();
  const rejectMutation = useRejectVersion();
  const runRuleSimMutation = useRunRuleSimExperiment();
  const [ruleSimExperimentId, setRuleSimExperimentId] = useState<string | null>(null);
  
  const handleRunRuleSim = () => {
    if (!sectionId || !versionId || !section) return;
    
    // Calculate default date range (last 6 months)
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 6);
    
    const targetRuleset: RuleSetRef = {
      id: sectionId,
      type: "doctrine_section",
      description: section.title,
    };
    
    runRuleSimMutation.mutate(
      {
        target_ruleset: targetRuleset,
        baseline_version_id: section.current_version_id,
        variant_version_id: versionId,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        path_a_config_name: "path_a_tw_basic_v1",
        note: `Rule simulation for Doctrine section ${sectionId}`,
      },
      {
        onSuccess: (response) => {
          setRuleSimExperimentId(response.experiment_id);
          alert(`Rule Simulation 已啟動！\n實驗 ID: ${response.experiment_id}\n狀態: ${response.status.status}`);
        },
        onError: (error) => {
          alert(`Rule Simulation 啟動失敗: ${error instanceof Error ? error.message : "未知錯誤"}`);
        },
      }
    );
  };
  
  const handleApprove = () => {
    if (!sectionId || !versionId) return;
    approveMutation.mutate(
      { sectionId, versionId },
      {
        onSuccess: () => {
          if (onBack) onBack();
        },
      }
    );
  };
  
  const handleReject = () => {
    if (!sectionId || !versionId) return;
    rejectMutation.mutate(
      { sectionId, versionId },
      {
        onSuccess: () => {
          if (onBack) onBack();
        },
      }
    );
  };
  
  if (sectionLoading || !section) {
    return <div className="p-6">載入中...</div>;
  }
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">
        審核工作台: {section.section_id}
      </h1>
      
      {/* Metadata */}
      <div className="mb-4 p-4 bg-gray-100 dark:bg-gray-800 rounded">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <strong>Issue Type:</strong> {section.metadata?.issue_type || "N/A"}
          </div>
          <div>
            <strong>Source:</strong> {section.source === "self-repair" ? "Self-Repair Engine" : "Manual"}
          </div>
          <div>
            <strong>Confidence:</strong>{" "}
            {section.metadata?.confidence
              ? `${(section.metadata.confidence * 100).toFixed(1)}%`
              : "N/A"}
          </div>
          <div>
            <strong>Report ID:</strong> {section.metadata?.repair_report_id || "N/A"}
          </div>
        </div>
      </div>
      
      {/* Side-by-side Comparison */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Current Approved Version */}
        <div className="border rounded p-4">
          <h3 className="font-semibold mb-2">Current APPROVED Version</h3>
          <div className="bg-white dark:bg-gray-900 p-3 rounded font-mono text-sm overflow-auto max-h-96">
            <pre className="whitespace-pre-wrap">{currentContent?.content || "載入中..."}</pre>
          </div>
        </div>
        
        {/* Pending Version */}
        <div className="border rounded p-4">
          <h3 className="font-semibold mb-2">Pending Version (FixProposal)</h3>
          <div className="bg-white dark:bg-gray-900 p-3 rounded font-mono text-sm overflow-auto max-h-96">
            <pre className="whitespace-pre-wrap">{pendingContent?.content || "載入中..."}</pre>
          </div>
        </div>
      </div>
      
      {/* Diff Viewer */}
      {diffData && (
        <div className="mb-4">
          <h3 className="font-semibold mb-2">Diff Viewer</h3>
          <div className="bg-gray-900 text-white p-4 rounded font-mono text-sm overflow-auto max-h-96">
            <pre className="whitespace-pre-wrap">{diffData.diff}</pre>
          </div>
        </div>
      )}
      
      {/* Rule Simulation Status */}
      {ruleSimExperimentId && (
        <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
          <div className="flex justify-between items-center">
            <div>
              <div className="font-semibold text-blue-900 dark:text-blue-100">
                Rule Simulation 已啟動
              </div>
              <div className="text-sm text-blue-700 dark:text-blue-300">
                實驗 ID: {ruleSimExperimentId.substring(0, 8)}...
              </div>
            </div>
            <button
              onClick={() => {
                window.dispatchEvent(new CustomEvent('ruleSim:navigate', {
                  detail: { page: 'detail', experimentId: ruleSimExperimentId }
                }));
              }}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
            >
              前往報告
            </button>
          </div>
        </div>
      )}
      
      {/* Action Buttons */}
      <div className="flex gap-4 flex-wrap">
        <button
          onClick={handleRunRuleSim}
          disabled={runRuleSimMutation.isPending}
          className="px-6 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
        >
          {runRuleSimMutation.isPending ? "啟動中..." : "在沙盒回測此修訂"}
        </button>
        <button
          onClick={handleApprove}
          disabled={approveMutation.isPending}
          className="px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
        >
          {approveMutation.isPending ? "批准中..." : "批准 (Approve)"}
        </button>
        <button
          onClick={handleReject}
          disabled={rejectMutation.isPending}
          className="px-6 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
        >
          {rejectMutation.isPending ? "拒絕中..." : "拒絕 (Reject)"}
        </button>
        {onBack && (
          <button
            onClick={onBack}
            className="px-6 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            返回列表
          </button>
        )}
      </div>
    </div>
  );
}

