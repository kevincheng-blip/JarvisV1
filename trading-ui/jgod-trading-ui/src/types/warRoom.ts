/**
 * War Room Data Contract & DTO Types
 * 
 * 定義所有 War Room API 的資料格式
 * 後端必須符合此格式，前端才能順利綁定
 */

// ============================================================================
// 10.1 Top N Long Predictions
// ============================================================================

export interface TopLongItem {
  symbol: string;
  name: string;
  final_score: number;      // Doctrine 修正後
  raw_score: number;        // 純量化分數
  win_prob?: number;        // optional，勝率估計
  risk_level?: 'low' | 'mid' | 'high';
  doctrine_flags: string[]; // ['over_concentration', 'chasing_high', ...]
}

// ============================================================================
// 10.2 Top N Short Predictions
// ============================================================================

export interface TopShortItem {
  symbol: string;
  name: string;
  final_score: number;
  raw_score: number;
  risk_level?: 'low' | 'mid' | 'high';
  doctrine_flags: string[];
}

// ============================================================================
// 10.3 Portfolio Risk
// ============================================================================

export interface PortfolioRisk {
  gross_exposure: number;      // 總曝險 %
  net_exposure: number;        // 多空淨曝險 %
  long_exposure: number;       // 多頭 %
  short_exposure: number;      // 空頭 %
  beta_exposure?: number;      // 對大盤 beta
  var_95?: number;             // Value at Risk(95%)
}

// ============================================================================
// 10.4 Portfolio Exposure
// ============================================================================

export interface ExposureBucket {
  bucket: string;      // e.g. 'Tech', 'Financials', 'SmallCap', 'HighMomentum'
  exposure: number;    // % 或權重
}

export interface ExposureResponse {
  buckets: ExposureBucket[];
}

// ============================================================================
// 10.5 Equity Curve
// ============================================================================

export interface EquityPoint {
  date: string;        // 'YYYY-MM-DD'
  equity: number;      // 淨值
  benchmark_equity?: number; // optional，bench
}

// ============================================================================
// 10.6 Final Orders
// ============================================================================

export interface FinalOrder {
  symbol: string;
  name: string;
  side: 'buy' | 'sell' | 'hold';
  size: number;              // 股數或金額
  confidence: number;        // 0~1
  final_score: number;
  doctrine_flags: string[];  // e.g. ['close_to_limit', 'trend_overextended']
}

// ============================================================================
// 10.7 Signal Conflicts
// ============================================================================

export interface StrategySignal {
  strategy_id: string;       // S1, S2, ...
  signal: 'long' | 'short' | 'neutral';
  score: number;             // 該策略內部分數
}

export interface ConflictItem {
  symbol: string;
  name: string;
  signals: StrategySignal[]; // 各策略對同一檔的看法
  consensus_score: number;   // 0~1，1 = 高共識
  conflict_level: 'none' | 'mild' | 'severe';
}

// ============================================================================
// 10.8 Microstructure Factors
// ============================================================================

export interface MicroFactor {
  symbol: string;
  spread_bps?: number;
  order_imbalance?: number;
  liquidity_score?: number;      // 0~1
  volatility_1d?: number;
  volatility_5d?: number;
}

// ============================================================================
// 10.9 Doctrine Alerts
// ============================================================================

export interface DoctrineAlert {
  id: string;
  symbol: string | null;
  severity: 'info' | 'warning' | 'critical';
  rule_id: string;        // 對應 Doctrine 條文
  message: string;        // 簡短說明
  created_at: string;
}

// ============================================================================
// 10.10 Position Health
// ============================================================================

export interface PositionHealth {
  concentration_risk: number;   // 0~1
  liquidity_risk: number;       // 0~1
  leverage_risk: number;        // 0~1
  comments?: string[];          // 自然語言提示
}

// ============================================================================
// 10.11 Market Sentiment
// ============================================================================

export interface SentimentResponse {
  index_value: number;       // 0~100 (0:極度恐懼,100:極度貪婪)
  label: string;             // '極度恐懼', '中性', '極度貪婪'
  sources?: string[];        // 來源簡述
}

// ============================================================================
// 10.12 System Logs
// ============================================================================

export interface SystemLog {
  id: string;
  level: 'info' | 'warning' | 'error';
  source: string;            // 'PolicyLoop', 'BacktestService', ...
  message: string;
  created_at: string;
}

