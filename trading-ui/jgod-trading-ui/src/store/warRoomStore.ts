/**
 * War Room Zustand Store
 * 
 * 全域狀態管理，所有 War Room Widget 共用
 * 
 * Schema 定義：
 * - selectedRunId: 選中的 Policy Experiment Run ID
 * - selectedSymbol: 選中的股票代號
 * - selectedErrorId: 選中的錯誤 ID（用於 Error Replay）
 * - dateRange: 日期範圍篩選
 */

import { create } from 'zustand';

export interface WarRoomState {
  // Selected Run ID (for Policy experiments)
  selectedRunId: string | null;
  setSelectedRunId: (id: string | null) => void;

  // Selected Symbol (for stock analysis)
  selectedSymbol: string | null;
  setSelectedSymbol: (symbol: string | null) => void;

  // Selected Error ID (for Error Replay)
  selectedErrorId: string | null;
  setSelectedErrorId: (errorId: string | null) => void;

  // Date Range Filter
  dateRange: { start: string; end: string };
  setDateRange: (start: string, end: string) => void;
}

export const useWarRoomStore = create<WarRoomState>((set) => ({
  // Initial state
  selectedRunId: null,
  selectedSymbol: null,
  selectedErrorId: null,
  dateRange: {
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days ago
    end: new Date().toISOString().split('T')[0], // today
  },

  // Actions
  setSelectedRunId: (id: string | null) => set({ selectedRunId: id }),
  setSelectedSymbol: (symbol: string | null) => set({ selectedSymbol: symbol }),
  setSelectedErrorId: (errorId: string | null) => set({ selectedErrorId: errorId }),
  setDateRange: (start: string, end: string) => set({ dateRange: { start, end } }),
}));

