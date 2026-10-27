# Personal assistant completion audit

Objective: make the project useful as a personal job-search assistant that finds, saves, tracks, and prepares opportunities in one place, while retaining a credible AI/ML portfolio story.

This audit keeps the full objective visible. Implemented features and passing unit tests do not prove that external account connections or the browser experience are complete.

| Requirement | Current evidence | Status |
| --- | --- | --- |
| Personal CV, portfolio, and profile | Latest CV imported locally; profile is outside Git; live opportunity review checked against the saved CV | Implemented and locally checked |
| Find and save real opportunities | Public Lever/Greenhouse search; live Lever feed and running-app search checked; save/deduplication tests preserve existing notes | Implemented; coverage limited to selected boards |
| Track applications, follow-ups, and next actions | PostgreSQL records; Today view; status and date regression tests | Implemented; visual browser checks pending |
| Keep documents, contacts, correspondence, and preparation together | Opportunity histories, exact-file download test, task completion tests, email-reference deduplication | Implemented; live Gmail import pending |
| Useful preparation assistance | Evidence quotes, requirement excerpts, interview prompts, editable draft templates; live CV review and nonmutation tests | Implemented; deterministic assistance, not an LLM agent |
| GitHub account context | Public project preview checked against the user's account; private repo authorization is not implemented | Partial: public context available |
| LinkedIn account context | User-confirmed profile link saved; full authenticated history sync is not implemented | Partial: profile link and CV evidence available |
| Gmail connection | User completed OAuth setup; the running app's Gmail search returned HTTP 200 on 2026-10-27 | Live read access verified; default job-search query returned zero headers, so real-message save-to-role remains unverified |
| Preserve the workspace | Snapshot ZIP, checksums, secrets excluded; isolated restore checked against all current tables | Verified locally; backups are manual and unencrypted |
| Avoid overwriting the wrong role | Real page scripts exercised with delayed/reordered responses; stale-form version rejection tested in backend | Verified by automated regression tests, not a browser |
| Easy daily use | Five focused views, one-command launcher, setup and usage guides | Visual desktop/mobile verification still required |
| Portfolio evaluation and attribution | 30 synthetic development cases, baseline/current reports, tests, source attribution | Implemented; no independent real-world quality claim |
| Screenshots and demo video | Narration and capture checklist prepared | Not complete: browser capture unavailable |
| Automated validation | 74 backend tests pass in a fresh isolated database; 9 JavaScript tests run all page scripts against a DOM test double | Locally verified; hosted CI not executed |

## External steps currently needed

- Gmail read access is now verified. Apply the job-search label to relevant correspondence or adjust the query, then verify saving a real message reference to a chosen role. A chat Gmail connection remains separate from this local authorization.
- Browser: connect Chrome or Edge for desktop/mobile UI checks and capture. The user indicated they can make a browser available; no browser was available at the last check.
- LinkedIn/private GitHub: decide whether linked public context and uploaded CV are sufficient for current daily use. Full LinkedIn employment-history sync cannot be promised from the standard basic identity scopes. Private GitHub data requires a separate, deliberately scoped app integration.

The goal remains active. Do not mark it complete from the green test count alone. External authorization, user-visible browser verification, and requested capture artifacts remain unproven.
