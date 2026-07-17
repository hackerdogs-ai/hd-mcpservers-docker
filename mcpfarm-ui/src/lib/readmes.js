// Bundled READMEs for local dev when the auth-gateway endpoint is unavailable.
const files = import.meta.glob('../../../*-mcp/README.md', {
  query: '?raw',
  import: 'default',
  eager: true,
});

export function getBundledReadme(serverName) {
  const suffix = serverName.endsWith('-mcp') ? serverName : `${serverName}-mcp`;
  const key = Object.keys(files).find(k => k.includes(`/${suffix}/README.md`));
  return key ? files[key] : null;
}
