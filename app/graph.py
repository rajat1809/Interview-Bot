from langgraph.graph import StateGraph, END
from app.state import InterviewState
from app.nodes import main_agent_router, interviewer_agent, evaluation_agent
import streamlit as st

def should_continue(state: InterviewState):
    if state["interview_status"] == "finished":
        return "evaluation_agent"
    return END 

@st.cache_resource
def build_graph():
    """Build and compile the interview graph. Cached to avoid recompilation on every rerun."""
    workflow = StateGraph(InterviewState)
    workflow.add_node("main_agent", main_agent_router)
    workflow.add_node("interviewer_agent", interviewer_agent)
    workflow.add_node("evaluation_agent", evaluation_agent)

    workflow.set_entry_point("main_agent")
    workflow.add_edge("main_agent", "interviewer_agent")
    workflow.add_conditional_edges(
        "interviewer_agent",
        should_continue,
        {
            END: END, 
            "evaluation_agent": "evaluation_agent"
        }
    )
    workflow.add_edge("evaluation_agent", END)
    return workflow.compile()

app_graph = build_graph()