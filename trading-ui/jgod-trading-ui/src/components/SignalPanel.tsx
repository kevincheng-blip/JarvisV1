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

// Helpers to parse backend string payloads like "{'code': 'C08', ...}"
function extractCode(raw: string): string {
  const match = raw.match(/'code':\s*'([^']+)'/);
  if (match) return match[1];
  return raw;
}

function extractMessage(raw: string): string {
  const match = raw.match(/'message':\s*'([^']+)'/);
  if (match) return match[1];
  return raw;
}

function extractSeverity(raw: string): string {
  const match = raw.match(/'severity':\s*'([^']+)'/);
  if (match) return match[1];
  return "";
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

  function getHumanAdvice(
    signal: string,
    score: number | null,
    hasRisk: boolean
  ): string {
    const s = signal.toUpperCase();

    if (s === "SHORT") {
      return "偏空訊號，偏向逢高放空或減碼，嚴控風險與部位。";
    }
    if (s === "BUY" || s === "STRONG_BUY") {
      return "偏多訊號，可考慮分批佈局，但仍需搭配大盤與個股風險評估。";
    }
    if (s === "AVOID") {
      if (hasRisk) {
        return "系統偵測到風險旗標，建議暫時觀望，等待結構好轉再進場。";
      }
      return "目前不適合進場，建議先觀察，避免追高或硬做方向。";
    }
    return "訊號中性，可等待更明確的方向再做決策。";
  }

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
            fontSize: "12px",
            color: "#666",
            marginBottom: "4px",
          }}
        >
          Positive Factors
        </div>
        {data.positive_factors.length === 0 ? (
          <div style={{ color: "#999", fontSize: "12px" }}>None</div>
        ) : (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
            {data.positive_factors.map((raw, idx) => {
              const code = extractCode(raw);
              return (
                <span
                  key={idx}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    padding: "2px 8px",
                    borderRadius: "9999px",
                    fontSize: "12px",
                    fontWeight: "500",
                    backgroundColor: "#dcfce7",
                    color: "#166534",
                  }}
                  title={raw}
                >
                  {code}
                </span>
              );
            })}
          </div>
        )}
      </div>

      {/* Negative Factors */}
      <div>
        <div
          style={{
            fontSize: "12px",
            color: "#666",
            marginBottom: "4px",
          }}
        >
          Negative Factors
        </div>
        {data.negative_factors.length === 0 ? (
          <div style={{ color: "#999", fontSize: "12px" }}>None</div>
        ) : (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
            {data.negative_factors.map((raw, idx) => {
              const code = extractCode(raw);
              return (
                <span
                  key={idx}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    padding: "2px 8px",
                    borderRadius: "9999px",
                    fontSize: "12px",
                    fontWeight: "500",
                    backgroundColor: "#fee2e2",
                    color: "#991b1b",
                  }}
                  title={raw}
                >
                  {code}
                </span>
              );
            })}
          </div>
        )}
      </div>

      {/* Risk Flags */}
      <div
        style={{
          marginTop: "12px",
          borderTop: "1px solid #e5e7eb",
          paddingTop: "8px",
        }}
      >
        <div
          style={{
            fontSize: "12px",
            color: "#666",
            marginBottom: "4px",
          }}
        >
          Risk Flags
        </div>
        {data.risk_flags.length === 0 ? (
          <div style={{ color: "#999", fontSize: "12px" }}>
            No major risk flags.
          </div>
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "4px",
            }}
          >
            {data.risk_flags.map((raw, idx) => {
              const message = extractMessage(raw);
              const severity = extractSeverity(raw) || "info";
              const severityLabel = severity.toUpperCase();

              return (
                <div
                  key={idx}
                  style={{
                    fontSize: "12px",
                    padding: "4px 8px",
                    borderRadius: "6px",
                    backgroundColor: "#fffbeb",
                    color: "#92400e",
                    border: "1px solid #fde68a",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                  title={raw}
                >
                  <span>⚠️</span>
                  <span style={{ fontWeight: "500" }}>{severityLabel}</span>
                  <span style={{ fontSize: "11px" }}>{message}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Human-readable advice */}
      <div
        style={{
          marginTop: "12px",
          borderTop: "1px solid #e5e7eb",
          paddingTop: "8px",
        }}
      >
        <div
          style={{
            fontSize: "12px",
            color: "#666",
            marginBottom: "4px",
          }}
        >
          J-GOD 建議
        </div>
        <div
          style={{
            fontSize: "14px",
            color: "#1f2937",
          }}
        >
          {getHumanAdvice(
            data.signal,
            data.score,
            data.risk_flags.length > 0
          )}
        </div>
      </div>
    </div>
  );
}

