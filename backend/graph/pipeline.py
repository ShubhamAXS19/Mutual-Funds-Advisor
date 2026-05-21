from langgraph.graph import StateGraph, END
from graph.state import MFAdvisorState, UserProfile
from agents.data_agent import data_agent
from agents.analyst_agent import analyst_agent
from agents.recommendation_agent import recommendation_agent
from agents.critic_agent import critic_agent
from agents.explainer_agent import explainer_agent


def route_critic(state: MFAdvisorState) -> str:
    """
    Conditional edge function — read by LangGraph after critic_agent runs.

    Returns:
      "explainer_agent"      if critic approved the recommendations
      "recommendation_agent" if critic wants a retry
    """
    if state.get("critic_approved", False):
        return "explainer_agent"
    return "recommendation_agent"


def build_pipeline() -> StateGraph:
    """
    Builds and compiles the Phase 1 + Track C LangGraph pipeline.

    Flow:
        data_agent
            → analyst_agent
            → recommendation_agent
            → critic_agent  ──── approved ────→ explainer_agent → END
                    ↑                 rejected         |
                    └─────────────────────────────────┘
                           (loops back, max 2 times)
    """
    graph = StateGraph(MFAdvisorState)

    # Register all nodes
    graph.add_node("data_agent", data_agent)
    graph.add_node("analyst_agent", analyst_agent)
    graph.add_node("recommendation_agent", recommendation_agent)
    graph.add_node("critic_agent", critic_agent)
    graph.add_node("explainer_agent", explainer_agent)

    # Linear edges
    graph.set_entry_point("data_agent")
    graph.add_edge("data_agent", "analyst_agent")
    graph.add_edge("analyst_agent", "recommendation_agent")
    graph.add_edge("recommendation_agent", "critic_agent")

    # Conditional edge — critic decides what happens next
    graph.add_conditional_edges(
        "critic_agent",
        route_critic,
        {
            "explainer_agent": "explainer_agent",
            "recommendation_agent": "recommendation_agent",
        },
    )

    graph.add_edge("explainer_agent", END)

    return graph.compile()


pipeline = build_pipeline()


async def run_pipeline(user_profile: UserProfile) -> MFAdvisorState:
    """Entry point called by FastAPI."""
    initial_state: MFAdvisorState = {
        "user_profile": user_profile,
        "fund_universe": [],
        "scored_funds": [],
        "recommended_funds": [],
        "explanation": {},
        "critic_feedback": [],
        "critic_approved": False,
        "critic_iterations": 0,
        "errors": [],
        "current_step": "init",
    }

    final_state = await pipeline.ainvoke(initial_state)
    return final_state