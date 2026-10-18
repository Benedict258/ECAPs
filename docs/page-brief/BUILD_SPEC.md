# Build spec: ECAPs project page (ecaps.benedictisaac.dev)

You are building the project page that the poster's QR code opens. Read this whole file first. The page copy is in `ECAPs_Page_Content.md` (attached). Copy is final: use it verbatim, do not rewrite, shorten, or add claims, numbers, names or logos.

## 0. Ask me first (do not guess)
1. The existing stack of benedictisaac.dev (inspect the repo). Build in the same stack and conventions if it is a static or Vite/Next site. If there is no site repo, use plain static HTML, CSS and a little JS.
2. The public URL of the ECAPs repository (I will make it public). Until I give it, use a single constant `REPO_URL` and render the "See the code" and "Open the repository" buttons as disabled with the label "Repository link coming soon". Never invent a URL.
3. Hosting and DNS for the subdomain `ecaps.benedictisaac.dev` (what is already used for benedictisaac.dev).

## 1. What this page is for
Visitors scan a QR on an A0 poster at BUILD26 (Abuja, 21 to 22 Oct 2026) on a phone, often on weak mobile data. In 5 seconds they should know what ECAPs is. Then they can read the research, see the code, and contact me. Mobile first. Fast. Calm. No marketing tone.

## 2. Hard rules (honesty)
- Stage badge everywhere it appears: "Research and development stage". Node sizes and specs are "proposed". Nothing is built in silicon.
- No results from a real run exist yet. Section 11 shows the four result slots F1 to F4 as empty framed placeholders with their captions and the line "Results will be published here when the runs are complete." Never put numbers, charts or screenshots in them. Never use mock-data output.
- The two bandwidth charts in section 6 use only the measured numbers given below. Label them as other people's measurements on other hardware, not ECAPs results.
- No pricing numbers, no named partners, no logos of any company, no claims of speed or energy savings for ECAPs.
- Contact details are mine and are meant to be public: benedictisaac258@gmail.com, +234 904 837 7499, benedictisaac.dev, GitHub Benedict258.

## 3. Look: "Paper and ink"
Tokens: paper #F5F3EE, ink #0B0B0B, charcoal #1A1A1A, rule grey #D9D5CC, muted text #4A4A45, amber #F2A900. Amber is never text on paper (amber on ink is fine). Body text ink on paper, contrast at least 7:1. Flat shapes, thin consistent line art, no gradients, no stock photos. Headings: Newsreader (fallback Source Serif 4, then Georgia). Body: Inter (fallback system-ui). Self-host subsetted fonts (Latin only, woff2, `font-display: swap`). Respect `prefers-reduced-motion`. Support dark mode only if it is trivial; paper and ink is the default and the priority.

## 4. Page structure (order = page order, each with an anchor id)
Sticky slim header: ECAPs mark + name, anchors (Problem, Approach, Nodes, Runtime, Partner, Contact). Sections 1 to 16 exactly as in `ECAPs_Page_Content.md`:
1 Hero #top, 2 Problem #problem, 3 Approach #approach, 4 Node family #nodes, 5 How it works #how, 6 Why memory bandwidth #bandwidth, 7 Proposed specs #specs, 8 Shared nodes #shared, 9 Robotics #robotics, 10 Inclusion and Tech Justice #inclusion, 11 ECAPs Node Runtime #runtime, 12 What's next #next, 13 Partner with us #partner, 14 Sources #sources, 15 FAQ #faq, 16 About and contact #contact.
Skip the "Page map", "How to use this file" and "Publishing checklist" parts of the content file. They are not page content.
Buttons: "Read the research" scrolls to #sources; "See the code" opens `REPO_URL`; "Partner with us" scrolls to #partner. Add one more link in the hero: "Download the poster (PDF)" pointing to `/assets/ECAPs_Poster_Build26-5P.pdf` (I will add the file; show the link only if the file exists at build time).
FAQ: native `<details>` elements, no JS.

## 5. Visual assets to build (each its own separate component or SVG file, so any one can be fixed alone)
All inline SVG or small SVG files, ink and amber on paper, thin line art, `role="img"` with a text alternative.
1. **Hero node-family illustration**: a cloud labelled "Central compute" above three node drawings (Node Mini, Node, Node Hub), dashed link labelled "when online", one shared bar underneath "ECAPs Node Runtime: one software stack for all three". Tag "Proposed design".
2. **Node Mini card**: small plug-in module attached to a host board (generic, no brand marks). Name Node Mini; label "Plug-in compute for robots and engineering systems".
3. **Node card**: compact unit with a small solar panel and battery symbol beside a simple house shape. Name Node; label "For homes and institutions".
4. **Node Hub card**: a larger shared unit with a second unit linked beside it. Name Node Hub; label "Shared community node".
5. **Edge-cloud collaboration diagram** (section 3): local first answer, escalate when needed, queue when offline, update when online. Four steps, simple arrows.
6. **Number tiles** (section 2), same size, each a big number plus a graphic: 18% bar (18 of 100 filled amber); 0.6% the same bar at the same scale with a thin true-width amber sliver and a small amber arrow pointing at it; 5% twenty small rack icons in two rows of ten, first one amber. Under them the line and source from the content file.
7. **Bandwidth charts** (section 6), drawn as SVG from data, not images:
   - Chart A "More memory bandwidth, faster text" (tokens per second): 68 GB/s 14; 100 GB/s 22; 200 GB/s 36; 400 GB/s 61; 800 GB/s 84. Ink bars, tallest amber.
   - Chart B "More compute, same bandwidth: little gain": at 400 GB/s, 24 cores 54.6 and 32 cores 61.2; at 800 GB/s, 48 cores 74.9 and 64 cores 83.7. Label under each pair: "+33% compute cores, about +12% speed". Same y-scale as Chart A. Show values to one decimal here.
   - Caption: "Same model (Llama 2 7B, 4-bit), same software (llama.cpp), measured by others across Apple M-series chips. Not ECAPs results. Source: llama.cpp discussion #4167." Link the source: https://github.com/ggml-org/llama.cpp/discussions/4167
   Keep the worked-example table and the speed-ceiling table as real HTML tables.
8. **Runtime stack diagram** (section 11): layers top to bottom Device interface, Agent runtime, Model manager, llama.cpp backend; side labels Power-aware modes, Local memory, Management API, Node discovery.
9. **Specs and solar tables** (section 7): real HTML tables, scrollable on mobile.
10. **Results placeholders** (section 11): four empty framed slots F1 to F4 with captions from the content file, plus a disabled "Raw data" link.
11. **Contact block** (section 16): name, role, email (mailto), phone (tel), website, GitHub, repository.

## 6. Technical requirements
- Total weight under 250 KB for the first load, excluding the optional poster PDF. No frameworks needed for static content. No third-party scripts, no analytics, no cookies, no tracking, no external fonts or CDNs at runtime.
- Works with JavaScript disabled (content, tables and FAQ all readable). Charts are inline SVG, so they render without JS.
- Mobile first at 360 px wide. No horizontal page scroll. Tap targets at least 44 px. Body text at least 17 px, line length about 65 characters.
- Accessibility: semantic landmarks, one `h1`, heading order, visible focus, skip link, text alternatives for every SVG, colour contrast 7:1 for body text, links distinguishable without colour.
- SEO and sharing: `<title>` "ECAPs: AI compute for the last mile", meta description (one sentence from the hero), canonical URL, Open Graph and Twitter card tags with an image `/assets/og.png` (1200x630, built from the hero illustration), `lang="en"`, favicon from the ECAPs mark (option 2: open square node).
- Include `robots.txt`, a small `sitemap.xml`, a custom 404 page, and security headers if the host allows (CSP with no external sources).
- HTTPS on `ecaps.benedictisaac.dev`.
- Print stylesheet so the page prints cleanly.

## 7. Acceptance checklist (run before you tell me it is done)
- [ ] Every section's text matches `ECAPs_Page_Content.md` exactly (diff it).
- [ ] No invented numbers. The only data numbers are those in the content file and section 5.7 above.
- [ ] F1 to F4 are empty placeholders.
- [ ] `REPO_URL` is set or the buttons are disabled.
- [ ] Lighthouse on mobile: Performance, Accessibility, Best Practices, SEO all 95 or higher. Test with throttled slow 4G.
- [ ] Checked at 360, 390, 768 and 1280 px, no horizontal scroll.
- [ ] All links work (internal anchors, mailto, tel, GitHub, the llama.cpp discussion).
- [ ] The page loads and reads fully with JS off.
- [ ] Deployed to `ecaps.benedictisaac.dev` over HTTPS.
Report back with: the live URL, the Lighthouse scores, the page weight, and anything you changed or could not do. Do not commit to my main branch without asking; work on a branch and open a pull request. Do not add co-author or AI attribution lines to commits or the PR.
