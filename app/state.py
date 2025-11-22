from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class InterviewState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    job_description: str
    candidate_details: str
    interview_role: Optional[str]
    interview_status: str
    num_questions_asked: int
    req_code_input: bool
    feedback_report: Optional[dict]
    detailed_evaluation: Optional[dict]