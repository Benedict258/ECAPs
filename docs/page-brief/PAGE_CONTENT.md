# ECAPs Project Page: Full Content

> **How to use this file.** Each section below is one section of the page, with its copy ready to paste. Build each visual as its own separate asset (the node cards, the stack diagram, the edge-cloud diagram, the number tiles, the QR block) and then assemble the page from them, so any asset can be fixed alone. A short publishing checklist at the end lists what must be confirmed before the page goes live. It is not part of the page.


### Page map

| # | Section | Purpose |
|---|---|---|
| 1 | Hero | State what ECAPs is and the takeaway in five seconds. |
| 2 | The problem | Relatable problem statement and the verified numbers, each with its meaning. |
| 3 | Our approach | A complementary layer, in plain words. |
| 4 | The node family | Node Mini, Node, Node Hub. |
| 5 | How it works | Agentic, offline-first, power, edge and cloud together. |
| 6 | Why memory bandwidth | The design reason, with a worked example. |
| 7 | Proposed node specifications | The three sizes, labelled proposed, with solar sizing. |
| 8 | Shared nodes and community | Pay per use, who manages, ownership. |
| 9 | Robotics and engineering | Node Mini for students and labs. |
| 10 | Inclusion and Tech Justice | Why this matters. |
| 11 | The ECAPs Node Runtime | The open reference software stack. |
| 12 | What's next | Roadmap without dates. |
| 13 | Partner with us | Who we want to talk to and what we ask. |
| 14 | Research and sources | References. |
| 15 | FAQ | Short settled answers. |
| 16 | About and contact | Who is behind it. |


## 1. Hero

**Headline:** AI that works where the grid, the cloud and the budget don't reach.

**Sub-headline:** ECAPs (Edge Computing Agentic Processors) brings AI compute to homes, schools, labs and communities across Africa. It works alongside central AI infrastructure, and carries its value to the last mile.

**Stage badge:** Research and development stage

**Buttons:** Read the research  |  See the code  |  Partner with us

**One line under the buttons:** Presented as poster Build26/5P at BUILD26, Africa's Shared Compute and AI Infrastructure Conference, Abuja, October 2026.

**Hero visual (asset):** the node family illustration, with the cloud above it as a partner.


## 2. The problem

**Heading (decided):** Inclusive AI needs inclusive infrastructure.

**Strapline:** Central compute is the base of Africa's AI future, but AI-ready compute is still scarce. Inclusive AI needs more of it, in more places.

**The problem:** AI-ready compute is scarce, so many institutions, schools, labs and communities cannot access AI, especially where power is unstable and connections are weak.

**Intro:** Africa has 18% of the world's people but little AI-ready compute. Central infrastructure is the foundation, and it takes time to build. Meanwhile institutions, schools, labs and communities are left waiting, or pay again and again to rent compute from far away. ECAPs adds AI compute close to people, alongside central infrastructure.

| Number tile (asset) | Reads as | What it means |
|---|---|---|
| 18% | of the world's people live in Africa | A large part of the world's AI future is here. |
| 0.6% | of the world's data-centre capacity is in Africa | The compute that runs AI sits mostly elsewhere. |
| 5% | of Africa's data centres are AI-ready | Few facilities can run AI work today. |

**Line under the tiles:** Africa's share of the world's compute is far smaller than its share of the world's people.

**Source line under the tiles:** World Bank, Africa Economic Update, October 2026.


#### What this means for people

- Schools, labs, institutions and community groups pay again and again to rent AI compute.
- Unstable power and weak connectivity cut off AI that depends on the cloud.
- Students and small teams need custom hardware for every robotics project.
- Building central compute takes time. ECAPs adds AI compute close to people, alongside it.


## 3. Our approach

**Heading:** A complementary layer: accessible edge compute

ECAPs proposes a complementary layer to Africa's central compute investment: accessible edge compute that extends AI's reach into homes, institutions, communities and technical systems that central infrastructure will take time to serve. We do not treat decentralisation as the goal. It is the mechanism by which central investment turns into everyday, widespread use. Every node is a new endpoint, a new source of demand and a broader market for the compute and chip providers building Africa's core infrastructure.

- A node runs AI models locally, at home, in a school or in a community.
- It keeps working offline, and is built for solar and low power.
- Heavy tasks go to larger cloud models when a connection is there.
- Every node becomes a new endpoint for central compute providers.
- One architecture and one software stack, in three sizes.

**Visual (asset):** the edge-cloud collaboration diagram: local-first answer, escalate when needed, queue when offline, update when online.


## 4. The node family

**Heading:** One architecture, three node sizes

ECAPs is a two-tier edge compute system, shown here as three sizes of one design. The sizes differ in compute, memory and power. They share one architecture and one software stack. All sizes below are proposed designs.

| Node | Who it is for | What it does |
|---|---|---|
| Node Mini | Robotics and engineering systems: student projects, research labs, small engineering teams | A plug-in compute add-on that gives a host board, such as an ESP32 or a Raspberry Pi, its own local AI. It brings its own fast memory. Its connection to the host (USB, SPI/UART, M.2 or similar) is still being defined. |
| Node (Tier 1) | Homes and institutions: schools, labs, universities, community organisations, builders | A compact, plug-and-play unit for local AI without dependence on constant cloud connectivity or a stable grid. Built for solar and low power. |
| Node Hub (Tier 2) | Neighbourhoods, schools, cooperatives and small organisations | A shared community node where people pool access to AI-ready compute. Users pay per use. ECAPs manages it. Several nodes can be networked, like racks, to serve more people. |

Nodes are networked to serve more users. They are not designed to split one model across machines.

**Visuals (assets):** one separate illustration per node, plus the shared software bar under all three.


## 5. How it works


#### Agentic: AI that acts locally

Agentic means a node runs local AI agents that sense, decide and act without waiting for the cloud. An agent reads a sensor, a small local model decides what to do, and the node acts, for example switching a pump on or logging an alert. ECAPs supports this with four things: an always-on, low-power design; input and output for sensors and machines; a small local memory of recent events; and a managed runtime that picks a model that fits the node.


#### Offline first

- Works with no internet: the local model, the agent loop, local memory and users on the local network.
- Uses the connection when it is there: escalating heavy tasks to a larger cloud model, downloading updates, remote monitoring.
- When the connection drops, events and actions are queued on the node and synced later (software prototype).


#### Built for solar and low power

Nodes are designed with DC input and low idle draw so they can run from a dedicated solar system or another renewable source. A power-aware mode (eco, normal, boost) lets the software adjust to the energy available.


#### Edge and cloud, working together

| Pattern | How it works |
|---|---|
| Local first | The small local model answers by default. |
| Escalate when needed | If a task is too heavy, the node passes it to a larger cloud model when connected. |
| Local data, cloud reasoning | Raw data stays on the node. Only what is needed goes up. |
| Update when online | The node pulls new models and software when there is a connection. |

This follows the edge and cloud collaboration patterns described in the research literature (see the sources).


## 6. Why memory bandwidth, not peak TOPS

On small devices, how fast an AI model writes text is set by memory bandwidth, the number of bytes per second the chip can read from memory, not by TOPS, the peak maths figure. To write each new word (token), the chip reads the model's whole set of weights from memory once. The maths per token is small, so the chip mostly waits for data.

**Rule of thumb:** tokens per second is at most memory bandwidth divided by model size in bytes.

**Worked example:** an 8-billion-parameter model on a board with about 100 GB/s of memory bandwidth.

| Precision | Bytes per weight | Model size | Speed ceiling |
|---|---|---|---|
| 16-bit | 2 | about 16 GB | about 6 tokens per second |
| 8-bit | 1 | about 8 GB | about 12 tokens per second |
| 4-bit | 0.5 | about 4 GB | about 25 tokens per second |

- Half the bandwidth means about half the speed.
- Half the bits per weight means about double the speed. This is why quantised models suit edge devices.
- Serving several users together (batching) lets one read of the weights help all of them. This is why a shared node gets more from the same hardware.
- So ECAPs ranks memory size and memory bandwidth per watt above peak TOPS when choosing an architecture.

The example is a back-of-envelope ceiling from the rule above. Real speeds are lower.

**Measured evidence.** The llama.cpp project keeps a public benchmark thread that runs one model (Llama 2 7B, 4-bit), with the same software and the same test (generating 128 tokens), on many Apple M-series chips and lists each chip's memory bandwidth beside its speed. These are other people's measurements on other hardware, not ECAPs results. They show the pattern the design relies on.

| Memory bandwidth | Text speed (tokens per second) |
|---|---|
| 68 GB/s | 14 |
| 100 GB/s | 22 |
| 200 GB/s | 36 |
| 400 GB/s | 61 |
| 800 GB/s | 84 |

| Same bandwidth, more compute | Compute cores | Text speed (tokens per second) |
|---|---|---|
| 400 GB/s | 24 then 32 | 54.6 then 61.2 |
| 800 GB/s | 48 then 64 | 74.9 then 83.7 |

More bandwidth gives faster text. A third more compute cores at the same bandwidth gives about 12% more speed. Speed does not grow in step with bandwidth, because other limits start to matter at the top, so the formula above is a ceiling.


## 7. Proposed node specifications

These are the proposed targets for each node size. They come from the rules below. They are design targets for the architecture we are proposing.

|  | Node Mini | Node | Node Hub |
|---|---|---|---|
| Models (4-bit) | 1 to 3 billion parameters | about 7 billion | 13 to 30 billion |
| Memory | 2 to 4 GB | about 8 GB | about 32 GB |
| Memory bandwidth class | about 25 to 50 GB/s | about 100 GB/s | 200 GB/s or more |
| Power | 3 to 5 W | 10 to 25 W | 40 to 60 W |
| Speed ceiling | about 17 tokens/s for a 3B model | about 28 tokens/s for a 7B model | about 13 tokens/s for a 30B model |

- Weights in GB = billions of parameters × bytes per weight (16-bit 2, 8-bit 1, 4-bit 0.5).
- Memory needed is about weights × 1.25, for the runtime and the conversation memory.
- Speed ceiling is memory bandwidth ÷ weights.


#### Sizing the solar system: an example

Assumptions: a node drawing 20 W all day, one day of battery autonomy, 80% of the battery usable, 5 peak sun hours a day and 70% system efficiency.

| Step | Calculation | Result |
|---|---|---|
| Daily energy | 20 W × 24 h | 480 Wh a day |
| Battery | 480 Wh ÷ 0.8 | 600 Wh |
| Solar panel | 480 Wh ÷ (5 h × 0.7) | about 137 W |

Sunshine varies by place and season. Old national records put the Abuja area at roughly 4.85 kWh per square metre per day, so 5 is a reasonable planning figure there. Size every real site from its own data.


## 8. Shared nodes and community

A Node Hub lets neighbourhoods, schools, cooperatives and small organisations pool access to AI-ready compute, so no single household has to own the hardware.

- **Who manages it:** ECAPs manages shared nodes: operation, updates and monitoring.
- **Who owns it:** ECAPs does not own them. A provider, an individual or a community group can own a node while ECAPs manages it.
- **Who pays:** users pay per use, which covers power and upkeep. A small optional management fee may come later. It is never compulsory.
- **Open to anyone:** individually owned nodes stay open to everyone. Shared nodes are one option, not the only one.

Community networks show that shared local infrastructure can work when ownership is local and the money for repairs is planned from the start. Zenzeleni, a cooperative-run network in Mankosi, South Africa, is one example: it started in 2012 and serves almost 6,000 people. The same lesson shapes the Node Hub model.

**Still being worked out:** the billing unit, payment where connectivity is weak, who repairs hardware, and how management scales as nodes multiply.


## 9. Robotics and engineering systems

ECAPs began in robotics and engineering. In this setting the same unit works as a plug-and-play compute module, giving robots and embedded systems on-device intelligence and agentic decision-making without building custom compute hardware into every system. This lowers the barrier for student projects, research labs and small engineering teams across Africa, who can build AI-capable robotics and automation on a shared, standard compute layer instead of custom silicon for each project.

- Host boards such as an ESP32 or a Raspberry Pi sense and act. The node adds local AI.
- A simulated sensor feed and a serial adapter for the ESP32 are part of the reference software.


## 10. Inclusion and Tech Justice

**Pull-quote (our own line):** Tech justice asks who builds technology, who owns it and who controls it. ECAPs puts compute closer to local hands, so everyone has a chance to use and build with AI.

**Infrastructure line:** Infrastructure that communities can build on, own and operate.

- More people and institutions can use AI without constant internet or a stable grid.
- Local models, including optional support for local-language models, can run on the same node.
- Tech justice has no single definition. Researchers describe it in terms of structural inequality and the history of extraction, and as a question of who develops, owns and has access to computing infrastructure. ECAPs addresses one part of it: access to compute.


## 11. The ECAPs Node Runtime

The ECAPs Node Runtime is the open reference software for every node size. It is a prototype in the research and development stage. It runs on an ordinary computer so that anyone can try and check it. Results shown on this page come from a stand-in reference machine, not from ECAPs hardware.

| Part | What it does |
|---|---|
| Backend interface | Runs models through llama.cpp, an open-source inference engine (MIT licence). |
| Model manager | Given a memory budget, picks the largest model that fits and explains why. |
| Agent runtime | Sense, plan, act. A model chooses a validated action, the runtime executes it, and a small local memory keeps recent events. |
| Power-aware modes | Eco, normal and boost modes adjust to the energy available. |
| Device interface | A simulated sensor feed, an ESP32 serial adapter and an MQTT adapter. |
| Offline queue | Events and actions are queued on the node and synced when a cloud endpoint is reachable. Cloud sync is off by default. |
| Node discovery and routing | Nodes on a local network find each other and a busy node can hand a request to a less busy one. |
| Management API | Read-only status, models and metrics for a manager. |


#### Benchmarks

Four benchmarks are defined and run with one command: B1 overhead compared with raw llama.cpp; B2 model choice at 2, 4 and 7 GB memory budgets; B3 an offline agent loop of about 20 tasks with and without a network; B4 eco, normal and boost power modes. Raw results and figures will be published on this page when the runs are complete. Each figure states the machine it was measured on.

**Results area (placeholder, to be filled from real result files only):** four figure slots F1 to F4 with their captions and a link to the raw data.


#### Models and licences

| Model | Licence |
|---|---|
| Qwen2.5-1.5B-Instruct | Apache 2.0 (checked on the model card, 17 Oct 2026) |
| Phi-3.5-mini-instruct (3.8B) | MIT (checked on the model card, 17 Oct 2026) |
| Qwen2.5-7B-Instruct | Apache 2.0 (checked on the model card, 17 Oct 2026) |
| llama.cpp | MIT (project page) |

**Buttons:** Open the repository  |  Run it yourself (guide)  |  Read the design notes


## 12. What's next

| Stage | Where it is |
|---|---|
| Concept | Done: the abstract was accepted at BUILD26. |
| Research and architecture | In progress: node sizes, specifications and the layers of the shared stack. |
| Reference software | Built; real benchmark results to follow. |
| Prototype on existing hardware | Next: simulate and prototype the architecture. |
| Pilot with an institution | Next. |
| Partners to produce the architecture | Open: we are looking for chip and infrastructure partners. |


## 13. Partner with us

**Heading:** We are looking for partners

ECAPs depends on collaboration with chip and compute infrastructure providers, not as competitors to central infrastructure but as partners extending its value into last-mile access, new markets and new demand.


#### Who we want to talk to

- Chip makers and hardware manufacturers.
- Compute and infrastructure providers.
- Institutions and builders who want to host a node.


#### What we would ask

- Co-design a reference edge module that puts memory capacity and memory bandwidth per watt first, with DC and solar-ready power input.
- Supply and pilot access: developer units and help with memory supply for pilots.
- Software and testing support so open models run well on the chosen chip, and a clear path for nodes to call central compute when connected.

**Call to action:** Let's talk. benedictisaac258@gmail.com or +234 904 837 7499.


## 14. Research and sources

| Source | Used for |
|---|---|
| World Bank, Africa Economic Update, October 2026 | 18%, 0.6% and 5% figures |
| Collaborative Inference and Learning between Edge SLMs and Cloud LLMs: A Survey (arXiv 2507.16731, 2025) | Edge and cloud collaboration patterns |
| Edge Computing: Vision and Challenges (IEEE Internet of Things Journal, 2016) | Definition and reasons for edge computing |
| On-Device Language Models: A Comprehensive Review (arXiv 2409.00088) | Model compression and on-device inference |
| Prefill vs Decode: LLM Inference Phases Explained (Redis); Why LLM Decoding Is Memory-Bound (DEV Community) | Why text generation is memory-bound |
| Community Networks and Sustainability: a Survey (arXiv 1707.06898) | Lessons for shared infrastructure |
| Research ICT Africa, Beyond fairness: why justice should guide Africa's AI future (2 July 2026) | Tech Justice framing |
| The Conversation, How a rural community built South Africa's first ISP owned and run by a cooperative (Zenzeleni) | Community-run network example |
| llama.cpp (github.com/ggml-org/llama.cpp) | Inference engine, MIT licence |
| llama.cpp discussion #4167, Performance of llama.cpp on Apple Silicon M-series (Llama 2 7B, 4-bit) | Measured bandwidth and speed in section 6 and on the poster |


## 15. FAQ

| Question | Answer |
|---|---|
| Does ECAPs replace the cloud? | No. It is a complementary layer. Nodes run models locally and call larger cloud models when they need to. |
| Do I need internet to use a node? | No for local work. The node runs the model, the agent loop and local users offline. A connection is used for heavy tasks, updates and remote monitoring. |
| Why not just a Raspberry Pi? | A Raspberry Pi is a good general board. An ECAPs Node is meant to be a complete, managed edge-AI package: reference hardware, preloaded local models, firmware and software to host and manage it, and a solar-ready power design. |
| Are you building a chip? | We are researching and choosing a compute architecture, and plan to partner with an existing provider to produce it. |
| Who runs a shared node? | ECAPs manages it. It does not own it. Users pay per use. |
| Who can get a node? | Anyone: homes, institutions and builders. We expect institutions to use it first. |
| Can it run local-language models? | Yes, that is the plan. Local-language models can run on the same node, including optional support for N-ATLAS. |
| What stage is ECAPs at? | Research and development. The design is proposed and the reference software is a prototype. |


## 16. About and contact

ECAPs is researched and developed by Benedict Isaac, Researcher, ECAPs. The work began in robotics and engineering systems and grew into the question of how to extend AI infrastructure to the last mile.

**Contact block (asset):** Benedict Isaac | benedictisaac258@gmail.com | +234 904 837 7499 | benedictisaac.dev | GitHub: Benedict258 | project repository.

**Footer:** ECAPs, Edge Computing Agentic Processors. Research and development stage. Poster Build26/5P, BUILD26, Abuja.


## Publishing checklist (not part of the page)

| Item | Why |
|---|---|
| Contact details on the page | Done: name, email, phone and website supplied by you. Confirm you are happy for email and phone to be public. |
| Approve the three partner asks in section 13 | Partners means chip makers and compute providers. The asks are drafted and need your OK. |
| Zenzeleni sentence in section 8 | Checked: 2012 start, almost 6,000 people and cooperative-run are in The Conversation article. |
| Make the repository public and link it | You will do this. The page links to it. |
| Fill the results area only from real result files | Placeholders stay until the PC run is done. Never publish mock-data figures. |
| Confirm the N-ATLAS FAQ line | N-ATLAS size and licence are still unchecked; the line only says optional support. |
| Confirm the Abuja sunshine sentence | Based on an old national dataset. Remove it or add a current source. |
| Test the page on a phone and on weak data | The QR code is scanned on phones at the conference. |
| Test the QR code on the printed poster | Scan with two phones from 2 metres. |
