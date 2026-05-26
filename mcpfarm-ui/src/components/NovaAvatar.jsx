import React from 'react';

/**
 * Animated SVG robot avatar for Nova.
 * state: 'idle' | 'thinking' | 'talking'
 */
export default function NovaAvatar({ state = 'idle', size = 140 }) {
  return (
    <div style={{ width: size, height: size, flexShrink: 0 }}>
      <style>{`
        @keyframes nova-blink {
          0%, 88%, 100% { transform: scaleY(1); }
          93% { transform: scaleY(0.08); }
        }
        @keyframes nova-breathe {
          0%, 100% { opacity: 0.7; }
          50% { opacity: 1; }
        }
        @keyframes nova-glow-pulse {
          0%, 100% { filter: drop-shadow(0 0 4px #3fb950) drop-shadow(0 0 8px #3fb95044); }
          50% { filter: drop-shadow(0 0 10px #3fb950) drop-shadow(0 0 20px #3fb95066); }
        }
        @keyframes nova-scan {
          0%, 100% { transform: translateX(0); }
          30% { transform: translateX(-5px); }
          70% { transform: translateX(5px); }
        }
        @keyframes nova-spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes nova-spin-rev {
          from { transform: rotate(0deg); }
          to { transform: rotate(-360deg); }
        }
        @keyframes nova-talk-bar {
          0%, 100% { transform: scaleY(0.3); }
          50% { transform: scaleY(1); }
        }
        @keyframes nova-antenna-pulse {
          0%, 100% { r: 3.5; opacity: 1; }
          50% { r: 5; opacity: 0.6; }
        }
        @keyframes nova-circuit-flash {
          0%, 90%, 100% { opacity: 0.15; }
          95% { opacity: 0.6; }
        }
        @keyframes nova-think-dot {
          0%, 100% { opacity: 0.2; }
          50% { opacity: 1; }
        }
      `}</style>

      <svg
        viewBox="0 0 100 115"
        width={size}
        height={size}
        style={{
          animation: 'nova-glow-pulse 3s ease-in-out infinite',
          filter: 'drop-shadow(0 0 6px #3fb95066)',
        }}
      >
        <defs>
          <radialGradient id="nova-eye-grad" cx="50%" cy="50%">
            <stop offset="0%" stopColor="#7ee787" />
            <stop offset="100%" stopColor="#3fb950" />
          </radialGradient>
          <radialGradient id="nova-head-grad" cx="50%" cy="30%">
            <stop offset="0%" stopColor="#1c2128" />
            <stop offset="100%" stopColor="#0d1117" />
          </radialGradient>
        </defs>

        {/* ── Outer spinning rings (thinking only) ── */}
        {state === 'thinking' && (
          <>
            <circle
              cx="50" cy="63" r="46"
              fill="none" stroke="#3fb950" strokeWidth="1"
              strokeDasharray="12 8"
              style={{ animation: 'nova-spin 3s linear infinite', transformOrigin: '50px 63px', opacity: 0.35 }}
            />
            <circle
              cx="50" cy="63" r="42"
              fill="none" stroke="#3fb950" strokeWidth="0.5"
              strokeDasharray="6 14"
              style={{ animation: 'nova-spin-rev 2s linear infinite', transformOrigin: '50px 63px', opacity: 0.25 }}
            />
          </>
        )}

        {/* ── Antenna ── */}
        <line x1="50" y1="20" x2="50" y2="6" stroke="#3fb950" strokeWidth="1.5" opacity="0.8" />
        <line x1="50" y1="12" x2="44" y2="7" stroke="#3fb950" strokeWidth="1" opacity="0.5" />
        <line x1="50" y1="12" x2="56" y2="7" stroke="#3fb950" strokeWidth="1" opacity="0.5" />
        <circle
          cx="50" cy="5" r="3.5" fill="#3fb950"
          style={{ animation: 'nova-antenna-pulse 1.5s ease-in-out infinite' }}
        />

        {/* ── Ear panels ── */}
        <rect x="11" y="38" width="6" height="22" rx="3" fill="#0d1117" stroke="#3fb950" strokeWidth="1" opacity="0.6" />
        <rect x="83" y="38" width="6" height="22" rx="3" fill="#0d1117" stroke="#3fb950" strokeWidth="1" opacity="0.6" />
        <rect x="12.5" y="43" width="3" height="3" rx="1" fill="#3fb950" opacity="0.5" />
        <rect x="84.5" y="43" width="3" height="3" rx="1" fill="#3fb950" opacity="0.5" />
        <rect x="12.5" y="49" width="3" height="3" rx="1" fill="#3fb950" opacity="0.3" />
        <rect x="84.5" y="49" width="3" height="3" rx="1" fill="#3fb950" opacity="0.3" />

        {/* ── Head ── */}
        <rect x="17" y="18" width="66" height="82" rx="14" fill="url(#nova-head-grad)" stroke="#3fb950" strokeWidth="1.5" />

        {/* ── Circuit traces on head ── */}
        <path d="M17 45 h8 v-7 h6 v3 h4" fill="none" stroke="#3fb950" strokeWidth="0.6"
          style={{ animation: 'nova-circuit-flash 5s ease-in-out infinite', opacity: 0.15 }} />
        <path d="M83 55 h-8 v7 h-5 v-3 h-4" fill="none" stroke="#3fb950" strokeWidth="0.6"
          style={{ animation: 'nova-circuit-flash 5s ease-in-out 2.5s infinite', opacity: 0.15 }} />
        <circle cx="29" cy="38" r="1.5" fill="#3fb950" opacity="0.2" />
        <circle cx="71" cy="72" r="1.5" fill="#3fb950" opacity="0.2" />
        <circle cx="71" cy="38" r="1.5" fill="#3fb950" opacity="0.2" />

        {/* ── Eye visor background ── */}
        <rect x="22" y="34" width="56" height="22" rx="6" fill="#0a0f14" stroke="#3fb95033" strokeWidth="1" />

        {/* ── Eyes (move for scan, blink for idle) ── */}
        <g style={state === 'thinking'
          ? { animation: 'nova-scan 1.8s ease-in-out infinite', transform: 'translateX(0)' }
          : {}
        }>
          {/* Left eye */}
          <rect
            x="26" y="38" width="20" height="13" rx="4"
            fill="url(#nova-eye-grad)"
            style={{
              transformBox: 'fill-box',
              transformOrigin: 'center',
              animation: state === 'idle' ? 'nova-blink 4s ease-in-out infinite' : 'none',
            }}
          />
          {/* Right eye */}
          <rect
            x="54" y="38" width="20" height="13" rx="4"
            fill="url(#nova-eye-grad)"
            style={{
              transformBox: 'fill-box',
              transformOrigin: 'center',
              animation: state === 'idle' ? 'nova-blink 4s ease-in-out 0.08s infinite' : 'none',
            }}
          />
          {/* Eye shine */}
          <rect x="30" y="40" width="5" height="4" rx="2" fill="#fff" opacity="0.25" />
          <rect x="58" y="40" width="5" height="4" rx="2" fill="#fff" opacity="0.25" />
        </g>

        {/* ── Nose ── */}
        <circle cx="50" cy="62" r="1.8" fill="#3fb950" opacity="0.45" />

        {/* ── Mouth ── */}
        <rect x="27" y="68" width="46" height="12" rx="6" fill="#0a0f14" stroke="#3fb950" strokeWidth="1" opacity="0.8" />

        {state === 'talking' ? (
          /* Animated speaker bars when talking */
          [0, 1, 2, 3, 4, 5].map((i) => (
            <rect
              key={i}
              x={31 + i * 7} y="70"
              width="4" height="8" rx="2"
              fill="#3fb950"
              style={{
                transformBox: 'fill-box',
                transformOrigin: 'center bottom',
                animation: `nova-talk-bar 0.35s ease-in-out ${i * 0.05}s infinite`,
              }}
            />
          ))
        ) : (
          /* Static dots when idle/thinking */
          [0, 1, 2, 3, 4, 5].map((i) => (
            <rect key={i} x={31 + i * 7} y="72" width="4" height="4" rx="2"
              fill="#3fb950" opacity={state === 'thinking' ? 0.6 : 0.3}
              style={state === 'thinking' ? {
                animation: `nova-think-dot 0.8s ease-in-out ${i * 0.13}s infinite`,
              } : {}}
            />
          ))
        )}

        {/* ── Chin bolts ── */}
        <circle cx="23" cy="90" r="2.5" fill="none" stroke="#3fb950" strokeWidth="1" opacity="0.45" />
        <circle cx="77" cy="90" r="2.5" fill="none" stroke="#3fb950" strokeWidth="1" opacity="0.45" />
        <circle cx="23" cy="90" r="1" fill="#3fb950" opacity="0.4" />
        <circle cx="77" cy="90" r="1" fill="#3fb950" opacity="0.4" />

        {/* ── Status bar ── */}
        <rect x="30" y="96" width="40" height="2.5" rx="1.25" fill="#161b22" />
        <rect
          x="30" y="96"
          width={state === 'idle' ? 40 : state === 'thinking' ? 22 : 38}
          height="2.5" rx="1.25" fill="#3fb950"
          style={
            state === 'thinking'
              ? { animation: 'nova-talk-bar 1s ease-in-out infinite', transformBox: 'fill-box', transformOrigin: 'left center' }
              : {}
          }
        />

        {/* ── Neck ── */}
        <rect x="40" y="100" width="20" height="8" rx="3" fill="#0d1117" stroke="#3fb950" strokeWidth="1" opacity="0.6" />
        <rect x="43" y="102" width="4" height="4" rx="1" fill="#3fb950" opacity="0.3" />
        <rect x="53" y="102" width="4" height="4" rx="1" fill="#3fb950" opacity="0.3" />
      </svg>
    </div>
  );
}
