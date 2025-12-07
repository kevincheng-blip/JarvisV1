/**
 * Prediction Summary Panel (B2)
 * 
 * 決策摘要 / 解釋面板
 */

import { useTranslation } from "react-i18next";
import type { Prediction } from "../types";

interface PredictionSummaryPanelProps {
  prediction?: Prediction;
  loading?: boolean;
}

export function PredictionSummaryPanel({ prediction, loading }: PredictionSummaryPanelProps) {
  const { t } = useTranslation();

  if (loading) {
    return <div>{t("label.loading")}</div>;
  }

  if (!prediction) {
    return <div style={{ padding: "16px", border: "1px solid #ccc", borderRadius: "8px" }}>
      <h3>{t("panel.prediction_summary")}</h3>
      <p>Select a symbol to view prediction summary</p>
    </div>;
  }

  return (
    <div style={{ padding: "16px", border: "1px solid #ccc", borderRadius: "8px" }}>
      <h3>{t("panel.prediction_summary")}</h3>
      <div>
        <p><strong>{t("label.symbol")}:</strong> {prediction.symbol}</p>
        <p><strong>{t("label.name")}:</strong> {prediction.name_zh || prediction.name_en || "-"}</p>
        <p><strong>{t("label.verdict")}:</strong> {t(`verdict.${prediction.verdict}`)}</p>
        <p><strong>{t("label.total_score")}:</strong> {prediction.total_score?.toFixed(2) || "-"}</p>
      </div>
    </div>
  );
}

