// categories.js — Category definitions, colors, and icon generation

import { getCurrentTheme } from './theme.js';

function isLightTheme() {
  return getCurrentTheme() === 'light';
}

function resolveCatColors(dark, light) {
  const lightMode = isLightTheme();
  const color = lightMode ? light : dark;
  const bgMix = lightMode ? 22 : 12;
  const borderMix = lightMode ? 48 : 30;
  return {
    color,
    bg: `color-mix(in srgb, ${color} ${bgMix}%, transparent)`,
    border: `color-mix(in srgb, ${color} ${borderMix}%, transparent)`,
  };
}

const CATEGORY_DEFS = {
  'core':            { label: 'Core',            dark: '#6eceda', light: '#0e7490' },
  'network-recon':   { label: 'Network Recon',   dark: '#58a6ff', light: '#1d4ed8' },
  'web-app':         { label: 'Web App',         dark: '#bc8cff', light: '#6d28d9' },
  'appsec':          { label: 'AppSec',          dark: '#9b8afb', light: '#4338ca' },
  'osint':           { label: 'OSINT',           dark: '#b19cd9', light: '#7c3aed' },
  'vuln-scanning':   { label: 'Vuln Scanning',   dark: '#da77f2', light: '#86198f' },
  'binary-re':       { label: 'Binary RE',       dark: '#f778ba', light: '#be185d' },
  'cloud-container': { label: 'Cloud',           dark: '#79c0ff', light: '#0369a1' },
  'exploitation':    { label: 'Exploitation',    dark: '#e091d4', light: '#7e22ce' },
  'network-attacks': { label: 'Net Attacks',     dark: '#8892ff', light: '#3730a3' },
  'misc':            { label: 'Misc',            dark: '#8b949e', light: '#4b5563' },
};

export const ALL_CATEGORIES = Object.keys(CATEGORY_DEFS);

export function getCategoryInfo(cat) {
  const def = CATEGORY_DEFS[cat] || CATEGORY_DEFS.misc;
  return { label: def.label, ...resolveCatColors(def.dark, def.light) };
}

const STATUS_PALETTE = {
  dark: {
    disabled:  { color: '#f85149', dot: '#f85149' },
    stopped:   { color: '#8b949e', dot: '#484f58' },
    running:   { color: '#3fb950', dot: '#3fb950' },
    unhealthy: { color: '#d29922', dot: '#d29922' },
  },
  light: {
    disabled:  { color: '#b91c1c', dot: '#dc2626' },
    stopped:   { color: '#4b5563', dot: '#374151' },
    running:   { color: '#15803d', dot: '#16a34a' },
    unhealthy: { color: '#b45309', dot: '#d97706' },
  },
};

function statusColors(key) {
  const palette = isLightTheme() ? STATUS_PALETTE.light : STATUS_PALETTE.dark;
  return palette[key];
}

export function isServerRunning(server) {
  if (!server) return false;
  const s = (server.status || '').toLowerCase();
  if (s === 'disabled' || s === 'stopped') return false;
  return server.health_ok === true;
}

export function getStatusInfo(server) {
  const s = (server.status || '').toLowerCase();
  if (s === 'disabled') return { label: 'Disabled', ...statusColors('disabled') };
  if (s === 'stopped') return { label: 'Stopped', ...statusColors('stopped') };
  if (server.health_ok) return { label: 'Running', ...statusColors('running') };
  if (s === 'running') return { label: 'Unhealthy', ...statusColors('unhealthy') };
  return { label: 'Stopped', ...statusColors('stopped') };
}

const INTERNAL_ENV_KEYS = new Set(['MCP_TRANSPORT', 'MCP_PORT']);

export function getRequiredEnvKeys(server) {
  const env = server?.env;
  if (!env) return [];
  let envObj;
  try {
    envObj = typeof env === 'string' ? JSON.parse(env) : env;
  } catch {
    return [];
  }
  return Object.keys(envObj).filter(k => !INTERNAL_ENV_KEYS.has(k));
}

export function serverRequiresKey(server) {
  return getRequiredEnvKeys(server).length > 0;
}

function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

export function getServerAbbrev(name) {
  const clean = name.replace(/-mcp$/, '').replace(/-/g, ' ');
  const words = clean.split(' ').filter(Boolean);
  if (words.length === 1) {
    return words[0].slice(0, 3).toUpperCase();
  }
  return words.slice(0, 3).map(w => w[0]).join('').toUpperCase();
}

export function generateServerIcon(name, category, size = 40) {
  const cat = getCategoryInfo(category);
  const abbrev = getServerAbbrev(name);
  const h = hashCode(name);
  const patternIndex = h % 4;
  const strokeOpacity = isLightTheme() ? 0.28 : 0.15;
  const fillOpacity = isLightTheme() ? 0.2 : 0.1;

  const patterns = [
    `<circle cx="${size/2}" cy="${size/2}" r="${size*0.38}" fill="none" stroke="${cat.color}" stroke-opacity="${strokeOpacity}" stroke-width="1"/>`,
    `<rect x="${size*0.15}" y="${size*0.15}" width="${size*0.7}" height="${size*0.7}" rx="${size*0.12}" fill="none" stroke="${cat.color}" stroke-opacity="${strokeOpacity}" stroke-width="1"/>`,
    `<line x1="${size*0.2}" y1="${size*0.8}" x2="${size*0.8}" y2="${size*0.2}" stroke="${cat.color}" stroke-opacity="${strokeOpacity * 0.7}" stroke-width="1"/>`,
    `<circle cx="${size*0.3}" cy="${size*0.7}" r="${size*0.08}" fill="${cat.color}" fill-opacity="${fillOpacity}"/><circle cx="${size*0.7}" cy="${size*0.3}" r="${size*0.08}" fill="${cat.color}" fill-opacity="${fillOpacity}"/>`,
  ];

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <rect width="${size}" height="${size}" rx="${size*0.2}" fill="${cat.bg}"/>
    ${patterns[patternIndex]}
    <text x="${size/2}" y="${size/2}" text-anchor="middle" dominant-baseline="central" fill="${cat.color}" font-family="system-ui,-apple-system,sans-serif" font-weight="600" font-size="${size * (abbrev.length > 2 ? 0.28 : 0.32)}">${abbrev}</text>
  </svg>`;
}

export function getServerDescription(name) {
  const n = name.replace(/-mcp$/, '');
  const descriptions = {
    'nmap': 'Network exploration and port scanning',
    'whois': 'Domain registration and WHOIS lookup',
    'nuclei': 'Fast vulnerability scanner with templates',
    'shodan': 'Internet-connected device search engine',
    'amass': 'Attack surface mapping and asset discovery',
    'subfinder': 'Passive subdomain discovery tool',
    'httpx': 'Fast HTTP probing and analysis',
    'naabu': 'Fast port scanning with SYN/CONNECT',
    'katana': 'Next-gen web crawling framework',
    'dnsx': 'Fast DNS toolkit for lookups and bruteforce',
    'sqlmap': 'Automatic SQL injection detection and exploitation',
    'gobuster': 'Directory and DNS bruteforce scanner',
    'ffuf': 'Fast web fuzzer for content discovery',
    'nikto': 'Web server vulnerability scanner',
    'masscan': 'Internet-scale port scanner',
    'feroxbuster': 'Recursive content discovery tool',
    'metasploit': 'Penetration testing framework',
    'hydra': 'Network authentication cracker',
    'hashcat': 'Advanced password recovery',
    'john': 'Password cracking utility',
    'rustscan': 'Fast port scanner in Rust',
    'whatweb': 'Web technology identification',
    'wapiti': 'Web application vulnerability scanner',
    'spiderfoot': 'OSINT automation tool',
    'theharvester': 'Email, subdomain, and name harvesting',
    'prowler': 'AWS/Azure/GCP security assessments',
    'scout-suite': 'Multi-cloud security auditing',
    'trivy': 'Container vulnerability scanner',
    'grype': 'Container image vulnerability scanner',
    'syft': 'Software bill of materials generator',
    'bandit': 'Python security linter',
    'semgrep': 'Lightweight static analysis',
    'gitleaks': 'Secret detection in git repos',
    'trufflehog': 'Credential scanner for git repos',
    'wireshark': 'Network protocol analyzer',
    'tcpdump': 'Command-line packet analyzer',
    'burp': 'Web security testing platform',
    'zap': 'Web app security scanner (OWASP)',
    'bloodhound': 'Active Directory attack path mapping',
    'certipy': 'Active Directory certificate abuse',
    'responder': 'LLMNR/NBT-NS/mDNS poisoner',
    'impacket': 'Network protocol toolkit',
    'crackmapexec': 'Network information gathering',
    'terraform': 'Infrastructure as code tool',
    'docker-scout': 'Docker image analysis',
    'cloudmapper': 'Cloud infrastructure visualization',
    'pacu': 'AWS exploitation framework',
    'cloudlist': 'Multi-cloud asset enumeration',
  };
  return descriptions[n] || `${n.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} MCP server`;
}
