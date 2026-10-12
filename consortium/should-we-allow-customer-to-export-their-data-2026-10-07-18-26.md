# Consortium: Customer Data Export for Tracely

## Decision

**Yes, customers should be able to export their data.** Tracely already ships partial export: per-conversation JSON (`backend/tracely/api/routers/sessions.py:126`), workspace-wide streamed NDJSON (`sessions.py:212`), and the `tracely export` CLI. These are prototypes, so we will not market "complete archives" yet. We will roll out in four phases:

1. **Fix the documentation now** so it matches what export actually does.
2. **Ship scoped API keys and admin-only async archive jobs.** Each job builds a manifest of IDs at start, writes a sealed and checksummed artifact, expires it after a fixed time, and is cancelled if the workspace is purged.
3. **Retire legacy-key reads on a published date**, across the whole read surface.
4. **Build filtered dataset export** (by judge verdict or cluster) on the same manifest infrastructure.

The stronger "complete archive" promise ships only after the acceptance checks in the Plan pass.

## Rationale

- **Export wins deals.** Data portability is a standard requirement in enterprise procurement. Competitors offer it, and Langfuse is open source. Holding raw traces hostage is a weak moat. Our real differentiation is the analysis layer: detection, clustering, regression gates and calibrated judges.
- **Export is also a feature, not just an exit door.** Customers often export traces to build fine-tuning datasets or load internal warehouses. Filtered export ("every trace the judge failed in cluster X") makes our analysis the reason to stay.
- **The real risk is overpromising.** Losing a customer more easily is a minor risk. The bigger one is promising "all your data" and then delivering archives that silently drop or duplicate conversations. Today's code has several problems:
  - Bulk export runs four database queries per conversation.
  - It uses offset pagination over a list that changes during the export.
  - It filters spans by `start_time` before grouping, so a conversation started yesterday can appear in today's window with contents outside the window.
- **Unthrottled bulk export hurts every tenant.** ClickHouse memory in production grows with query traffic, so heavy exports compete with normal use.
- **Why each design choice:**
  - *Frozen ID manifest:* defines completeness, handles spans that arrive late, and stops records drifting in or out between pages when cluster or verdict membership changes.
  - *Sealed artifact with checksum:* makes retries return the same file instead of re-reading data that has since changed. Customers can verify the download themselves.
  - *Status wording:* "N of N written to the artifact" is accurate. "Delivered" would overclaim, because the server can't know what reached the customer.
- **Window semantics:** keep span-timestamp filtering, since storage is span-indexed, and document it plainly. Conversation-start windows are withdrawn unless a customer asks for them.
- **Key scoping:** ingest keys can currently read the whole surface: export, session listing, conversation fetch, and the `/api/gate/suite` endpoint used by `tracely gate` and `tracely replay`. The key table has no scope field. Blocking only `/api/export` would fix nothing, so the whole read surface needs scoped keys. Cutting off ingest-key export abruptly would break workflows we have documented and that customers probably rely on.
- **Lifecycle:** a sealed artifact is a full copy of customer data in MinIO. Without expiry, purge integration and in-flight cancellation, we could still hold a downloadable copy of a workspace the customer deleted. That is exactly the finding that loses procurement reviews.

## Plan

**Phase 1: Documentation (this week)**
- Update `docs/pages/api-reference.mdx:228`:
  - `--from-ts` / `--to-ts` filter on **span start time**, not conversation start.
  - Add a concrete example: a conversation begun yesterday can qualify through a span today, and its exported contents can fall outside the window.
  - Exported contents reflect what was read during the export, not a point-in-time snapshot.
  - Conversation export returns JSON; bulk export returns NDJSON.
  - Judge scores and verdicts are included. Cluster membership is not.

**Phase 2: Scoped keys and async archive jobs**
- Add key scopes: ingest, read, regression (gate/replay), and export. Existing keys keep their legacy behaviour during migration, and every legacy-key read is logged.
- Archive jobs:
  - Only OWNER/ADMIN can create them, using the existing `require_role("OWNER", "ADMIN")`. Every run is logged.
  - The manifest of eligible IDs is frozen when the job is created. The count and IDs are shown to the customer up front. Later arrivals require a new export.
  - Use keyset pagination in a background job instead of offset streaming.
  - The artifact is sealed, validated against the manifest, and given a SHA-256 checksum before completion is published as "N of N written to the artifact".
  - Downloads require authorization again. A failed download fetches the same artifact rather than re-extracting.
  - Artifacts expire after a fixed TTL (7 days proposed).
  - `tracely.purge_project` deletes export artifacts. A workspace wipe cancels running jobs, revokes download access immediately, and blocks cancelled jobs from ever publishing.
- **Acceptance checks, all required before any "complete archive" claim:**
  - Selection stays stable while traces arrive and conversations update.
  - Each manifest ID appears exactly once, including after an interrupted job resumes.
  - The artifact's checksum and contents verify against the manifest.
  - Purging during an in-flight export leaves no artifact published afterward.

**Phase 3: Legacy-key retirement**
- Once scoped keys work in the CLI and CI, publish a **calendar** deprecation deadline (not "one release later"), using telemetry on legacy-key reads. Enforce from that date across the whole read surface.

**Phase 4: Filtered dataset export**
- Filter by judge verdict or cluster at manifest-creation time, reusing the Phase 2 infrastructure. This is backlogged until Phase 2 passes acceptance.

## Dissent

None. All three members converged and each lists no remaining disagreement. The Engineer adds one caveat, about readiness rather than direction: existing export routes and queued purge tasks are building blocks, not proof that archive jobs work. The stronger promise depends on the acceptance checks passing.

## Open questions for the human

1. **Plan gating:** should bulk/archive export be available on every plan, as The Engineer suggested for basic export, or tiered? The Strategist raised this and the table never resolved it.
2. **TTL length:** is 7 days right for archive artifacts, or do contracts or compliance needs call for a different value?
3. **Deprecation deadline:** how long a notice period after scoped keys ship in the CLI and CI, and who owns the customer communication?
4. **Cluster membership in archives:** deferred indefinitely. Do you want it on the roadmap, and should it reflect state at export time or current state?
5. **Conversation-start windows:** withdrawn for now. Is there any known customer demand that would bring them back?
6. **Prior-art claims:** several arguments relied on statements about how other vendors (Datadog, PostHog, Langfuse, Snowflake, and others) handle export and key scoping. These were not verified at the table, so it's worth checking any that will appear in external positioning or security documentation.
7. **Storage cost:** sealed artifacts duplicate customer data in MinIO. Should there be per-workspace limits on concurrent or total export jobs?

---

## Agreement matrix
Row agrees (✓) or disagrees (✗) with column, from each member's final vote.

| | The Strategist | The Engineer | The Researcher |
|---|---|---|---|
| The Strategist | — | ✓ | ✓ |
| The Engineer | ✓ | — | ✓ |
| The Researcher | ✓ | ✓ | — |

## Panel
| Label | Lens | CLI | Model |
|---|---|---|---|
| The Strategist | Strategist | Claude Code | claude-opus-5-5 · chair |
| The Engineer | Engineer | Codex | gpt-6.1-sol |
| The Researcher | Researcher | Gemini CLI | gemini-3.8-flash |

21 turns · full consensus · reported cost $1.32 · 10/7/2026, 11:18:21 AM
