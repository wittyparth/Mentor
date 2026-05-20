# DevMentor — Product Specification
### AI-Powered Project Mentor That Simulates a Real Software Company

---

## 1. What Is This?

DevMentor is an AI application that helps beginner and intermediate web developers build real projects — by simulating the experience of working inside a professional software company.

Instead of a tutorial that tells you *what* to do, DevMentor acts as your **tech lead, product manager, and mentor** in one. It asks the right questions, researches the right tech, builds a professional plan, and pushes everything directly to your Jira board — so you spend zero time planning and 100% of your time actually building.

The core pain point it solves: **developers start projects without a clear vision, get overwhelmed by decisions, lose momentum, and either build something half-baked or quit entirely.** DevMentor eliminates all of that.

---

## 2. Target Users

- **Beginners** — building their first real project, learning a framework or language
- **Intermediate developers** — know the basics but struggle to structure and ship complete projects
- **Any stack, any framework** — React, Vue, Node, Express, Python/Flask, full-stack MERN, T3, etc. The tool is framework-agnostic.

---

## 3. Core User Flow (The Big Picture)

```
User arrives → Onboarding interview → AI research phase 
→ Plan generation → User reviews plan → Push to Jira → User builds
```

Each phase is detailed below.

---

## 4. Feature Breakdown

### Phase 1 — Onboarding Interview (Multi-Stage Questionnaire)

This is the most critical section. The AI doesn't accept vague input. It guides the user through a structured interview across multiple stages to extract a complete picture of what they want to build.

**Stage 1 — Project Concept**
- What do you want to build? (free text, intentionally vague to start)
- Why are you building this? (learning a tech, portfolio, real product, etc.)
- What is the core thing this app should do? (one sentence)

**Stage 2 — Technical Context**
- What framework/language/package are you trying to learn or use?
- What is your current skill level with that technology? (beginner / some experience / comfortable)
- Do you have any preference for the tech stack beyond the main framework?
- Have you already started this project? If yes, what exists so far?

**Stage 3 — Scope & Constraints**
- How many hours per week can you realistically work on this?
- What is your target deadline or timeline? (e.g. "4 weeks", "no deadline", "2 months")
- Are there any specific features that are absolutely required?
- Are there any features you want to explicitly avoid for now?

**Stage 4 — Planning Style**
- Choose your project management style:
  - **Sprint-based** — 2-week sprints, Agile tickets, just like a real company (recommended, best Jira integration)
  - **Milestone-based** — complete Phase 1, then unlock Phase 2 (self-paced gates)
  - **Hybrid** — big milestones as epics, sprints inside each one

**Stage 5 — Jira Connection**
- Connect your Jira account (OAuth 2.0 — see Section 6)
- Select or create a Jira project for this work

> **Design note:** The questionnaire is presented as a conversational multi-step UI, not a wall of form fields. Each stage builds on the previous. The AI can ask follow-up questions dynamically if answers are vague.

---

### Phase 2 — AI Research

After the interview, the AI autonomously researches everything needed to plan the project well. This runs in the background while a loading screen updates the user with what's being investigated.

**What the AI researches:**
- The framework/library/package the user wants to learn (official docs, best practices, common gotchas)
- Industry-standard architecture patterns for this type of project
- A realistic feature set for a project of this scope
- Common beginner mistakes in this tech stack to warn against
- Recommended folder structure and project setup
- What packages/tools are typically used alongside the main framework
- Estimated complexity and time per feature

**Output:** The research is synthesized into an internal "project brief" that feeds directly into Phase 3. The user never sees raw research — they see its result.

---

### Phase 3 — Plan Generation

The AI takes the interview answers + research and generates a **professional project plan**, structured exactly like a real software company would structure it.

#### Jira Structure Used

```
Project
└── Epics (major feature areas)
    └── Stories (user-facing features, one per sprint-deliverable unit)
        └── Subtasks (specific implementation steps)
Sprints (contain stories, 2-week cycles — for sprint-based style)
```

#### What Gets Generated

**Epics** — Major phases or feature areas of the project. Examples:
- `Project Setup & Infrastructure`
- `Authentication System`
- `Core Feature: [X]`
- `UI & Styling`
- `Testing & Deployment`

**Stories** — User-facing features within each epic, written as proper user stories:
- `As a user, I want to register with email and password so I can access my account`
- `As a user, I want to see a dashboard with my recent activity`

Each story includes:
- Clear acceptance criteria (what "done" looks like)
- Story points estimate (based on complexity)
- Priority (Critical / High / Medium / Low)
- Dependencies on other stories
- Suggested time estimate

**Subtasks** — The actual implementation steps inside each story:
- `Install and configure bcrypt for password hashing`
- `Create POST /api/auth/register endpoint`
- `Build registration form component with validation`
- `Write unit test for registration handler`

**Sprints** (sprint-based mode only):
- Named and dated sprints (e.g. "Sprint 1 — Foundation", "Sprint 2 — Auth & Users")
- Stories distributed across sprints based on dependency order and estimated hours
- Sprint goals written clearly

#### Plan Review Screen

Before anything is pushed to Jira, the user sees a full visual review of the plan:
- Timeline view of sprints / milestones
- All epics expanded with their stories
- Estimated total hours and per-sprint breakdown
- Ability to request changes ("add a feature", "remove testing for now", "this sprint is too heavy")

The AI revises the plan based on feedback before pushing.

---

### Phase 4 — Push to Jira

Once the user approves the plan, everything is created in Jira automatically via the REST API.

**What gets created in Jira:**
1. Epics (one per major feature area)
2. Stories linked to their parent epic
3. Subtasks linked to their parent story
4. Sprints created and stories assigned to them (sprint mode)
5. Story points and priority set on each issue
6. Due dates set on sprints and epics
7. Descriptions populated with acceptance criteria and context

**After push:**
- User is shown a success screen with a direct link to their Jira board
- The app displays a "your first sprint starts now" briefing with what to tackle first
- Optional: daily digest feature (send user an email/notification with what to work on today)

---

## 5. Application Architecture

### Frontend
- **Framework:** React (Next.js recommended for routing + SSR)
- **Key screens:**
  - Landing / onboarding
  - Multi-step interview wizard
  - Research loading screen (animated, shows what AI is doing)
  - Plan review screen (visual Jira-style board preview)
  - Success / dashboard screen
- **State management:** Zustand or React Context for interview state
- **UI:** Tailwind CSS

### Backend
- **Framework:** Node.js + Express (or Next.js API routes)
- **Key responsibilities:**
  - Orchestrating the AI research + plan generation pipeline
  - Handling Jira OAuth 2.0 token exchange and storage
  - Making Jira REST API calls on behalf of the user
  - Storing user sessions and generated plans
- **AI:** Anthropic Claude API (claude-sonnet-4) — used for research synthesis and plan generation
- **Database:** PostgreSQL (store user accounts, generated plans, Jira tokens)

### Jira Integration
- **Auth method:** OAuth 2.0 (3LO) — see Section 6
- **APIs used:**
  - `POST /rest/api/3/issue` — create epics, stories, subtasks
  - `POST /rest/agile/1.0/sprint` — create sprints
  - `POST /rest/agile/1.0/sprint/{sprintId}/issue` — assign stories to sprints
  - `GET /rest/agile/1.0/board` — fetch user's boards
  - `GET /rest/api/3/project` — fetch user's projects

---

## 6. Jira Integration — Technical Details

### Authentication: OAuth 2.0 (3LO)

Jira Cloud uses **three-legged OAuth 2.0** for third-party apps acting on behalf of users. This is the only compliant method — API tokens or basic auth are not suitable for multi-user apps.

**Flow:**
1. User clicks "Connect Jira" in the app
2. App redirects user to Atlassian's authorization screen
3. User grants permission
4. Atlassian redirects back with an authorization `code`
5. Backend exchanges `code` for `access_token` + `refresh_token`
6. Tokens are stored securely (encrypted) in the database
7. All subsequent Jira API calls use the `access_token` in the `Authorization: Bearer` header

**Setup required (one-time, by you as developer):**
- Register an OAuth 2.0 app in the [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
- Set scopes: `read:jira-work`, `write:jira-work`, `read:jira-user`, `manage:jira-project`
- Set a redirect URI pointing to your backend callback endpoint
- Store `client_id` and `client_secret` as environment variables

**Token refresh:**
- Access tokens expire; use the `refresh_token` to get a new pair
- Atlassian uses rotating refresh tokens — store the new refresh token each time

### Creating Jira Issues Programmatically

**Epic creation:**
```json
POST /rest/api/3/issue
{
  "fields": {
    "project": { "key": "PROJECT_KEY" },
    "summary": "Authentication System",
    "issuetype": { "name": "Epic" },
    "customfield_10011": "Authentication System"
  }
}
```

**Story creation (linked to epic):**
```json
POST /rest/api/3/issue
{
  "fields": {
    "project": { "key": "PROJECT_KEY" },
    "summary": "As a user, I want to register with email",
    "issuetype": { "name": "Story" },
    "customfield_10014": "EPIC_KEY",
    "customfield_10016": 3,
    "priority": { "name": "High" },
    "description": { ... }
  }
}
```

**Sprint creation:**
```json
POST /rest/agile/1.0/sprint
{
  "name": "Sprint 1 — Foundation",
  "originBoardId":