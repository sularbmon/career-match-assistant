# Career Match — Explainable Resume Matching API

A backend portfolio project comparing resumes with job descriptions, explaining skill gaps, and retrieving learning material. Built with FastAPI, PostgreSQL, pgvector, and scikit-learn.

## Features

The personal workspace has five focused views: **Today**, **Search**, **Compare**, **Tracker**, and **Accounts**. Today shows due follow-ups, upcoming dates, pipeline counts, and roles that need a next action. The tracker preserves job descriptions for later comparison. Search direction is saved on the local server.

Each saved role also has an opportunity history: contacts, notes, email summaries, scheduled tasks/interviews, submitted documents, and automatic status-change records. Accounts provides a private backup download. See [backup and recovery](docs/BACKUP_AND_RECOVERY.md).

The opportunity assistant reviews saved posting text against a selected CV, quotes skill evidence, surfaces requirements to clarify, and prepares interview prompts and editable email templates. These are deterministic preparation aids, not hiring predictions or automatic messages. Reviewed Gmail header references can be saved to a role's timeline after authorization.

**Live discovery:** Search selected public Lever/Greenhouse company boards, preview descriptions, and save postings directly to Tracker. Source failures and limits are visible; coverage is limited to configured companies. See [job discovery](docs/JOB_DISCOVERY.md).

- Text-based PDF upload, normalization, and dictionary-based skill extraction.
- Persistent resumes, job descriptions, and explainable matching results.
- Weighted skill coverage and TF-IDF cosine similarity.
- MiniLM embeddings and skill-filtered vector retrieval for learning recommendations.
- Database initialization, repeatable knowledge seeding, and workflow regression tests.

This prototype measures text/skill overlap. Its score is not a validated prediction of job performance or hiring success. Recommendations use retrieval and templates, without an external generative LLM.

## Windows setup

Use Python 3.10 and PostgreSQL 17 with the pgvector server extension installed. The Python pgvector package does not install the server extension.

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Skip copying the example if you already have a working `.env`. Save this setting inside that file (not in PowerShell), using your password:

```dotenv
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/ai_job_match_db
```

Create the database once, then initialize and start:

```powershell
psql -h localhost -U postgres -W -c "CREATE DATABASE ai_job_match_db;"
.\.venv\Scripts\python.exe -m app.database.init_db
.\.venv\Scripts\python.exe -m app.services.seed_knowledge
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. The embedding model downloads on the first seed or recommendation request, rather than during API startup. Sequential seed reruns skip unchanged chunks; old duplicates are retained.

Open **http://127.0.0.1:8000/dashboard** for the web workspace. Select **Use sample data**, then **Compare with this role** to demonstrate the full workflow without a personal resume. The dashboard is served by FastAPI; no separate frontend server or build is needed.

For regular use after initial dependency and database setup, run `.\.venv\Scripts\python.exe scripts/run.py` and open `/dashboard#today`. Use the **Compare** view for sample comparisons. The launcher applies additive local schema updates before starting the API.

Starting from scratch? Use the [job-search guide](docs/JOB_SEARCH_GUIDE.md). You can set a direction, open job-board searches, and save roles without a resume. The tracker stores posting links, statuses, notes, and follow-up dates. Resume reuse and evidence-based tailoring prompts support later applications. Run `python -m app.database.init_db` after updating to create the tracker table (the local initializer also permits roles without a comparison).

**My accounts:** preview public GitHub projects, save your LinkedIn profile link, and authorize read-only Gmail header searches with your own local OAuth client. See [account setup and current limits](docs/INTEGRATIONS.md). These are separate from chat account connections. Gmail authorization has not been completed automatically.

### Optional Docker database

`compose.yaml` supplies a separate pgvector database on port **5433**, avoiding the native database on 5432. Add `POSTGRES_PASSWORD=your-local-password` to `.env` and change `DATABASE_URL` to that password and port 5433. Run `docker compose up -d --wait`, then the initialization command above. Local verification used native PostgreSQL; the Compose path has not been exercised locally.

## Demo

With the API running:

```powershell
.\.venv\Scripts\python.exe scripts/demo.py
```

This creates synthetic resume, job, and match records in the local database. In Swagger, use these endpoints in order, substituting returned IDs:

| Step | Endpoint | Input |
| --- | --- | --- |
| Resume | `POST /api/v1/resume/upload` | Text-based PDF up to 10 MB |
| Job | `POST /api/v1/jobs/analyze` | `{"job_description":"Python FastAPI developer with AWS experience"}` |
| Match | `POST /api/v1/matching/match` | `{"resume_id":1,"job_id":1}` |
| Learning plan | `GET /api/v1/rag/recommendations/{match_result_id}` | Match ID |

`GET /health` checks the app; `GET /api/v1/database/health` checks database connectivity.

## Architecture and decisions

```text
Resume PDF / job text → cleaning → skill extraction → PostgreSQL
                                       ↓
                 skill coverage + TF-IDF cosine similarity
                                       ↓
                       persisted matching breakdown
                                       ↓
missing skill → MiniLM embedding → pgvector retrieval → learning material
```

Final score = `0.70 × skill coverage (%) + 0.30 × text similarity (%)`. Skill coverage is the fraction of unique job skills found in the resume. TF-IDF is fitted to the two compared documents, so scores are not calibrated across unrelated jobs. Matching uses TF-IDF; embeddings are used for learning-material retrieval.

Retrieval filters by the normalized missing skill, then orders by cosine distance. Missing curated content is explicitly reported instead of returning unrelated material. The sample knowledge base contains only AWS, NLP, and RAG topics.

| Directory | Responsibility |
| --- | --- |
| `app/api` | HTTP routes |
| `app/schemas` | Request validation |
| `app/services` | Parsing, scoring, embeddings, retrieval |
| `app/models`, `app/database` | Persistence and initialization |
| `data` | Skill aliases and learning material |
| `tests` | Unit, API, and PostgreSQL workflow tests |
| `scripts` | Synthetic demo |

## Tests

The backend suite and page-script regression suite cover different layers. The latter runs actual classic scripts together with a lightweight DOM test double, including delayed requests and role switching; it does not render CSS or replace desktop/mobile browser verification.

Initialize a dedicated test database, set `DATABASE_URL` to it, and run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

With Node.js 24 LTS available, run `node --test tests/frontend/workspace.test.cjs`. This test suite has no npm dependencies. CI is configured to run both suites. See [completion audit](docs/COMPLETION_AUDIT.md) for the remaining external checks.

Tests cover scoring, input validation, database routes, invalid PDFs, vector ranking/filtering, and upload-to-recommendations behavior. New workflow tests roll back records and remove their PDFs. Recommendation embeddings are stubbed in tests to avoid model downloads. GitHub Actions runs against a separate pgvector PostgreSQL service.

## Portfolio revision

- Repaired broken vector search and filtered recommendations by missing skill.
- Deferred embedding model loading until needed.
- Made sequential seed reruns skip unchanged chunks.
- Fixed consumed upload streams, invalid PDFs, size limits, and failure cleanup.
- Fixed timestamp defaults, location-dependent skill paths, and alias boundaries.
- Added database initialization, an environment example, Docker database setup, a synthetic demo, and CI.
- Added a responsive dashboard with sample data, transparent scores, and learning-plan recovery.
- Created 30 synthetic development cases, measured a baseline, and fixed explicit absence statements being counted as experience.

## Evaluation and presentation

```powershell
.\.venv\Scripts\python.exe scripts/evaluate.py
```

See [evaluation methodology and results](docs/EVALUATION.md) and the [portfolio presentation kit](docs/PORTFOLIO.md). On the synthetic development set, extraction precision improved from 98.48% to 100%; all 10 role ranking checks passed before and after. These are regression results, not a real-world hiring benchmark. The presentation kit includes a 90-second narration and screenshot checklist; browser screenshots and video have not yet been captured.

## Limits and next milestones

There is no authentication, tenant separation, OCR, schema migration history, or independent matching-quality benchmark. Resume files and extracted text remain on the server; use synthetic resumes for demos. Dictionary extraction cannot infer proficiency or experience depth; negation handling covers only a few explicit phrases. Seed concurrency is not protected by a unique constraint. Dependencies are currently unpinned. Database initialization supports new local/demo databases, not production schema migrations.

Next milestones: independent held-out evaluation, migration tooling, data deletion/retention, and recorded desktop/mobile browser verification.

## Attribution

Derived from [Ko-Bhone/Ai_Job_Match_Platform](https://github.com/Ko-Bhone/Ai_Job_Match_Platform). The original architecture and initial implementation belong to the upstream project. The portfolio changes above should be distinguished from that work. No license file was present in this checkout; confirm upstream licensing before public redistribution.
