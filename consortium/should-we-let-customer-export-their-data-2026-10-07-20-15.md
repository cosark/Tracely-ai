# Consortium: Customer data export for Tracely

## Decision
Yes, let customers export their data. Write the spec now and ship one release: a hardened version of the existing `/api/export` endpoint plus a UI download button. The release includes calibration labels and human annotations. It is documented as an "analytical export", not an audit-grade snapshot. The same behavior and caps apply on every plan, including free. Async jobs and checksummed manifests are deferred.

## Rationale
- **Trust and adoption.** Export answers lock-in concerns directly, helps stalled evaluations and security questionnaires, and mostly serves fine-tuning and warehouse use cases rather than churn.
- **It is not cheap.** The current export omits annotations (stored in Postgres), uses offset pagination with four queries per conversation, and loads all spans before serializing. The retrieval rework is the main cost of the release.
- **Pagination.** A cursor on `last_ts` would miss conversations, because that field changes when a conversation receives another turn. Selecting a capped list of thread IDs once, upfront, fixes membership without durable jobs.
- **Caps must apply at retrieval.** A single conversation can hold tens of megabytes. Checking size after loading leaves the memory risk in place, so byte and span caps have to be enforced while spans are loaded.
- **Compatibility.** The SDK treats every NDJSON line as a conversation, so a completion record must be opt-in and versioned, not unconditional.
- **Load control.** Per-workspace limits alone cannot protect a shared ClickHouse instance, and an in-process semaphore gives each replica its own allowance. Limits need shared, expiring leases.
- **Async is not a cure.** Moving an expensive scan into a background worker does not make it cheaper. No customer has asked for audit-grade snapshots, so that work waits.

## Plan
1. **Write the spec** covering the items below, then review it.
2. **Completeness.** Include human annotations and calibration labels. Document exactly what is exported.
3. **ID snapshot.** Select a capped list of thread IDs once at the start, then export those IDs.
4. **Retrieval-time caps** on bytes, spans, and duration.
   - Skip any oversized conversation entirely and record its ID and reason.
   - If the total budget runs out, stop and mark the remaining IDs as unexported.
   - Never emit a partial conversation.
5. **Opt-in versioned format** (e.g. a version or `include_summary` parameter) ending with a completion record: IDs selected, IDs exported, skipped IDs with reasons, and whether any cap truncated the export. The UI and updated SDK use it by default. Existing callers see no change.
6. **Concurrency limits.** One export per workspace, plus a limit across all API replicas using TTL-backed leases (Redis or database-backed). Slots are released on disconnect and recover after a process crash.
7. **Busy response.** Reject before streaming starts with HTTP 429, a machine-readable body, and `Retry-After`. The UI shows a friendly "try again in a few minutes" message.
8. **Release gates (all must pass):**
   - cross-project isolation test
   - oversized-conversation test
   - disconnect and crash tests showing capacity becomes available again
9. **Docs** use the "analytical export" wording and state the limits.
10. **Load follow-up.** If a customer asks for a consistent snapshot, or ClickHouse memory or query-time metrics rise after launch, investigate first (batching, stricter limits, scheduling, query tuning). Build async jobs only if that investigation shows they are warranted.

## Dissent
None. All three members ended aligned. Earlier disagreements were resolved in the discussion:
- The Strategist withdrew the claim that export is cheap, the timestamp-and-row-count approach, and the conversation-count cap.
- The Researcher withdrew the async-first design.
- The Strategist moved toward The Engineer on plan gating and the load trigger.

## Open questions for the human
- Which shared store will hold the concurrency leases (Redis or database-backed)? Does the current deployment already have one?
- What are the initial values for the byte, span, duration, and ID-count caps, and for the global concurrency limit?
- Is it acceptable that scores and labels may change during a download, given the "analytical export" framing? Any customer needing a consistent snapshot would trigger the follow-up.
- Should higher caps for paid plans be revisited later as a pricing decision? This release keeps them identical.
- Who owns the spec review and the cross-project isolation verification before the button goes live?

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
| The Strategist | Strategist | Claude Code | claude-sonnet-5-5 · chair |
| The Engineer | Engineer | Codex | gpt-6.1-sol |
| The Researcher | Researcher | Gemini CLI | gemini-3.8-flash |

18 turns · full consensus · reported cost $0.39 · 10/7/2026, 1:10:15 PM
