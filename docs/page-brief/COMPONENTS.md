# ECAPs page: component inventory

States listed are the ones built. "Sections" use the anchor ids.

| Component | States | Used in |
|---|---|---|
| site-header (sticky, skip link, inline nav, menu) | default, scrolled (soft shadow), menu closed, menu open | all |
| button: primary / amber on dark | default, hover (charcoal fill + amber ring; amber button gets paper ring), focus-visible (ink ring on paper, amber ring on dark), active, disabled | #top, #runtime, #partner |
| button: outline | default, hover (paper-2 fill), focus-visible, active, disabled | #top, #runtime, #partner |
| button: text link with arrow | default, hover (underline thickens), focus-visible | #top |
| disabled button ("coming soon") | dashed outline, wraps to two lines, 44 px minimum | #runtime, #contact |
| badge (stage) and tag ("Proposed design", "Proposed") | static | #top, #nodes, #specs |
| number-tile (V6a, V6b, V6c) | static | #problem |
| node-card (V2, V3, V4) | static | #nodes |
| shared-bar | static | #nodes |
| edge-cloud-diagram (V5) and stacked step list | desktop diagram, phone list | #approach |
| block (icon + text) and power-mode strip | static | #how |
| table (real table, stacked rows on phones) | desktop, phone | #how, #bandwidth, #runtime, #sources |
| formula-chips | static | #bandwidth |
| chart (V7a, V7b) | default, hover on a bar (SVG title shows value), values always visible | #bandwidth |
| specs-table and spec-card | table at 768 px and up, three cards below | #specs |
| step-flow (solar sizing) | static | #specs |
| definition row (icon + term) | static | #shared |
| note-box | static | #shared |
| results-slot (V9) | empty (always) | #runtime |
| runtime-stack (V8) | static | #runtime |
| timeline (status shape + text: Done, In progress, Built, Next, Open) | static | #next |
| pull-quote | static | #inclusion |
| accordion (native details) | closed, open | #faq |
| contact-block with copy-email button | default, copied, copy failed (shows the address) | #contact |
| site-footer | static | all |
| back-to-top | hidden, shown after one screen | all |
| 404 page | static | 404.html |
| print view | black on white, no header, no backgrounds | all |

Tokens: design-tokens.css. Assets: assets/V1 to V10. Fonts: fonts/ (Inter variable, Newsreader 700, Latin subset).
