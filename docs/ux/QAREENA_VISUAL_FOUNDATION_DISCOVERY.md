# Qareena Visual Foundation — Phase 0 Discovery

**Run ID:** `qareena-visual-foundation-20260901`  
**Figma:** [Qareena Low-Fidelity Wireframes — Gate Approved](https://www.figma.com/design/L6FRBHQ4M3Q7ik1OV5Fwzi)  
**Phase:** 0 — Discovery  
**Status:** Awaiting Phase 1 approval

## P0.a — Code source of truth

The live visual source is the root CSS block in `app.py`. There are no dedicated production token files. The audit-report theme under `outputs/` is a generated report asset and is not a Qareena product token source.

### Current color contract

| CSS token / usage | Value | Proposed primitive |
|---|---|---|
| `--page` | `#F4F7F5` | `neutral/50` |
| `--panel` | `#FFFFFF` | `neutral/0` |
| `--panel-soft` | `#F8FBF9` | `neutral/25` |
| sidebar background | `#EEF4F1` | `neutral/75` |
| `--ink` | `#17211F` | `neutral/800` |
| `--muted` | `#66736E` | `neutral/500` |
| `--line` | `#DBE7E1` | `neutral/200` |
| inverse surface | `#101917` | `neutral/900` |
| `--teal` | `#0B6B53` | `brand/500` |
| gradient teal | `#167D62` | `brand/600` |
| gradient dark teal | `#134F42` | `brand/700` |
| `--teal-soft` | `#E5F2EE` | `brand/50` |
| text on brand | `#E8F6F1` | `brand/100` |
| `--amber` | `#B87918` | `status/amber/600` |
| `--blue` | `#1C5D99` | `status/blue/600` |
| `--rose` | `#A73F54` | `status/rose/600` |
| inverse primary text | `#F5FBF8` | `inverse/primary` |
| inverse secondary text | `#C7D9D2` | `inverse/secondary` |
| chart neutral | `#6F7F78` | `data/neutral` |
| forecast downside | `#B84A4A` | `data/downside` |

### Current shape and elevation contract

- Radius values in production: `8`, `10`, `12`, and `999px`.
- Repeated shadows: `0 10 26 / 6%`, `0 12 28 / 6–16%`, `0 14 30 / 7%`, `0 16 34 / 16%`.
- Layout max width: `1540px`.
- Existing spacing is local and irregular (`.35rem`, `.55rem`, `.65rem`, etc.); it is not a named token system.

### Typography conflict

- Code stack: `Segoe UI, Tahoma, Arial, sans-serif`.
- None of those families is available in the Figma file.
- Cairo Regular/Medium/SemiBold/Bold is available and already used by the approved Low-Fidelity frames.

## P0.b — Existing Figma file

| Item | Existing |
|---|---:|
| Pages | 1 — `Qareena Low-Fidelity` |
| Low-Fidelity top-level frames | 29 |
| Local variable collections | 0 |
| Local variables | 0 |
| Local text styles | 0 |
| Local effect styles | 0 |
| Local grid styles | 0 |
| Local components | 0 |

The approved Low-Fidelity page remains immutable during Visual Foundation work.

## P0.c — Library discovery

Material 3, Simple Design System, and Apple community libraries are subscribed. Simple Design System includes generic color, spacing, radius, type, and shadow assets, but its brand semantics and typography do not match Qareena. Decision: use it as a structural reference only; do not import its brand tokens into Qareena foundations.

## P0.d — Proposed v1 scope

### Collections and variables

| Collection | Modes | Planned variables |
|---|---:|---:|
| `Primitives` | Value | 20 color primitives |
| `Color` | Light | 22 semantic aliases |
| `Dimension` | Value | 10 spacing + 6 radius |
| `Typography` | Value | 1 family + 4 styles + 9 sizes + 8 line heights |
| **Total** | **4 modes** | **80 variables** |

All primitive scopes will be empty. Semantic colors, spacing, radius, and typography will use specific scopes. Every variable will receive WEB code syntax. Existing CSS names are preserved where they exist; new normalized tokens use a documented future `--qareena-*` contract without changing production code in this phase.

### Styles

- 10 Cairo-based text styles: Display, Heading, Body, Label, and Metric roles.
- 4 effect styles matching current production shadow recipes.
- 2 grid styles: Desktop 12-column and Mobile 4-column.

### Explicitly out of scope

- Components and variants.
- Applying color or typography to the 22 wireframes.
- Dark mode; no production source exists for it.
- Product code or CSS changes.
- New features or IA changes.

## P0.e — Code → Figma resolution

| Topic | Code | Figma | Resolution |
|---|---|---|---|
| Brand colors | Defined in `app.py` | No local tokens | Code values win |
| Token architecture | Flat CSS variables + local values | Empty | Create primitive/semantic split; preserve CSS mapping |
| Spacing | Irregular local values | Empty | Normalize to a 4px foundation; no code change now |
| Radius | 8/10/12/full | Empty | Preserve all production values |
| Shadows | Four recurring recipes | Empty | Create four effect styles |
| Typography | Segoe/Tahoma/Arial | Cairo on Low-Fidelity | User approval required: adopt Cairo for Figma foundation |
| Dark mode | None | None | Light mode only |
| Community libraries | Generic systems | Subscribed | Reference only; no brand-token import |

## P0.f — Gap analysis

### Code exists, Figma missing

- All Qareena color, spacing, radius, typography, effect, and grid foundations.
- Semantic roles for KPI evidence, status, forecast, and inference displays.

### Figma exists, code missing

- Cairo is currently a Figma-only font choice used by the Low-Fidelity frames.
- Community-library tokens exist remotely but are not Qareena source truth.

### Conflicts requiring approval

1. Typography: keep an unavailable system-font contract, or adopt Cairo as the Figma Visual Foundation. Recommendation: adopt Cairo because Qareena is Arabic-first and it is available in all required weights.
2. New normalized spacing tokens do not yet exist in code. Recommendation: define them in Figma as the future contract, without changing product CSS in this phase.

## Phase 0 exit status

P0.a–P0.f are complete. Phase 1 may start only after explicit approval of the proposed scope and the Cairo/normalized-spacing resolutions.
