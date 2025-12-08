"use client";

import { useState, useEffect } from "react";
import { Theme, getTheme, setTheme, THEME_CONFIG } from "@/lib/theme";

export function ThemeToggle() {
  const [currentTheme, setCurrentTheme] = useState<Theme>("dark");

  useEffect(() => {
    const theme = getTheme();
    setCurrentTheme(theme);
    document.documentElement.setAttribute("data-theme", theme);
  }, []);

  const toggleTheme = () => {
    const newTheme: Theme = currentTheme === "dark" ? "ultra-dark" : "dark";
    setTheme(newTheme);
    setCurrentTheme(newTheme);
  };

  return (
    <button
      onClick={toggleTheme}
      className="px-3 py-1.5 rounded-lg bg-gray-800/50 border border-gray-700 text-sm text-gray-300 hover:border-gray-600 transition-colors"
      title={`切換到 ${currentTheme === "dark" ? "Ultra Dark" : "Dark"} 主題`}
    >
      {currentTheme === "dark" ? "🌙 Ultra Dark" : "☀️ Dark"}
    </button>
  );
}

