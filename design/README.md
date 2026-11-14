# Design reference — [Nume aplicație]

Exported from the Claude Design canvas "[Nume aplicație] · Vizibilitate în Gemini" (https://claude.ai/artifact/KZN94BAmNRbhVsZxoocBVp). This folder is the **source of truth for layout, copy and look**. Rebuild the screens in Next.js + Tailwind; do not try to run these files.

## How to read these files

- Each `*.dc.html` file is one artboard. Markup and inline styles are exact: copy spacing, radii, colours and Romanian text from them.
- They use the canvas runtime's custom tags, which are **not** included here (`support.js` is missing on purpose):
  - `<x-dc>` wraps the artboard; `<helmet>` holds fonts and keyframes.
  - `<sc-for list="{{ items }}" as="x">` = a loop (`items.map`).
  - `<sc-if value="{{ cond }}">` = conditional rendering.
  - `<dc-import name="ScoreRing" score="42" …>` = a shared component with props.
  - `{{ value }}` = a binding to what `renderVals()` returns in the `<script type="text/x-dc">` block at the bottom.
  - `class Component extends DCLogic` holds state and mock data (`setState`, timers). Treat it as a behaviour spec: it shows the states, transitions and timings (e.g. 1.5 s generating, toast for 3.2 s).
- Data in `renderVals()` is mock data for Cafeneaua Boema. It matches the demo fixture (overall 42, Gemini 2/12, chapter scores 65/50/35/50/35/25/55/20).
- `canvas.json` lists every artboard with its title, size and position.

## Artboards → routes

| Screen | Desktop (1440 px) | Mobile (390 px) | Route |
| --- | --- | --- | --- |
| 1 · Configurare (chat onboarding) | `Main.dc.html` | `MConfigurare.dc.html` | `/start` |
| Analysis in progress | `Analiza.dc.html` | `MAnaliza.dc.html` | `/scan/[id]/loading` |
| Link can't be read | `Eroare.dc.html` | — | error state on `/start` |
| 2 · Panou principal | `Panou.dc.html` | `MPanou.dc.html` | `/scan/[id]` |
| 3 · Capitol | `Capitol.dc.html` | `MCapitol.dc.html` | `/scan/[id]/[chapter]` |
| Chapter fully solved | `CapitolGol.dc.html` | — | empty state of the chapter route |
| 4 · Rezolvare: Instagram text | `Rezolva.dc.html` | `MRezolva.dc.html` | side panel / bottom sheet on the chapter route |
| 4 · Rezolvare: info page | `FisaInfo.dc.html` | `MFisaInfo.dc.html` | side panel / bottom sheet on the chapter route |
| 5 · Vizibilitate în Gemini | `Gemini.dc.html` | `MGemini.dc.html` | `/scan/[id]/gemini` |
| 6 · Conversații (list) | `Conversatii.dc.html` | `MConversatii.dc.html` | `/scan/[id]/conversatii` |
| 6 · Chat (mark as solved) | `Chat.dc.html` | `MChat.dc.html` | `/scan/[id]/conversatii/[cid]` |
| Score ring component | `ScoreRing.dc.html` | — | `components/ScoreRing.tsx` |
| Desktop sidebar | `Sidebar.dc.html` | — | `components/Sidebar.tsx` |
| Mobile tab bar | — | `TabBar.dc.html` | `components/TabBar.tsx` |
| Design system | `Sistem.dc.html` | — | `tailwind.config` tokens |

## Design tokens (from `Sistem.dc.html`)

- **Font:** Plus Jakarta Sans, weights 400–800 (Google Fonts; covers ă â î ș ț).
- **Accent (the only blue):** `#2563EB` actions and links · `#1D4ED8` hover / active text · `#EAF1FE` selected background · `#C9D8F8` outline-button border · `#1E40AF` outline-button text.
- **Neutrals:** ink `#0F172A` · text `#475569` · muted `#64748B` · border `#E4E9F0` · page `#F6F8FB` · surface `#FFFFFF` · chip/input fill `#F1F4F9`.
- **Score tiers (ring / text / tint):** under 40 `#E5484D` / `#B42318` / `#FDECEC` · 40–69 `#F5A524` / `#B45309` / `#FEF4E2` · 70+ `#2FB36E` / `#157F45` / `#E5F6EC`. Ring track `#E9EEF5`. The number always sits inside the ring.
- **Type scale:** score 56/800 · title 32/800 · section 22/700 · card 17/700 · body 15/500 · small 13/600.
- **Radii:** 14 inputs · 20 small cards · 28 cards · 999 buttons and chips.
- **Spacing:** 4, 8, 12, 16, 24, 32, 48.
- **Motion:** ring fills in 1.1 s ease-out (cubic) with a 6% scale bump at the end · panel/sheet slides in over 280 ms on a dimmed backdrop (`rgba(15,23,42,0.32)`) · toast rises 12 px and stays ~3 s.
- **Light mode only.** No dark mode.

## Shared components to build first

`ScoreRing` (props: `score`, `size`, `thick`, `showMax`, `animateFrom`) · `Sidebar` (active item, open-problem counts per chapter, "Începe de aici" marker) · `TabBar` (Acasă, Gemini, Capitole, Asistent) · `ChapterCard` · `ProblemCard` · `FixPanel` (side panel on desktop, bottom sheet on mobile) · `ChatMessage` + quick-reply chips · `ActionCard` ("Am marcat ca rezolvate" with "Anulează") · `Toast` ("+X puncte").
