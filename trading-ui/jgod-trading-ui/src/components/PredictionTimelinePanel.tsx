/**
 * Prediction Timeline Panel
 * 
 * 預測時間軸面板，使用 Recharts 顯示指定股票在日期區間內的預測時間序列折線圖
 */

import { useEffect, useState, useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { api } from "../api/client";
import type { PredictionTimelineResponse } from "../types";

interface PredictionTimelinePanelProps {
  symbol: string;
  startDate: string;
  endDate: string;
}

// Signal color mapping
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

// Custom dot component that colors based on signal
const CustomDot = (props: any) => {
  const { cx, cy, payload } = props;
  if (!cx || !cy || !payload) return null;
  const signal = payload.signal || "UNKNOWN";
  const color = getSignalColor(signal);
  return (
    <circle
      cx={cx}
      cy={cy}
      r={5}
      fill={color}
      stroke={color}
      strokeWidth={2}
    />
  );
};

// Custom tooltip component
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    if (!data) return null;

    const signal = data.signal || "UNKNOWN";
    const score = data.score;

    return (
      <div
        style={{
          backgroundColor: "white",
          border: "1px solid #ccc",
          borderRadius: "4px",
          padding: "8px",
          boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
        }}
      >
        <p style={{ margin: "4px 0", fontWeight: "bold" }}>{data.date}</p>
        <p style={{ margin: "4px 0" }}>
          <span style={{ color: "#666" }}>Score:</span>{" "}
          <span style={{ fontWeight: "bold" }}>{Number(score).toFixed(2)}</span>
        </p>
        <p style={{ margin: "4px 0" }}>
          <span style={{ color: "#666" }}>Signal:</span>{" "}
          <span style={{ fontWeight: "bold", color: getSignalColor(signal) }}>
            {signal}
          </span>
        </p>
      </div>
    );
  }
  return null;
};

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

  // Sort points by date (ascending) and prepare chart data
  const chartData = useMemo(() => {
    if (!data?.points) return [];

    const sorted = [...data.points].sort((a, b) => a.date.localeCompare(b.date));
    return sorted.map((point) => ({
      date: point.date,
      score: point.score,
      signal: point.signal,
    }));
  }, [data]);

  return (
    <div style={{ padding: "16px", border: "1px solid #ccc", borderRadius: "8px" }}>
      <h3>J-GOD Score Timeline – {symbol}</h3>

      {loading && <div>載入中…</div>}

      {error && (
        <div style={{ color: "red", marginTop: "8px" }}>
          載入預測資料失敗: {error}
        </div>
      )}

      {!loading && !error && data && (
        <>
          {chartData.length === 0 ? (
            <p>目前此區間沒有預測資料</p>
          ) : (
            <div style={{ width: "100%", height: "300px", marginTop: "16px" }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 80 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                  <XAxis
                    dataKey="date"
                    stroke="#666"
                    style={{ fontSize: "12px" }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis
                    stroke="#666"
                    style={{ fontSize: "12px" }}
                    label={{ value: "Score", angle: -90, position: "insideLeft" }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  {/* Single line with dots colored by signal */}
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#8884d8"
                    strokeWidth={2}
                    dot={<CustomDot />}
                    activeDot={{ r: 7 }}
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
}
