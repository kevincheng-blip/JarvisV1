/**
 * Universe API
 * 
 * Fetch universe stocks list from backend
 */

import axios from "axios";

export interface UniverseStock {
  symbol: string;
  name?: string;
  score_coverage?: number;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch universe stocks from coverage API
 * 
 * Uses /api/universe/coverage endpoint to get all stocks.
 * Falls back to mock data if API fails.
 */
export async function fetchUniverseStocks(): Promise<UniverseStock[]> {
  try {
    // Use coverage endpoint with a recent date range to get all stocks
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 90); // Last 90 days

    const response = await client.get("/api/universe/coverage", {
      params: {
        start_date: startDate.toISOString().split("T")[0],
        end_date: endDate.toISOString().split("T")[0],
      },
    });

    // Map CoverageItem to UniverseStock
    const items = response.data.items || [];
    return items.map((item: any) => ({
      symbol: item.symbol || "",
      name: item.name || undefined,
      score_coverage: item.coverage || undefined,
    }));
  } catch (error) {
    console.error("Error fetching universe stocks from API:", error);
    
    // Fallback to mock data
    console.warn("Falling back to mock universe stocks");
    return [
      { symbol: "2330", name: "台積電" },
      { symbol: "2317", name: "鴻海" },
      { symbol: "2454", name: "聯發科" },
      { symbol: "2603", name: "長榮" },
      { symbol: "2412", name: "中華電" },
      { symbol: "2308", name: "台達電" },
      { symbol: "2882", name: "國泰金" },
      { symbol: "2891", name: "中信金" },
      { symbol: "2881", name: "富邦金" },
      { symbol: "1301", name: "台塑" },
    ];
  }
}

