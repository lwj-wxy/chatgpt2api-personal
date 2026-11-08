# 0003: Image route evidence and parameter capabilities

Status: pending-verification

- Owner: ChatGPT2API
- Created: 2026-10-21
- Related ADRs: 0002, 0003, 0004 (unchanged)

## Problem and user outcome

The Model Catalog exposes Flare and Sunburst names through one Web `auto`
conversation route. A successful image is not evidence that either image engine
was selected. Users need truthful model selection, target sizes and quality,
and Call Records that distinguish requested parameters from measured results.

## Evidence and scope

Live model/init reads exposed no independent Flare/Sunburst selector. One
generation per compatibility name returned an image and conversation metadata
`gpt-6`, without an image model or quality identifier. This does not establish
that no other upstream interface could select those engines.

Keep existing routing; publish per-model profiles, label compatibility entries,
offer target size presets through 4K with explicit Web prompt semantics, reject
malformed/oversized parameters before account acquisition, and record measured
source/delivery dimensions. Explicit image tool result metadata is the only
source of actual image-model/quality claims. Conversation model identifiers and
tool arguments must never become image-engine evidence.

Non-goals: official API integration, new credentials, invented upstream flags,
forced image engines, enabling local upscaling, new aliases or storage migrations.

## Owners and interfaces

| Concern | Owner | Consumers |
| --- | --- | --- |
| Wire model mapping and parameter limits | `utils.helper` | Backend adapter, protocol, catalog |
| Capability projection | `ModelCatalogService`, `contracts.models` | Studio via `/api/model-catalog` |
| Request-local upstream observations | `OpenAIBackendAPI` | Image protocol |
| Source/delivery measurements | Image protocol formatter | Call Record metadata |
| Private metadata filtering and persistence | `LoggedCall` | Call Record detail projection |
| Human-facing result fields | `request_detail_view` | Generic detail drawer |
| Catalog transport validation | `useModelCatalog` | Studio form runtime |
| Draft selection/layout/focus | Studio runtime/composer | Browser |

Profiles are additive to schema 1; clients may still consume legacy catalogs.
No new database schema or persistent owner is introduced. Evidence travels in
existing private response metadata and is stripped from public responses.
Existing admission, retries, quota checks and submission guards remain intact.

## Acceptance and verification

- [x] Flare/Sunburst compatibility status is visible in the model picker.
- [x] Size/quality options come from the backend profile, with prompt/native semantics.
- [x] Bad parameters fail before upstream/account activity.
- [x] Logs distinguish request, conversation route, reported image engine/quality,
  measured source dimensions, delivery dimensions and local resizing.
- [x] Missing evidence, including historical records, remains unknown.
- [x] Backend regressions, targeted frontend runtime checks, production build,
  desktop/mobile browser checks and post-deploy real generation have evidence.

The original frontend runtime suite is absent from this checkout (its first
entry `local-icons-runtime.mjs` is missing); this must be reported separately
from targeted checks. User acceptance remains pending after agent checks.

Agent validation: 133 backend tests and 22 subtests passed; 7 targeted frontend
runtime checks and the production build passed. Independent read-only review
found no remaining blockers after correcting Codex wire-model facts and binding
image evidence to the delivered asset. Browser checks covered eight routes,
desktop and 390×844 mobile, with no relevant console errors or document overflow.

Post-deploy calls through the website: Image-2 generation 17.263s,
1536×1024 requested/delivered; Flare edit 22.424s, 2048² requested and 1254²
delivered; Sunburst generation 21.213s, 4096² requested and 1254² delivered.
Each succeeded with one attempt and one image. The 2.5 calls reported the
conversation model `gpt-6`, not an image engine; actual image model/quality
remain unknown. These timings are individual functional checks, not a benchmark.

## Documentation and rollback

The 2026-10-22 resolution update uses the same preset matrix as ToolOrbit. The
16:9 targets are 1536×864 (1K), 2560×1440 (2K), and 3840×2160 (4K).
Presets preserve exact aspect ratios, use multiples of 16, have no edge above
3840 pixels, and remain within 655,360–8,294,400 pixels. The 4K group is a pixel
budget tier rather than a promise of a 4096-pixel edge: its square preset is
2880×2880. Sizes above 3,686,400 pixels remain experimental under the official
image API guidance; those API limits are not evidence that the Web route
supports native size control.

Web requests now explicitly ask for native canvas width, height and aspect
ratio. Automatic size/quality values do not become literal prompt targets.
The existing Web wire protocol remains unchanged and `size_mode=prompt_hint`
remains accurate. If the tool cannot control the requested size, its original
image is retained without asking it to fabricate a native higher-resolution
result. Acceptance of a size parameter is not native-size success; compare
the measured source and delivered dimensions. No new automatic retry,
postprocessing, provider switch or account-status change is introduced.

References: [OpenAI image tool size contract](https://developers.openai.com/api/reference/resources/responses/methods/create),
[image model size constraints](https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide).

Update Backend Map, CONTEXT and CHANGELOG. No new ADR: existing domain ownership
and storage boundaries are retained. Deployment backs up runtime Python files
and console assets, verifies baseline hashes and restores both on failure.
