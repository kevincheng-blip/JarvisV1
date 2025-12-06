/**
 * Smart Watchlist Component
 * 
 * 智能自選股列表，支援收藏和最近使用記錄
 */

import { useEffect, useState, useMemo } from "react";
import { fetchUniverseStocks, type UniverseStock } from "../api/universeApi";

interface SmartWatchlistProps {
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
}

const STORAGE_KEYS = {
  FAVORITES: "jgod_favorite_symbols",
  RECENTS: "jgod_recent_symbols",
};

const MAX_RECENTS = 20;

export function SmartWatchlist({
  selectedSymbol,
  onSelectSymbol,
}: SmartWatchlistProps) {
  const [allStocks, setAllStocks] = useState<UniverseStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [recents, setRecents] = useState<string[]>([]);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const favsJson = localStorage.getItem(STORAGE_KEYS.FAVORITES);
      const recentsJson = localStorage.getItem(STORAGE_KEYS.RECENTS);
      
      if (favsJson) {
        const favs = JSON.parse(favsJson);
        if (Array.isArray(favs)) {
          setFavorites(favs);
        }
      }
      
      if (recentsJson) {
        const recs = JSON.parse(recentsJson);
        if (Array.isArray(recs)) {
          setRecents(recs);
        }
      }
    } catch (err) {
      console.error("Error loading from localStorage:", err);
    }
  }, []);

  // Fetch universe stocks
  useEffect(() => {
    const loadStocks = async () => {
      setLoading(true);
      setError(null);
      try {
        const stocks = await fetchUniverseStocks();
        setAllStocks(stocks);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "載入股票列表失敗";
        setError(errorMessage);
        console.error("Error loading universe stocks:", err);
      } finally {
        setLoading(false);
      }
    };

    loadStocks();
  }, []);

  // Handle symbol selection
  const handleSelectSymbol = (symbol: string) => {
    onSelectSymbol(symbol);

    // Update recents
    setRecents((prev) => {
      const filtered = prev.filter((s) => s !== symbol);
      const updated = [symbol, ...filtered].slice(0, MAX_RECENTS);
      
      // Save to localStorage
      try {
        localStorage.setItem(STORAGE_KEYS.RECENTS, JSON.stringify(updated));
      } catch (err) {
        console.error("Error saving recents to localStorage:", err);
      }
      
      return updated;
    });
  };

  // Handle favorite toggle
  const handleToggleFavorite = (symbol: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering symbol selection

    setFavorites((prev) => {
      const isFavorite = prev.includes(symbol);
      const updated = isFavorite
        ? prev.filter((s) => s !== symbol)
        : [...prev, symbol];

      // Save to localStorage
      try {
        localStorage.setItem(STORAGE_KEYS.FAVORITES, JSON.stringify(updated));
      } catch (err) {
        console.error("Error saving favorites to localStorage:", err);
      }

      return updated;
    });
  };

  // Organize stocks into groups
  const { favoriteStocks, recentStocks, otherStocks } = useMemo(() => {
    const favoriteSet = new Set(favorites);
    const recentSet = new Set(recents);
    
    // Combine favorites and recents (favorites first, then recents)
    const favoriteAndRecent = [
      ...favorites.map((sym) => allStocks.find((s) => s.symbol === sym)).filter(Boolean),
      ...recents
        .filter((sym) => !favoriteSet.has(sym))
        .map((sym) => allStocks.find((s) => s.symbol === sym))
        .filter(Boolean),
    ] as UniverseStock[];

    // Other stocks (not in favorites or recents)
    const other = allStocks.filter(
      (stock) => !favoriteSet.has(stock.symbol) && !recentSet.has(stock.symbol)
    );

    return {
      favoriteStocks: favoriteAndRecent,
      recentStocks: [], // Already included in favoriteAndRecent
      otherStocks: other,
    };
  }, [allStocks, favorites, recents]);

  if (loading) {
    return (
      <div style={{ padding: "16px", border: "1px solid #ccc", borderRadius: "8px" }}>
        <h3>Smart Watchlist</h3>
        <div>載入中…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "16px", border: "1px solid #ccc", borderRadius: "8px" }}>
        <h3>Smart Watchlist</h3>
        <div style={{ color: "red" }}>載入失敗: {error}</div>
      </div>
    );
  }

  const renderStockItem = (stock: UniverseStock) => {
    const isSelected = stock.symbol === selectedSymbol;
    const isFavorite = favorites.includes(stock.symbol);
    const displayName = stock.name ? `${stock.symbol} ${stock.name}` : stock.symbol;

    return (
      <div
        key={stock.symbol}
        onClick={() => handleSelectSymbol(stock.symbol)}
        style={{
          padding: "8px 12px",
          cursor: "pointer",
          backgroundColor: isSelected ? "#e3f2fd" : "transparent",
          borderLeft: isSelected ? "4px solid #2196f3" : "4px solid transparent",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "2px",
          borderRadius: "4px",
          transition: "background-color 0.2s",
        }}
        onMouseEnter={(e) => {
          if (!isSelected) {
            e.currentTarget.style.backgroundColor = "#f5f5f5";
          }
        }}
        onMouseLeave={(e) => {
          if (!isSelected) {
            e.currentTarget.style.backgroundColor = "transparent";
          }
        }}
      >
        <span style={{ fontWeight: isSelected ? "bold" : "normal" }}>
          {displayName}
        </span>
        <button
          onClick={(e) => handleToggleFavorite(stock.symbol, e)}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontSize: "18px",
            padding: "0 4px",
            color: isFavorite ? "#ffd700" : "#ccc",
          }}
          title={isFavorite ? "取消收藏" : "加入收藏"}
        >
          {isFavorite ? "★" : "☆"}
        </button>
      </div>
    );
  };

  return (
    <div style={{ padding: "16px", border: "1px solid #ccc", borderRadius: "8px" }}>
      <h3>Smart Watchlist</h3>

      {favoriteStocks.length > 0 && (
        <div style={{ marginTop: "16px" }}>
          <div
            style={{
              fontSize: "12px",
              color: "#666",
              fontWeight: "bold",
              marginBottom: "8px",
            }}
          >
            常用 / 收藏 (Favorites & Recent)
          </div>
          {favoriteStocks.map(renderStockItem)}
        </div>
      )}

      {otherStocks.length > 0 && (
        <div style={{ marginTop: "16px" }}>
          <div
            style={{
              fontSize: "12px",
              color: "#666",
              fontWeight: "bold",
              marginBottom: "8px",
            }}
          >
            全部股票 (All)
          </div>
          {otherStocks.map(renderStockItem)}
        </div>
      )}

      {allStocks.length === 0 && (
        <div style={{ marginTop: "16px", color: "#666" }}>
          目前沒有可用的股票列表
        </div>
      )}
    </div>
  );
}

