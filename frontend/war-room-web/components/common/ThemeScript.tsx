"use client";

import { useEffect } from "react";
import { getTheme } from "@/lib/theme";

export function ThemeScript() {
  useEffect(() => {
    // 初始化主題
    const theme = getTheme();
    document.documentElement.setAttribute("data-theme", theme);
  }, []);

  return null;
}

