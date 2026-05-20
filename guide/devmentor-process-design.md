# DevMentor — Complete Process Design
### From user arrival to Jira board, end to end

---

## Overview

The app has three phases that flow into each other:

```
Phase 1: Extraction    →    Phase 2: Research    →    Phase 3: Jira Creation
(What does the user         (What do we need            (Turn everything into
 actually need?)             to know to plan it?)         a real board)
```

Each phase is designed around one core principle: **the user should never feel like they're filling out a form or being interrogated.** They should feel like they just got handed to a senior engineer who knows exactly what to ask, does their homework, and comes back with a real plan.

---

---

# PHASE 1 — EXTRACTION
## Getting everything we need from the user

---

### The core problem with this phase

Most apps ask users to fill out a form. Name, stack, deadline, experience level — checkboxes and dropdowns. The problem: beginners and intermediate developers **don't know what they don't know.** 

A user who says "I want to build a React app" doesn't know they need to tell you they've never touched a database, that they work 5 hours a week, that they get stuck when debugging, and that they have two months. You have to **pull** that out of them intelligently — not ask them to declare it upfront.

The solution is a **hybrid UI**: structured wizard stages for things that have known good answers (tech stack, time), and a conversational AI step for everything that's fuzzy (idea clarity, scope, ambiguity resolution).

---

### The five extraction stages

#### Stage 1 — Entry Point Detection (UI, ~30 seconds)

The very first screen does one thing: figure out what the user is bringing.

Three paths, presented as large visual cards — not a dropdown:

```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  I have a tech I    │  │  I have a project   │  │  I have both —      │
│  want to learn      │  │  idea in mind       │  │  a tech + an idea   │
│                     │  │                     │  │                     │
│  "I want to learn   │  │  "I want to build   │  │  "I want to build   │
│   Next.js"          │  │   a budget tracker" │  │   a todo app with   │
│                     │  │                     │  │   React"            │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

**Why this matters for the backend:** Each path activates a different extraction flow. Path 1 means we need to suggest a project idea. Path 2 means we need to suggest a tech stack. Path 3 is the full flow. The AI research phase also changes based on this — if we're suggesting the idea, we research "good beginner/intermediate projects for X stack."

**Backend:** Store `entry_type: "tech_only" | "idea_only" | "both"` on the session. This flag controls the subsequent stages.

---

#### Stage 2 — The Core Input (UI + smart text fields, ~2 minutes)

Based on entry type, show the relevant inputs. These are **not forms** — they are large, friendly text areas with placeholder examples that feel like a conversation.

**If "tech only":**
```
What tech or framework do you want to work with?
[ Next.js                                        ]

What's your experience with it?
○ Heard of it, never used it
○ Done a tutorial or two  
○ Built something small with it
○ Comfortable, want to go deeper
```

**If "idea only":**
```
Describe your project idea in plain English — don't overthink it:
[ I want to build a budget tracker where I can add         ]
[ expenses and see charts of where my money is going      ]

What tech do you want to use? (leave blank if unsure)
[ not sure yet                                            ]
```

**If "both":**
```
What do you want to build?
[ A recipe sharing app                                    ]

What tech stack are you working with?
[ React + Node.js                                         ]

How comfortable are you with this stack?
○ Just starting out
○ Know the basics, want to apply them
○ Comfortable, want to build something real
```

**Why free text over dropdowns for the idea:** Dropdowns and radio buttons give you categorical data. Free text gives you signal about how clearly the user has thought this through. A user who writes "I want to build something with React" needs different treatment than one who writes "A recipe app where users can sign up, post recipes with photos, and follow each other." The AI in Stage 4 uses this signal.

**Backend:** Save raw text exactly as typed. Do not normalize it. The AI needs the original wording to assess clarity and ask the right follow-ups.

---

#### Stage 3 — Constraints Collection (UI, structured, ~1 minute)

This stage collects the **hard constraints** — things that directly determine how the plan gets scoped. These ARE structured because the answers are genuinely categorical.

```
How many hours per week can you realistically work on this?
○ 1–3 hours     ○ 4–7 hours     ○ 8–14 hours     ○ 15+ hours

What's your target timeline?
○ 2 weeks       ○ 1 month       ○ 2 months       ○ 3+ months      ○ No deadline

What's your main goal with this project?
○ Learn a specific tech / framework
○ Build a portfolio piece to show employers
○ Build something I'll actually use
○ All of the above

What planning style do you want?
○ Sprint-based (2-week sprints, Agile — most realistic)
○ Milestone-based (complete phase 1, unlock phase 2)
○ Hybrid (milestones as big goals, sprints inside each)
```

**Why these are structured:** These feed directly into math. 4 hours/week × 4 weeks = ~16 hours total. The AI uses this to scope the feature set and distribute story points. Free text here would require an extra normalization step and introduce error. Structure wins.

**Backend:** Store as typed fields — `hours_per_week: int`, `timeline_weeks: int | null`, `goal: enum`, `planning_style: enum`. These are passed directly to the plan generator.

---

#### Stage 4 — AI Clarification (Conversational, 2–4 exchanges)

This is where the hybrid model earns its keep. After collecting stages 1–3, the backend sends everything to the LLM and asks it to identify gaps, ambiguities, and missing critical information.

**What the AI looks for:**

1. **Idea vagueness** — "build a social app" is too vague to plan. The AI asks: "What's the one core thing a user should be able to do on day one?"

2. **Scope mismatch** — User says "2 weeks, 4 hours/week" but describes a full e-commerce platform. The AI flags this: "That's roughly 8 hours of work time. I'd suggest we focus on [X] for this timeline — does that work?"

3. **Missing critical technical decisions** — "React app" without any mention of backend, auth, or data storage. The AI asks: "Does this app need user accounts? And where should data live — just the browser, or a real database?"

4. **Ambiguous features** — "users can share things" — share how? Public feed? DMs? Links?

5. **Tech stack completeness** — If user says "Next.js" but no DB, no auth library, no deployment target, the AI asks these specifically.

**How it's presented in the UI:**

Not a chat window — a series of **focused question cards** that appear one at a time. Each card has a question, a free text answer field, and a "Skip" option for non-critical questions. Max 4 questions, min 0 (if the AI finds nothing ambiguous).

```
┌─────────────────────────────────────────────────────────┐
│  Quick question before we start researching...          │
│                                                         │
│  Your recipe app sounds great. Does it need user        │
│  accounts (so people can save their own recipes),       │
│  or is it more of a public browsing experience?         │
│                                                         │
│  [ Users should have accounts and their own recipes  ]  │
│                                                         │
│  [Continue]                          [Skip this one]    │
└─────────────────────────────────────────────────────────┘
        Question 1 of 3  ●●○○
```

**Why max 4 questions:** Beyond 4 questions, users abandon. The AI must prioritize ruthlessly — only ask what would meaningfully change the plan if answered differently.

**Backend:** 
- POST `/interview/clarify` with all stage 1–3 data
- LLM returns structured JSON: `{ questions: [{id, question, why_it_matters, is_critical}] }`
- Only the top 4 critical ones are shown
- User answers are stored and appended to the project context object

---

#### Stage 5 — Jira Connection (UI, ~1 minute)

Last step before research begins. Simple OAuth connect screen.

```
┌─────────────────────────────────────────────────────────┐
│  Almost there. Connect your Jira account so we can      │
│  push your plan directly to your board.                 │
│                                                         │
│  [  Connect Jira  ]                                     │
│                                                         │
│  Don't have Jira? → Create a free account               │
│  Using a different tool? → Export as markdown instead   │
└─────────────────────────────────────────────────────────┘
```

After OAuth, user selects or creates a Jira project:
```
Which Jira project should we use?
○ Create a new project: "Recipe App"
○ Use existing: [dropdown of their projects]
```

**Backend:**
- Standard Atlassian OAuth 2.0 (3LO) flow
- Store `access_token`, `refresh_token`, `cloud_id`, `project_key` encrypted in DB
- Token refresh handled automatically on expiry

---

### What we have after Phase 1

A single **Project Context Object** that looks like this:

```json
{
  "entry_type": "both",
  "raw_idea": "A recipe sharing app where users can post recipes with photos",
  "tech_stack": {
    "primary": "React",
    "additional": ["Node.js", "Express"],
    "gaps": ["database", "auth", "hosting"]
  },
  "skill_level": "knows_basics",
  "constraints": {
    "hours_per_week": 7,
    "timeline_weeks": 8,
    "total_hours_available": 56,
    "goal": "portfolio_piece",
    "planning_style": "sprint_based"
  },
  "clarifications": [
    { "question": "Does it need user accounts?", "answer": "Yes, users should have profiles" },
    { "question": "Photo uploads — real uploads or just URLs?", "answer": "Real uploads" }
  ],
  "jira": {
    "cloud_id": "...",
    "project_key": "RECIPE",
    "access_token": "...(encrypted)"
  }
}
```

This object drives everything in Phase 2.

---

---

# PHASE 2 — RESEARCH
## Deciding the quality of the output

---

### Why this phase determines everything

The difference between a generic AI-generated plan ("Set up project → Build auth → Add features → Deploy") and a genuinely useful one is **specificity grounded in real knowledge.** 

Generic plans come from the LLM's training data alone — which is broad but shallow on "what does a beginner actually need to know when building auth in Next.js 14 with the App Router today?"

Good plans come from combining the LLM's reasoning with **fresh, specific, real-world information** — actual documentation, current best practices, realistic time estimates, known beginner traps.

The research phase is what creates that specificity. It runs as a background job (ARQ + Redis) in 4 sequential sub-steps.

---

### Research Sub-step 1 — Stack Completion & Gap Analysis

**What happens:** Before researching anything, the LLM analyzes the tech stack and identifies every decision that needs to be made to actually build this project. Things the user mentioned plus things they didn't.

**Input:** The Project Context Object from Phase 1.

**LLM prompt goal:** "Given this project and stack, what is the complete list of technologies, tools, and architectural decisions needed? Identify what the user has specified and what still needs to be decided."

**Example output for the recipe app:**
```
Specified:
- React (frontend framework)
- Node.js + Express (backend)

Needs to be decided:
- Database: PostgreSQL vs MongoDB (recipes + users = relational → recommend PostgreSQL)
- Auth: NextAuth vs Clerk vs custom JWT
- File storage: S3 vs Cloudinary for photo uploads
- Deployment: Vercel (frontend) + Railway/Render (backend)
- ORM: Prisma (beginner-friendly with PostgreSQL)
```

The LLM makes opinionated recommendations for each gap, appropriate for the user's skill level. These recommendations are what get researched in step 2.

**Why this matters:** You can't research "the stack" — you can only research specific things. This step produces the specific list of things to research.

---

### Research Sub-step 2 — Parallel Web Research (Exa)

**What happens:** The backend fires **parallel Exa search queries** — not sequential — for each item identified in step 1. Each query is crafted by the LLM to be maximally specific.

**Query generation:** The LLM generates search queries for each research target. Not generic — very specific to the stack, skill level, and project type.

**Example queries fired in parallel for the recipe app:**

```python
queries = [
  # Architecture & setup
  "Next.js 14 App Router project structure beginner best practices 2024",
  "PostgreSQL Prisma setup Node.js Express tutorial beginner",
  
  # Auth (the gap that was identified)
  "NextAuth.js vs Clerk comparison 2024 beginner React",
  "JWT authentication Node.js Express beginner implementation",
  
  # File uploads (critical because user confirmed real uploads)
  "Cloudinary image upload React Node.js tutorial 2024",
  "multer file upload Express beginner guide",
  
  # Common mistakes (always researched)
  "common mistakes React Node.js beginner projects",
  "Next.js beginner mistakes App Router 2024",
  
  # Time estimates
  "how long does it take to build auth Node.js Express from scratch",
  "realistic timeline React full-stack beginner project",
  
  # Deployment
  "deploy React Node.js app Vercel Railway free tier 2024"
]
```

**All queries fire in parallel.** Exa returns results for each. The raw results are stored in the job's Redis context, ready for step 3.

**Why parallel and not sequential:** Sequential research on 10 queries at ~1s each = 10s minimum. Parallel = ~2–3s total. The user is waiting. Speed matters.

**What makes a good vs bad query:**
- Bad: "React authentication" → generic, shallow results
- Good: "NextAuth.js setup Next.js 14 App Router beginner step by step 2024" → specific, actionable results
- Bad: "deploy app" → useless
- Good: "deploy Next.js frontend Vercel + Express backend Railway free tier together" → exactly what we need

The LLM generates the queries, which is why step 1 has to come first — you need the completed stack to know what to search for.

---

### Research Sub-step 3 — Synthesis

**What happens:** The LLM takes all raw Exa search results and synthesizes them into a structured **Research Brief**. This is not shown to the user — it's the internal document that feeds plan generation.

**The Research Brief contains:**

```markdown
## Stack Decisions (final, with rationale)
- Auth: Clerk recommended over NextAuth for this skill level — 
  simpler setup, less boilerplate, free tier covers this project
- DB: PostgreSQL + Prisma — relational data fits recipes/users, 
  Prisma abstracts raw SQL which suits beginner-intermediate level
- File storage: Cloudinary — free tier, simple React SDK, no S3 
  complexity

## Feature Scope (calibrated to 56 hours)
Must-have (core app):
- User auth (signup/login) — estimated 6–8 hours
- Recipe CRUD (create/edit/delete) — estimated 10–12 hours  
- Photo upload — estimated 4–6 hours
- Recipe browsing/search — estimated 8–10 hours
- User profiles — estimated 6–8 hours

Nice-to-have (if time allows):
- Follow other users — 4–6 hours
- Recipe ratings/comments — 6–8 hours

Cut for this timeline:
- Real-time notifications — too complex
- Social feed algorithm — too complex

## Folder Structure (recommended)
/app (Next.js App Router)
  /api (route handlers)
  /(auth) (auth pages)
  /(dashboard) (protected pages)
/components
/lib (db client, helpers)
/prisma

## Key Beginner Traps to Warn About
1. Not setting up environment variables properly from day 1
2. Trying to build everything before testing anything
3. Not understanding async/await in route handlers
4. Forgetting to handle loading and error states in UI

## Per-Task Learning Resources
- Prisma setup: prisma.io/docs/getting-started
- Clerk auth: clerk.com/docs/quickstarts/nextjs
- Cloudinary upload: cloudinary.com/documentation/react_integration
- Deployment: railway.app/docs
```

**Why synthesize instead of passing raw results to plan generation:**
Raw search results are noisy, redundant, and unstructured. If you pass 10 Exa result sets directly into the plan generator prompt, you waste tokens on duplicate content and the LLM buries the useful signal in noise. Synthesis creates a clean, dense, high-signal document that the plan generator can use reliably.

---

### Research Sub-step 4 — Scope Calibration

**What happens:** Before generating the plan, one final LLM pass calibrates the feature scope against the user's hard constraints.

**Input:** Research Brief + constraints (`56 hours total`, `sprint_based`, `portfolio_piece goal`)

**What it does:**
- Assigns hour estimates to each feature
- Sums them up and checks against total available hours
- If over budget: marks features as "nice-to-have" or "cut"
- If under budget: suggests stretch goals
- Distributes features across the sprint count (56h ÷ ~7h/sprint = 8 sprints)

**Output:** A scoped feature list with sprint assignments, ready for plan generation.

```json
{
  "total_hours": 56,
  "sprint_count": 8,
  "sprint_duration_weeks": 2,
  "features": [
    { "name": "Project setup + deployment pipeline", "hours": 4, "sprint": 1, "priority": "critical" },
    { "name": "Database schema + Prisma setup", "hours": 4, "sprint": 1, "priority": "critical" },
    { "name": "Auth (Clerk)", "hours": 7, "sprint": 2, "priority": "critical" },
    { "name": "Recipe CRUD", "hours": 11, "sprint": "3-4", "priority": "critical" },
    { "name": "Photo uploads (Cloudinary)", "hours": 5, "sprint": 4, "priority": "critical" },
    { "name": "Recipe browsing + search", "hours": 9, "sprint": "5-6", "priority": "critical" },
    { "name": "User profiles", "hours": 7, "sprint": 6, "priority": "critical" },
    { "name": "Polish + bug fixes + deploy", "hours": 5, "sprint": 7, "priority": "critical" },
    { "name": "Follow system", "hours": 5, "sprint": 8, "priority": "nice_to_have" }
  ]
}
```

---

### What we have after Phase 2

- A complete **Research Brief** (internal, drives plan quality)
- A **Scoped Feature List** with sprint assignments and hour estimates
- Final **Stack Decisions** with rationale
- **Beginner traps** to embed in ticket descriptions
- **Per-task learning resources** to attach to tickets

---

---

# PHASE 3 — JIRA CREATION
## Turning everything into a real board

---

### The Jira hierarchy we create

```
Project (already exists from Phase 1)
└── Epics (major feature areas, ~5–7 per project)
    └── Stories (user-facing features, one per deliverable unit)
        └── Subtasks (specific implementation steps, 3–6 per story)
Sprints (created separately, stories assigned to them)
```

---

### Step 1 — Generate the full plan as structured JSON

Before touching the Jira API at all, generate the **entire plan as a JSON object** in one LLM call. This is critical — it means if the Jira push fails halfway, you have everything and can retry without re-generating.

**LLM prompt inputs:**
- Research Brief
- Scoped Feature List
- User's skill level + goal
- Planning style (sprint-based)

**LLM output format (strict JSON):**

```json
{
  "epics": [
    {
      "id": "epic_1",
      "name": "Project Foundation",
      "description": "Setting up the project structure, tooling, and deployment pipeline before writing any features",
      "color": "blue",
      "stories": [
        {
          "id": "story_1_1",
          "summary": "As a developer, I want a working Next.js project with Prisma connected so I can start building features",
          "description": "Set up the base project with all tools configured. This sprint's goal is: by the end, you should be able to run the app locally AND deploy an empty version to production. Deploying early catches infra problems before they block feature work.",
          "story_points": 4,
          "priority": "Highest",
          "sprint": 1,
          "why_first": "Foundation must come before everything else. A broken setup will block every subsequent task.",
          "subtasks": [
            {
              "summary": "Initialise Next.js 14 project with TypeScript and Tailwind",
              "description": "Run: npx create-next-app@latest recipe-app --typescript --tailwind --app\n\nWhat this does: Creates your project folder with the App Router structure, TypeScript config, and Tailwind already wired up.\n\nVerify it works: npm run dev — you should see the Next.js welcome page at localhost:3000.\n\nWhat to google if stuck: 'Next.js 14 App Router getting started'",
              "estimated_hours": 0.5
            },
            {
              "summary": "Set up PostgreSQL database and connect Prisma ORM",
              "description": "1. Create a free PostgreSQL database on Railway or Supabase\n2. Install Prisma: npm install prisma @prisma/client\n3. Run: npx prisma init\n4. Paste your database connection string into .env as DATABASE_URL\n5. Run: npx prisma db push\n\nWhy Prisma: It lets you interact with your database using JavaScript objects instead of raw SQL — much friendlier for your level.\n\nWhat to google if stuck: 'Prisma getting started Next.js'",
              "estimated_hours": 1.5
            },
            {
              "summary": "Define initial database schema (User and Recipe models)",
              "description": "Add this to your schema.prisma file:\n\nmodel User {\n  id        String   @id @default(cuid())\n  email     String   @unique\n  name      String?\n  recipes   Recipe[]\n  createdAt DateTime @default(now())\n}\n\nmodel Recipe {\n  id          String   @id @default(cuid())\n  title       String\n  description String?\n  authorId    String\n  author      User     @relation(fields: [authorId], references: [id])\n  createdAt   DateTime @default(now())\n}\n\nThen run: npx prisma db push\n\nBeginner trap: Don't skip this step and try to add it later. Getting your schema right early saves you from painful migrations.",
              "estimated_hours": 1.0
            },
            {
              "summary": "Deploy empty app to Vercel and verify it works",
              "description": "Push your code to GitHub, then:\n1. Go to vercel.com → New Project → Import from GitHub\n2. Add your DATABASE_URL as an environment variable\n3. Deploy\n\nWhy deploy now, before any features: If deployment breaks later, you won't know if it's the deployment or your new code. Deploying early gives you a clean baseline.\n\nWhat to google if stuck: 'deploy Next.js Vercel GitHub'",
              "estimated_hours": 1.0
            }
          ]
        }
      ]
    }
  ],
  "sprints": [
    {
      "id": "sprint_1",
      "name": "Sprint 1 — Foundation",
      "goal": "Working local dev environment + live empty deployment. By end of this sprint you should be able to open your app in a browser from any device.",
      "story_ids": ["story_1_1"],
      "duration_weeks": 2,
      "start_offset_days": 0
    }
  ]
}
```

**Key design decisions in the JSON:**

1. **Every subtask has a full description** with the actual commands, code snippets, beginner traps, and "what to google if stuck." This is what makes the tickets genuinely useful, not just labels.

2. **Stories explain WHY** — not just what to build but why it's being built in this order. This is the company simulation: a good tech lead always tells you why.

3. **Sprint goals are written as outcomes** — "by end of this sprint you should be able to..." — not just task lists.

4. **Story points are calibrated** to the user's skill level, not an expert developer's pace.

---

### Step 2 — Plan preview screen (read-only)

Before touching Jira, show the user what's about to be created. This is the "read-only preview" you decided on.

The UI shows:
- Sprint timeline (horizontal scroll of sprint cards)
- Each sprint expanded with its epics and stories
- Total story count, sprint count, estimated hours
- A single "Push to Jira →" button

No editing. If they don't like it, they can go back (which re-runs generation with a feedback note). But for most users, this screen is where they go "this is exactly what I needed."

---

### Step 3 — Jira push sequence (the order matters)

The Jira REST API has dependencies — you must create things in the right order or you get foreign key errors.

**Correct creation order:**

```
1. Create Scrum board (if new project)
        ↓
2. Create all Sprints (POST /rest/agile/1.0/sprint)
   — store sprint_id mapping: our sprint_1 → Jira sprint ID 12345
        ↓
3. Create all Epics (POST /rest/api/3/issue, issuetype: Epic)
   — store epic_id mapping: our epic_1 → Jira issue key REC-1
        ↓
4. Create all Stories, linked to their Epic
   (POST /rest/api/3/issue, issuetype: Story, customfield_10014: epic_key)
   — store story_id mapping: our story_1_1 → Jira issue key REC-2
        ↓
5. Create all Subtasks, linked to their parent Story
   (POST /rest/api/3/issue, issuetype: Subtask, parent: story_key)
        ↓
6. Assign Stories to Sprints
   (POST /rest/agile/1.0/sprint/{sprintId}/issue, issueKeys: [...])
```

**Why batching matters:** The Jira API has rate limits. For a medium project (5 epics, 20 stories, 80 subtasks = 106 API calls), naive sequential calls take ~30–40 seconds and risk hitting rate limits. Solution: batch story creation in groups of 10 with a small delay between batches. Stories within a batch fire in parallel.

**Error handling:** Every API call is wrapped in retry logic (3 attempts, exponential backoff). If a push fails midway, the job records which items were successfully created. Retry only pushes the remaining items — it never creates duplicates.

**Progress tracking via SSE:** As each stage completes, the FastAPI worker sends an SSE event to the frontend:

```
event: progress
data: {"stage": "creating_epics", "done": 2, "total": 5, "message": "Creating epics..."}

event: progress  
data: {"stage": "creating_stories", "done": 8, "total": 20, "message": "Creating stories..."}

event: complete
data: {"board_url": "https://yourteam.atlassian.net/jira/software/projects/REC/boards"}
```

The frontend shows a live progress bar during the push — not a spinner.

---

### Step 4 — Post-push: the "You're hired" screen

After successful push, the user lands on a screen that gives them everything they need to actually start:

```
┌─────────────────────────────────────────────────────────────┐
│  ✓ Your board is ready. You start Monday.                   │
│                                                             │
│  Sprint 1 — Foundation                                      │
│  Goal: Working local dev + live deployment                  │
│  4 tasks · ~7 hours                                         │
│                                                             │
│  Your first task:                                           │
│  "Initialise Next.js 14 project with TypeScript"            │
│  → Open in Jira                                             │
│                                                             │
│  [  View your full board  ]    [  See the sprint plan  ]    │
└─────────────────────────────────────────────────────────────┘
```

---

---

# HOW THE THREE PHASES CONNECT — end-to-end data flow

```
PHASE 1: EXTRACTION
────────────────────────────────────────────────
User → Entry type detection
     → Core input (idea + stack)
     → Constraints (hours, timeline, goal, style)
     → AI clarification (max 4 questions)
     → Jira OAuth connect

Output: Project Context Object (JSON, stored in DB)

                    ↓ triggers

PHASE 2: RESEARCH (background job, ARQ + Redis)
────────────────────────────────────────────────
Project Context Object
     → Sub-step 1: Stack completion + gap analysis (LLM)
     → Sub-step 2: Parallel Exa searches (10–14 queries)
     → Sub-step 3: Synthesis into Research Brief (LLM)
     → Sub-step 4: Scope calibration against constraints (LLM)

Output: Research Brief + Scoped Feature List (stored in DB)

SSE events → frontend "Research in progress" status screen

                    ↓ triggers

PHASE 3: JIRA CREATION (continues in same background job)
────────────────────────────────────────────────
Research Brief + Scoped Feature List
     → Plan generation as structured JSON (single LLM call)
     → Store complete plan in DB
     → Show read-only preview to user

User clicks "Push to Jira"
     → Jira push sequence (epics → stories → subtasks → sprint assignment)
     → SSE progress events → frontend progress bar
     → On complete: redirect to "You're hired" screen

Output: Fully populated Jira board
```

---

---

# WHAT MAKES EACH TICKET GENUINELY USEFUL

Every subtask ticket in Jira contains:

```
Title: Short, action-oriented (what to do)

Description:
├── What this task is (1–2 sentences, plain English)
├── Why it matters / why it's in this order
├── Step-by-step instructions with actual commands/code
├── Beginner trap: the most common mistake on this specific task
├── How to verify it worked
└── What to Google if stuck (specific search query, not just "google it")

Story Points: calibrated to user's skill level
Priority: Highest / High / Medium / Low
Epic Link: which feature area this belongs to
Sprint: which sprint it's assigned to
```

This is what separates DevMentor from any generic project generator. The tickets are written by someone who has built this before and knows exactly where beginners get stuck.

---

---

# SUMMARY TABLE

| Phase | Where | What happens | Output |
|-------|-------|-------------|--------|
| Entry detection | UI (card select) | Identify what user brings | `entry_type` |
| Core input | UI (text fields) | Capture idea + stack | Raw text |
| Constraints | UI (structured) | Hours, timeline, goal, style | Typed fields |
| AI clarification | Hybrid (AI-driven cards) | Fill gaps, resolve ambiguity | Answered questions |
| Jira connect | UI (OAuth) | Get write access | Tokens + project key |
| Stack completion | Background (LLM) | Fill tech gaps, make decisions | Complete stack |
| Web research | Background (Exa, parallel) | Get real, current, specific info | Raw search results |
| Synthesis | Background (LLM) | Turn results into research brief | Research Brief |
| Scope calibration | Background (LLM) | Fit features to available hours | Scoped feature list |
| Plan generation | Background (LLM) | Generate full structured plan | Plan JSON |
| Preview | UI (read-only) | User reviews before pushing | Approval |
| Jira push | Background (API calls) | Create board, epics, stories, tasks | Live Jira board |
| Handoff | UI | First task, sprint goal, board link | User starts building |
