import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

interface PolicyExperimentHistoryItem {
  run_id: string;
  timestamp: string;
  start_date: string;
  end_date: string;
  score: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_return: number;
  win_rate: number;
  num_days: number;
  num_trades: number;
  long_budget?: number;
  short_budget?: number;
  max_weight_per_symbol?: number;
  min_score?: number;
  allow_short?: boolean;
  tag?: string;
}

interface PolicyActiveConfig {
  file_path: string;
  exists: boolean;
  risk_version?: number;
  run_id?: string;
  start_date?: string;
  end_date?: string;
  long_budget?: number;
  short_budget?: number;
  max_weight_per_symbol?: number;
  min_score?: number;
  allow_short?: boolean;
  sharpe_ratio?: number;
  max_drawdown?: number;
  total_return?: number;
  win_rate?: number;
}

export function PolicyEvolutionPanel() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeConfig, setActiveConfig] = useState<PolicyActiveConfig | null>(null);
  const [experiments, setExperiments] = useState<PolicyExperimentHistoryItem[]>([]);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [limit, setLimit] = useState<number>(50);

  // 設定預設日期範圍（最近 30 天）
  useEffect(() => {
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    setEndDate(today.toISOString().split('T')[0]);
    setStartDate(thirtyDaysAgo.toISOString().split('T')[0]);
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // 並行請求 Active Config 和 Experiments
      const [configResponse, experimentsResponse] = await Promise.all([
        axios.get<PolicyActiveConfig>(`${API_BASE_URL}/api/v1/policy/risk-config/active`),
        axios.get<PolicyExperimentHistoryItem[]>(`${API_BASE_URL}/api/v1/policy/experiments/history`, {
          params: {
            start_date: startDate || undefined,
            end_date: endDate || undefined,
            limit: limit,
            order_by: 'timestamp',
          },
        }),
      ]);

      setActiveConfig(configResponse.data);
      setExperiments(experimentsResponse.data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || err.message || 'Failed to load data');
      } else {
        setError('An unexpected error occurred');
      }
      console.error('Failed to fetch policy evolution data:', err);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, limit]);

  useEffect(() => {
    if (startDate && endDate) {
      fetchData();
    }
  }, [fetchData, startDate, endDate]);

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return dateStr;
    }
  };

  const formatRunId = (runId: string) => {
    if (runId.length > 12) {
      return `${runId.substring(0, 8)}...${runId.substring(runId.length - 4)}`;
    }
    return runId;
  };

  const quickDateRange = (days: number) => {
    const today = new Date();
    const pastDate = new Date();
    pastDate.setDate(today.getDate() - days);
    
    setStartDate(pastDate.toISOString().split('T')[0]);
    setEndDate(today.toISOString().split('T')[0]);
  };

  return (
    <div style={{
      border: '1px solid #e0e0e0',
      borderRadius: '8px',
      padding: '16px',
      marginBottom: '20px',
      backgroundColor: '#ffffff',
      boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
    }}>
      <h2 style={{ fontSize: '1.2em', marginBottom: '16px', color: '#333' }}>
        {t("policy_evolution.title", "Policy Evolution")}
      </h2>

      {loading && <p>{t("label.loading", "Loading")}...</p>}
      {error && <p style={{ color: 'red', fontSize: '0.9em', marginBottom: '12px' }}>{error}</p>}

      {/* Active RiskConfig Card */}
      <div style={{
        border: '1px solid #ddd',
        borderRadius: '6px',
        padding: '12px',
        marginBottom: '20px',
        backgroundColor: '#f9f9f9'
      }}>
        <h3 style={{ fontSize: '1em', marginBottom: '10px', color: '#555' }}>
          {t("policy_evolution.active_config", "Active RiskConfig")}
        </h3>
        
        {activeConfig && activeConfig.exists ? (
          <div>
            <div style={{ marginBottom: '8px' }}>
              <strong>{t("policy_evolution.file_path", "File")}:</strong> {activeConfig.file_path}
            </div>
            {activeConfig.run_id && (
              <div style={{ marginBottom: '8px' }}>
                <strong>{t("policy_evolution.run_id", "Run ID")}:</strong> {formatRunId(activeConfig.run_id)}
              </div>
            )}
            {activeConfig.sharpe_ratio !== undefined && (
              <div style={{ marginBottom: '8px' }}>
                <strong>{t("metrics.sharpe_ratio", "Sharpe Ratio")}:</strong> {activeConfig.sharpe_ratio.toFixed(4)}
              </div>
            )}
            <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid #ddd' }}>
              <strong>{t("policy_evolution.config", "Config")}:</strong>
              <ul style={{ marginTop: '5px', paddingLeft: '20px' }}>
                {activeConfig.long_budget !== undefined && (
                  <li>{t("config.long_budget", "Long Budget")}: {(activeConfig.long_budget * 100).toFixed(1)}%</li>
                )}
                {activeConfig.short_budget !== undefined && (
                  <li>{t("config.short_budget", "Short Budget")}: {(activeConfig.short_budget * 100).toFixed(1)}%</li>
                )}
                {activeConfig.max_weight_per_symbol !== undefined && (
                  <li>{t("config.max_weight_per_symbol", "Max Weight/Symbol")}: {(activeConfig.max_weight_per_symbol * 100).toFixed(1)}%</li>
                )}
                {activeConfig.min_score !== undefined && (
                  <li>{t("config.min_score", "Min Score")}: {activeConfig.min_score.toFixed(2)}</li>
                )}
                {activeConfig.allow_short !== undefined && (
                  <li>{t("config.allow_short", "Allow Short")}: {activeConfig.allow_short ? t("label.yes", "Yes") : t("label.no", "No")}</li>
                )}
              </ul>
            </div>
          </div>
        ) : (
          <p style={{ color: '#888', fontStyle: 'italic' }}>
            {t("policy_evolution.no_active_config", "No active RiskConfig found")}
          </p>
        )}
      </div>

      {/* Experiment History Card */}
      <div>
        <h3 style={{ fontSize: '1em', marginBottom: '12px', color: '#555' }}>
          {t("policy_evolution.experiment_history", "Experiment History")}
        </h3>

        {/* Filters */}
        <div style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '12px',
          flexWrap: 'wrap',
          alignItems: 'center'
        }}>
          <label style={{ fontSize: '0.9em', color: '#555' }}>
            {t("label.start_date", "Start Date")}:
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={{
                marginLeft: '4px',
                padding: '4px',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            />
          </label>
          <label style={{ fontSize: '0.9em', color: '#555' }}>
            {t("label.end_date", "End Date")}:
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={{
                marginLeft: '4px',
                padding: '4px',
                border: '1px solid #ccc',
                borderRadius: '4px'
              }}
            />
          </label>
          <div style={{ display: 'flex', gap: '4px' }}>
            <button
              onClick={() => quickDateRange(7)}
              style={{
                padding: '4px 8px',
                fontSize: '0.85em',
                backgroundColor: '#f0f0f0',
                border: '1px solid #ccc',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {t("policy_evolution.last_7_days", "7d")}
            </button>
            <button
              onClick={() => quickDateRange(30)}
              style={{
                padding: '4px 8px',
                fontSize: '0.85em',
                backgroundColor: '#f0f0f0',
                border: '1px solid #ccc',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {t("policy_evolution.last_30_days", "30d")}
            </button>
            <button
              onClick={() => quickDateRange(90)}
              style={{
                padding: '4px 8px',
                fontSize: '0.85em',
                backgroundColor: '#f0f0f0',
                border: '1px solid #ccc',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {t("policy_evolution.last_90_days", "90d")}
            </button>
          </div>
          <button
            onClick={fetchData}
            disabled={loading}
            style={{
              padding: '4px 12px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
              fontSize: '0.9em'
            }}
          >
            {t("label.reload", "Reload")}
          </button>
        </div>

        {/* Table */}
        {experiments.length === 0 ? (
          <p style={{ color: '#888', fontStyle: 'italic', padding: '20px', textAlign: 'center' }}>
            {t("policy_evolution.no_experiments", "No experiments found. Run Policy Loop first.")}
          </p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '0.9em'
            }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
                  <th style={{ padding: '8px', textAlign: 'left' }}>{t("policy_evolution.timestamp", "Timestamp")}</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>{t("policy_evolution.run_id", "Run ID")}</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>{t("metrics.sharpe_ratio", "Sharpe")}</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>{t("metrics.max_drawdown", "MaxDD")}</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>{t("metrics.total_return", "Return")}</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>{t("metrics.score", "Score")}</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>{t("policy_evolution.config", "Config")}</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((exp, idx) => (
                  <tr
                    key={exp.run_id}
                    style={{
                      borderBottom: '1px solid #eee',
                      backgroundColor: idx % 2 === 0 ? '#fff' : '#fafafa'
                    }}
                  >
                    <td style={{ padding: '8px' }}>{formatDate(exp.timestamp)}</td>
                    <td style={{ padding: '8px', fontFamily: 'monospace', fontSize: '0.85em' }}>
                      {formatRunId(exp.run_id)}
                    </td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>{exp.sharpe_ratio.toFixed(4)}</td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>{(exp.max_drawdown * 100).toFixed(2)}%</td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>{(exp.total_return * 100).toFixed(2)}%</td>
                    <td style={{ padding: '8px', textAlign: 'right' }}>{exp.score.toFixed(4)}</td>
                    <td style={{ padding: '8px', fontSize: '0.85em', color: '#666' }}>
                      {exp.long_budget !== undefined && `LB:${(exp.long_budget * 100).toFixed(0)}%`}
                      {exp.short_budget !== undefined && ` SB:${(exp.short_budget * 100).toFixed(0)}%`}
                      {exp.max_weight_per_symbol !== undefined && ` MW:${(exp.max_weight_per_symbol * 100).toFixed(0)}%`}
                      {exp.min_score !== undefined && ` MS:${exp.min_score.toFixed(1)}`}
                      {exp.allow_short !== undefined && (exp.allow_short ? ' SHORT' : ' LONG')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ marginTop: '8px', fontSize: '0.85em', color: '#666' }}>
              {t("policy_evolution.total_experiments", "Total")}: {experiments.length}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

