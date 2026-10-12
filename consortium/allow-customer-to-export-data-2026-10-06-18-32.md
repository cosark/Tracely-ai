# Consortium: Customer data export for Tracely

## Decision
Ship the existing NDJSON conversation export as a documented, discoverable, workspace-level UI feature. Settle who may call it before it is advertised. Describe it narrowly as "conversation records in NDJSON, including scores and span steps". Evaluators, scenarios and annotations are deferred until they have a defined, versioned portable format.

## Rationale
- The backend already does the hard work. `GET /api/export` streams workspace conversations in pages, and the single-thread endpoint uses the same payload builder (`backend/tracely/api/routers/sessions.py:126`, `sessions.py:212`). The SDK and CLI support it too (`sdk/tracely_sdk/export.py:75`). Tests cover pagination, limits, auth and metadata filtering (`backend/tests/test_bulk_export.py:72`). Rebuilding any of this would be wasted effort.
- The gap is customer access. The frontend only has a per-session proxy (`frontend/app/api/sessions/[id]/export/route.ts`). A hosted-cloud customer asking "can I leave?" should not need the CLI.
- The endpoint accepts ingest keys as well as human sessions, and the payload contains prompts, outputs and tool data. The access policy has to be decided before a button makes the feature prominent.
- The current payload is not a full workspace backup. Marketing it as one would over-promise.
- The two members converged on this scope and ordering.

## Plan
1. **Decide the access policy.** Confirm whether ingest-key access to bulk export is intentional. Then restrict bulk export to owner or admin roles, or to a separate read credential.
2. **Add the workspace-level frontend proxy** for the bulk export endpoint, modelled on the existing per-session proxy.
3. **Add an "Export" button** in workspace settings, with a DocLink in the existing style. The button states the scope: conversation records, NDJSON, scores and span steps.
4. **Write the docs.** Describe the format and the entry points (UI, CLI/SDK), and list what is not included.
5. **Add a per-project concurrency or rate limit.** Each conversation is assembled from several sequential reads, and prod ClickHouse is sensitive to query load. Monitor query load and export duration.
6. **Later, as a separate effort,** define a versioned archive format for evaluators, scenarios and annotations.
7. **Fallback for very large workspaces:** a background job with a download link, reusing the `purge_project` queue pattern.

## Dissent
None. Both members ended at the same position. The Strategist conceded on the workspace-level UI entry point and on staging. The Engineer conceded that the CLI alone does not answer the hosted buyer's question.

## Open questions for the human
- Is ingest-key access to bulk export intentional or an oversight? This is the main security risk.
- Is the driver a practical conversation download, analytics, or a compliance requirement such as GDPR portability and deletion? Compliance would change the scope, format and priority.
- Has any customer asked for this, or is a customer evaluating the hosted plan? If not, docs alone may be enough for now.
- How large are the biggest workspaces? This decides whether streaming is enough or a background job is needed.

---

## Agreement matrix
Row agrees (✓) or disagrees (✗) with column, from each member's final vote.

| | The Strategist | The Engineer |
|---|---|---|
| The Strategist | — | ✓ |
| The Engineer | ✓ | — |

## Panel
| Label | Lens | CLI | Model |
|---|---|---|---|
| The Strategist | Strategist | Claude Code | claude-sonnet-5-5 · chair |
| The Engineer | Engineer | Codex | gpt-6-luna |

Rounds: 3 · full consensus · reported cost $0.22 · 10/6/2026, 11:31:56 AM
