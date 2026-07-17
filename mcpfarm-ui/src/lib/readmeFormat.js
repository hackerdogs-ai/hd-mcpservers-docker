/** Normalize README markdown that mixes HTML banners with GFM. */
export function preprocessReadme(source) {
  if (!source) return '';

  let text = source;

  // Drop centered HTML logo/header blocks common in Hackerdogs READMEs.
  text = text.replace(/<p align="center">[\s\S]*?<\/p>\s*/gi, '');

  // Convert collapsible sections to markdown headings.
  text = text.replace(
    /<details>\s*<summary>([\s\S]*?)<\/summary>([\s\S]*?)<\/details>/gi,
    (_, title, body) => `\n\n### ${title.trim()}\n${body.trim()}\n`
  );

  // Strip remaining HTML tags.
  text = text.replace(/<[^>]+>/g, '');

  // Decode a few common entities.
  text = text
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>');

  return text.trim();
}
