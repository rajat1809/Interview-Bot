from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from app.state import InterviewState
from app.prompts import ROUTER_SYSTEM_PROMPT, INTERVIEWER_SYSTEM_PROMPT, FEEDBACK_SYSTEM_PROMPT, EVALUATION_SYSTEM_PROMPT
from app.models import FeedbackScore, DetailedEvaluation
from dotenv import load_dotenv

load_dotenv()

# User claims gpt-5-nano is valid, so we keep it.
llm = ChatOpenAI(model="gpt-5-nano", temperature=0.7)

def main_agent_router(state: InterviewState):
    # If we already have a role, don't re-route or reset
    if state.get("interview_role"):
        return {"interview_role": state["interview_role"]}
        
    messages = [SystemMessage(content=ROUTER_SYSTEM_PROMPT)] + state['messages']
    response = llm.invoke(messages)
    return {"interview_role": response.content, "num_questions_asked": 0, "interview_status": "active"}

def interviewer_agent(state: InterviewState):
    if state.get("num_questions_asked", 0) >= 5:
        return {"interview_status": "finished"}

    system_prompt = INTERVIEWER_SYSTEM_PROMPT.format(
        role=state['interview_role'],
        jd=state['job_description'],
        candidate=state['candidate_details']
    )
    
    messages = [SystemMessage(content=system_prompt)] + state['messages']
    response = llm.invoke(messages)
    
    if "INTERVIEW_FINISHED" in response.content:
        return {"interview_status": "finished"}
        
    ask_for_code = "write code" in response.content.lower() or "code snippet" in response.content.lower()

    # Increment the question count since we just asked a question
    return {
        "messages": [response], 
        "num_questions_asked": state["num_questions_asked"] + 1,
        "req_code_input": ask_for_code
    }

def feedback_agent(state: InterviewState):
    structured_llm = llm.with_structured_output(FeedbackScore)
    messages = [SystemMessage(content=FEEDBACK_SYSTEM_PROMPT)] + state['messages']
    report = structured_llm.invoke(messages)
    return {"feedback_report": report.dict(), "interview_status": "completed"}

def evaluation_agent(state: InterviewState):
    """Generate detailed evaluation with ratings and recommendations"""
    structured_llm = llm.with_structured_output(DetailedEvaluation)
    messages = [SystemMessage(content=EVALUATION_SYSTEM_PROMPT)] + state['messages']
    evaluation = structured_llm.invoke(messages)
    return {"detailed_evaluation": evaluation.dict(), "interview_status": "completed"}