/**
 * Signal Panel Component
 * 
 * 顯示最新預測結果的重點資訊：score、signal、positive/negative factors、risk flags
 */

import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { LatestPrediction } from "../types";

interface SignalPanelProps {
  symbol: string;
}

// Signal color mapping (consistent with Timeline)
const getSignalColor = (signal: string): string => {
  switch (signal.toUpperCase()) {
    case "BUY":
      return "#22c55e"; // 綠色
    case "STRONG_BUY":
      return "#15803d"; // 深綠
    case "SHORT":
      return "#ef4444"; // 紅色
    case "AVOID":
      return "#6b7280"; // 灰色
    default:
      return "#3b82f6"; // 藍色
  }
};

export function SignalPanel({ symbol }: SignalPanelProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<LatestPrediction | null>(null);

  useEffect(() => {
    const fetchLatestPrediction = async () => {
      if (!symbol) return;

      setLoading(true);
      setError(null);
      try {
        const result = await api.getLatestPrediction(symbol);
        setData(result);
      } catch (err: any) {
        const errorMessage =
          err.response?.status === 404
            ? `No prediction found for ${symbol}`
            : err.message || "載入最新預測失敗";
        setError(errorMessage);
        console.error("Error loading latest prediction:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchLatestPrediction();
  }, [symbol]);

  if (loading) {
    return (
      <div
        style={{
          padding: "16px",
          border: "1px solid #ccc",
          borderRadius: "8px",
        }}
      >
        <h3>J-GOD Signal – {symbol}</h3>
        <div>載入中…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          padding: "16px",
          border: "1px solid #ccc",
          borderRadius: "8px",
        }}
      >
        <h3>J-GOD Signal – {symbol}</h3>
        <div style={{ color: "red", marginTop: "8px" }}>{error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div
        style={{
          padding: "16px",
          border: "1px solid #ccc",
          borderRadius: "8px",
        }}
      >
        <h3>J-GOD Signal – {symbol}</h3>
        <div style={{ marginTop: "8px", color: "#666" }}>
          目前沒有預測資料
        </div>
      </div>
    );
  }

  const signalColor = getSignalColor(data.signal);

  return (
    <div
      style={{
        padding: "16px",
        border: "1px solid #ccc",
        borderRadius: "8px",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h3>J-GOD Signal – {data.symbol}</h3>
        <span style={{ fontSize: "12px", color: "#666" }}>{data.date}</span>
      </div>

      {/* Main Signal Block */}
      <div
        style={{
          padding: "16px",
          backgroundColor: "#f9fafb",
          borderRadius: "8px",
          border: `2px solid ${signalColor}`,
        }}
      >
        <div
          style={{
            fontSize: "24px",
            fontWeight: "bold",
            color: signalColor,
            marginBottom: "8px",
          }}
        >
          {data.signal}
        </div>
        <div style={{ fontSize: "18px", color: "#666" }}>
          Score: <strong>{data.score.toFixed(2)}</strong>
        </div>
      </div>

      {/* Positive Factors */}
      <div>
        <div
          style={{
            fontSize: "14px",
            fontWeight: "bold",
            color: "#666",
            marginBottom: "8px",
          }}
        >
          Positive Factors
        </div>
        {data.positive_factors.length === 0 ? (
          <div style={{ color: "#999", fontSize: "14px" }}>None</div>
        ) : (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {data.positive_factors.map((factor, idx) => (
              <span
                key={idx}
                style={{
                  padding: "4px 8px",
                  backgroundColor: "#dcfce7",
                  color: "#166534",
                  borderRadius: "4px",
                  fontSize: "12px",
                }}
              >
                {factor}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Negative Factors */}
      <div>
        <div
          style={{
            fontSize: "14px",
            fontWeight: "bold",
            color: "#666",
            marginBottom: "8px",
          }}
        >
          Negative Factors
        </div>
        {data.negative_factors.length === 0 ? (
          <div style={{ color: "#999", fontSize: "14px" }}>None</div>
        ) : (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {data.negative_factors.map((factor, idx) => (
              <span
                key={idx}
                style={{
                  padding: "4px 8px",
                  backgroundColor: "#fee2e2",
                  color: "#991b1b",
                  borderRadius: "4px",
                  fontSize: "12px",
                }}
              >
                {factor}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Risk Flags */}
      <div>
        <div
          style={{
            fontSize: "14px",
            fontWeight: "bold",
            color: "#666",
            marginBottom: "8px",
          }}
        >
          Risk Flags
        </div>
        {data.risk_flags.length === 0 ? (
          <div style={{ color: "#999", fontSize: "14px" }}>
            No major risk flags
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {data.risk_flags.map((flag, idx) => (
              <div
                key={idx}
                style={{
                  padding: "8px 12px",
                  backgroundColor: "#fff7ed",
                  border: "1px solid #fb923c",
                  borderRadius: "4px",
                  color: "#9a3412",
                  fontSize: "13px",
                }}
              >
                ⚠️ {flag}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

