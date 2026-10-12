# Consortium: Customer data export for Tracely

## Decision
Yes. Officially support customer data export, scoped by org and workspace, rate-limited, role-gated and audited. This rests on one member's position, because the other two did not respond in the final round (see Dissent). Treat it as a recommendation to be validated, not a settled consensus.

## Rationale
- **Export already exists.** `tracely export --evals --meta` is in the SDK README (`sdk/tracely_sdk/export.py`), and `backend/tests/test_bulk_export.py` covers the bulk path. An undocumented, unowned export is a worse position than a supported one. (The Strategist)
- **Trust and competitive position.** Langfuse is self-hostable, and LangSmith and Langfuse have shipped clustering and a CI gate. Easy exit removes a lock-in objection against hosted Tracely. (The Strategist)
- **Monetization.** "Export before it expires" makes the free quota, the 90-day OTLP expiry and the open per-plan retention decision easier to defend. (The Strategist)
- **Customer value.** Exported traces, eval scores and calibration labels feed fine-tuning and regression sets, which helps Tracely become a customer's system of record. (The Strategist)
- **Load is manageable by design.** Route exports through the existing PREWHERE-friendly ClickHouse reader, with pagination and per-org limits, and no unbounded `events` scans. (The Strategist)

These claims about the repo come from The Strategist and were not independently verified by the other members.

## Plan
1. **Audit the existing export path.** Confirm that every route resolves scope through `get_project_id` and org membership (migration 0023). Fix any bypass before anything else.
2. **Define scope.** Decide whether v1 covers traces only, or also evaluators, gates, annotations and clusters. A partial export can still read as lock-in.
3. **Harden.**
   - Paginate and apply per-org rate limits.
   - Use the PREWHERE-friendly reader only.
   - Block unbounded `events` scans.
4. **Control access to PII.** Add role gating and an audit log of who exported what and when, since prompts and tool outputs may contain PII.
5. **Document and ship.** Move the CLI from README mention to documented, supported feature. Check whether a UI export exists or is needed.
6. **Tie to retention.** Reference export in the 90-day OTLP expiry and per-plan retention messaging.

## Dissent
None stated. This is not full convergence. The Researcher and The Skeptic did not respond in the final round because of API errors, and their earlier positions are stale and were not carried forward. The Strategist explicitly held, "nothing has been stated, so nothing has moved me." The Strategist expects The Skeptic to raise tenant isolation, PII egress and ClickHouse load, and has treated these as conditions on shipping rather than reasons to withhold. The Strategist's confidence is 0.85. These expected objections are anticipated, not actual.

The Strategist would change position if:
- the bulk path bypasses workspace or org scoping and cannot be fixed cheaply;
- exports cannot be bounded without a major ClickHouse change;
- a compliance or contract constraint forbids bulk egress.

## Open questions for the human
- Does any compliance, contract or customer-agreement constraint restrict bulk data egress?
- What should v1 export scope be: traces only, or also evaluators, gates, annotations and clusters?
- Is the CLI the only export path today, or does a UI export exist or need building?
- Which roles may export, given that prompts and tool outputs may contain PII?
- Do you want to re-run the consortium to get The Researcher and The Skeptic on record, particularly on isolation and ClickHouse load?

---

## Agreement matrix
Row agrees (✓) or disagrees (✗) with column, from each member's final vote.

| | The Strategist | The Researcher | The Skeptic |
|---|---|---|---|
| The Strategist | — | · | · |
| The Researcher | · | — | · |
| The Skeptic | · | · | — |

## Panel
| Label | Lens | CLI | Model |
|---|---|---|---|
| The Strategist | Strategist | Claude Code | claude-sonnet-5-5 · chair |
| The Researcher | Researcher | Codex | gpt-6.1-sol |
| The Skeptic | Skeptic | Gemini CLI | gemini-3.8-flash |

Rounds: 3 · dissent recorded · reported cost $0.21 · 10/6/2026, 11:30:13 AM
