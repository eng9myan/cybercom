"use client";

import { createContext, useContext, useLayoutEffect, useState, useCallback } from "react";

type Theme = "dark" | "light";

interface ThemeContextValue {
  theme: Theme;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({ theme: "dark", toggle: () => {} });

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("dark");

  useLayoutEffect(() => {
    const stored = localStorage.getItem("cy-theme") as Theme | null;
    const preferLight = window.matchMedia("(prefers-color-scheme: light)").matches;
    const resolved: Theme = stored ?? (preferLight ? "light" : "dark");
    applyTheme(resolved);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTheme(resolved);
  }, []);

  const toggle = useCallback(() => {
    setTheme((current) => {
      const next: Theme = current === "dark" ? "light" : "dark";
      localStorage.setItem("cy-theme", next);
      applyTheme(next);
      return next;
    });
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  root.classList.toggle("light", theme === "light");
  root.classList.toggle("dark", theme === "dark");
}

// Inline script to prevent flash — embed in <head> via dangerouslySetInnerHTML
export const themeScript = `
(function(){
  try {
    var t = localStorage.getItem('cy-theme');
    var prefer = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    var theme = t || prefer;
    document.documentElement.classList.toggle('light', theme === 'light');
    document.documentElement.classList.toggle('dark', theme === 'dark');
  } catch(e) {
    document.documentElement.classList.add('dark');
  }
})();
`.trim();
