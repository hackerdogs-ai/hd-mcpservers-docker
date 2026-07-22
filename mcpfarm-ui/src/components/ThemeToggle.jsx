import React, { useState, useEffect } from 'react';
import { getCurrentTheme, setTheme } from '../lib/theme.js';
import Icon from './Icon.jsx';

export default function ThemeToggle() {
  const [theme, setThemeState] = useState(getCurrentTheme);

  useEffect(() => {
    const onThemeChanged = () => setThemeState(getCurrentTheme());
    window.addEventListener('theme-changed', onThemeChanged);
    return () => window.removeEventListener('theme-changed', onThemeChanged);
  }, []);

  function toggle() {
    const next = getCurrentTheme() === 'dark' ? 'light' : 'dark';
    setTheme(next);
    setThemeState(next);
  }

  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      className="theme-toggle-btn"
      id="headerThemeToggle"
      title={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      onClick={toggle}
    >
      <Icon name={isDark ? 'light_mode' : 'dark_mode'} size={18} />
    </button>
  );
}
