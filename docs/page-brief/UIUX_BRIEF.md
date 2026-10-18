# UI/UX brief for Claude Design: the ECAPs project page

Attach with this brief: `ECAPs_Page_Content.md` (all the page copy), the QR image is NOT needed on the page, and the final poster PNG (for the visual language and the existing assets). Claude Code will build the live page from your HTML export, so the export must be clean, semantic and easy to turn into the real site.

## 1. What you are designing
The project page at `ecaps.benedictisaac.dev`. It is what the QR code on the A0 poster Build26/5P opens. People scan it at a conference on a phone, often on weak mobile data, standing up. In 5 seconds they must know what ECAPs is. Then they can read the research, open the code, or contact Benedict. Researchers, engineers, chip and infrastructure people and conference organisers will also read it on laptops.

Priorities: 1) phone first, 2) fast and light, 3) calm, honest, credible, 4) easy to scan, 5) matches the poster so it feels like the same project.

## 2. Copy rules (important)
All text comes from `ECAPs_Page_Content.md`. Use it exactly. Do not rewrite, shorten, add or invent claims, numbers, names or logos. Skip the "Page map", "How to use this file" and "Publishing checklist" parts of that file: they are notes, not page content. Where this brief gives a label for a UI element (buttons, nav, captions), use it as written.

Honesty rules that the design must respect:
- "Research and development stage" badge is visible in the hero and in the footer. Node sizes and specs are labelled "Proposed".
- Results area (F1 to F4) is four empty framed placeholders. Never fill them with charts, numbers or screenshots.
- The two bandwidth charts are other people's measurements, labelled that way. No ECAPs speed numbers anywhere.
- No company logos, no named partners, no stock photos, no people clip-art.

## 3. Look: "Paper and ink" (same as the poster)
Tokens (define as CSS custom properties in `:root`):
- `--paper #F5F3EE`, `--ink #0B0B0B`, `--charcoal #1A1A1A`, `--rule #D9D5CC`, `--muted #4A4A45`, `--amber #F2A900`
- Optional tints for hover and surfaces: `--paper-2 #ECE9E1`, `--amber-soft #FBE7B0` (only if needed; say so in the token list).
Rules: ink on paper for text, contrast 7:1 or better for body text. Amber is an accent for bars, markers, focus rings and small shapes. Never amber text on paper (amber on ink is fine). Dark sections (hero, partner, footer) use ink or charcoal. Dark share of the page about 20 to 25%. Flat shapes, thin consistent line art (about 2 px at 1x), no gradients, no glossy 3D, no shadows except a very soft one on the sticky header.
Type: headings Newsreader (fallback Source Serif 4, Georgia); body, labels, numbers and UI Inter (fallback system-ui). Sentence case. Small tracked caps only for section labels and the stage badge.
Type scale (mobile / desktop): h1 34 / 56 px, h2 28 / 40, h3 20 / 24, body 17 / 18 (line-height 1.55, line length about 65 characters), small 14 / 15 (captions, table notes, sources), nothing below 14 px.
Spacing: 8 px base; section padding 56 / 96 px vertical; content column max 1120 px, text column max 680 px. Radius: 12 px for cards, 999 px for badges, 0 for table rules. Line weights: 1 px rules in `--rule`, 2 px line art.

## 4. Process
1. Design system page first: tokens, type scale, spacing, grid, buttons, links, badges, cards, tables, diagram style, focus states. Show it for approval before building the page.
2. Every visual as its own separate asset, exportable alone as SVG (and PNG): see section 7. Reuse the poster assets and style so the page and poster match.
3. Assemble the page from those assets as linked components, so a fix to one asset updates the page.
4. Show: mobile (360 and 390 px), tablet (768 px), desktop (1280 px) for the whole page.
5. Export (section 10).

## 5. Layout and navigation
- Mobile first, single column. 16 px side gutters on mobile, 24 px on tablet, 12-column grid on desktop with a 1120 px max width.
- **Sticky header** (56 px mobile, 64 px desktop): ECAPs mark + "ECAPs" at the left. On mobile a "Menu" button opens a full-width panel listing: Problem, Approach, Nodes, How it works, Bandwidth, Specs, Runtime, Partner, Sources, FAQ, Contact. On desktop show the short set inline: Problem, Approach, Nodes, Runtime, Partner, Contact. Header has a hairline bottom rule and, once scrolled, a very soft shadow. A "Skip to content" link appears on keyboard focus.
- Section order is fixed: 1 Hero, 2 Problem, 3 Approach, 4 Node family, 5 How it works, 6 Why memory bandwidth, 7 Proposed specs, 8 Shared nodes, 9 Robotics, 10 Inclusion and Tech Justice, 11 ECAPs Node Runtime, 12 What's next, 13 Partner, 14 Sources, 15 FAQ, 16 About and contact. Anchor ids: `#top #problem #approach #nodes #how #bandwidth #specs #shared #robotics #inclusion #runtime #next #partner #sources #faq #contact`.
- Alternate section backgrounds sparingly (paper, paper-2) and use thin rules between sections. Each section starts with a small tracked-caps label, then the heading. No decorative clutter.
- A subtle "back to top" button appears after the first screen of scrolling (bottom right, 44 px).

## 6. Section-by-section design
Describe each at mobile first; say how it changes on desktop. Text is from the content file.

**1 Hero (dark, ink).** Stage badge "Research and development stage" (amber outline pill). Headline (serif, large): "AI that works where the grid, the cloud and the budget don't reach." Sub-headline below. Three buttons: primary "Read the research" (amber fill, ink text), secondary "See the code" (outline, light), tertiary "Partner with us" (text link with arrow). Add a fourth small text link "Download the poster (PDF)" (shown only if the file exists). Under them, one small line: the "Presented as poster Build26/5P…" text. Then the hero visual (asset V1): the node family with the cloud above as a partner, on a paper-coloured panel with rounded corners so it reads on the dark hero. Mobile: stacked, visual below text. Desktop: text left (6 columns), visual right (6 columns).

**2 The problem (paper).** Heading and strapline first, then the problem sentence and intro. Then the three number tiles (asset V6): mobile stacked full width, desktop three across, same size, paper cards with ink outline and an amber top bar. Each tile: big number (serif, 64 px mobile / 88 desktop), the "reads as" line, the graphic (bar or racks), and the "what it means" line in small type. Under the tiles: the line in serif italic, then the World Bank source in small muted type with the source linked. Then the four "what this means for people" bullets as a clean list with small amber square markers.

**3 Our approach (paper).** Heading, the paragraph (text column), the five bullets, then the edge-cloud diagram (V5) full width: four steps "Local first", "Escalate when needed", "Queue when offline", "Update when online". Mobile: the diagram becomes a vertical four-step flow.

**4 Node family (paper-2).** Heading, intro paragraph, then three node cards (V2, V3, V4) sharing one layout, outline and amber highlight for the active part. Mobile: stacked cards; desktop: three across. Each card: drawing, name, label, "Who it is for", "What it does" (from the table in the content file). A "Proposed design" tag in the top right of each card. Under the cards, one shared bar spanning all three: "ECAPs Node Runtime: one software stack for all three". The sentence "Nodes are networked to serve more users. They are not designed to split one model across machines." under the bar. Never show one model split across nodes.

**5 How it works (paper).** Four blocks: "Agentic: AI that acts locally", "Offline first", "Built for solar and low power", "Edge and cloud, working together". Use a two-column grid on desktop (text and a small icon or diagram each), single column on mobile. The edge-and-cloud patterns table is a real table that becomes stacked label/value rows on mobile. Include a small power-mode strip showing Eco, Normal, Boost as three segments (labels only, no numbers).

**6 Why memory bandwidth (paper).** Heading, the explanation paragraphs, then the formula as three chips: "memory bandwidth" ÷ "model size" = "ceiling on text speed" (the last chip amber). The worked-example table (16-bit, 8-bit, 4-bit). Then the "Measured evidence" block: two charts (V7a and V7b) side by side on desktop, stacked on mobile, with the caption "Same model (Llama 2 7B, 4-bit), same software (llama.cpp), measured by others across Apple M-series chips. Not ECAPs results." and a source link to the llama.cpp discussion #4167. The charts use exactly these numbers:
- Chart A, "More memory bandwidth, faster text", tokens per second: 68 GB/s = 14; 100 GB/s = 22; 200 GB/s = 36; 400 GB/s = 61; 800 GB/s = 84. Ink bars, the tallest amber, values above bars.
- Chart B, "More compute, same bandwidth: little gain": at 400 GB/s, 24 cores = 54.6 and 32 cores = 61.2; at 800 GB/s, 48 cores = 74.9 and 64 cores = 83.7. Label under each pair: "+33% compute cores, about +12% speed". Same y-scale as chart A. Ink bars.
Under the charts, the four bullets and the one-line note "Speed does not grow in step with bandwidth, so the formula is a ceiling." Charts must be inline SVG with `role="img"`, a text alternative, and the data values in the SVG as text so Claude Code can regenerate them.

**7 Proposed node specifications (paper-2).** Intro line. The specs table (rows: Models (4-bit), Memory, Memory bandwidth class, Power, Speed ceiling; columns Node Mini, Node, Node Hub), always headed "Proposed". On mobile show it as three stacked cards (one per node) instead of a wide table. Below it the three rules (bullets) and the solar sizing example: assumptions line, then the three-step table (daily energy, battery, solar panel) laid out as a small step flow, and the Abuja sunshine sentence in muted small type.

**8 Shared nodes and community (paper).** Four labelled rows (Who manages it, Who owns it, Who pays, Open to anyone) as a definition list with a small icon each. Then the community-network paragraph with the Zenzeleni sentence, and the "Still being worked out" note in a quiet bordered box.

**9 Robotics and engineering (paper-2).** The paragraph and two bullets, with the Node Mini drawing (V2) beside it on desktop, above on mobile.

**10 Inclusion and Tech Justice (dark, charcoal).** The Tech Justice line as a large serif pull-quote in paper colour, then the infrastructure line beneath it, then three bullets. No quotation marks and no attribution on the lines (they are our own words).

**11 The ECAPs Node Runtime (paper).** Intro paragraph with the "prototype, research and development stage" note. The runtime stack diagram (V8): Device interface, Agent runtime, Model manager, llama.cpp backend, with side labels Power-aware modes, Local memory, Management API, Node discovery. The parts table (Part, What it does). "Benchmarks" paragraph, then the results area: four empty framed slots F1 to F4 (landscape cards, dashed outline, a small "Results to come" label, caption under each from the content file) and the line "Results will be published here when the runs are complete." plus a disabled "Raw data" link. Then the models and licences table. Buttons: "Open the repository" (primary), "Run it yourself (guide)", "Read the design notes". If the repository URL is not set, show "Open the repository" as a disabled button labelled "Repository link coming soon".

**12 What's next (paper-2).** The stage table as a simple vertical timeline without dates: five rows with a status marker each (Done, In progress, Built, Next, Open) using shape plus text (never colour alone).

**13 Partner with us (dark, ink).** Heading "We are looking for partners", the paragraph, two lists ("Who we want to talk to", "What we would ask") in two columns on desktop, stacked on mobile. Call to action "Let's talk." as a large serif line with two buttons: "Email Benedict" (mailto) and "Call" (tel). Keep the tone warm and open, not salesy.

**14 Research and sources (paper).** The sources table with two columns (Source, Used for); links open in a new tab with `rel="noopener"`. On mobile each row becomes a stacked item.

**15 FAQ (paper-2).** Eight questions as an accordion using native `<details>`/`<summary>`; first item closed; plus/minus indicator; 48 px minimum tap target.

**16 About and contact (paper), then footer (dark).** The about paragraph and the contact block: Benedict Isaac, Researcher, ECAPs; email and phone as tap-to-act links; website; GitHub Benedict258; project repository. A "Copy email" small button is allowed (needs a tiny script with a fallback). Footer: "ECAPs, Edge Computing Agentic Processors. Research and development stage. Poster Build26/5P, BUILD26, Abuja." and the small ECAPs mark.

## 7. Visual assets (each its own frame, exportable as SVG and PNG)
Reuse the poster drawings and style. Thin line art, ink on paper with amber for the active part. Every SVG has a `<title>` and `<desc>`.
- **V1** Hero node-family illustration: cloud "Central compute" above, dashed link "when online", three nodes, shared bar "ECAPs Node Runtime: one software stack for all three", tag "Proposed design".
- **V2** Node Mini card drawing: small plug-in module attached to a host board (generic, no brand marks).
- **V3** Node card drawing: compact unit, small solar panel and battery symbol, simple house shape.
- **V4** Node Hub card drawing: larger shared unit with a second unit linked beside it.
- **V5** Edge-cloud collaboration diagram: local first, escalate when needed, queue when offline, update when online.
- **V6** Number tiles with graphics: 18% (bar, 18 of 100 amber), 0.6% (the same bar, same scale, true-width sliver in amber with a small amber arrow pointing at it), 5% (20 rack icons in two rows of ten, first amber).
- **V7a / V7b** The two bandwidth charts (data in section 6).
- **V8** Runtime stack diagram.
- **V9** Results placeholder slot (one component used four times).
- **V10** ECAPs mark (option 2, open square node) in light and dark versions, plus a 32 px favicon version and a 1200x630 Open Graph image built from V1.
Make V1 to V4 and V8 identical in drawing style to the poster so the two feel like one project.

## 8. Components and states (design all of these)
Buttons (primary amber on ink backgrounds, primary ink on paper, secondary outline, text link with arrow): default, hover, focus-visible (3 px amber ring with 2 px offset, visible on both light and dark), active, disabled (with the "coming soon" label). Links: underlined, hover thickens the underline. Badges and tags. Cards. Tables (desktop and the mobile stacked version). Accordion (open and closed). Menu panel (closed, open). Chart (default, hover on a bar shows its value; also readable without hover). Copy-email button (default, copied). Empty results slot. 404 page (the mark, "This page does not exist", a link back to the home page). Print view: black on white, no sticky header, no backgrounds.
Motion: minimal. 150 to 200 ms ease for hover, accordion and menu. No scroll-triggered animation, no parallax. Respect `prefers-reduced-motion`.

## 9. Accessibility and performance
- Semantic HTML: header, nav, main, section, footer, one h1, correct heading order.
- Body contrast 7:1. Large text and UI components at least 4.5:1. Never use colour alone to carry meaning.
- Tap targets 44 px or larger. Visible focus everywhere. Keyboard operable menu and accordion.
- Works fully with JavaScript turned off (menu may fall back to a plain list of links).
- Light: no framework, no external requests (fonts self-hosted and subset, Latin only), all SVG inline or tiny files, first load under 250 KB excluding the poster PDF.
- No cookies, no analytics, no third-party scripts.

## 10. What to hand over (so Claude Code can build fast)
1. **One `index.html`** for the whole page: semantic HTML, all CSS in one `<style>` block using the custom properties from section 3, a small `<script>` only for the menu, back-to-top and copy-email. Comment each component, for example `<!-- COMPONENT: node-card -->`, and each section with its anchor id. No inline `style` attributes except for chart bar heights. Mobile first with `min-width` media queries at 768 and 1120 px.
2. **Separate SVG files** for V1 to V10 in an `assets/` folder, each also inlined in the HTML where used.
3. **`design-tokens.css`**: the `:root` variables only.
4. **Screenshots** of the page at 360, 390, 768 and 1280 px, and of the open menu, an open FAQ item and the disabled-button state.
5. **A short component inventory** listing each component, its states and which sections use it.
6. A short **"Notes for the developer"** block at the top of the HTML (as a comment): the `REPO_URL` placeholder, the poster PDF path `/assets/ECAPs_Poster_Build26-5P.pdf` (link hidden if missing), the contact details, and a reminder that F1 to F4 stay empty.
Check before you hand over: every text matches the content file; nothing below 14 px; contrast 7:1 for body; no horizontal scroll at 360 px; the page reads in full with no JavaScript; no invented numbers; charts use exactly the numbers in section 6.
