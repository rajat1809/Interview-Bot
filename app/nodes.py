from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from app.state import InterviewState
from app.prompts import (
    ROUTER_SYSTEM_PROMPT, 
    INTERVIEWER_SYSTEM_PROMPT, 
    INTERVIEWER_REACT_PROMPT,
    FEEDBACK_SYSTEM_PROMPT, 
    EVALUATION_SYSTEM_PROMPT
)
from app.models import FeedbackScore, DetailedEvaluation
from app.rag_utils import create_retrieval_tool
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
    """
    Interviewer agent that can use both JD and resume RAG tools.
    Uses function calling to decide when to retrieve context from either source.
    Falls back to simple LLM if no retrievers available.
    """
    if state.get("num_questions_asked", 0) >= 5:
        return {"interview_status": "finished"}

    # Check for retrievers
    jd_retriever = state.get("retriever")
    resume_retriever = state.get("resume_retriever")
    
    # Build list of available tools
    tools = []
    if jd_retriever:
        from app.rag_utils import create_retrieval_tool
        tools.append(create_retrieval_tool(jd_retriever))
    if resume_retriever:
        from app.rag_utils import create_resume_retrieval_tool
        tools.append(create_resume_retrieval_tool(resume_retriever))
    
    if tools:
        # Use LLM with tool calling for RAG
        llm_with_tools = llm.bind_tools(tools)
        
        # Create system prompt
        system_prompt = INTERVIEWER_REACT_PROMPT.format(
            role=state['interview_role'],
            candidate=state['candidate_details']
        )
        
        messages = [SystemMessage(content=system_prompt)] + state['messages']
        
        try:
            # First call - LLM decides if it needs to use tools
            response = llm_with_tools.invoke(messages)
            
            # Check if LLM wants to use tools
            if response.tool_calls:
                # Execute tool calls and collect context
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    # Find the matching tool
                    matching_tool = next((t for t in tools if t.name == tool_name), None)
                    if matching_tool:
                        query = tool_call['args'].get('query', '')
                        context = matching_tool.func(query)
                        # Add context to messages
                        messages.append(AIMessage(content=f"Retrieved context: {context}"))
                
                # Generate final response with context
                response = llm.invoke(messages)
            
            response_content = response.content
        except Exception as e:
            # Fallback to simple LLM if tool calling fails
            print(f"Tool calling error: {e}, falling back to simple LLM")
            system_prompt = INTERVIEWER_SYSTEM_PROMPT.format(
                role=state['interview_role'],
                jd=state['job_description'],
                candidate=state['candidate_details']
            )
            messages = [SystemMessage(content=system_prompt)] + state['messages']
            response = llm.invoke(messages)
            response_content = response.content
    else:
        # No PDFs uploaded, use simple LLM
        system_prompt = INTERVIEWER_SYSTEM_PROMPT.format(
            role=state['interview_role'],
            jd=state['job_description'],
            candidate=state['candidate_details']
        )
        messages = [SystemMessage(content=system_prompt)] + state['messages']
        response = llm.invoke(messages)
        response_content = response.content
    
    if "INTERVIEW_FINISHED" in response_content:
        return {"interview_status": "finished"}
        
    ask_for_code = "write code" in response_content.lower() or "code snippet" in response_content.lower()

    # Create AIMessage for response
    response_message = AIMessage(content=response_content)

    # Increment the question count since we just asked a question
    return {
        "messages": [response_message], 
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
