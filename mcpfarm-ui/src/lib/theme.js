/** Theme helpers — follows worldmonitor-main theme-manager conventions. */

import { useState, useEffect } from 'react';

export const STORAGE_KEY = 'worldmonitor-theme';
const DEFAULT_THEME = 'dark';

/** @typedef {'dark' | 'light'} Theme */

/** @returns {Theme} */
export function getCurrentTheme() {
  const value = document.documentElement.dataset.theme;
  if (value === 'dark' || value === 'light') return value;
  return DEFAULT_THEME;
}

/** @returns {Theme} */
export function getStoredTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'dark' || stored === 'light') return stored;
  } catch {
    /* localStorage unavailable */
  }
  return DEFAULT_THEME;
}

/** @param {Theme} theme */
export function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    /* localStorage unavailable */
  }
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.content = theme === 'dark' ? '#212121' : '#ffffff';
  }
  window.dispatchEvent(new CustomEvent('theme-changed', { detail: { theme } }));
}

/** Re-render when the document theme changes. */
export function useTheme() {
  const [theme, setThemeState] = useState(getCurrentTheme);
  useEffect(() => {
    const onThemeChanged = () => setThemeState(getCurrentTheme());
    window.addEventListener('theme-changed', onThemeChanged);
    return () => window.removeEventListener('theme-changed', onThemeChanged);
  }, []);
  return theme;
}

/** Apply stored theme before React mounts (FOUC safety net). */
export function applyStoredTheme() {
  const theme = getStoredTheme();
  document.documentElement.dataset.theme = theme;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.content = theme === 'dark' ? '#212121' : '#ffffff';
  }
}
