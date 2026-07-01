// categories.js — Category definitions, colors, and icon generation

function catColors(color) {
  return {
    color,
    bg: `color-mix(in srgb, ${color} 12%, transparent)`,
    border: `color-mix(in srgb, ${color} 30%, transparent)`,
  };
}

export const CATEGORIES = {
  'core':            { label: 'Core',            ...catColors('#3fb950') },
  'network-recon':   { label: 'Network Recon',   ...catColors('#58a6ff') },
  'web-app':         { label: 'Web App',         ...catColors('#bc8cff') },
  'appsec':          { label: 'AppSec',          ...catColors('#f0883e') },
  'osint':           { label: 'OSINT',           ...catColors('#d29922') },
  'vuln-scanning':   { label: 'Vuln Scanning',   ...catColors('#f85149') },
  'binary-re':       { label: 'Binary RE',       ...catColors('#f778ba') },
  'cloud-container': { label: 'Cloud',           ...catColors('#79c0ff') },
  'exploitation':    { label: 'Exploitation',    ...catColors('#ff7b72') },
  'network-attacks': { label: 'Net Attacks',     ...catColors('#e3b341') },
  'misc':            { label: 'Misc',            ...catColors('#8b949e') },
};

export const ALL_CATEGORIES = Object.keys(CATEGORIES);

export function getCategoryInfo(cat) {
  return CATEGORIES[cat] || CATEGORIES['misc'];
}

export function isServerRunning(server) {
  if (!server) return false;
  const s = (server.status || '').toLowerCase();
  if (s === 'disabled' || s === 'stopped') return false;
  return server.health_ok === true;
}

export function getStatusInfo(server) {
  const s = (server.status || '').toLowerCase();
  if (s === 'disabled') return { label: 'Disabled', color: '#f85149', dot: '#f85149' };
  if (s === 'stopped') return { label: 'Stopped', color: '#8b949e', dot: '#484f58' };
  if (server.health_ok) return { label: 'Running', color: '#3fb950', dot: '#3fb950' };
  if (s === 'running') return { label: 'Unhealthy', color: '#d29922', dot: '#d29922' };
  return { label: 'Stopped', color: '#8b949e', dot: '#484f58' };
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

  const patterns = [
    `<circle cx="${size/2}" cy="${size/2}" r="${size*0.38}" fill="none" stroke="${cat.color}" stroke-opacity="0.15" stroke-width="1"/>`,
    `<rect x="${size*0.15}" y="${size*0.15}" width="${size*0.7}" height="${size*0.7}" rx="${size*0.12}" fill="none" stroke="${cat.color}" stroke-opacity="0.15" stroke-width="1"/>`,
    `<line x1="${size*0.2}" y1="${size*0.8}" x2="${size*0.8}" y2="${size*0.2}" stroke="${cat.color}" stroke-opacity="0.1" stroke-width="1"/>`,
    `<circle cx="${size*0.3}" cy="${size*0.7}" r="${size*0.08}" fill="${cat.color}" fill-opacity="0.1"/><circle cx="${size*0.7}" cy="${size*0.3}" r="${size*0.08}" fill="${cat.color}" fill-opacity="0.1"/>`,
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
