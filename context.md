# MF Advisor — Project Context for Claude

## What this project is

A multi-agent AI system that recommends Indian mutual funds based on a user's
risk profile, built as a portfolio project to showcase agentic AI with LangGraph.

## Tech stack

- Backend: FastAPI + LangGraph + Groq (llama-3.1-8b-instant)
- Frontend: Next.js 14 (App Router) + TypeScript + Tailwind + Recharts
- DB: PostgreSQL via Prisma (frontend-side only)
- Cache: Redis (provisioned, not yet used)
- Auth: NextAuth v5 (beta) + Google OAuth
- Data sources: AMFI NAVAll.txt (portal.amfiindia.com) + MFAPI.in

## Agent pipeline (LangGraph, backend/graph/pipeline.py)

1. data_agent — fetches funds from AMFI (SEBI category) + MFAPI (NAV history)
2. analyst_agent — computes CAGR (1Y/3Y/5Y), Sharpe ratio, volatility
3. recommendation_agent — picks top N, enforces 1 fund per fund house
4. critic_agent — validates category match, volatility limits, concentration;
   fixes concentration in-place, loops back (max 2x) for per-fund issues
5. explainer_agent — Groq LLM returns {summary, bullets} JSON per fund

Conditional edge: critic_agent → explainer_agent (if approved) or → recommendation_agent (retry)

## Key architectural decisions

- Groq over OpenAI — free tier, fast inference (llama-3.1-8b-instant)
- AMFI NAVAll.txt for category — proper SEBI categories vs keyword matching on scheme names
- Expense ratio is a SEBI-cap-based category proxy (1.05% equity, 1.00% hybrid, 0.50% debt)
  — NOT fund-specific, AMFI factsheet AUM endpoint returns 404 (unresolved)
- 1 fund per fund house rule (recommendation_agent) — prevents 5x ICICI variants dominating
- Critic fixes concentration in-place (keeps top-scoring funds per category, drops rest)
  — only loops back to recommendation_agent for category-mismatch/volatility issues
- SSE streaming (/recommend/stream) for live agent progress in frontend
- Next.js API routes for watchlist (auth-dependent) — FastAPI stays pure agent pipeline
- Prisma used only in frontend (Next.js API routes), backend has no DB access yet

## What's working (V1 + V2 foundation complete)

- Full recommendation pipeline end to end, tested via curl and frontend
- Next.js frontend: profile form → live agent tracker (5 steps, critic shown in amber) → fund cards
- Each fund card: metrics grid, 1Y NAV chart, expense ratio, AUM, score
- "📝 Summary" / "✦ Why this fund?" toggle — bullets are {3 reasons + 1 caveat}
- Google OAuth sign-in working (NextAuth v5 + Prisma adapter)
- "＋ Watchlist" button on fund cards → saves to PostgreSQL via /api/watchlist
- /dashboard page shows saved watchlist with SIP start date, remove button

## Known issues / unresolved

- AUM always null — AMFI factsheet endpoint (portal.amfiindia.com/modules/LoadFundFactsheet)
  returns 404. Expense ratio uses category-level proxy, not real per-fund data.
- No performance tracking yet (XIRR from sipStartDate to now)
- Redis provisioned but unused — no caching implemented yet

## Critical setup gotchas (already solved, don't re-suggest)

- Two separate .env files exist: backend/.env and frontend/.env — don't mix them up
- NextAuth v5 beta needs AUTH_SECRET (not just NEXTAUTH_SECRET) — auth.ts has fallback:
  `secret: process.env.AUTH_SECRET ?? process.env.NEXTAUTH_SECRET`
- Prisma client explicitly passes `datasourceUrl: process.env.DATABASE_URL` in
  src/lib/prisma.ts to avoid env-loading issues
- SSE parser bug (FIXED): eventType must be declared OUTSIDE the while loop in
  page.tsx, otherwise large `complete` payloads split across chunks lose their
  event type and silently fail to render

## V2 roadmap

Step 1 ✅ Auth (NextAuth + Google)
Step 2 ✅ Database schema (Prisma — User, WatchlistEntry, FundIntelligence tables)
Step 3 ✅ Watchlist (save/remove via /api/watchlist)
Step 4 ⬜ Performance tracking — XIRR from sipStartDate using MFAPI NAV history
Step 5 ⬜ Holdings agent — fetch fund portfolio holdings (data source TBD, AMFI
portfolio disclosure is a monthly PDF — complex to parse)
Step 6 ⬜ Compliance agent — SEBI mandate drift checks (e.g. large cap fund with >20% mid-cap exposure)
Step 7 ⬜ Sentiment agent — map holdings → sector themes → news → LLM summary
(e.g. "24% in IT — here's the sector outlook")

## Repo structure

mf-advisor/
├── backend/
│ ├── agents/ (data, analyst, recommendation, critic, explainer)
│ ├── graph/ (state.py, pipeline.py)
│ ├── tools/ (amfi.py, mfapi.py)
│ ├── main.py (FastAPI, /recommend + /recommend/stream)
│ └── .env (GROQ*API_KEY)
├── frontend/
│ ├── prisma/schema.prisma
│ ├── src/
│ │ ├── lib/ (auth.ts, prisma.ts)
│ │ ├── app/ (page.tsx, dashboard/, auth/signin/, api/auth/, api/watchlist/)
│ │ └── components/ (ProfileForm, AgentTracker, FundCard, NavChart, Navbar, Providers)
│ └── .env (GOOGLE_CLIENT_ID/SECRET, DATABASE_URL, NEXTAUTH*\*, AUTH_SECRET)
└── docker-compose.yml (postgres, redis, backend, frontend)

## How to run locally

docker compose up postgres redis -d
cd backend && uvicorn main:app --reload
cd frontend && npm run dev
