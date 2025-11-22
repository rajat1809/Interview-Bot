import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import app_graph

load_dotenv()

def test_question_counting():
    print("Testing Question Counting Logic...")
    
    # Turn 1: Start
    print("\n--- Turn 1: Start Interview ---")
    state1 = {
        "messages": [HumanMessage(content="Start the interview.")],
        "job_description": "Python Dev",
        "candidate_details": "5 years exp",
        "interview_role": None,
        "num_questions_asked": 0,
        "interview_status": "active"
    }
    
    events1 = list(app_graph.stream(state1))
    
    role = None
    q_count = 0
    ai_msg = ""
    
    for event in events1:
        for key, value in event.items():
            if key == "main_agent" and "interview_role" in value:
                role = value["interview_role"]
            if key == "interviewer_agent":
                if "num_questions_asked" in value:
                    q_count = value["num_questions_asked"]
                if "messages" in value:
                    ai_msg = value["messages"][-1].content
    
    print(f"After Turn 1: num_questions_asked = {q_count} (Expected: 0)")
    print(f"AI asked: {ai_msg[:50]}...")
    
    # Turn 2: User answers
    print("\n--- Turn 2: User Answers Q1 ---")
    state2 = {
        "messages": [
            HumanMessage(content="Start the interview."),
            AIMessage(content=ai_msg),
            HumanMessage(content="I have 5 years of Python experience.")
        ],
        "job_description": "Python Dev",
        "candidate_details": "5 years exp",
        "interview_role": role,
        "num_questions_asked": q_count,
        "interview_status": "active"
    }
    
    events2 = list(app_graph.stream(state2))
    
    for event in events2:
        for key, value in event.items():
            if key == "interviewer_agent":
                if "num_questions_asked" in value:
                    q_count = value["num_questions_asked"]
                if "messages" in value:
                    ai_msg = value["messages"][-1].content
    
    print(f"After Turn 2: num_questions_asked = {q_count} (Expected: 1)")
    print(f"AI asked: {ai_msg[:50]}...")
    
    if q_count == 1:
        print("\n✅ SUCCESS: Question counting is correct!")
    else:
        print(f"\n❌ FAIL: Expected 1 question, got {q_count}")

if __name__ == "__main__":
    test_question_counting()
