from dotenv import load_dotenv
load_dotenv()

import json
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from graph.state import UserProfile, MFAdvisorState
from graph.pipeline import run_pipeline

app = FastAPI(title="MF Advisor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response schemas ────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    age: int = Field(..., ge=18, le=80)
    monthly_sip: float = Field(..., ge=500)
    horizon_years: int = Field(..., ge=1, le=30)
    risk_level: str = Field(..., pattern="^(low|medium|high)$")
    goal: str = Field(..., min_length=3)


class NavPoint(BaseModel):
    date: str
    nav: float


class FundRecommendation(BaseModel):
    scheme_code: str
    scheme_name: str
    category: str
    cagr_1y: float | None
    cagr_3y: float | None
    cagr_5y: float | None
    sharpe_ratio: float | None
    volatility: float | None
    score: float
    explanation: str
    nav_history: list[NavPoint]     # last 1 year for chart


class RecommendResponse(BaseModel):
    recommendations: list[FundRecommendation]
    errors: list[str]
    total_funds_analysed: int


# ── SSE helpers ───────────────────────────────────────────────────────────────

def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


AGENT_META = {
    "data_agent": {
        "label": "Data agent",
        "description": "Fetching mutual fund universe from MFAPI",
    },
    "analyst_agent": {
        "label": "Analyst agent",
        "description": "Computing CAGR, Sharpe ratio, and volatility",
    },
    "recommendation_agent": {
        "label": "Recommendation agent",
        "description": "Filtering top 5 funds for your profile",
    },
    "explainer_agent": {
        "label": "Explainer agent",
        "description": "Generating plain-English rationale via LLM",
    },
}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/recommend/stream")
async def recommend_stream(body: RecommendRequest):
    """
    SSE endpoint. Emits:
      - event: agent_start   { agent, label, description }
      - event: agent_done    { agent, label }
      - event: complete      { recommendations, errors, total_funds_analysed }
      - event: error         { message }
    """
    user_profile = UserProfile(
        age=body.age,
        monthly_sip=body.monthly_sip,
        horizon_years=body.horizon_years,
        risk_level=body.risk_level,
        goal=body.goal,
    )

    async def event_stream():
        try:
            # Monkey-patch each agent to emit SSE events around it
            from agents import data_agent as da_mod
            from agents import analyst_agent as aa_mod
            from agents import recommendation_agent as ra_mod
            from agents import explainer_agent as ea_mod

            queue: asyncio.Queue = asyncio.Queue()

            async def wrap(agent_fn, agent_key, state):
                meta = AGENT_META[agent_key]
                await queue.put(sse_event("agent_start", {
                    "agent": agent_key,
                    "label": meta["label"],
                    "description": meta["description"],
                }))
                result = await agent_fn(state)
                await queue.put(sse_event("agent_done", {
                    "agent": agent_key,
                    "label": meta["label"],
                }))
                return result

            async def run_with_events():
                initial_state: MFAdvisorState = {
                    "user_profile": user_profile,
                    "fund_universe": [],
                    "scored_funds": [],
                    "recommended_funds": [],
                    "explanation": {},
                    "errors": [],
                    "current_step": "init",
                }
                state = await wrap(da_mod.data_agent, "data_agent", initial_state)
                state = await wrap(aa_mod.analyst_agent, "analyst_agent", state)
                state = await wrap(ra_mod.recommendation_agent, "recommendation_agent", state)
                state = await wrap(ea_mod.explainer_agent, "explainer_agent", state)
                await queue.put(None)   # sentinel
                return state

            pipeline_task = asyncio.create_task(run_with_events())

            # Stream events as they arrive
            final_state = None
            while True:
                item = await queue.get()
                if item is None:
                    final_state = await pipeline_task
                    break
                yield item

            # Build final response
            recs = []
            for sf in final_state["recommended_funds"]:
                # Last 252 trading days for chart (1 year)
                nav_slice = sf.fund.nav_history[-252:]
                recs.append({
                    "scheme_code": sf.fund.scheme_code,
                    "scheme_name": sf.fund.scheme_name,
                    "category": sf.fund.category,
                    "cagr_1y": sf.cagr_1y,
                    "cagr_3y": sf.cagr_3y,
                    "cagr_5y": sf.cagr_5y,
                    "sharpe_ratio": sf.sharpe_ratio,
                    "volatility": sf.volatility,
                    "score": sf.score,
                    "explanation": final_state["explanation"].get(sf.fund.scheme_code, ""),
                    "nav_history": nav_slice,
                })

            yield sse_event("complete", {
                "recommendations": recs,
                "errors": final_state["errors"],
                "total_funds_analysed": len(final_state["scored_funds"]),
            })

        except Exception as e:
            yield sse_event("error", {"message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# Keep the original POST endpoint for curl testing
@app.post("/recommend", response_model=RecommendResponse)
async def recommend(body: RecommendRequest):
    user_profile = UserProfile(
        age=body.age,
        monthly_sip=body.monthly_sip,
        horizon_years=body.horizon_years,
        risk_level=body.risk_level,
        goal=body.goal,
    )

    try:
        state = await run_pipeline(user_profile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    recommendations = []
    for sf in state["recommended_funds"]:
        nav_slice = sf.fund.nav_history[-252:]
        recommendations.append(FundRecommendation(
            scheme_code=sf.fund.scheme_code,
            scheme_name=sf.fund.scheme_name,
            category=sf.fund.category,
            cagr_1y=sf.cagr_1y,
            cagr_3y=sf.cagr_3y,
            cagr_5y=sf.cagr_5y,
            sharpe_ratio=sf.sharpe_ratio,
            volatility=sf.volatility,
            score=sf.score,
            explanation=state["explanation"].get(sf.fund.scheme_code, ""),
            nav_history=[NavPoint(date=p["date"], nav=p["nav"]) for p in nav_slice],
        ))

    return RecommendResponse(
        recommendations=recommendations,
        errors=state["errors"],
        total_funds_analysed=len(state["scored_funds"]),
    )