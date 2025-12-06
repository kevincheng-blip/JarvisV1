/**
 * Prediction Timeline Panel
 * 
 * 預測時間軸面板，顯示指定股票在日期區間內的預測時間序列
 */

import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { PredictionTimelineResponse, PredictionTimelinePoint } from "../types";

interface PredictionTimelinePanelProps {
  symbol: string;
  startDate: string;
  endDate: string;
}

export function PredictionTimelinePanel({
  symbol,
  startDate,
  endDate,
}: PredictionTimelinePanelProps) {
  const [data, setData] = useState<PredictionTimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.getPredictionTimeline({
          symbol,
          startDate,
          endDate,
        });
        setData(result);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "載入預測資料失敗";
        setError(errorMessage);
        console.error("Error loading prediction timeline:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [symbol, startDate, endDate]);

  // Sort points by date (ascending)
  const sortedPoints: PredictionTimelinePoint[] = data?.points
    ? [...data.points].sort((a, b) => a.date.localeCompare(b.date))
    : [];

  return (
    <div style={{ padding: "16px", border: "1px solid #ccc", borderRadius: "8px" }}>
      <h3>J-GOD Prediction Timeline ({symbol})</h3>

      {loading && <div>載入中…</div>}

      {error && (
        <div style={{ color: "red", marginTop: "8px" }}>
          載入預測資料失敗: {error}
        </div>
      )}

      {!loading && !error && data && (
        <>
          {sortedPoints.length === 0 ? (
            <p>目前此區間沒有預測資料</p>
          ) : (
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                marginTop: "12px",
              }}
            >
              <thead>
                <tr style={{ background: "#f0f0f0" }}>
                  <th style={{ padding: "8px", textAlign: "left", border: "1px solid #ddd" }}>
                    Date
                  </th>
                  <th style={{ padding: "8px", textAlign: "left", border: "1px solid #ddd" }}>
                    Score
                  </th>
                  <th style={{ padding: "8px", textAlign: "left", border: "1px solid #ddd" }}>
                    Signal
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedPoints.map((point, index) => (
                  <tr key={`${point.date}-${index}`}>
                    <td style={{ padding: "8px", border: "1px solid #ddd" }}>
                      {point.date}
                    </td>
                    <td style={{ padding: "8px", border: "1px solid #ddd" }}>
                      {point.score.toFixed(2)}
                    </td>
                    <td style={{ padding: "8px", border: "1px solid #ddd" }}>
                      {point.signal}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}

