# Portfolio presentation kit

## Project description

Career Match is an explainable resume comparison prototype. It combines dictionary-based skill coverage with TF-IDF similarity and retrieves curated learning material with MiniLM and pgvector. A FastAPI dashboard exposes the full workflow and explains how scores are calculated.

This is an extension of Ko-Bhone/Ai_Job_Match_Platform, not an entirely original system. My revision repairs upload and retrieval failures, defers model loading, makes sequential seeding repeatable, introduces workflow tests and a synthetic evaluation, and adds a dashboard and reproducible demo. Confirm upstream licensing before public redistribution.

## Suggested 90-second recording

| Time | Action | Narration |
| --- | --- | --- |
| 0–15 s | Show `/dashboard` empty state | “This tool compares resume text with a job description and explains the overlap.” |
| 15–30 s | Select Use sample data; point to the job description | “The demo uses a synthetic resume. It recognizes Python, FastAPI, PostgreSQL, Docker, and REST API experience; the role also asks for AWS.” |
| 30–50 s | Select Compare with this role | “The backend stores the documents, extracts skills, and computes a weighted score: 70% skill coverage and 30% text similarity.” |
| 50–65 s | Show score and missing skill | “AWS is missing from the resume. This score measures overlap, not proficiency or hiring success.” |
| 65–80 s | Show learning material | “The learning plan uses skill-filtered vector search over curated content. It reports missing content instead of inventing resources.” |
| 80–90 s | Show evaluation report | “Thirty synthetic development cases exposed a negation error. I added a narrow fix and regression checks. Real-world validation is still future work.” |

Wait for loading to finish before each result shot. The first recommendation may download a model. The browser dashboard uses a different sample sentence from the CLI demo, so their numeric text-similarity scores can differ.

## Screenshot checklist

1. Desktop empty state at approximately 1440 × 1000.
2. Completed synthetic comparison with score breakdown and AWS learning material visible.
3. Mobile layout at approximately 390 × 844, scrolling to check both panels.
4. Evaluation results table and the test run.

Browser capture was unavailable during this implementation. Screenshots and a video have not yet been recorded. Do not present mockups as captured application evidence.

## Run for recording

```powershell
.\.venv\Scripts\python.exe -m app.database.init_db
.\.venv\Scripts\python.exe -m app.services.seed_knowledge
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/dashboard. Use synthetic data. Each comparison persists records and an uploaded file; there is no deletion UI yet.

## Release checklist

- Run evaluation and tests against a dedicated test database.
- Verify the dashboard on desktop and mobile, including malformed PDF and offline/retrieval failure behavior.
- Confirm upstream licensing and retain attribution.
- Review Git changes; never commit `.env`, database files, or real resumes.
- Capture the screenshots and video above.
- Commit the reviewed changes and publish only after choosing hosting, authentication, and data retention requirements.

No public hosting deployment was performed. Source control publication is separate from hosting the application; private source publication does not expose the local CV, account tokens, or database.
