/**
 * Doctrine Editor Page
 * 
 * Markdown editor for editing Doctrine sections with live preview.
 */

import { useState, useEffect } from "react";
import { useDoctrineSection, useVersionContent, useCreateDraft, useSubmitForReview } from "../hooks/useDoctrineV2";

interface DMCEditPageProps {
  sectionId: string;
  onBack?: () => void;
}

export function DMCEditPage({ sectionId, onBack }: DMCEditPageProps) {
  
  const [content, setContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  
  const { data: section } = useDoctrineSection(sectionId || null);
  const { data: currentContent } = useVersionContent(
    sectionId || null,
    section?.current_version_id || null
  );
  
  const createDraftMutation = useCreateDraft();
  const submitMutation = useSubmitForReview();
  
  // Load content when available
  useEffect(() => {
    if (currentContent) {
      setContent(currentContent.content);
    }
  }, [currentContent]);
  
  const handleSaveDraft = () => {
    if (!sectionId) return;
    setIsSaving(true);
    createDraftMutation.mutate(
      { sectionId, content },
      {
        onSuccess: () => {
          setIsSaving(false);
          alert("草稿已儲存");
        },
        onError: () => {
          setIsSaving(false);
        },
      }
    );
  };
  
  const handleSubmit = () => {
    if (!sectionId) return;
    // First save as draft, then submit
    createDraftMutation.mutate(
      { sectionId, content },
      {
        onSuccess: () => {
          submitMutation.mutate(sectionId, {
            onSuccess: () => {
              alert("已提交審核");
              if (onBack) onBack();
            },
          });
        },
      }
    );
  };
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">
        編輯 Doctrine: {sectionId}
      </h1>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Editor */}
        <div>
          <h3 className="font-semibold mb-2">Markdown 編輯器</h3>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full h-96 p-4 border rounded font-mono text-sm"
            placeholder="輸入 Markdown 內容..."
          />
        </div>
        
        {/* Preview */}
        <div>
          <h3 className="font-semibold mb-2">即時預覽</h3>
          <div className="h-96 p-4 border rounded overflow-auto bg-white dark:bg-gray-900 prose dark:prose-invert max-w-none">
            <pre className="whitespace-pre-wrap font-sans">{content || "預覽將顯示在這裡..."}</pre>
          </div>
        </div>
      </div>
      
      {/* Revision History */}
      {section && section.revision_history.length > 0 && (
        <div className="mb-4">
          <h3 className="font-semibold mb-2">版本歷史</h3>
          <div className="space-y-2">
            {section.revision_history
              .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
              .map((revision, idx) => (
                <div
                  key={revision.version_id}
                  className="p-3 bg-gray-100 dark:bg-gray-800 rounded text-sm"
                >
                  <div className="flex justify-between">
                    <span>
                      <strong>{revision.change_type}</strong> - {revision.version_id.substring(0, 8)}
                    </span>
                    <span className="text-gray-600 dark:text-gray-400">
                      {new Date(revision.timestamp).toLocaleString("zh-TW")} by {revision.operator}
                    </span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
      
      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={handleSaveDraft}
          disabled={isSaving || createDraftMutation.isPending}
          className="px-6 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50"
        >
          {isSaving ? "儲存中..." : "儲存草稿 (Save Draft)"}
        </button>
        <button
          onClick={handleSubmit}
          disabled={isSaving || submitMutation.isPending}
          className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {submitMutation.isPending ? "提交中..." : "提交審核 (Submit for Review)"}
        </button>
        {onBack && (
          <button
            onClick={onBack}
            className="px-6 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            取消
          </button>
        )}
      </div>
    </div>
  );
}

