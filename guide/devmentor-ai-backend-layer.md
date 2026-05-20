# DevMentor — AI Layer & Backend Layer
### Complete Technical Instructions

---

## Table of Contents

1. [What We Are Building](#1-what-we-are-building)
2. [Folder Structure](#2-folder-structure)
3. [Database Schema](#3-database-schema)
4. [Core Infrastructure](#4-core-infrastructure)
5. [AI Layer — Multi-Provider Client](#5-ai-layer--multi-provider-client)
6. [AI Layer — Structured Outputs with Instructor](#6-ai-layer--structured-outputs-with-instructor)
7. [AI Layer — Prompts](#7-ai-layer--prompts)
8. [Background Job System — ARQ + Redis](#8-background-job-system--arq--redis)
9. [Research Pipeline](#9-research-pipeline)
10. [Plan Generator](#10-plan-generator)
11. [Jira Integration](#11-jira-integration)
12. [SSE Real-Time Updates](#12-sse-real-time-updates)
13. [API Routes](#13-api-routes)
14. [Auth & Security](#14-auth--security)
15. [Error Handling](#15-error-handling)
16. [Environment Variables](#16-environment-variables)
17. [Full Dependency List](#17-full-dependency-list)

---

---

## 1. What We Are Building

The backend is a **FastAPI** application. It runs as **two separate processes** that share the same codebase:

- **Web process** — serves HTTP requests, OAuth flows, SSE streams
- **Worker process** — runs background jobs (research pipeline, Jira push) via ARQ

Redis is the bridge between them. The web process enqueues jobs into Redis. The worker process picks them up and executes them. Progress events flow back from the worker to the frontend via Redis pub/sub → SSE.

**The full request-to-board flow:**

```
User submits interview
        ↓
POST /interview/submit  →  creates project in DB  →  enqueues ARQ job
        ↓
Frontend opens SSE connection to GET /jobs/{project_id}/sse
        ↓
ARQ Worker runs research_pipeline_task():
  Step 1: Stack analysis (LLM call)
  Step 2: Search query generation (LLM call)
  Step 3: Parallel Exa searches (10–14 async HTTP calls in parallel)
  Step 4: Synthesis (LLM call)
  Step 5: Scope calibration (LLM call)
  Step 6: Plan generation (LLM call)
  → Each step: publishes progress to Redis pub/sub → SSE → frontend
  → Each step: writes output to DB before moving on (crash-safe)
        ↓
Frontend shows read-only plan preview
        ↓
User clicks "Push to Jira"
        ↓
POST /jira/push  →  enqueues jira_push_task()
        ↓
ARQ Worker runs jira_push_task():
  Creates sprints → epics → stories → subtasks → assigns stories to sprints
  → Publishes progress via SSE
  → Stores board URL to DB on completion
        ↓
Frontend redirects to "You're hired" screen with board link
```

---

---

## 2. Folder Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory, CORS, routers, startup events
│   ├── worker.py                # ARQ WorkerSettings: registers job functions, Redis config
│   │
│   ├── core/
│   │   ├── config.py            # All settings via Pydantic BaseSettings (reads .env)
│   │   ├── database.py          # Async SQLAlchemy engine + session factory
│   │   ├── redis.py             # Shared async Redis pool (used by web + worker)
│   │   ├── security.py          # JWT creation/verification, bcrypt password hashing
│   │   ├── encryption.py        # AES-256 encrypt/decrypt for API keys and OAuth tokens
│   │   └── exceptions.py        # Custom exception classes + global exception handlers
│   │
│   ├── api/
│   │   ├── deps.py              # Shared FastAPI dependencies: get_db, get_current_user, get_redis
│   │   └── v1/
│   │       ├── auth.py          # Register, login, refresh token
│   │       ├── interview.py     # Clarification endpoint + interview submit
│   │       ├── jobs.py          # Job status + SSE stream endpoint
│   │       ├── projects.py      # List and get projects
│   │       ├── jira.py          # OAuth start/callback, list sites, push to Jira
│   │       └── settings.py      # AI provider config (save, get, delete)
│   │
│   ├── services/                # All business logic lives here — no DB calls, no HTTP directly
│   │   ├── interview_service.py
│   │   ├── project_service.py
│   │   ├── job_service.py
│   │   ├── jira_service.py
│   │   └── user_service.py
│   │
│   ├── repositories/            # All database queries live here — nothing else touches the DB
│   │   ├── user_repo.py
│   │   ├── project_repo.py
│   │   ├── job_repo.py
│   │   └── jira_token_repo.py
│   │
│   ├── models/                  # SQLAlchemy ORM table definitions
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── job.py
│   │   └── jira_token.py
│   │
│   ├── schemas/                 # Pydantic models for HTTP request/response validation
│   │   ├── interview.py
│   │   ├── project.py
│   │   ├── job.py
│   │   └── user.py
│   │
│   ├── ai/
│   │   ├── client.py            # Multi-provider LiteLLM + Instructor client factory
│   │   ├── prompts/             # One file per prompt — each exports a build_*_prompt() function
│   │   │   ├── clarification.py
│   │   │   ├── stack_analysis.py
│   │   │   ├── query_generation.py
│   │   │   ├── synthesis.py
│   │   │   ├── scope_calibration.py
│   │   │   └── plan_generation.py
│   │   ├── output_models/       # Pydantic models for every LLM structured output
│   │   │   ├── clarification.py
│   │   │   ├── stack_analysis.py
│   │   │   ├── research.py
│   │   │   └── plan.py
│   │   └── pipeline/            # Pure async functions, one per pipeline step
│   │       ├── stack_analysis.py
│   │       ├── search.py
│   │       ├── synthesis.py
│   │       ├── scope_calibration.py
│   │       └── plan_generator.py
│   │
│   ├── jobs/                    # ARQ job functions (what the worker actually executes)
│   │   ├── research_job.py      # Orchestrates all pipeline steps in sequence
│   │   └── jira_push_job.py     # Orchestrates the full Jira creation sequence
│   │
│   └── integrations/
│       ├── exa.py               # Exa search API client
│       └── jira/
│           ├── oauth.py         # Atlassian OAuth 2.0 (3LO): build URL, exchange code, refresh
│           ├── client.py        # Jira REST API async client with auto token refresh
│           ├── push.py          # High-level functions: create_epic, create_story, etc.
│           └── adf.py           # Converts plain text / markdown to Atlassian Document Format
│
├── alembic/                     # Database migrations
│   └── versions/
├── tests/
├── .env.example
├── pyproject.toml
└── Dockerfile
```

**Rules that must be respected throughout:**
- Routers only: validate input schema, call one service method, return response. Zero logic.
- Services only: business logic, calling repositories and external services. Never import SQLAlchemy directly.
- Repositories only: all DB queries. Return ORM models or plain dicts. Never contain business logic.
- AI pipeline functions: pure async functions that take typed inputs and return Pydantic output models. No DB access.
- Job functions: orchestrate pipeline steps, handle DB checkpointing, publish SSE progress. The only place that calls both pipeline functions AND repositories.

---

---

## 3. Database Schema

Six tables. Use SQLAlchemy async ORM with Alembic for migrations.

---

### `users`
Standard user table. `password_hash` is nullable because later you may add Google/GitHub OAuth login.

Fields: `id` (UUID PK), `email` (unique), `name`, `password_hash` (nullable), `created_at`

---

### `ai_provider_configs`
Stores the user's chosen AI provider and BYOK API key. One active config per user. The `api_key_enc` field stores the API key encrypted with AES-256 — never store raw API keys.

Fields: `id`, `user_id` (FK → users), `provider` (enum: `openai | groq | openrouter | together | custom`), `model_name`, `base_url` (nullable — only for custom endpoints), `api_key_enc`, `is_active` (boolean), `created_at`

**Important:** only one row per user can have `is_active = true`. Enforce this in the repository update method, not in the DB constraint.

---

### `projects`
The central table. One row per user planning session. Stores the entire lifecycle: from raw interview answers all the way to the final Jira board URL. Uses JSONB for the nested structured fields because they are always read/written as complete units and their shape evolves.

Fields:
- `id`, `user_id` (FK → users)
- `entry_type` — `"tech_only" | "idea_only" | "both"`
- `raw_idea` — the user's free-text description, stored exactly as typed
- `tech_stack` — JSONB: `{primary, additional, gaps}`
- `skill_level` — `"just_starting" | "knows_basics" | "comfortable"`
- `constraints` — JSONB: `{hours_per_week, timeline_weeks, total_hours, goal, planning_style}`
- `clarifications` — JSONB array: `[{question, answer}]`, default `[]`
- `stack_analysis` — JSONB: output of Step 1, null until complete
- `research_brief` — JSONB: output of Step 4 synthesis, null until complete
- `scoped_features` — JSONB: output of Step 5 calibration, null until complete
- `plan_json` — JSONB: the full `FullPlan` object, null until complete
- `jira_cloud_id`, `jira_site_name`, `jira_project_key`, `jira_board_id` (int), `jira_board_url`
- `jira_created_keys` — JSONB: tracks `{sprint_1: 42, epic_epic_1: "PROJ-1", ...}` for idempotent push retries
- `status` — `"draft" | "researching" | "planning" | "ready" | "pushing" | "pushed" | "failed"`
- `created_at`, `updated_at`

---

### `jobs`
Tracks background jobs. One row per ARQ job. Keeps state so the frontend can query status without hitting Redis directly.

Fields: `id`, `project_id` (FK → projects), `type` (`"research_pipeline" | "jira_push"`), `arq_job_id` (ARQ's internal ID), `status` (`"queued" | "running" | "completed" | "failed"`), `progress` (JSONB: `{stage, done, total, message}`), `error` (text, nullable), `created_at`, `updated_at`

---

### `jira_tokens`
OAuth tokens for Jira. Both tokens encrypted at rest with AES-256. Unique constraint on `(user_id, cloud_id)` — one token set per Jira site per user.

Fields: `id`, `user_id` (FK → users), `cloud_id`, `site_name`, `access_token_enc`, `refresh_token_enc`, `expires_at` (timestamptz), `created_at`

---

**On JSONB vs normalized tables:** The plan, research brief, and stack analysis are deeply nested structures (plan alone has epics → stories → subtasks → sprints). They are always read and written as complete atomic units — never queried field by field. Normalizing them into separate tables would add 10+ joins and a migration every time the shape changes during development. JSONB is the right call here. If you later need to query specific fields (e.g. "all projects using Next.js"), add a GIN index on that specific JSONB path.

---

---

## 4. Core Infrastructure

### `core/config.py`
Use `pydantic-settings` `BaseSettings`. All config reads from environment variables with type validation. Group settings logically:

- **App**: `APP_ENV`, `SECRET_KEY`, `ENCRYPTION_KEY` (32-byte key for AES-256)
- **Database**: `DATABASE_URL` (async postgres DSN: `postgresql+asyncpg://...`)
- **Redis**: `REDIS_URL`
- **JWT**: `JWT_SECRET_KEY`, `JWT_ALGORITHM` (HS256), `ACCESS_TOKEN_EXPIRE_MINUTES` (30), `REFRESH_TOKEN_EXPIRE_DAYS` (30)
- **AI (default)**: `OPENAI_API_KEY`, `DEFAULT_CHEAP_MODEL` (gpt-4o-mini for light tasks), `DEFAULT_SMART_MODEL` (gpt-4o for plan generation)
- **Exa**: `EXA_API_KEY`
- **Jira OAuth**: `JIRA_CLIENT_ID`, `JIRA_CLIENT_SECRET`, `JIRA_REDIRECT_URI`

### `core/database.py`
Create an async SQLAlchemy engine using `asyncpg`. Create an `AsyncSessionLocal` factory. Export a `get_async_session()` async context manager and a FastAPI dependency `get_db()` that yields a session and closes it after the request.

### `core/redis.py`
Create a single async Redis connection pool using `redis.asyncio`. Export `get_redis_pool()` which returns the shared pool. Import this in both the web process (for SSE subscriptions) and the worker process (for pub/sub publishing). Never create a new connection per request — always use the pool.

### `core/encryption.py`
Implement AES-256-GCM encrypt and decrypt functions using `cryptography` library. The encryption key comes from `settings.ENCRYPTION_KEY`. Use this for: API key storage (`ai_provider_configs.api_key_enc`), Jira token storage (`jira_tokens.access_token_enc`, `refresh_token_enc`). Never store sensitive credentials in plain text.

---

---

## 5. AI Layer — Multi-Provider Client

### How it works

Every AI call goes through `ai/client.py`. It exposes one function: `get_ai_client(config)` that returns an **Instructor-patched async client**. The caller never interacts with LiteLLM or OpenAI SDK directly — it just calls `client.chat.completions.create(response_model=SomePydanticModel, messages=[...])` and gets back a validated Pydantic object.

### Provider routing logic

There are two cases:

**Case 1 — Standard providers (OpenAI, Groq, OpenRouter, Together):**
Use `litellm.acompletion` with the model name prefixed by the provider: `"groq/llama-3.1-70b"`, `"openrouter/meta-llama/llama-3.1-405b"`, `"openai/gpt-4o"`. LiteLLM handles all the request format differences between providers. Patch the litellm async completion function with `instructor.from_litellm()`.

**Case 2 — Custom / OpenAI-compatible endpoint (OpenCode.go, Ollama, vLLM, self-hosted):**
Use `AsyncOpenAI` SDK directly with `base_url` overridden to the user's custom endpoint. This works for any OpenAI-compatible API. Patch with `instructor.from_openai()`.

### BYOK vs Default

- **Free tier users**: use `get_default_ai_client()` which uses DevMentor's own OpenAI API key. Use `DEFAULT_CHEAP_MODEL` for clarification and query generation (low token cost). Use `DEFAULT_SMART_MODEL` for synthesis and plan generation (needs more intelligence).
- **BYOK users**: use `get_ai_client(user.ai_config)` which decrypts their stored key and routes to their chosen provider/model.

### Instructor mode

Always use `instructor.Mode.JSON` unless the provider natively supports structured outputs (OpenAI with `gpt-4o` supports `Mode.JSON_SCHEMA` which is stricter). Use `Mode.JSON` as the safe default across all providers for maximum compatibility.

---

---

## 6. AI Layer — Structured Outputs with Instructor

### The problem Instructor solves

Raw LLM JSON mode fails 5–20% of the time in production — the model wraps output in markdown fences, uses wrong field names, or truncates midway. Never use raw JSON mode and `json.loads()` in production.

### How Instructor works

You define a Pydantic model describing the shape you want. You pass it as `response_model=YourModel` to the Instructor-patched client. Instructor converts the Pydantic model into a JSON schema and passes it to the LLM. When the response comes back, it validates it against the schema. If validation fails, it automatically constructs a correction prompt (including the validation error) and retries — up to `max_retries` times. You get a fully typed, validated Pydantic object back. No parsing, no try/except around json.loads().

### All output models to define

Define these in `ai/output_models/`. Each is a Pydantic `BaseModel`. Add `Field(description=...)` to every field — Instructor includes these in the schema it sends to the model, and descriptive field metadata measurably reduces validation failures.

**`clarification.py` — `ClarificationOutput`**
- `questions: List[ClarificationQuestion]` — max 4, ordered by importance
- Each `ClarificationQuestion`: `id`, `question` (friendly tone, max 2 sentences), `why_it_matters` (internal — how the answer changes the plan), `is_critical` (bool), `suggested_options: List[str]` (2–3 short example answers, or empty)
- `confidence_assessment: str` — one sentence about how clear the input was

**`stack_analysis.py` — `StackAnalysisOutput`**
- `confirmed_stack: List[str]` — what the user explicitly mentioned, normalized
- `decisions: List[TechDecision]` — each gap filled with a recommendation
- Each `TechDecision`: `category` (e.g. "database"), `recommended`, `rationale` (1–2 sentences calibrated to skill level), `alternatives: List[str]`, `is_required: bool`
- `complete_stack: List[str]` — confirmed + all recommendations combined
- `folder_structure: str` — recommended top-level structure as ASCII tree
- `skill_assessment: str` — one sentence: is this stack appropriate for the user's level?

**`research.py` — `SearchQueryList`, `ResearchBriefOutput`**
- `SearchQueryList.queries: List[SearchQuery]` — 10–14 queries, each with `query`, `purpose`, `priority` (1–3)
- `ResearchBriefOutput`: `final_stack_decisions`, `architecture_notes`, `must_have_features: List[str]`, `nice_to_have_features: List[str]`, `cut_features: List[str]`, `beginner_traps: List[BeginnerTrap]`, `learning_resources: List[LearningResource]`, `estimated_hours_per_feature: dict`
- Each `BeginnerTrap`: `task_area`, `trap` (1 sentence), `how_to_avoid` (1–2 sentences)
- Each `LearningResource`: `topic`, `url`, `description` (1 sentence)

**`plan.py` — `FullPlan`**
- `epics: List[Epic]` — each with `id`, `name`, `description`, `color`
- `stories: List[Story]` — each with `summary` (user story format), `description`, `story_points` (Fibonacci: 1–13), `priority` (Highest/High/Medium/Low), `sprint_number`, `epic_id`, `subtasks: List[Subtask]`
- Each `Subtask`: `summary` (action-oriented title, max 10 words), `description` (see prompt section for exact format), `estimated_hours: float`
- `sprints: List[Sprint]` — each with `number`, `name`, `goal` (outcome statement: "By end of this sprint, you should be able to..."), `story_ids: List[str]`, `duration_weeks`
- `total_estimated_hours: float`
- `plan_summary: str` — 2–3 sentence overview for the user

---

---

## 7. AI Layer — Prompts

All prompts live in `ai/prompts/`. Each file exports a single `build_*_prompt(context, ...) -> list[dict]` function. Prompts are never inline f-strings scattered in job functions. They take typed inputs and return OpenAI-format message lists.

### Rules for all prompts

- The system message defines role, constraints, and quality bar. Keep it tight and specific.
- The user message injects the actual project context: idea, stack, constraints, clarifications.
- Never put variable context in the system message — it belongs in the user message.
- Always include the user's skill level and total available hours in every prompt. These two numbers change everything about tone, recommendations, and scope.
- Use negative constraints ("Never recommend X", "Do not ask about Y") — they prevent common LLM drift.

### Clarification prompt

System: Senior engineer identifying gaps before planning. Rules: only ask if the answer meaningfully changes the plan, max 4 questions, never ask about things with safe defaults, never re-ask what was already answered in constraints.

User message injects: raw idea, confirmed stack, skill level description, hours/week, timeline, goal.

### Stack analysis prompt

System: Technical architect completing a project's tech stack. Calibrate recommendations to skill level explicitly: beginners → simplest thing that works (Clerk over custom auth, Prisma over raw SQL); intermediate → industry standard. Never recommend bleeding-edge or poorly-documented tools.

User message injects: project idea, mentioned stack, clarification Q&A.

### Query generation prompt

System: Generates precise Exa search queries. Rules: be specific (include version/year), include "beginner" or "step by step" for beginners, cover docs + best practices + common mistakes + time estimates + deployment. Generate 10–14 queries.

User message injects: project idea, skill level, complete stack from stack analysis, gaps to research.

### Synthesis prompt

System: Synthesizes research into a project brief. Rules on feature scoping: be honest about what fits, beginners spend 30–50% more time than experts, core functionality first. Only link to official docs or well-known tutorials.

User message injects: stack decisions, formatted search results (title + snippet per hit, top 3 hits per query).

**Important:** do not dump all raw search results into the prompt. Format them first: query → top 3 results as bullet `title: snippet`. Keep each snippet under 800 characters. Total search results section should be under 8,000 tokens.

### Scope calibration prompt

System: Calibrates a feature list to a fixed time budget. Math: take `total_hours`, assign realistic per-feature estimates for the skill level, mark features as must-have / nice-to-have / cut based on what fits. Sprint distribution: divide total hours by hours per sprint, assign features to sprints in dependency order.

User message injects: research brief, constraints.

### Plan generation prompt

This is the most important prompt in the system. Quality bar: a developer following these tickets should be able to build the entire project without asking anyone for help beyond what the tickets already say.

System: Senior tech lead writing a plan. Per-skill-level story point calibration (beginners: 2–3x expert speed; intermediate: 1.5–2x). Exact subtask description format to follow:

```
**What this is:** [1–2 sentences plain English]
**Why in this order:** [1 sentence — what would break if this was done later]
**Steps:** [numbered, with actual commands and code snippets where relevant]
**Beginner trap:** [the one specific mistake that will cost them hours]
**Verify it worked:** [how to confirm the task is complete]
**If stuck, search:** "[specific quoted Google query]"
```

Sprint goals are outcome statements, not task lists. Every sprint goal starts with "By the end of this sprint, you should be able to..."

User message injects: project idea, research brief (full), scoped feature list with sprint assignments.

---

---

## 8. Background Job System — ARQ + Redis

### Why ARQ over Celery

The entire pipeline is async — all LLM calls, Exa calls, and Jira API calls are `await`-based. ARQ is async-native: all tasks run inside a single async event loop, so 50 concurrent I/O operations (parallel Exa searches, batched Jira API calls) run in one process with no forking. Celery has no native async/await support — using it with async code requires hacks and loses all the concurrency benefits. ARQ also natively stores job status in Redis, which is exactly what the SSE progress endpoint needs.

### Worker setup (`worker.py`)

Create an ARQ `WorkerSettings` class with:
- `functions` — list of all job functions: `[research_pipeline_task, jira_push_task]`
- `redis_settings` — from `settings.REDIS_URL`
- `max_jobs = 10` — max concurrent jobs per worker instance
- `job_timeout = 300` — kill and mark failed if job runs longer than 5 minutes
- `on_startup` — async function that initializes shared resources and stores them in `ctx`: db session factory, redis pool
- `on_shutdown` — async function that closes the redis pool

Run the worker with: `arq app.worker.WorkerSettings`

### Job enqueuing

When the interview is submitted, the web process enqueues a job using the Redis pool. Use a deterministic `_job_id` (e.g. `f"research:{project_id}"`) to prevent duplicate jobs if the frontend retries the submit. Immediately create a row in the `jobs` table with `status="queued"` and the ARQ job ID for frontend status polling.

### Checkpoint pattern (crash safety)

Every pipeline step must check if its output already exists in the DB before running. If it does, skip the LLM call and use the stored output. This means if the worker crashes mid-pipeline, ARQ retries the job and it resumes from the last completed step — not from the beginning. This is especially important because plan generation is a ~30-second LLM call you don't want to repeat unnecessarily.

Pattern for every step:
1. Check if `project.{step_output_field}` is not null in DB
2. If not null → load it as the Pydantic model and skip to next step
3. If null → run the step, validate output, write to DB, then proceed

### Progress publishing pattern

After each step, publish a progress event to Redis pub/sub channel `devmentor:progress:{project_id}`. The event is a JSON object: `{stage, done, total, message, timestamp}`. Also write the current progress to the `jobs` table so SSE clients that connect mid-job can get the current state immediately without waiting for the next event.

---

---

## 9. Research Pipeline

The research pipeline runs entirely inside `jobs/research_job.py` as a single ARQ job function. It calls pure functions from `ai/pipeline/` in sequence.

### Step 1 — Stack Analysis

Call `run_stack_analysis(ai_client, context)` from `ai/pipeline/stack_analysis.py`. This is a single Instructor LLM call that returns `StackAnalysisOutput`. Publish progress: "Analyzing your tech stack..." Write output to `project.stack_analysis`.

### Step 2 — Search Query Generation

Call `run_query_generation(ai_client, context, stack_analysis)`. Returns `SearchQueryList` with 10–14 queries. Do not write this to DB — it's transient. Publish: "Identifying what to research..."

### Step 3 — Parallel Exa Search

This is the most important step for output quality. Implementation in `ai/pipeline/search.py`:

Selection logic: always include all priority-1 queries. Fill up to 14 total with priority-2. Add priority-3 only if under 10 total. Fire all selected queries simultaneously with `asyncio.gather()`. Each query hits the Exa API with `type: "neural"` (semantic search), `numResults: 5`, `useAutoprompt: true` (Exa rewrites the query for better results), and `contents.text.maxCharacters: 800`.

Handle individual failures gracefully: if one query fails (network error, rate limit), store an empty result for that query and continue. A degraded research set is better than a failed pipeline. Publish: "Researching {n} topics in parallel..."

### Step 4 — Synthesis

Call `run_synthesis(ai_client, context, stack_analysis, search_results)`. Before calling the LLM, format the search results: for each query, take the top 3 hits and format as `"Query: {q}\n- {title}: {snippet}\n..."`. Cap each snippet at 800 chars. This keeps the prompt under the context window budget. Returns `ResearchBriefOutput`. Write to `project.research_brief`. Publish: "Synthesizing research findings..."

### Step 5 — Scope Calibration

Call `run_scope_calibration(ai_client, context, research_brief)`. This LLM call takes the research brief and the user's exact time budget and returns a calibrated feature list with sprint assignments. Returns a `ScopedFeatureList` Pydantic model. Write to `project.scoped_features`. Publish: "Calibrating scope to your timeline..."

### Step 6 — Plan Generation

Call `run_plan_generation(ai_client, context, research_brief, scoped_features)`. This is the most expensive call — use the smart model regardless of which model is used for other steps (if on free tier, use `DEFAULT_SMART_MODEL`). Returns `FullPlan`. Write to `project.plan_json`. Update `project.status` to `"ready"`. Publish final event: `{event: "complete", project_id}` which signals the SSE stream to close.

---

---

## 10. Plan Generator

The plan generator (`ai/pipeline/plan_generator.py`) is a single Instructor call that produces a `FullPlan`. A few important implementation details:

**Use `max_retries=3`** in the Instructor call. The FullPlan schema is deeply nested and large — retries are important.

**Use `temperature=0.3`** not 0. Zero temperature makes the model overly repetitive across stories. 0.3 gives slight variation in wording while keeping structure consistent.

**After getting the FullPlan back, run a post-validation check** — not just Pydantic schema validation, but referential integrity:
- Every `story.epic_id` must reference an ID that exists in `plan.epics`
- Every `sprint.story_ids` element must reference a story that exists
- The sum of `story.story_points` per sprint should not wildly exceed the target hours

If these checks fail, raise a `ValueError`. Instructor will catch it, include the error in the correction prompt, and retry. This catches the most common plan generation error: the LLM hallucinating an epic ID that doesn't exist.

---

---

## 11. Jira Integration

### OAuth 2.0 (3LO) Flow

Implement in `integrations/jira/oauth.py`. There are four functions:

1. **`build_authorization_url(state)`** — builds the Atlassian consent URL with scopes: `read:jira-work write:jira-work read:jira-user offline_access`. The `state` parameter is a CSRF token — generate it per session and verify it in the callback. Required param: `offline_access` scope — without this you don't get a refresh token.

2. **`exchange_code_for_tokens(code)`** — POSTs to `https://auth.atlassian.com/oauth/token` to get `access_token` and `refresh_token`. Store both encrypted in `jira_tokens` table. Store `expires_at = now() + expires_in seconds`.

3. **`refresh_access_token(refresh_token)`** — Atlassian uses rotating refresh tokens. When you refresh, you get a new refresh token too. Always update both tokens in the DB. Handle this automatically in the Jira client (see below).

4. **`get_accessible_resources(access_token)`** — hits `https://api.atlassian.com/oauth/token/accessible-resources` to get the list of Jira sites the user has access to. Returns `[{id (cloud_id), name, url}]`. This is what populates the "select your Jira site" dropdown.

### OAuth Callback Route

In `api/v1/jira.py`:
- `GET /jira/oauth/start` → verify user is logged in, generate CSRF state token, store in Redis with 10-minute TTL keyed to user ID, redirect to Atlassian auth URL
- `GET /jira/oauth/callback` → verify state matches what's in Redis, exchange code for tokens, encrypt and store tokens, redirect to frontend with `?jira_connected=true`

### Jira REST API Client

Implement in `integrations/jira/client.py` as an async class. Base URL is `https://api.atlassian.com/ex/jira/{cloud_id}/rest`.

The client needs one central `_request(method, path, **kwargs)` method that:
- Adds `Authorization: Bearer {access_token}` header
- On 401: refreshes the token, updates DB via callback, retries the request once
- On 429: reads `Retry-After` header (default to exponential backoff if absent), sleeps, retries up to 3 times
- Raises a custom `JiraAPIError` on other 4xx/5xx responses with the status code and response body

Methods to implement: `create_sprint()`, `create_issue()`, `assign_issues_to_sprint()`, `get_projects()`, `create_board()`.

### Jira Push Sequence

Implement in `jobs/jira_push_job.py`. The creation order is strict — Jira has dependencies:

1. **Create sprints** via `POST /agile/1.0/sprint`. Store `sprint_number → jira_sprint_id` mapping in `project.jira_created_keys`.
2. **Create epics** via `POST /api/3/issue` with `issuetype: Epic`. Store `epic_{id} → jira_issue_key` (e.g. `PROJ-1`) in `project.jira_created_keys`.
3. **Create stories** via `POST /api/3/issue` with `issuetype: Story`. Set `customfield_10014` (epic link) to the epic's Jira key. Set `customfield_10016` (story points). Set `priority`. Create in batches of 10 with `asyncio.gather()` within each batch and a 500ms sleep between batches to avoid rate limits. Store `story_{summary_hash} → jira_issue_key`.
4. **Create subtasks** via `POST /api/3/issue` with `issuetype: Subtask` and `parent: {key: story_key}`. Also batch these.
5. **Assign stories to sprints** via `POST /agile/1.0/sprint/{sprint_id}/issue`. Group all story keys by sprint_id and fire one call per sprint.

**Idempotency:** before creating any item, check if its key already exists in `project.jira_created_keys`. If it does, skip creation and use the stored key. Write the updated `jira_created_keys` to DB after every batch. This means the push job is safe to retry from any point.

### Atlassian Document Format (ADF)

Jira's API rejects plain text and Markdown in description fields. You must convert to ADF (a JSON format). Implement `integrations/jira/adf.py` with a `markdown_to_adf(text: str) -> dict` converter.

Key conversions to handle:
- Paragraphs → `{type: "paragraph", content: [...]}`
- `**bold**` → text node with `marks: [{type: "strong"}]`
- `` `inline code` `` → text node with `marks: [{type: "code"}]`
- ` ```code block``` ` → `{type: "codeBlock", attrs: {language: "..."}, content: [...]}`
- Numbered list `1. item` → `{type: "orderedList", content: [{type: "listItem", ...}]}`
- Headings `**What this is:**` → `{type: "paragraph"}` with strong mark (Jira subtasks don't render heading nodes well — use bold paragraphs instead)

---

---

## 12. SSE Real-Time Updates

### Architecture

The worker publishes to a Redis pub/sub channel: `devmentor:progress:{project_id}`. The FastAPI SSE endpoint subscribes to this channel and streams the events to the browser. Redis pub/sub is the right tool here because: the publisher (worker process) and subscriber (web process) are different OS processes; pub/sub is built for exactly this one-to-many event streaming pattern.

### SSE Endpoint

Implement `GET /api/v1/jobs/{project_id}/sse` using `sse_starlette`'s `EventSourceResponse`.

The async generator inside the endpoint must:
1. First, fetch the current job progress from DB and send it immediately — this handles clients that connect after the job has already started (they get the current state instantly, not just future events).
2. Subscribe to the Redis pub/sub channel for this project.
3. Yield each message as it arrives. Each message is a JSON object.
4. On terminal events (`complete`, `jira_complete`, `failed`) — break the loop and return. This closes the SSE connection cleanly.
5. In a `finally` block — always unsubscribe and close the pub/sub connection. Memory leak if you skip this.

Set response headers: `Cache-Control: no-cache`, `X-Accel-Buffering: no` (the second one prevents Nginx from buffering SSE events, which would break the real-time behavior).

### Heartbeat

Send a heartbeat event every 30 seconds to keep the connection alive through proxies and load balancers that close idle connections. The heartbeat is a comment line (`: heartbeat`) in the SSE stream — the browser ignores it but it keeps the TCP connection open.

### Frontend

Use the browser's native `EventSource` API in a custom React hook `useJobProgress(projectId)`. EventSource auto-reconnects on dropped connections — no manual reconnect logic needed. Close the EventSource on terminal events and on component unmount.

---

---

## 13. API Routes

Complete route specification. All routes under `/api/v1/`. All protected routes require `Authorization: Bearer {access_token}` header.

### Auth (public)
- `POST /auth/register` — body: `{email, password, name}` → `{user, access_token, refresh_token}`
- `POST /auth/login` — body: `{email, password}` → `{access_token, refresh_token}`
- `POST /auth/refresh` — body: `{refresh_token}` → `{access_token, refresh_token}`

### Settings (protected)
- `GET /settings/ai-provider` → `{provider, model_name, base_url, has_key: bool}` (never return the raw key)
- `POST /settings/ai-provider` — body: `{provider, model_name, base_url?, api_key}` → 200. Encrypts and stores the key.
- `DELETE /settings/ai-provider` → 200. Removes BYOK — user falls back to default.

### Interview (protected)
- `POST /interview/clarify` — body: full Stage 1–3 data → `{questions: [...]}`. This is the lightweight AI call that runs synchronously (not as a background job) because it's fast and the user is waiting.
- `POST /interview/submit` — body: full context including clarification answers → `{project_id, job_id}`. Creates the project, enqueues the research job, returns immediately.

### Jobs (protected)
- `GET /jobs/{project_id}/status` → `{status, progress: {stage, done, total, message}}`. Polling fallback if SSE fails.
- `GET /jobs/{project_id}/sse` → SSE stream. Returns `EventSourceResponse`.

### Projects (protected)
- `GET /projects` → `[{id, status, title, created_at}]`
- `GET /projects/{id}` → full project including `plan_json` (once `status = "ready"`)

### Jira (protected)
- `GET /jira/oauth/start` → 302 redirect to Atlassian consent URL
- `GET /jira/oauth/callback` → verifies state, exchanges code, stores tokens, 302 redirect to frontend
- `GET /jira/sites` → `[{cloud_id, name, url}]` — requires connected Jira account
- `GET /jira/projects/{cloud_id}` → `[{key, name}]`
- `POST /jira/push/{project_id}` — body: `{cloud_id, project_key}` → `{job_id}`. Stores Jira target on project, enqueues push job.

---

---

## 14. Auth & Security

### JWT Strategy

Two tokens per session:
- **Access token** — short-lived (30 minutes). Sent in `Authorization: Bearer` header on every request.
- **Refresh token** — long-lived (30 days). Sent only to `POST /auth/refresh` to get a new access token. Store the refresh token in the DB (or a Redis set) so you can invalidate it on logout.

Use `python-jose[cryptography]` for JWT. Use `bcrypt` via `passlib` for password hashing.

### FastAPI Auth Dependency

Create `get_current_user` in `api/deps.py`. It reads the Bearer token from the request header, decodes and validates the JWT, fetches the user from DB. Inject it into protected routes with `Depends(get_current_user)`. Any route using this dependency is automatically protected.

### API Key Encryption

Before storing any user API key or Jira token: encrypt with AES-256-GCM using the `ENCRYPTION_KEY` from settings. Never log, print, or return raw keys. When you need to use the key (to make an API call), decrypt in memory, use it, and let it be garbage collected. The decrypted key should never touch the DB or logs.

### CORS

Configure CORS in `main.py` to allow only the Next.js frontend origin. In development: `http://localhost:3000`. In production: your actual domain. Never use `allow_origins=["*"]` in production.

### Jira OAuth CSRF

Generate a random `state` token per OAuth flow. Store it in Redis keyed to `jira_oauth_state:{user_id}` with a 10-minute TTL. Verify it matches the `state` param in the callback. Reject if it doesn't match or has expired. This prevents CSRF attacks on the OAuth flow.

---

---

## 15. Error Handling

### Custom Exception Classes (`core/exceptions.py`)

Define these exception classes:
- `DevMentorError(Exception)` — base class
- `NotFoundError(DevMentorError)` — 404
- `AuthError(DevMentorError)` — 401
- `ForbiddenError(DevMentorError)` — 403
- `ValidationError(DevMentorError)` — 422
- `AIProviderError(DevMentorError)` — LLM call failed after retries
- `JiraAPIError(DevMentorError)` — Jira API call failed, stores `status_code` and `response_body`
- `JiraRateLimitError(JiraAPIError)` — rate limit hit after all retries
- `JobNotFoundError(NotFoundError)` — ARQ job ID not found

### Global Exception Handlers

Register these in `main.py` using `@app.exception_handler(ExceptionClass)`:
- `DevMentorError` subtypes → return appropriate HTTP status with `{error: message}` JSON body
- `RequestValidationError` (Pydantic input validation) → 422 with detailed field errors
- Unhandled `Exception` → 500, log the full traceback, return generic `{error: "Internal server error"}`

Never leak stack traces or internal error details to the client in production. Log everything server-side.

### Pipeline Error Handling

In `research_job.py` and `jira_push_job.py`, wrap the entire job in a try/except. On any unhandled exception:
1. Update `job.status = "failed"` and `job.error = str(exception)` in DB
2. Update `project.status = "failed"` in DB
3. Publish a `{event: "failed", error: message}` event to the Redis pub/sub channel so the frontend can show an error state
4. Re-raise the exception so ARQ marks the job as failed (not re-queued — we don't retry pipeline failures automatically; the user should re-submit)

---

---

## 16. Environment Variables

```
# App
APP_ENV=development
SECRET_KEY=<random 32+ char string>
ENCRYPTION_KEY=<exactly 32 bytes, base64 encoded — for AES-256>

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/devmentor

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=<random 64+ char string>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# AI — DevMentor default (free tier)
OPENAI_API_KEY=sk-...
DEFAULT_CHEAP_MODEL=gpt-4o-mini
DEFAULT_SMART_MODEL=gpt-4o

# Exa Search
EXA_API_KEY=...

# Jira OAuth
JIRA_CLIENT_ID=...
JIRA_CLIENT_SECRET=...
JIRA_REDIRECT_URI=http://localhost:8000/api/v1/jira/oauth/callback

# Frontend URL (for redirects after OAuth)
FRONTEND_URL=http://localhost:3000
```

---

---

## 17. Full Dependency List

```toml
[tool.poetry.dependencies]
python = "^3.11"

# Web framework
fastapi = "^0.115"
uvicorn = {extras = ["standard"], version = "^0.30"}
python-multipart = "*"          # for form data

# Database
sqlalchemy = {extras = ["asyncio"], version = "^2.0"}
asyncpg = "*"                   # async PostgreSQL driver
alembic = "*"                   # migrations

# Background jobs
arq = "*"                       # async task queue
redis = {extras = ["asyncio"], version = "^5.0"}  # Redis client

# AI
litellm = "*"                   # multi-provider LLM routing
instructor = "*"                # structured LLM outputs via Pydantic
openai = "*"                    # base SDK (used directly for custom endpoints)

# HTTP client (for Exa + Jira API calls)
httpx = "*"

# SSE
sse-starlette = "*"

# Auth & Security
python-jose = {extras = ["cryptography"], version = "*"}
passlib = {extras = ["bcrypt"], version = "*"}
cryptography = "*"              # AES-256 for encrypting API keys

# Config
pydantic-settings = "*"

# Utilities
python-dateutil = "*"

[tool.poetry.dev-dependencies]
pytest = "*"
pytest-asyncio = "*"
httpx = "*"                     # for TestClient in tests
pytest-mock = "*"
```

---

---

## How Everything Connects — Final Summary

```
User submits interview wizard
        ↓
POST /interview/clarify  (sync — fast AI call)
  └─ interview_service → get_default_ai_client() → Instructor → ClarificationOutput
        ↓
POST /interview/submit
  └─ project_service → project_repo.create() → arq.enqueue(research_pipeline_task)
  └─ job_repo.create(status="queued")
  └─ returns {project_id, job_id}
        ↓ (browser opens SSE connection)
GET /jobs/{project_id}/sse
  └─ subscribes to Redis pub/sub channel devmentor:progress:{project_id}
        ↓ (worker picks up job)
research_pipeline_task(ctx, project_id, user_id)
  └─ get_ai_client(user.ai_config) OR get_default_ai_client()
  └─ Step 1: stack_analysis  → LLM → StackAnalysisOutput → project_repo.update()
  └─ Step 2: query_gen       → LLM → SearchQueryList (transient)
  └─ Step 3: parallel_search → Exa (asyncio.gather) → raw results
  └─ Step 4: synthesis       → LLM → ResearchBriefOutput → project_repo.update()
  └─ Step 5: scope_calib     → LLM → ScopedFeatureList → project_repo.update()
  └─ Step 6: plan_gen        → LLM (smart model) → FullPlan → project_repo.update()
  └─ publish {event: "complete"} → Redis pub/sub
        ↓ (SSE delivers "complete" → frontend shows plan preview)
User clicks "Push to Jira"
        ↓
POST /jira/push/{project_id}
  └─ jira_service → project_repo.update(jira_cloud_id, project_key)
  └─ arq.enqueue(jira_push_task)
        ↓ (worker picks up job)
jira_push_task(ctx, project_id, user_id)
  └─ jira_token_repo.get() → decrypt tokens → JiraClient
  └─ Create sprints → epics → stories (batched) → subtasks (batched) → assign to sprints
  └─ Each batch: project_repo.update(jira_created_keys) [checkpoint]
  └─ publish {event: "jira_complete", board_url: "..."}
        ↓ (SSE delivers "jira_complete" → frontend redirects to "You're hired" screen)
```
