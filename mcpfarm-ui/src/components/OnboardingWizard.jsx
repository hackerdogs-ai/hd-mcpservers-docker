import React, { useState } from 'react';
import {
  bootstrapAdminSecret,
  reloadRoutes,
  saveSettings,
  verifyAdminSecret,
} from '../lib/api.js';

/**
 * First-run only: shown when the gateway has no admin secret yet.
 * Generate creates the secret; Continue enters the farm.
 * API keys are created later in Settings when needed.
 */
export default function OnboardingWizard({ onComplete }) {
  const [adminSecret, setAdminSecret] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  }

  async function handleGenerate() {
    setError(null);
    setBusy(true);
    try {
      const data = await bootstrapAdminSecret();
      const secret = data.admin_secret;
      setAdminSecret(secret);
      await copyText(secret);
    } catch (e) {
      setError(e.message || 'Failed to generate admin secret');
    } finally {
      setBusy(false);
    }
  }

  async function handleContinue() {
    const secret = adminSecret.trim();
    if (!secret) {
      setError('Generate or enter an admin secret to continue.');
      return;
    }
    setError(null);
    setBusy(true);
    try {
      try {
        await bootstrapAdminSecret(secret);
      } catch (e) {
        if (!String(e.message).includes('already configured')) throw e;
      }
      await verifyAdminSecret(secret);
      saveSettings({ adminSecret: secret });

      try {
        await reloadRoutes();
      } catch {
        /* routes may already be loaded; non-fatal */
      }

      localStorage.setItem('hd_setup_complete', '1');
      onComplete({ adminSecret: secret });
    } catch (e) {
      setError(e.message || 'Could not complete setup');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="hd-modal-overlay" style={{ position: 'fixed', inset: 0 }}>
      <div className="hd-modal" style={{ maxWidth: 480 }} role="dialog" aria-labelledby="setup-title">
        <div className="hd-modal__head">
          <h2 id="setup-title" className="hd-modal__title">
            Welcome — create your admin secret
          </h2>
        </div>

        <div className="hd-modal__body space-y-4">
          <p className="text-sm" style={{ opacity: 0.85 }}>
            Before you use the farm, create an admin secret. This unlocks
            start/stop, Settings, and API key management — no need to set it on
            the command line. Store it somewhere safe.
          </p>
          <div>
            <label className="hd-label" htmlFor="setup-admin-secret">
              Admin secret
            </label>
            <div className="flex gap-2">
              <input
                id="setup-admin-secret"
                type="text"
                autoComplete="off"
                spellCheck={false}
                value={adminSecret}
                onChange={(e) => setAdminSecret(e.target.value)}
                placeholder="Click Generate, or type your own (min 16 chars)"
                className="hd-input flex-1 text-sm font-mono"
              />
              <button
                type="button"
                className="hd-btn hd-btn--secondary whitespace-nowrap"
                disabled={busy}
                onClick={handleGenerate}
              >
                {busy ? '…' : copied ? 'Copied' : 'Generate'}
              </button>
            </div>
          </div>
          {error && (
            <p className="text-xs hd-text-err" role="alert">
              {error}
            </p>
          )}
        </div>

        <div className="hd-modal__foot" style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="button"
            className="hd-btn hd-btn--primary"
            disabled={busy || !adminSecret.trim()}
            onClick={handleContinue}
          >
            {busy ? 'Setting up…' : 'Continue'}
          </button>
        </div>
      </div>
    </div>
  );
}
