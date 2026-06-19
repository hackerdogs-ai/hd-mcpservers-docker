import React, { useEffect, useRef, useImperativeHandle, forwardRef, useState } from 'react';
import { LiveAvatarSession, SessionEvent } from '@heygen/liveavatar-web-sdk';

const TOKEN_URL = 'https://api.liveavatar.com/v1/sessions/token';

const HeyGenAvatar = forwardRef(function HeyGenAvatar({ apiKey, avatarId, width = 200 }, ref) {
  const videoRef = useRef(null);
  const sessionRef = useRef(null);
  const readyRef = useRef(false);
  const [phase, setPhase] = useState('idle'); // idle | connecting | reconnecting | ready | error
  const [errMsg, setErrMsg] = useState('');
  const [sessionKey, setSessionKey] = useState(0); // increment to trigger reconnect

  useImperativeHandle(ref, () => ({
    speak(text) {
      if (!sessionRef.current || !readyRef.current || !text?.trim()) return;
      try {
        sessionRef.current.repeat(text);
      } catch (e) {
        console.warn('[LiveAvatar] speak error:', e);
      }
    },
    interrupt() {
      try { sessionRef.current?.interrupt(); } catch {}
    },
  }));

  useEffect(() => {
    if (!apiKey || !avatarId) return;
    let alive = true;
    readyRef.current = false;

    (async () => {
      setPhase(sessionKey > 0 ? 'reconnecting' : 'connecting');
      setErrMsg('');
      try {
        const res = await fetch(TOKEN_URL, {
          method: 'POST',
          headers: { 'X-API-KEY': apiKey, 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: 'FULL', avatar_id: avatarId, avatar_persona: {} }),
        });
        if (!res.ok) {
          const txt = await res.text().catch(() => '');
          throw new Error(`LiveAvatar ${res.status}: ${txt.slice(0, 180)}`);
        }
        const json = await res.json();
        const token = json.data?.session_token ?? json.session_token;
        if (!token) throw new Error('No session_token in LiveAvatar response');
        if (!alive) return;

        const session = new LiveAvatarSession(token);
        sessionRef.current = session;

        session.on(SessionEvent.SESSION_STREAM_READY, () => {
          if (!alive) return;
          if (videoRef.current) session.attach(videoRef.current);
          readyRef.current = true;
          setPhase('ready');
        });

        session.on(SessionEvent.SESSION_DISCONNECTED, () => {
          if (!alive) return;
          readyRef.current = false;
          // Auto-reconnect after 2s
          setTimeout(() => {
            if (alive) setSessionKey((k) => k + 1);
          }, 2000);
        });

        await session.start();

        // Keep session alive every 15s
        const keepAliveInterval = setInterval(async () => {
          if (!alive || !readyRef.current) return;
          try { await session.keepAlive(); } catch {}
        }, 15000);
        session._keepAliveInterval = keepAliveInterval;
      } catch (err) {
        if (alive) { setPhase('error'); setErrMsg(err.message); }
      }
    })();

    return () => {
      alive = false;
      readyRef.current = false;
      if (sessionRef.current?._keepAliveInterval) {
        clearInterval(sessionRef.current._keepAliveInterval);
      }
      sessionRef.current?.stop().catch(() => {});
      sessionRef.current = null;
    };
  }, [apiKey, avatarId, sessionKey]);

  const height = Math.round(width * 1.35);

  const placeholder = (content) => (
    <div style={{
      width, height, borderRadius: 16, border: '1px solid #30363d',
      background: '#161b22', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: 10, flexShrink: 0,
    }}>
      {content}
    </div>
  );

  if (!apiKey || !avatarId) {
    return placeholder(
      <>
        <span style={{ fontSize: 34 }}>🤖</span>
        <span style={{ fontSize: 11, color: '#8b949e', textAlign: 'center', padding: '0 14px', lineHeight: 1.6 }}>
          Add your HeyGen API key and Avatar ID in Settings to enable the live avatar
        </span>
      </>
    );
  }

  return (
    <div style={{ width, flexShrink: 0, position: 'relative' }}>
      <video
        ref={videoRef}
        autoPlay
        playsInline
        style={{
          width: '100%', height,
          objectFit: 'cover',
          borderRadius: 16,
          background: '#0a0f14',
          display: phase === 'ready' ? 'block' : 'none',
        }}
      />
      {phase !== 'ready' && placeholder(
        (phase === 'connecting' || phase === 'reconnecting') ? (
          <>
            <style>{`@keyframes la-spin { to { transform: rotate(360deg); } }`}</style>
            <div style={{
              width: 30, height: 30, borderRadius: '50%',
              border: '2.5px solid #3fb95033', borderTopColor: '#3fb950',
              animation: 'la-spin 0.75s linear infinite',
            }} />
            <span style={{ fontSize: 12, color: '#8b949e' }}>
              {phase === 'reconnecting' ? 'Reconnecting…' : 'Connecting to avatar…'}
            </span>
          </>
        ) : phase === 'error' ? (
          <>
            <span style={{ fontSize: 26 }}>⚠️</span>
            <span style={{ fontSize: 11, color: '#f85149', textAlign: 'center', padding: '0 12px', lineHeight: 1.5 }}>
              {errMsg}
            </span>
          </>
        ) : (
          <span style={{ fontSize: 34 }}>🤖</span>
        )
      )}
    </div>
  );
});

export default HeyGenAvatar;
