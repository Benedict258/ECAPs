// Builds site/dist from site/src and the static files. No dependencies.
// Run: node build.mjs   (Vercel runs it with Root Directory = site)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Single constant. Set to the public ECAPs repository address. Empty = disabled buttons.
const REPO_URL = 'https://github.com/Benedict258/ECAPs';

const SITE = 'https://ecaps.benedictisaac.dev';
const POSTER = 'assets/ECAPs_Poster_Build26-5P.pdf';
const root = path.dirname(fileURLToPath(import.meta.url));
const dist = path.join(root, 'dist');

fs.rmSync(dist, { recursive: true, force: true });
fs.mkdirSync(dist, { recursive: true });
for (const d of ['assets', 'fonts']) fs.cpSync(path.join(root, d), path.join(dist, d), { recursive: true });
for (const f of ['styles.css', 'site.js', 'design-tokens.css', 'robots.txt']) fs.copyFileSync(path.join(root, f), path.join(dist, f));

const hasPoster = fs.existsSync(path.join(root, POSTER));

function transform(html) {
  // Repository links: <a ... data-repo ...>Label</a>
  html = html.replace(/<a ([^>]*?)data-repo([^>]*)>([^<]*)<\/a>/g, (m, a, b, label) => {
    const attrs = (a + b).replace(/\s*href=""/, '').replace(/\s*data-plain/, '').trim();
    const plain = /data-plain/.test(a + b);
    if (REPO_URL) return `<a ${attrs} href="${REPO_URL}" target="_blank" rel="noopener">${label}</a>`;
    const cls = (attrs.match(/class="([^"]*)"/) || [, ''])[1].replace('btn-primary', '').replace('btn-link', '').trim();
    if (plain) return `<span class="muted">Repository link coming soon</span>`;
    return `<span class="btn ${cls.replace(/\bbtn\b/, '').trim()} is-disabled" aria-disabled="true">Repository link coming soon</span>`;
  });
  // Poster link only if the file exists
  html = html.replace(/<a ([^>]*?)data-poster([^>]*)>([^<]*)<\/a>/g, (m, a, b, label) =>
    hasPoster ? `<a ${(a + b).trim()}>${label}</a>` : '');
  return html;
}

for (const [src, out] of [['index.html', 'index.html'], ['404.html', '404.html']]) {
  fs.writeFileSync(path.join(dist, out), transform(fs.readFileSync(path.join(root, 'src', src), 'utf8')));
}

const today = new Date().toISOString().slice(0, 10);
fs.writeFileSync(path.join(dist, 'sitemap.xml'),
`<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>${SITE}/</loc><lastmod>${today}</lastmod></url>
</urlset>
`);
console.log(`built: repo=${REPO_URL || '(disabled)'} poster=${hasPoster ? 'yes' : 'no'}`);
