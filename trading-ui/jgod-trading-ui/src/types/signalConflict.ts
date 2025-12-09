/**
 * Signal Conflict Types
 * 
 * TypeScript type definitions for signal conflict and consensus analysis.
 */

export type SignalConflictItem = {
  symbol: string;
  name: string;
  consensus_score: number;  // 0-100
  conflict_score: number;   // 0-100
  majority_vote: 1 | -1 | 0;  // 1: long, -1: short, 0: neutral
  strategy_votes: Record<string, -1 | 0 | 1>;  // {"S1": 1, "S2": -1, ...}
  raw_score?: number | null;
  final_score?: number | null;
};

