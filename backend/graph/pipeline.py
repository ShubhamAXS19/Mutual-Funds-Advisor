from langgraph.graph import StateGraph, END
from graph.state import MFAdvisorState, UserProfile
from agents.data_agent import data_agent
from agents.analyst_agent import analyst_agent
from agents.recommendation_agent import recommendation_agent
from agents.explainer_agent import explainer_agent


def build_pipeline() -> StateGraph:
    """
    Builds and compiles the Phase 1 LangGraph pipeline.

    Flow:
        data_agent → analyst_agent → recommendation_agent → explainer_agent → END
    """
    graph = StateGraph(MFAdvisorState)

    # Register nodes
    graph.add_node("data_agent", data_agent)
    graph.add_node("analyst_agent", analyst_agent)
    graph.add_node("recommendation_agent", recommendation_agent)
    graph.add_node("explainer_agent", explainer_agent)

    # Linear edges
    graph.set_entry_point("data_agent")
    graph.add_edge("data_agent", "analyst_agent")
    graph.add_edge("analyst_agent", "recommendation_agent")
    graph.add_edge("recommendation_agent", "explainer_agent")
    graph.add_edge("explainer_agent", END)

    return graph.compile()


# Module-level compiled pipeline (import this in main.py)
pipeline = build_pipeline()


async def run_pipeline(user_profile: UserProfile) -> MFAdvisorState:
    """
    Entry point called by FastAPI.
    Initialises state and runs the full graph.
    """
    initial_state: MFAdvisorState = {
        "user_profile": user_profile,
        "fund_universe": [],
        "scored_funds": [],
        "recommended_funds": [],
        "explanation": {},
        "errors": [],
        "current_step": "init",
    }

    final_state = await pipeline.ainvoke(initial_state)
    return final_state