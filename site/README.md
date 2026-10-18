# ECAPs project page

Static page for ecaps.benedictisaac.dev (the poster QR code target). Plain HTML, CSS and a little JS. No framework, no third-party requests, no analytics, no cookies.

- `src/index.html`, `src/404.html`: the page markup (design from Claude Design, copy from `ECAPs_Page_Content.md`).
- `styles.css`, `design-tokens.css`, `site.js`, `fonts/`, `assets/`: served as they are.
- `build.mjs`: copies everything to `dist/`. It holds the one constant `REPO_URL`. Empty means the repository buttons render as disabled "Repository link coming soon". It also keeps the poster link only if `assets/ECAPs_Poster_Build26-5P.pdf` exists, and writes `sitemap.xml`.
- `vercel.json`: build command, clean URLs, security headers (CSP with no external sources).

Build and view: `node build.mjs`, then serve `dist/` with any static server.

Deploy: a Vercel project with Root Directory `site`, build command `node build.mjs`, output `dist` (already in `vercel.json`). Add `ecaps.benedictisaac.dev` as the domain and a CNAME `ecaps` to `cname.vercel-dns.com`.
