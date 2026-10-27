# Evidence Grounded Paper Review

Local-first MVP for reviewing one scientific paper with evidence that can be opened at its original PDF page or DOCX paragraph. The user uploads the main paper, optionally selects uploaded related work, defines a qualitative rubric, runs the harness, edits findings, verifies edits and approves a Markdown report.

The stack is FastAPI, Next.js/Node.js, LangGraph and Groq API. Four logical agents are hosted by the custom harness: Supervisor, Scientific Review, Related-Work Comparator and Evidence Verifier. The harness calls one worker at a time and controls tools, run scope, context, checkpoints, budgets and output validation. MarkItDown converts PDF/DOCX to Markdown; independent extraction resolves citations to original source positions.

## Run locally with Docker Desktop

1. Install and start Docker Desktop.
2. Copy `.env.example` to `.env`. The default `DEMO_LLM_MODE=fixture` runs without an API key. To use Groq, set `DEMO_LLM_MODE=groq` and provide `GROQ_API_KEY` in `.env`. The key is passed to the backend only.
3. From the repository root, run:

   ```powershell
   docker compose up --build -d
   docker compose ps
   ```

4. Open [http://localhost:3000](http://localhost:3000). FastAPI docs are at [http://localhost:8000/docs](http://localhost:8000/docs).
5. To load the example library, run:

   ```powershell
   docker compose exec backend python -m app.demo.seed
   ```

   The command can be run again safely. From the browser, open **Bản review**, select `Demo · Evidence Links Pilot`, the `Demo · Scientific Review` rubric and optionally `Demo · Related Study`, then create a draft and run it. Fixture mode labels every report and is only a workflow demonstration.
6. Inspect the actual decisions, skipped agents, tool permissions, contexts, checkpoints and evidence-gate results in the run inspector. Open a finding's source link to compare it with the original version.
7. Stop the services with `docker compose down`. The `app_data` named volume keeps uploads, database records, run checkpoints and approved exports. `docker compose down -v` also deletes that volume.

Useful commands:

```powershell
docker compose logs -f backend
docker compose restart backend
docker compose up --build -d
```

The app is designed for one local user and one backend worker process. Scanned PDFs without a text layer are rejected; OCR, automatic web search and Literature Review are later extensions. DOCX citations point to paragraphs; PDF citations point to pages.

## Project map

```text
backend/app/api/v1/          FastAPI controllers and Pydantic views
backend/app/domain/          Domain models, repository ports and policies
backend/app/services/        CRUD, run orchestration, approval and report
backend/app/infrastructure/  SQLAlchemy, SQLite, local files, Groq/fixture
backend/app/ingestion/       MarkItDown and original-source locators
backend/app/agents/          Four LangGraph agent contracts and prompts
backend/app/harness/         Loop, state, tools, context, permissions, gate
backend/app/workers/         Single local checkpointed worker
frontend/src/app/            Library, rubric, review and run inspector
demo_data/                   Small generated PDF/DOCX fixture documents
docs/architecture/           MVC/MVT and harness diagrams
docs/api/                     REST resource contract
```

## Development checks

Backend commands (run from repository root):

```powershell
python -m pip install -e "./backend[dev]"
$env:PYTHONPATH = "backend"
pytest backend/tests -q
pylint backend/app --rcfile=backend/pyproject.toml
pycodestyle backend/app backend/tests backend/migrations
```

Frontend commands (run in `frontend/`):

```powershell
npm ci
npm run lint
npm run build
npm run test:e2e
```

Playwright's end-to-end flow needs the fixture backend and Next.js running at ports 8000 and 3000. Start Compose in fixture mode, then run `npm run test:e2e` in another terminal under `frontend/`. No Groq key is required. See [MVC/MVT and patterns](docs/architecture/mvc.md), [harness design](docs/architecture/harness.md), [REST contract](docs/api/rest-contract.md), [approved design](docs/superpowers/specs/2026-10-26-ai-paper-review-design.md) and [step-by-step plan](docs/superpowers/plans/2026-10-26-paper-review-mvp.md).
