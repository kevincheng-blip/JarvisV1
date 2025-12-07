/**
 * Watchlist Panel (A1)
 * 
 * 自選股 / 宇宙清單面板
 */

import { useTranslation } from "react-i18next";
import type { Prediction } from "../types";

interface WatchlistPanelProps {
  predictions: Prediction[];
  loading?: boolean;
}

export function WatchlistPanel({ predictions, loading }: WatchlistPanelProps) {
  const { t } = useTranslation();

  if (loading) {
    return <div>{t("label.loading")}</div>;
  }

  return (
    <div style={{ padding: "16px", border: "1px solid #ccc", borderRadius: "8px" }}>
      <h3>{t("panel.watchlist")}</h3>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th>{t("label.symbol")}</th>
            <th>{t("label.name")}</th>
            <th>{t("label.verdict")}</th>
            <th>{t("label.total_score")}</th>
            <th>{t("label.sector")}</th>
          </tr>
        </thead>
        <tbody>
          {predictions.map((pred) => (
            <tr key={pred.symbol}>
              <td>{pred.symbol}</td>
              <td>{pred.name_zh || pred.name_en || "-"}</td>
              <td>{t(`verdict.${pred.verdict}`)}</td>
              <td>{pred.total_score?.toFixed(2) || "-"}</td>
              <td>{pred.sector_zh || pred.sector_en || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {predictions.length === 0 && <p>No data available</p>}
    </div>
  );
}

